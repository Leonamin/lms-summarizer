import type { SettingsFieldsProps, SecretRenderer } from "./types";

export function AccountSettings({
  draft,
  change,
  isSaving,
  secret,
}: SettingsFieldsProps & { secret: SecretRenderer }) {
  return (
    <fieldset disabled={isSaving}>
      <legend>LMS 계정</legend>
      <p className="muted">
        과목 조회와 URL 다운로드에 사용합니다. 저장한 비밀번호는 다시 조회하지
        않습니다.
      </p>
      <div className="settings-grid">
        <label>
          학번
          <input
            value={draft.student_id}
            autoComplete="off"
            onChange={(event) => change("student_id", event.target.value)}
          />
        </label>
        {secret("lms_password", "LMS 비밀번호")}
      </div>
    </fieldset>
  );
}
