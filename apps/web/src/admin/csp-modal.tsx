"use client";

import * as Dialog from "@radix-ui/react-dialog";
import {
  type KeyboardEvent,
  type ReactElement,
  type ReactNode,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

const ADMIN_BACKGROUND = "[data-admin-background-root]";
const FOCUSABLE = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  '[tabindex]:not([tabindex="-1"])',
].join(",");

function focusableChildren(container: HTMLElement): HTMLElement[] {
  return Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(
    (element) =>
      !element.hidden &&
      element.getAttribute("aria-hidden") !== "true" &&
      element.getClientRects().length > 0,
  );
}

type ModalRender = (controls: { close: () => void }) => ReactNode;

export function CspModal({
  children,
  contentClassName = "site-switcher-dialog",
  description,
  title,
  trigger,
}: {
  children: ReactNode | ModalRender;
  contentClassName?: string;
  description: ReactNode;
  title: ReactNode;
  trigger: ReactElement;
}) {
  const [open, setOpen] = useState(false);
  const [contentElement, setContentElement] = useState<HTMLDivElement | null>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const restoreBackgroundRef = useRef<() => void>(() => undefined);
  const bindContent = useCallback((element: HTMLDivElement | null) => {
    contentRef.current = element;
    setContentElement(element);
  }, []);

  function restoreBackground() {
    restoreBackgroundRef.current();
    restoreBackgroundRef.current = () => undefined;
  }

  function changeOpen(next: boolean) {
    if (!next) restoreBackground();
    setOpen(next);
  }

  function focusFirst() {
    const content = contentElement;
    if (!content) return;
    (focusableChildren(content)[0] ?? content).focus();
  }

  useEffect(() => {
    if (!open) return;
    const content = contentRef.current;
    const background = document.querySelector<HTMLElement>(ADMIN_BACKGROUND);
    if (!content || !background) return;

    const hadInert = background.hasAttribute("inert");
    const priorInertAttribute = background.getAttribute("inert");
    const priorInert = background.inert;
    background.inert = true;
    const restore = () => {
      background.inert = priorInert;
      if (hadInert) background.setAttribute("inert", priorInertAttribute ?? "");
      else background.removeAttribute("inert");
    };
    restoreBackgroundRef.current = restore;

    const containFocus = (event: FocusEvent) => {
      if (!content.contains(event.target as Node)) focusFirst();
    };
    // Inert background controls reject focus, so browser pointer handling can
    // move activation to body without a later focusin event.
    const containPointer = () => {
      if (!content.contains(document.activeElement)) focusFirst();
    };
    document.addEventListener("focusin", containFocus);
    document.addEventListener("pointerup", containPointer);
    queueMicrotask(focusFirst);
    return () => {
      document.removeEventListener("focusin", containFocus);
      document.removeEventListener("pointerup", containPointer);
      restore();
      if (restoreBackgroundRef.current === restore) {
        restoreBackgroundRef.current = () => undefined;
      }
    };
  }, [contentElement, open]);

  function containTab(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key !== "Tab") return;
    const content = contentRef.current;
    if (!content) return;
    const focusable = focusableChildren(content);
    if (focusable.length === 0) {
      event.preventDefault();
      content.focus();
      return;
    }
    const first = focusable[0]!;
    const last = focusable.at(-1)!;
    const active = document.activeElement;
    if (event.shiftKey && (active === first || !content.contains(active))) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && (active === last || !content.contains(active))) {
      event.preventDefault();
      first.focus();
    }
  }

  const close = () => changeOpen(false);
  return (
    <Dialog.Root modal={false} open={open} onOpenChange={changeOpen}>
      <Dialog.Trigger asChild>{trigger}</Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay
          className="site-switcher-overlay"
          onPointerDown={(event) => event.preventDefault()}
        />
        <Dialog.Content
          aria-modal="true"
          className={contentClassName}
          onKeyDown={containTab}
          onInteractOutside={(event) => event.preventDefault()}
          onOpenAutoFocus={(event) => event.preventDefault()}
          ref={bindContent}
          tabIndex={-1}
        >
          <Dialog.Title>{title}</Dialog.Title>
          <Dialog.Description>{description}</Dialog.Description>
          {typeof children === "function" ? children({ close }) : children}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
