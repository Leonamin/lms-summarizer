import { useEffect, useId, useRef, useState } from "react";
import type { KeyboardEvent } from "react";

export type DropdownOption = {
  value: string;
  label: string;
  disabled?: boolean;
};

/**
 * Accessible listbox dropdown that replaces the native <select>.
 * Larger touch targets, keyboard navigation and type-ahead.
 */
export function Dropdown({
  value,
  onChange,
  options,
  ariaLabel,
  disabled = false,
  className = "",
  placeholder = "선택하세요",
}: {
  value: string;
  onChange: (value: string) => void;
  options: DropdownOption[];
  ariaLabel: string;
  disabled?: boolean;
  className?: string;
  placeholder?: string;
}) {
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const baseId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLUListElement>(null);
  const itemsRef = useRef<(HTMLLIElement | null)[]>([]);

  const selectedIndex = options.findIndex((option) => option.value === value);

  const firstEnabled = (from = 0, step = 1) => {
    for (let i = from; i >= 0 && i < options.length; i += step)
      if (!options[i].disabled) return i;
    return -1;
  };

  const close = (focusTrigger = true) => {
    setOpen(false);
    setActive(-1);
    if (focusTrigger) triggerRef.current?.focus();
  };

  const choose = (index: number) => {
    const option = options[index];
    if (!option || option.disabled) return;
    onChange(option.value);
    close();
  };

  // Close on outside pointer.
  useEffect(() => {
    if (!open) return;
    const onPointer = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) close(false);
    };
    document.addEventListener("mousedown", onPointer);
    return () => document.removeEventListener("mousedown", onPointer);
  }, [open]);

  // Move focus to the active option.
  useEffect(() => {
    if (!open || active < 0) return;
    const item = itemsRef.current[active];
    item?.focus();
    item?.scrollIntoView({ block: "nearest" });
  }, [open, active]);

  const openMenu = () => {
    setOpen(true);
    setActive(selectedIndex >= 0 ? selectedIndex : firstEnabled());
  };

  const onTriggerKeyDown = (event: KeyboardEvent) => {
    if (!["ArrowDown", "ArrowUp", "Enter", " "].includes(event.key)) return;
    event.preventDefault();
    openMenu();
  };

  const onMenuKeyDown = (event: KeyboardEvent) => {
    if (event.key === "Escape") {
      event.preventDefault();
      close();
      return;
    }
    if (event.key === "Tab") {
      event.preventDefault();
      close();
      return;
    }
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      if (active >= 0) choose(active);
      return;
    }
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      const step = event.key === "ArrowDown" ? 1 : -1;
      const next =
        active < 0
          ? firstEnabled()
          : firstEnabled(active + step, step) >= 0
            ? firstEnabled(active + step, step)
            : active;
      setActive(next);
      return;
    }
    if (event.key === "Home" || event.key === "End") {
      event.preventDefault();
      setActive(
        event.key === "Home"
          ? firstEnabled()
          : firstEnabled(options.length - 1, -1),
      );
      return;
    }
    // Type-ahead.
    if (event.key.length === 1) {
      const query = event.key.toLowerCase();
      const match = options.findIndex(
        (option, index) =>
          !option.disabled &&
          index !== active &&
          option.label.toLowerCase().startsWith(query),
      );
      if (match >= 0) setActive(match);
    }
  };

  const selectedLabel =
    selectedIndex >= 0 ? options[selectedIndex].label : placeholder;

  return (
    <div
      className={"dropdown" + (open ? " open" : "") + (className ? " " + className : "")}
      ref={rootRef}
    >
      <button
        type="button"
        ref={triggerRef}
        className="dropdown-trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={ariaLabel}
        aria-controls={open ? baseId + "-menu" : undefined}
        disabled={disabled}
        onClick={() => (open ? close() : openMenu())}
        onKeyDown={onTriggerKeyDown}
      >
        <span className="dropdown-value">{selectedLabel}</span>
        <span className="dropdown-caret" aria-hidden="true">
          ▾
        </span>
      </button>
      {open && (
        <ul
          id={baseId + "-menu"}
          role="listbox"
          aria-label={ariaLabel}
          className="dropdown-menu"
          ref={menuRef}
          onKeyDown={onMenuKeyDown}
        >
          {options.map((option, index) => (
            <li
              key={option.value}
              id={baseId + "-opt-" + index}
              role="option"
              aria-selected={option.value === value}
              aria-disabled={option.disabled || undefined}
              tabIndex={-1}
              ref={(node) => {
                itemsRef.current[index] = node;
              }}
              className={
                "dropdown-item" +
                (option.value === value ? " selected" : "") +
                (index === active ? " active" : "")
              }
              onMouseMove={() => !option.disabled && setActive(index)}
              onClick={() => choose(index)}
            >
              <span>{option.label}</span>
              {option.value === value && (
                <span className="dropdown-check" aria-hidden="true">
                  ✓
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
