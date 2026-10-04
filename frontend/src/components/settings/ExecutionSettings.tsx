import type { SettingsFieldsProps } from "./types";
import { Dropdown } from "../Dropdown";

export function ExecutionSettings({
  draft,
  change,
  isSaving,
}: SettingsFieldsProps) {
  return (
    <fieldset disabled={isSaving}>
      <legend>실행 · 보관</legend>
      <div className="settings-grid">
        <label>
          공급자 요청 제한 시간 (초)
          <input
            type="number"
            min={5}
            max={1800}
            value={draft.request_timeout ?? 120}
            onChange={(event) =>
              change("request_timeout", Number(event.target.value))
            }
          />
        </label>
        <label className="check">
          <input
            type="checkbox"
            checked={draft.keep_source}
            onChange={(event) => change("keep_source", event.target.checked)}
          />
          처리 후 원본 영상 저장
        </label>
        <label className="check">
          <input
            type="checkbox"
            checked={draft.keep_audio}
            onChange={(event) => change("keep_audio", event.target.checked)}
          />
          처리 후 변환 오디오 저장
        </label>
        <label>
          파일 이름 prefix
          <Dropdown
            value={draft.filename_scope ?? "lecture"}
            onChange={(value) => change("filename_scope", value)}
            ariaLabel="파일 이름 prefix 범위"
            options={[
              { value: "lecture", label: "강의명만" },
              { value: "week", label: "주차 + 강의명" },
              { value: "course", label: "과목 + 주차 + 강의명" },
            ]}
          />
        </label>
      </div>
      <p className="muted">
        원본 영상과 변환 오디오는 각 항목을 선택한 경우에만 보관하고, 선택하지
        않으면 처리 완료 후 서버에서 정리합니다. 다운로드 파일 이름은 선택한
        prefix 뒤에 역할(영상·음성·대본·요약·프롬프트)을 붙여 저장합니다.
        실패·취소·중단 입력은 재시도용으로 보존합니다. 원문·요약·프롬프트와 작업
        이력은 자동 삭제하지 않습니다. 파일은 서버 볼륨에 저장하며 이 기기로
        다운로드할 수 있습니다.
      </p>
    </fieldset>
  );
}
