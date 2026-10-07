import React, { createContext, useContext, useEffect, useState } from "react";

type SelectContextValue = { value?: string; open: boolean; setOpen: (open: boolean) => void; choose: (value: string) => void; labels: Record<string, string>; register: (value: string, label: string) => void };
const SelectContext = createContext<SelectContextValue | null>(null);
function useSelect() { const value = useContext(SelectContext); if (!value) throw new Error("Select component must be inside Select"); return value; }

export function Select({ value, onValueChange, children }: { value?: string; onValueChange?: (value: string) => void; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const [labels, setLabels] = useState<Record<string, string>>({});
  const register = (itemValue: string, label: string) => setLabels((current) => current[itemValue] === label ? current : { ...current, [itemValue]: label });
  const choose = (next: string) => { onValueChange?.(next); setOpen(false); };
  return <SelectContext.Provider value={{ value, open, setOpen, choose, labels, register }}><div className="select">{children}</div></SelectContext.Provider>;
}

export function SelectTrigger({ className = "", children }: React.HTMLAttributes<HTMLButtonElement>) { const { open, setOpen } = useSelect(); return <button type="button" className={`select-trigger ${className}`.trim()} aria-expanded={open} onClick={() => setOpen(!open)}>{children}<span aria-hidden="true">▾</span></button>; }
export function SelectValue({ placeholder = "Select" }: { placeholder?: string }) { const { value, labels } = useSelect(); return <span className="select-value">{value ? labels[value] ?? value : placeholder}</span>; }
export function SelectContent({ className = "", children }: React.HTMLAttributes<HTMLDivElement>) {
  const { open, setOpen } = useSelect();
  useEffect(() => {
    if (!open) return;
    const close = (event: MouseEvent) => { if (!(event.target as HTMLElement).closest(".select")) setOpen(false); };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open, setOpen]);
  return <div className={`select-content ${className}`.trim()} hidden={!open}>{children}</div>;
}
export function SelectItem({ value, children, className = "", disabled }: { value: string; children: React.ReactNode; className?: string; disabled?: boolean }) {
  const { value: selected, choose, register } = useSelect();
  const getText = (node: React.ReactNode): string => {
    if (typeof node === "string" || typeof node === "number") return String(node);
    if (Array.isArray(node)) return node.map(getText).join("");
    if (React.isValidElement<{ children?: React.ReactNode }>(node)) return getText(node.props.children);
    return "";
  };
  const label = getText(children);
  useEffect(() => register(value, label), [value, label]);
  return <button type="button" className={`select-item ${selected === value ? "select-item--selected" : ""} ${className}`.trim()} disabled={disabled} onClick={() => choose(value)}>{children}</button>;
}
export function SelectGroup({ children }: { children: React.ReactNode }) { return <>{children}</>; }
export function SelectLabel({ children }: { children: React.ReactNode }) { return <div className="select-label">{children}</div>; }
export function SelectSeparator() { return <hr className="select-separator" />; }
export function SelectScrollUpButton() { return null; }
export function SelectScrollDownButton() { return null; }
