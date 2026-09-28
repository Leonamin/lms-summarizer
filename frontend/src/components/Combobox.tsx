import { useEffect, useId, useRef, useState } from "react";
import type { KeyboardEvent } from "react";

export type ComboOption = { value: string; label: string };

/**
 * Editable combobox: free text input with a filtered suggestion listbox.
 * Used where a value can be typed or picked (e.g. model IDs).
 */
export function Combobox({
  value,
  onChange,
  options,
  ariaLabel,
  disabled = false,
  placeholder = "",
  className = "",
}: {
  value: string;
  onChange: (value: string) => void;
  options: ComboOption[];
  ariaLabel: string;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState<string | null>(null);
  const [active, setActive] = useState(-1);
  const baseId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const matchesFor = (text: string | null) =>
    options.filter(
      (option) =>
        !text ||
        option.label.toLowerCase().includes(text.toLowerCase()) ||
        option.value.toLowerCase().includes(text.toLowerCase()),
    );
  const filtered = matchesFor(query);

  const close = () => {
    setOpen(false);
    setQuery(null);
    setActive(-1);
  };

  const commit = (option: ComboOption) => {
    onChange(option.value);
    close();
    inputRef.current?.focus();
  };

  useEffect(() => {
    if (!open) return;
    const onPointer = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) close();
    };
    document.addEventListener("mousedown", onPointer);
    return () => document.removeEventListener("mousedown", onPointer);
  }, [open]);

  const onKeyDown = (event: KeyboardEvent) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (!open) {
        setOpen(true);
        setActive(0);
        return;
      }
      const step = event.key === "ArrowDown" ? 1 : -1;
      if (!filtered.length) return;
      setActive((current) => {
        const next = current < 0 ? 0 : current + step;
        return Math.max(0, Math.min(filtered.length - 1, next));
      });
      return;
    }
    if (event.key === "Enter") {
      if (open && active >= 0 && filtered[active]) {
        event.preventDefault();
        commit(filtered[active]);
      }
      return;
    }
    if (event.key === "Escape") {
      close();
      return;
    }
    if (event.key === "Tab") {
      close();
    }
  };

  return (
    <div
      className={"combobox" + (className ? " " + className : "")}
      ref={rootRef}
    >
      <input
        ref={inputRef}
        role="combobox"
        aria-expanded={open}
        aria-controls={open ? baseId + "-list" : undefined}
        aria-autocomplete="list"
        aria-activedescendant={
          open && active >= 0 ? baseId + "-opt-" + active : undefined
        }
        aria-label={ariaLabel}
        className="combobox-input"
        value={value}
        disabled={disabled}
        placeholder={placeholder}
        onChange={(event) => {
          const next = event.target.value;
          onChange(next);
          setQuery(next);
          setOpen(true);
          setActive(matchesFor(next).length ? 0 : -1);
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={onKeyDown}
      />
      <button
        type="button"
        className="combobox-toggle"
        aria-label={open ? "목록 닫기" : "목록 열기"}
        tabIndex={-1}
        disabled={disabled}
        onMouseDown={(event) => event.preventDefault()}
        onClick={() => {
          if (open) close();
          else {
            setOpen(true);
            setQuery(null);
            inputRef.current?.focus();
          }
        }}
      >
        <span className="dropdown-caret" aria-hidden="true">
          ▾
        </span>
      </button>
      {open && (
        <ul
          id={baseId + "-list"}
          role="listbox"
          aria-label={ariaLabel}
          className="dropdown-menu combobox-menu"
        >
          {filtered.length === 0 ? (
            <li className="combobox-empty">
              일치하는 모델이 없습니다. 입력한 값을 그대로 사용합니다.
            </li>
          ) : (
            filtered.map((option, index) => (
              <li
                key={option.value}
                id={baseId + "-opt-" + index}
                role="option"
                aria-selected={option.value === value}
                className={
                  "dropdown-item" +
                  (index === active ? " active" : "") +
                  (option.value === value ? " selected" : "")
                }
                onMouseMove={() => setActive(index)}
                onMouseDown={(event) => {
                  event.preventDefault();
                  commit(option);
                }}
              >
                <span>{option.label}</span>
                {option.value === value && (
                  <span className="dropdown-check" aria-hidden="true">
                    ✓
                  </span>
                )}
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}
