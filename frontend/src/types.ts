export interface Settings {
  ai_engine: string;
  ai_model: string;
  base_url: string;
  stt_engine: string;
  stt_model: string;
  stt_base_url: string;
  stt_compatible_model: string;
  stt_params: Record<string, unknown>;
  student_id: string;
  prompt_mode: string;
  summary_mode: string;
  subject_category: string;
  subject_custom: string;
  custom_prompt: string;
  keep_source: boolean;
  request_timeout: number;
  auto_detect_enabled: boolean;
  auto_detect_interval_minutes: number;
  auto_detect_courses: string;
  auto_save_scope: string;
}
export interface SettingsResponse {
  revision: number;
  settings_revision: string;
  settings: Settings;
  secrets: Record<string, { configured: boolean }>;
}
export interface Artifact {
  id: string;
  kind: string;
  display_name: string;
  size: number;
  state: string;
  attempt_id: string | null;
}
export interface Stage {
  stage: number;
  status: string;
  started_at: string | null;
  ended_at: string | null;
}
export interface Attempt {
  id: string;
  number: number;
  status: string;
  current_stage: number;
  stages: Stage[];
  error_code: string | null;
  safe_message: string | null;
  started_at: string | null;
  ended_at: string | null;
}
export interface Job {
  settings_revision_id: string;
  id: string;
  display_name: string;
  status: string;
  revision: number;
  created_at: string;
  initial_stage: number;
  end_stage: number;
  current_attempt_id: string;
  result_kind: string | null;
  retryable: boolean;
  attempts: Attempt[];
  artifacts: Artifact[];
}
export interface Upload {
  id: string;
  filename: string;
  status: string;
  artifact_id: string | null;
}

export interface Playback {
  id: string;
  title: string;
  status: string;
  attended: boolean;
  error_code: string | null;
  lecture_url: string;
  created_at: string;
}
