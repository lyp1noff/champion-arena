import React, { createContext, useContext, useEffect } from "react";
import { createPortal } from "react-dom";
import { useI18n } from "@/lib/i18n";

type DialogContextValue = { open: boolean; setOpen: (open: boolean) => void };
const DialogContext = createContext<DialogContextValue | null>(null);
function useDialog() {
  const value = useContext(DialogContext);
  if (!value) throw new Error("Dialog component must be inside Dialog");
  return value;
}

export function Dialog({ open, onOpenChange, children }: { open: boolean; onOpenChange: (open: boolean) => void; children: React.ReactNode }) {
  return <DialogContext.Provider value={{ open, setOpen: onOpenChange }}>{children}</DialogContext.Provider>;
}

export function DialogTrigger({ asChild, children }: { asChild?: boolean; children: React.ReactNode }) {
  const { setOpen } = useDialog();
  if (asChild && React.isValidElement(children)) {
    const child = children as React.ReactElement<{ onClick?: React.MouseEventHandler }>;
    return React.cloneElement(child, { onClick: (event: React.MouseEvent) => { child.props.onClick?.(event); if (!event.defaultPrevented) setOpen(true); } });
  }
  return <button type="button" onClick={() => setOpen(true)}>{children}</button>;
}

export function DialogContent({ className = "", children, showCloseButton = true }: { className?: string; children: React.ReactNode; showCloseButton?: boolean }) {
  const { open, setOpen } = useDialog();
  const { t } = useI18n();
  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => { if (event.key === "Escape") setOpen(false); };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, setOpen]);
  if (!open) return null;
  return createPortal(
    <div className="dialog-layer" role="presentation" onMouseDown={() => setOpen(false)}>
      <section className={`dialog-content ${className}`.trim()} role="dialog" aria-modal="true" onMouseDown={(event) => event.stopPropagation()}>
        {children}
        {showCloseButton && <button type="button" className="dialog-close" aria-label={t("common.close")} onClick={() => setOpen(false)}>×</button>}
      </section>
    </div>, document.body,
  );
}

export function DialogHeader({ className = "", ...props }: React.HTMLAttributes<HTMLDivElement>) { return <div className={`dialog-header ${className}`.trim()} {...props} />; }
export function DialogFooter({ className = "", ...props }: React.HTMLAttributes<HTMLDivElement>) { return <div className={`dialog-footer ${className}`.trim()} {...props} />; }
export function DialogTitle({ className = "", ...props }: React.HTMLAttributes<HTMLHeadingElement>) { return <h2 className={`dialog-title ${className}`.trim()} {...props} />; }
export function DialogDescription({ className = "", ...props }: React.HTMLAttributes<HTMLParagraphElement>) { return <p className={`dialog-description ${className}`.trim()} {...props} />; }
export function DialogClose({ children }: { children: React.ReactNode }) { const { setOpen } = useDialog(); return <button type="button" onClick={() => setOpen(false)}>{children}</button>; }
export function DialogOverlay() { return null; }
export function DialogPortal({ children }: { children: React.ReactNode }) { return <>{children}</>; }
