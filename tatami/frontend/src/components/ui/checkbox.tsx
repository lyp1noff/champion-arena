import React from "react";

type CheckboxProps = Omit<React.InputHTMLAttributes<HTMLInputElement>, "type" | "onChange"> & {
  onCheckedChange?: (checked: boolean) => void;
};

export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(function Checkbox(
  { className = "", onCheckedChange, ...props }, ref,
) {
  return <input ref={ref} type="checkbox" className={`checkbox ${className}`.trim()} onChange={(event) => onCheckedChange?.(event.currentTarget.checked)} {...props} />;
});
