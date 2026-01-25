"""Coaching conversation handler with tool-calling loop."""

import json
import uuid
from datetime import date
from typing import Any, AsyncGenerator, Optional

from trainy.database import Repository
from trainy.config import settings
from .tools import COACHING_TOOLS, WRITE_TOOLS, execute_tool
from .openrouter import chat_with_tools


COACHING_SYSTEM_PROMPT = """You are an expert endurance coach helping an athlete with their training.

You have access to tools that let you:
- Query their training data (activities, fitness metrics, pain history, wellness trends, power curve)
- View and manage their planned workouts

When the user asks questions about their training, use the appropriate tools to gather data before answering.
When they ask you to create or modify workouts, use the write tools to generate proposals.

Guidelines:
- Be conversational and supportive
- Use data to back up your recommendations
- Consider injury history and recovery status when planning
- Progress training gradually (no more than 10% weekly volume increase)
- Balance workout types appropriately (easy, tempo, intervals, long)
- Always explain your reasoning briefly

For workout creation:
- Easy runs: HR Zone 2, conversational pace
- Tempo runs: HR Zone 3-4, comfortably hard
- Intervals: HR Zone 4-5, with appropriate recovery
- Long runs: HR Zone 2, building aerobic base
- Recovery: Very easy or complete rest

Response formatting:
- Use markdown formatting for readability
- Use **bold** for emphasis and key metrics
- Use bullet points or numbered lists for multiple items
- Use headers (##) sparingly for major sections
- Keep responses concise but well-structured

Today's date is {today}."""


async def run_coaching_conversation(
    message: str,
    conversation_history: list[dict],
    repo: Repository,
    max_iterations: int = 5,
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

    # Collect proposals from write tools
    all_proposals: list[dict] = []
    all_deletions: list[dict] = []

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
                    "proposal_id": str(uuid.uuid4()),
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
                    all_proposals.extend(result["proposals"])
                if "deletion" in result:
                    all_deletions.append(result["deletion"])

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
            "proposal_id": str(uuid.uuid4()),
        }}
