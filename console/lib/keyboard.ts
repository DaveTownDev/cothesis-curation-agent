/** Review workspace keyboard shortcuts. */

export const SHORTCUTS = [
  { keys: "?", description: "Show / hide shortcut help" },
  { keys: "a", description: "Approve & publish (when checklist passes)" },
  { keys: "r", description: "Open reject form" },
  { keys: "b", description: "Send back to pipeline" },
  { keys: "j or →", description: "Next item in queue" },
  { keys: "k or ←", description: "Previous item in queue" },
  { keys: "Esc", description: "Close help / cancel form" },
] as const

export function isTypingTarget(target: EventTarget | null): boolean {
  if (!target || !(target instanceof HTMLElement)) return false
  const tag = target.tagName
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || target.isContentEditable
}
