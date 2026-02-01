// Activity types
export interface Activity {
  id: number
  fit_file_hash: string
  start_time: string
  end_time: string | null
  activity_type: string
  source: string | null
  duration_seconds: number
  distance_meters: number | null
  avg_speed_mps: number | null
  max_speed_mps: number | null
  total_ascent_m: number | null
  total_descent_m: number | null
  avg_hr: number | null
  max_hr: number | null
  avg_power: number | null
  max_power: number | null
  normalized_power: number | null
  avg_cadence: number | null
  calories: number | null
  title: string | null
  imported_at: string | null
  duration_formatted: string
  distance_km: number | null
}

export interface ActivityMetrics {
  activity_id: number
  tss: number | null
  tss_method: string | null
  intensity_factor: number | null
  efficiency_factor: number | null
  variability_index: number | null
  peak_power_5s: number | null
  peak_power_1min: number | null
  peak_power_5min: number | null
  peak_power_20min: number | null
  calculated_at: string | null
}

export interface ActivityWithMetrics {
  activity: Activity
  metrics: ActivityMetrics | null
}

// Metrics types
export interface CurrentMetrics {
  date: string
  ctl: number
  atl: number
  tsb: number
  tss_7day: number | null
  tss_30day: number | null
  tss_90day: number | null
  acwr: number | null
  monotony: number | null
  strain: number | null
  form_status: string
  form_color: string
  acwr_status: string
  acwr_color: string
}

export interface DailyMetricsItem {
  date: string
  total_tss: number
  activity_count: number
  total_duration_s: number
  total_distance_m: number
  ctl: number | null
  atl: number | null
  tsb: number | null
  acwr: number | null
  monotony: number | null
  strain: number | null
}

export interface DailyMetrics {
  start_date: string
  end_date: string
  items: DailyMetricsItem[]
}

export interface WeeklyTSSItem {
  week_start: string
  week_end: string
  total_tss: number
  activity_count: number
}

export interface WeeklyTSS {
  weeks: number
  items: WeeklyTSSItem[]
}

// Profile types
export interface Profile {
  id: number | null
  ftp: number
  lthr: number
  max_hr: number
  resting_hr: number
  threshold_pace_minkm: number
  swim_threshold_pace: number
  weight_kg: number
  effective_from: string
  metrics_dirty: boolean
}

export interface ProfileUpdate {
  ftp?: number
  lthr?: number
  max_hr?: number
  resting_hr?: number
  threshold_pace_minkm?: number
  swim_threshold_pace?: number
  weight_kg?: number
}

export interface MaxHRDetection {
  detected_max_hr: number | null
  sample_count: number
  confidence: 'high' | 'medium' | 'low' | 'none'
  message: string
}

// Calendar types
export interface CalendarActivity {
  id: number
  activity_type: string
  title: string | null
  duration_seconds: number
  distance_meters: number | null
  tss: number | null
  calories: number | null
}

export interface CalendarPlannedWorkout {
  id: number
  activity_type: string
  workout_type: string | null
  title: string
  description: string | null
  target_duration_s: number | null
  target_tss: number | null
  target_calories: number | null
  status: string
  completed_activity_id: number | null
}

export interface CalendarDay {
  date: string
  activities: CalendarActivity[]
  planned_workouts: CalendarPlannedWorkout[]
  total_tss: number
  activity_count: number
}

export interface CalendarMonth {
  year: number
  month: number
  days: CalendarDay[]
}

export interface CalendarDate {
  date: string
  activities: CalendarActivity[]
  planned_workouts: CalendarPlannedWorkout[]
  total_tss: number
}

// Planned workout types
export interface PlannedWorkout {
  id: number
  planned_date: string
  activity_type: string
  workout_type: string | null
  title: string
  description: string | null
  structured_workout: string | null
  target_duration_s: number | null
  target_distance_m: number | null
  target_tss: number | null
  target_calories: number | null
  target_hr_zone: number | null
  target_pace_minkm: number | null
  status: string
  completed_activity_id: number | null
  created_at: string | null
}

export interface GeneratedWorkoutsResponse {
  workouts: PlannedWorkout[]
  count: number
}

export interface UpcomingWorkoutsResponse {
  workouts: PlannedWorkout[]
  days: number
}

export interface DateWorkoutsResponse {
  date: string
  workouts: PlannedWorkout[]
}

// Common types
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  offset: number
  limit: number
  has_more: boolean
}

export interface SuccessResponse {
  success: boolean
  message: string | null
}

export interface ImportStatus {
  available: boolean
  file_count: number
  message: string
}

export interface ImportEvent {
  event: 'start' | 'import' | 'skip' | 'error' | 'complete'
  data: ImportStartData | ImportProgressData | ImportCompleteData | ImportErrorData
}

export interface ImportStartData {
  total: number
}

export interface ImportProgressData {
  file: string
  activity_type?: string
  date?: string
  tss?: number | null
  reason?: string
  progress: number
  total: number
}

export interface ImportCompleteData {
  imported: number
  skipped: number
  errors: number
  total: number
}

export interface ImportErrorData {
  file: string
  error: string
}

// Recalculate metrics types
export interface RecalculateStartData {
  total_activities: number
  total_days: number
}

export interface RecalculateProgressData {
  activity_id?: number
  activity_type?: string
  date: string | null
  progress: number
  total: number
  phase: 'activities' | 'daily'
}

export interface RecalculateCompleteData {
  activities_processed: number
  days_processed: number
}

// Conversational planning types
export interface ConversationMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ProposedWorkout {
  date: string
  activity_type: string
  workout_type: string | null
  title: string
  description: string | null
  target_duration_minutes: number
  target_tss: number | null
  target_calories: number | null
  existing_workout_id?: number | null  // Set if editing an existing workout
}

export interface WorkoutProposal {
  workouts: ProposedWorkout[]
  assistant_message: string
}

export interface GenerateStreamRequest {
  prompt: string
  conversation_history: ConversationMessage[]
}

export interface RefineStreamRequest {
  refinement: string
  current_proposal: ProposedWorkout[]
  conversation_history: ConversationMessage[]
}

export interface AcceptProposalRequest {
  workouts: ProposedWorkout[]
}

// SSE event types
export interface ThinkingEvent {
  phase: 'analyzing' | 'generating'
  message: string
}

export interface ProposalEvent {
  workouts: ProposedWorkout[]
  assistant_message: string
}

export interface QuestionEvent {
  message: string
  options?: string[]
}

export interface ErrorEvent {
  message: string
}

// Analytics types
export interface PowerCurvePoint {
  duration_seconds: number
  duration_label: string
  best_watts: number | null
  best_watts_per_kg: number | null
  activity_id: number | null
  activity_date: string | null
}

export interface PowerCurveResponse {
  start_date: string
  end_date: string
  weight_kg: number
  ftp: number
  eftp: number | null
  w_prime: number | null
  eftp_method: string
  points: PowerCurvePoint[]
}

// Data management types
export interface DataStats {
  activities: number
  planned_workouts: number
  activity_metrics: number
  daily_metrics: number
  workout_feedback: number
}

export interface DeleteResponse {
  success: boolean
  deleted: Record<string, number>
  message: string | null
}

// Wellness types
export interface UserSettings {
  id: number | null
  morning_checkin_enabled: boolean
  morning_sleep_quality_enabled: boolean
  morning_sleep_hours_enabled: boolean
  morning_muscle_soreness_enabled: boolean
  morning_energy_enabled: boolean
  morning_mood_enabled: boolean
  post_workout_feedback_enabled: boolean
  post_workout_rpe_enabled: boolean
  post_workout_pain_enabled: boolean
  post_workout_session_feel_enabled: boolean
  post_workout_notes_enabled: boolean
}

export interface UserSettingsUpdate {
  morning_checkin_enabled?: boolean
  morning_sleep_quality_enabled?: boolean
  morning_sleep_hours_enabled?: boolean
  morning_muscle_soreness_enabled?: boolean
  morning_energy_enabled?: boolean
  morning_mood_enabled?: boolean
  post_workout_feedback_enabled?: boolean
  post_workout_rpe_enabled?: boolean
  post_workout_pain_enabled?: boolean
  post_workout_session_feel_enabled?: boolean
  post_workout_notes_enabled?: boolean
}

export interface MorningCheckin {
  id: number | null
  checkin_date: string
  sleep_quality: number | null
  sleep_hours: number | null
  muscle_soreness: number | null
  energy_level: number | null
  mood: number | null
  notes: string | null
  created_at: string | null
}

export interface MorningCheckinRequest {
  checkin_date: string
  sleep_quality?: number | null
  sleep_hours?: number | null
  muscle_soreness?: number | null
  energy_level?: number | null
  mood?: number | null
  notes?: string | null
}

export interface PendingActivityItem {
  id: number
  activity_type: string
  title: string | null
  start_time: string
  duration_seconds: number
  distance_meters: number | null
}

export interface PendingFeedback {
  activities: PendingActivityItem[]
  morning_checkin_pending: boolean
  total_count: number
}

export interface ActivityFeedback {
  id: number | null
  activity_id: number
  rpe: number | null
  comfort_level: number | null
  has_pain: boolean
  pain_location: string | null
  pain_severity: number | null
  notes: string | null
  created_at: string | null
}

export interface ActivityFeedbackRequest {
  rpe?: number | null
  comfort_level?: number | null
  has_pain?: boolean
  pain_location?: string | null
  pain_severity?: number | null
  notes?: string | null
}

// Injury Analysis types
export interface PainEvent {
  date: string
  pain_location: string | null
  pain_severity: number | null
  activity_type: string
  activity_id: number
  activity_title: string | null
}

export interface PainLocationSummary {
  location: string | null
  count: number
  avg_severity: number | null
  max_severity: number | null
}

export interface PainActivitySummary {
  activity_type: string
  count: number
  avg_severity: number | null
}

export interface InjuryAnalysisResponse {
  start_date: string
  end_date: string
  total_pain_events: number
  pain_events: PainEvent[]
  by_location: PainLocationSummary[]
  by_activity: PainActivitySummary[]
}

export interface PainLocationCount {
  location: string
  count: number
}

export interface MergePainLocationsRequest {
  source_locations: string[]
  target_location: string
}

export interface MergePainLocationsResponse {
  updated_count: number
}

// Projection types
export interface ProjectedDataPoint {
  date: string
  ctlProjected: number
  atlProjected: number
  tsbProjected: number
  plannedTss: number
  isRestDay: boolean
}

// Track/GPS types
export interface TrackPoint {
  lat: number
  lng: number
}

export interface ActivityTrackResponse {
  activity_id: number
  has_track: boolean
  points: TrackPoint[]
}

// Activity streams types
export interface ActivityStreams {
  activity_id: number
  timestamps: number[]
  heart_rate: (number | null)[] | null
  power: (number | null)[] | null
  cadence: (number | null)[] | null
  speed: (number | null)[] | null
  elevation: (number | null)[] | null
  distance: number[]
  position: (TrackPoint | null)[] | null
}

// Coaching chat types
export interface ToolCallInfo {
  tool_name: string
  arguments: Record<string, unknown>
}

export interface ToolResultInfo {
  tool_name: string
  result: Record<string, unknown>
  summary: string
}

export interface CoachingMessage {
  role: 'user' | 'assistant'
  content: string
  toolCalls?: ToolCallInfo[]
  toolResults?: ToolResultInfo[]
}

export interface WorkoutProposalItem {
  date: string
  activity_type: string
  workout_type: string | null
  title: string
  description: string | null
  target_duration_minutes: number
  target_tss: number | null
  target_calories: number | null
  existing_workout_id: number | null
}

export interface WorkoutDeletionItem {
  workout_id: number
  title: string
  date: string
}

export interface CoachingProposal {
  proposal_id: string
  workouts: WorkoutProposalItem[]
  deletions: WorkoutDeletionItem[]
}

// Coaching SSE event types
export interface CoachingThinkingEvent {
  message: string
}

export interface CoachingToolCallEvent {
  tool_name: string
  arguments: Record<string, unknown>
}

export interface CoachingToolResultEvent {
  tool_name: string
  result: Record<string, unknown>
  summary: string
}

export interface CoachingTextEvent {
  content: string
}

export interface CoachingProposalEvent {
  workouts: WorkoutProposalItem[]
  deletions: WorkoutDeletionItem[]
  proposal_id: string
}

export interface CoachingErrorEvent {
  message: string
}

export interface AcceptCoachingProposalResponse {
  created_ids: number[]
  updated_ids: number[]
  deleted_ids: number[]
  message: string
}

// Rowing PRs types
export interface RowingDistancePR {
  distance_meters: number
  distance_label: string
  total_seconds: number | null
  split_seconds: number | null
  activity_id: number | null
  activity_date: string | null
}

export interface RowingPowerPR {
  duration_seconds: number
  duration_label: string
  best_watts: number | null
  activity_id: number | null
  activity_date: string | null
}

export interface RowingTimePR {
  duration_seconds: number
  duration_label: string
  best_distance_meters: number | null
  split_seconds: number | null
  activity_id: number | null
  activity_date: string | null
}

export interface RowingPRsResponse {
  distance_prs: RowingDistancePR[]
  time_prs: RowingTimePR[]
  power_prs: RowingPowerPR[]
}
