import type { PuckData } from "./puck-adapter";

/** Puck's public selector shape for the currently selected component. */
export interface PuckItemSelector {
  readonly index: number;
  readonly zone?: string;
}

/** The public Puck action used for an in-zone sibling reorder. */
export interface PuckReorderAction {
  readonly type: "reorder";
  readonly sourceIndex: number;
  readonly destinationIndex: number;
  readonly destinationZone: string;
  readonly recordHistory: true;
}

/** Puck's public selection-only action; it must never add history. */
export interface PuckSelectionAction {
  readonly type: "setUi";
  readonly ui: {
    readonly itemSelector: {
      readonly index: number;
      readonly zone: string;
    };
  };
  readonly recordHistory: false;
}

export interface PuckReorderPlan {
  readonly reorder: PuckReorderAction;
  readonly selection: PuckSelectionAction;
  readonly actions: readonly [PuckReorderAction, PuckSelectionAction];
}

export interface PuckSiblingReorderActions {
  readonly zone: string | null;
  readonly sourceIndex: number | null;
  readonly siblingCount: number;
  readonly moveUp: PuckReorderPlan | null;
  readonly moveDown: PuckReorderPlan | null;
}

export const PUCK_ROOT_ZONE = "root:default-zone";

const unavailable = (): PuckSiblingReorderActions => ({
  zone: null,
  sourceIndex: null,
  siblingCount: 0,
  moveUp: null,
  moveDown: null,
});

/**
 * Derive general sibling actions from Puck's selected-item selector and data.
 * The helper never chooses a component or zone and fails closed for stale or
 * unresolvable selectors.
 */
export function derivePuckSiblingReorderActions(
  data: Pick<PuckData, "content" | "zones">,
  selector: PuckItemSelector | null | undefined,
): PuckSiblingReorderActions {
  if (!selector || !Number.isInteger(selector.index) || selector.index < 0) {
    return unavailable();
  }

  const zone = selector.zone ?? PUCK_ROOT_ZONE;
  const siblings = zone === PUCK_ROOT_ZONE ? data.content : data.zones?.[zone];
  if (!Array.isArray(siblings) || selector.index >= siblings.length) {
    return unavailable();
  }

  const makePlan = (destinationIndex: number): PuckReorderPlan => {
    const reorder: PuckReorderAction = {
      type: "reorder",
      sourceIndex: selector.index,
      destinationIndex,
      destinationZone: zone,
      recordHistory: true,
    };
    const selection: PuckSelectionAction = {
      type: "setUi",
      ui: { itemSelector: { index: destinationIndex, zone } },
      recordHistory: false,
    };
    return { reorder, selection, actions: [reorder, selection] };
  };

  return {
    zone,
    sourceIndex: selector.index,
    siblingCount: siblings.length,
    moveUp: selector.index > 0 ? makePlan(selector.index - 1) : null,
    moveDown:
      selector.index < siblings.length - 1 ? makePlan(selector.index + 1) : null,
  };
}
