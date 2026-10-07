import React from "react";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
  size?: "default" | "sm" | "lg" | "icon";
  asChild?: boolean;
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className = "", variant = "default", size = "default", asChild = false, children, ...props }, ref,
) {
  const classes = `button button--${variant} button--${size} ${className}`.trim();
  if (asChild && React.isValidElement(children)) {
    const child = children as React.ReactElement<{ className?: string }>;
    return React.cloneElement(child, { ...props, className: `${classes} ${child.props.className ?? ""}`.trim() });
  }
  return <button ref={ref} className={classes} {...props}>{children}</button>;
});
