import { useEffect, useState } from "react";
import { api } from "../api";
import type { SettingsResponse } from "../types";

export function SecretField({
  name,
  label,
  settings,
  onChange,
  report,
  disabled,
  onBusy,
}: {
  name: string;
  label: string;
  settings: SettingsResponse;
  onChange: (settings: SettingsResponse) => void;
  report: (cause: unknown) => void;
  disabled: boolean;
  onBusy: (busy: boolean) => void;
}) {
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [show, setShow] = useState(false);
  useEffect(() => {
    setValue("");
    setShow(false);
  }, [name]);

  async function change(remove = false) {
    setBusy(true);
    onBusy(true);
    try {
      await api("/secrets/" + encodeURIComponent(name), {
        method: remove ? "DELETE" : "PUT",
        ...(remove ? {} : { body: JSON.stringify({ value }) }),
      });
      setValue("");
      onChange(await api<SettingsResponse>("/settings"));
    } catch (cause) {
      report(cause);
    } finally {
      setBusy(false);
      onBusy(false);
    }
  }

  return (
    <div className="secret-field">
      <label>
        {label}{" "}
        <span className="muted">
          {settings.secrets[name]?.configured ? "저장됨 · 입력하면 교체" : "미설정"}
        </span>
        <input
          type={show ? "text" : "password"}
          autoComplete="new-password"
          value={value}
          disabled={disabled || busy}
          onChange={(event) => setValue(event.target.value)}
        />
      </label>
      <div className="secret-actions">
        <label className="check">
          <input
            type="checkbox"
            checked={show}
            onChange={(event) => setShow(event.target.checked)}
          />
          입력 값 보기
        </label>
        <button
          type="button"
          className="ghost"
          disabled={disabled || busy || !value.trim()}
          onClick={() => void change()}
        >
          저장·교체
        </button>
        <button
          type="button"
          className="button-danger"
          disabled={disabled || busy || !settings.secrets[name]?.configured}
          onClick={() => void change(true)}
        >
          삭제
        </button>
      </div>
    </div>
  );
}
