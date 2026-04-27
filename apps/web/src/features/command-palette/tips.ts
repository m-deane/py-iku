/**
 * Idle-state pro-tips shown in the empty palette as a 4-second carousel.
 *
 * The palette pauses rotation while the user is interacting (typing, focused
 * input, hovering) and resumes once the input is empty + idle for a beat.
 * Keep this list short — the carousel feels stale once it loops back to the
 * first tip the user has already seen.
 */
export interface PaletteTip {
  id: string;
  label: string;
}

export const PALETTE_TIPS: readonly PaletteTip[] = [
  { id: "tab-sections", label: "Tab to switch sections" },
  { id: "pin", label: "Cmd+P to pin a result for next time" },
  { id: "jump", label: "Cmd+1..6 to jump straight into a section" },
  { id: "args", label: "Pick Convert and press ↵ to choose mode + provider" },
  { id: "shortcuts", label: "Press ? to see every keyboard shortcut" },
];

export const TIP_ROTATE_MS = 4000;
