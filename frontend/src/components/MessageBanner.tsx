export function MessageBanner({
  error,
  notice,
  onDismiss,
}: {
  error: string;
  notice: string;
  onDismiss: (kind: "error" | "notice") => void;
}) {
  return (
    <>
      {error && (
        <div role="alert" className="message error">
          {error}
          <button aria-label="오류 닫기" onClick={() => onDismiss("error")}>
            ×
          </button>
        </div>
      )}
      {notice && (
        <div role="status" className="message notice">
          {notice}
          <button aria-label="안내 닫기" onClick={() => onDismiss("notice")}>
            ×
          </button>
        </div>
      )}
    </>
  );
}
