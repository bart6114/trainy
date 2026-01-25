"""Coaching conversation handler with tool-calling loop."""

import json
import uuid
from datetime import date
from typing import Any, AsyncGenerator, Optional

from trainy.database import Repository
from trainy.config import settings
from .tools import COACHING_TOOLS, WRITE_TOOLS, execute_tool
from .openrouter import chat_with_tools


COACHING_SYSTEM_PROMPT = """You are an expert endurance coach. Be brief and direct - no fluff.

Tools available:
- Query training data (activities, fitness, pain history, wellness, power curve)
- View and manage planned workouts

Guidelines:
- Use data to back up recommendations
- Consider injury history and recovery when planning
- Max 10% weekly volume increase
- Balance workout types (easy, tempo, intervals, long)

Workout zones:
- Easy: HR Zone 2, conversational
- Tempo: HR Zone 3-4, comfortably hard
- Intervals: HR Zone 4-5, with recovery
- Long: HR Zone 2, aerobic base

Response style:
- SHORT and to the point - 1-3 sentences max for simple questions
- Use bullet points for lists
- Bold key metrics only
- Skip pleasantries and filler words

Workout titles:
- Use descriptive names like "Easy Run", "Tempo Intervals", "Long Ride"
- Do NOT add day numbers like "Day 1/7" or "Week 1 Day 3"
- Do NOT add dates in titles - the date field handles that

Today's date is {today}."""


async def run_coaching_conversation(
    message: str,
    conversation_history: list[dict],
    repo: Repository,
    max_iterations: int = 5,
    current_proposal: Optional[dict] = None,
) -> AsyncGenerator[dict, None]:
    """Run a coaching conversation with tool-calling loop.

    Yields SSE events:
    - thinking: {message: str}
    - tool_call: {tool_name: str, arguments: dict}
    - tool_result: {tool_name: str, result: dict, summary: str}
    - text: {content: str}
    - proposal: {workouts: list, deletions: list}
    - error: {message: str}
    """
    if not settings.has_openrouter_key:
        yield {"event": "error", "data": {"message": "OpenRouter API key not configured"}}
        return

    # Build messages with system prompt
    system_prompt = COACHING_SYSTEM_PROMPT.format(today=date.today().isoformat())
    messages = [{"role": "system", "content": system_prompt}]

    # Add conversation history
    for msg in conversation_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Add current user message
    messages.append({"role": "user", "content": message})

    # Initialize proposals from current state (for iterative refinement)
    all_proposals: list[dict] = []
    all_deletions: list[dict] = []
    proposal_id = str(uuid.uuid4())

    if current_proposal:
        all_proposals = list(current_proposal.get("workouts", []))
        all_deletions = list(current_proposal.get("deletions", []))
        proposal_id = current_proposal.get("proposal_id", proposal_id)

    # Tool-calling loop
    for iteration in range(max_iterations):
        yield {"event": "thinking", "data": {"message": "Thinking..." if iteration == 0 else "Processing..."}}

        # Call LLM with tools
        response = await chat_with_tools(messages, COACHING_TOOLS)

        if response is None:
            yield {"event": "error", "data": {"message": "Failed to get response from AI"}}
            return

        # Check for errors
        if "error" in response:
            yield {"event": "error", "data": {"message": response["error"]}}
            return

        # Extract the assistant message
        assistant_message = response.get("message", {})
        tool_calls = assistant_message.get("tool_calls", [])
        content = assistant_message.get("content", "")
        finish_reason = response.get("finish_reason", "")

        # If no tool calls and we have content, we're done
        if not tool_calls:
            if content:
                yield {"event": "text", "data": {"content": content}}

            # If we collected proposals, emit them
            if all_proposals or all_deletions:
                yield {"event": "proposal", "data": {
                    "workouts": all_proposals,
                    "deletions": all_deletions,
                    "proposal_id": proposal_id,
                }}
            return

        # Add assistant message to history for context
        messages.append(assistant_message)

        # Process tool calls
        tool_results = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("function", {}).get("name", "")
            arguments_str = tool_call.get("function", {}).get("arguments", "{}")
            tool_call_id = tool_call.get("id", "")

            try:
                arguments = json.loads(arguments_str) if arguments_str else {}
            except json.JSONDecodeError:
                arguments = {}

            # Emit tool call event
            yield {"event": "tool_call", "data": {"tool_name": tool_name, "arguments": arguments}}

            # Execute the tool
            result = execute_tool(tool_name, repo, arguments)

            # Emit tool result event
            yield {"event": "tool_result", "data": {
                "tool_name": tool_name,
                "result": result,
                "summary": result.get("summary", ""),
            }}

            # Collect proposals from write tools
            if tool_name in WRITE_TOOLS:
                if "proposals" in result:
                    if tool_name == "create_workouts":
                        # create_workouts replaces entire proposal (new schedule)
                        all_proposals = list(result["proposals"])
                    else:
                        # modify_workout merges by existing_workout_id
                        for new_workout in result["proposals"]:
                            existing_id = new_workout.get("existing_workout_id")
                            if existing_id:
                                # Replace the workout being modified
                                replaced = False
                                for i, existing in enumerate(all_proposals):
                                    if existing.get("existing_workout_id") == existing_id:
                                        all_proposals[i] = new_workout
                                        replaced = True
                                        break
                                if not replaced:
                                    all_proposals.append(new_workout)
                            else:
                                all_proposals.append(new_workout)
                if "deletion" in result:
                    deletion = result["deletion"]
                    # Don't add duplicate deletions
                    if not any(d["workout_id"] == deletion["workout_id"] for d in all_deletions):
                        all_deletions.append(deletion)
                    # Remove from proposals if we're deleting it
                    all_proposals = [p for p in all_proposals
                                   if p.get("existing_workout_id") != deletion["workout_id"]]

            # Add tool result to messages
            tool_results.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": json.dumps(result),
            })

        # Add all tool results to messages
        messages.extend(tool_results)

    # If we hit max iterations, return what we have
    yield {"event": "text", "data": {"content": "I've gathered the information. Let me know if you need anything else."}}

    if all_proposals or all_deletions:
        yield {"event": "proposal", "data": {
            "workouts": all_proposals,
            "deletions": all_deletions,
            "proposal_id": proposal_id,
        }}
