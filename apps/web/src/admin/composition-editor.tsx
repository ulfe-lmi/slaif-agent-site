"use client";

import { DropZone, Puck, type Config, type Data } from "@measured/puck";
import {
  COMPONENT_CATALOG,
  COMPONENT_TYPES,
  type ComponentDefinition,
} from "@slaif-agent-site/component-catalog";
import {
  compositionToPuck,
  puckToComposition,
  type NormalizedCompositionNode,
  type PuckComponentConfig,
  type PuckData,
  type PuckNodeMetadata,
} from "@slaif-agent-site/composition-schema";
import { useEffect, useRef, useState } from "react";

import { renderComponent } from "../renderer/components";
import { Button, Card, StatusPanel } from "../components/ui/primitives";
import {
  addCompositionNode,
  deleteCompositionNode,
  loadAuthority,
  loadComposition,
  moveCompositionNode,
  updateCompositionNode,
  type CurrentAuthority,
} from "./api";

const ALLOWED_TYPES = [...COMPONENT_TYPES];

function fieldFor(
  definition: ComponentDefinition,
  name: string,
): PuckComponentConfig["fields"][string] {
  const prop = definition.propsSchema[name];
  if (!prop) return { type: "text", label: name };
  if (prop.type === "enum") {
    return {
      type: "select",
      label: name,
      options: [...(prop.enumValues ?? [])],
    };
  }
  if (prop.type === "number") {
    const field: PuckComponentConfig["fields"][string] = {
      type: "number",
      label: name,
    };
    if (prop.bounded?.min !== undefined) field.min = prop.bounded.min;
    if (prop.bounded?.max !== undefined) field.max = prop.bounded.max;
    return field;
  }
  if (prop.type === "boolean") return { type: "checkbox", label: name };
  if (prop.type === "object" || prop.type === "array") {
    return { type: "textarea", label: `${name} (JSON)` };
  }
  return { type: "text", label: name };
}

function trustedPuckComponent(
  definition: ComponentDefinition,
  props: Record<string, unknown>,
) {
  const { id: _id, ...componentProps } = props;
  void _id;
  const zones = definition.allowedSlots.map((slot) => (
    <DropZone
      key={slot}
      zone={slot}
      allow={ALLOWED_TYPES}
      className="puck-trusted-zone"
    />
  ));
  const rendered = renderComponent(
    { componentType: definition.type, props: componentProps, children: zones },
    "en",
  ) ?? (
    <div className="puck-trusted-fallback">
      <strong>{definition.type}</strong>
      {zones}
    </div>
  );
  return (
    <div data-puck-component={definition.type} className="puck-trusted-component">
      {rendered}
    </div>
  );
}

const PUCK_CONFIG = {
  components: Object.fromEntries(
    COMPONENT_CATALOG.map((definition) => [
      definition.type,
      {
        label: definition.type,
        fields: Object.fromEntries(
          Object.keys(definition.propsSchema).map((name) => [
            name,
            fieldFor(definition, name),
          ]),
        ),
        render: (props: Record<string, unknown>) =>
          trustedPuckComponent(definition, props),
      },
    ]),
  ),
} as Config;

function editorMessage(reason: unknown): string {
  const code = reason instanceof Error ? reason.message : "";
  if (code === "unauthenticated") return "Your session ended. Sign in and try again.";
  if (code === "denied" || code === "not-found")
    return "This page is unavailable or you do not have editing authority.";
  if (code === "conflict")
    return "The composition changed. Reload before saving again.";
  if (code === "invalid")
    return "The server rejected this composition. No change was assumed.";
  if (code === "unavailable") return "The editor service is temporarily unavailable.";
  return "The composition could not be saved. No change was assumed.";
}

function sameJson(left: unknown, right: unknown): boolean {
  return JSON.stringify(left) === JSON.stringify(right);
}

function moveFirstRootComponent(data: PuckData): PuckData {
  const [first, second] = data.content;
  if (!first || !second) return data;
  return {
    ...data,
    content: [second, first, ...data.content.slice(2)],
  };
}

function depth(
  node: NormalizedCompositionNode,
  byId: Map<string, NormalizedCompositionNode>,
): number {
  let current = node;
  let value = 0;
  const seen = new Set<string>();
  while (current.parentId) {
    if (seen.has(current.id)) throw new Error("composition-cycle");
    seen.add(current.id);
    const parent = byId.get(current.parentId);
    if (!parent) throw new Error("composition-parent-missing");
    current = parent;
    value += 1;
  }
  return value;
}

async function reconcileComposition(
  siteId: string,
  pageId: string,
  before: readonly NormalizedCompositionNode[],
  after: readonly NormalizedCompositionNode[],
): Promise<void> {
  const beforeById = new Map(before.map((node) => [node.id, node]));
  const createdIds = new Map<string, string>();
  const resolveId = (id: string | null) => (id ? (createdIds.get(id) ?? id) : null);
  const afterById = new Map(after.map((node) => [node.id, node]));

  for (const node of [...before]
    .filter((item) => !afterById.has(item.id))
    .sort((left, right) => depth(right, beforeById) - depth(left, beforeById))) {
    await deleteCompositionNode(siteId, pageId, node.id);
  }

  const additions = after.filter((node) => !beforeById.has(node.id));
  const remaining = new Map(additions.map((node) => [node.id, node]));
  while (remaining.size) {
    let progressed = false;
    for (const [temporaryId, node] of [...remaining]) {
      const parentId = resolveId(node.parentId);
      if (
        node.parentId &&
        !createdIds.has(node.parentId) &&
        !beforeById.has(node.parentId)
      )
        continue;
      const created = await addCompositionNode(siteId, pageId, {
        ...node,
        parentId,
      });
      createdIds.set(temporaryId, created.id);
      remaining.delete(temporaryId);
      progressed = true;
    }
    if (!progressed) throw new Error("composition-parent-missing");
  }

  for (const node of after.filter((item) => beforeById.has(item.id))) {
    const previous = beforeById.get(node.id);
    if (!previous) continue;
    if (!sameJson(previous.props, node.props)) {
      await updateCompositionNode(siteId, pageId, node.id, node.props);
    }
    if (
      previous.parentId !== node.parentId ||
      previous.slotKey !== node.slotKey ||
      previous.orderKey !== node.orderKey
    ) {
      await moveCompositionNode(
        siteId,
        pageId,
        node.id,
        resolveId(node.parentId),
        node.slotKey,
        node.orderKey,
      );
    }
  }
}

export function CompositionEditor({
  siteId,
  pageId,
}: {
  siteId: string;
  pageId: string;
}) {
  const [authority, setAuthority] = useState<CurrentAuthority | null>(null);
  const [nodes, setNodes] = useState<NormalizedCompositionNode[] | null>(null);
  const [data, setData] = useState<PuckData | null>(null);
  const [puckRenderKey, setPuckRenderKey] = useState(0);
  const metadata = useRef<Record<string, PuckNodeMetadata>>({});
  const latestData = useRef<Data | null>(null);
  const pending = useRef(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  async function refresh() {
    const [loadedAuthority, loadedNodes] = await Promise.all([
      loadAuthority(siteId),
      loadComposition(siteId, pageId),
    ]);
    setAuthority(loadedAuthority);
    setNodes(loadedNodes);
    const converted = compositionToPuck(loadedNodes);
    metadata.current = converted.metadata ?? {};
    latestData.current = converted;
    setData(converted);
    setPuckRenderKey((key) => key + 1);
  }

  useEffect(() => {
    void refresh().catch((reason: unknown) => setError(editorMessage(reason)));
  }, [siteId, pageId]);

  async function publish(nextData: Data) {
    if (pending.current || !nodes) return;
    pending.current = true;
    setError("");
    setNotice("");
    try {
      const nextNodes = [...puckToComposition(nextData, metadata.current)];
      await reconcileComposition(siteId, pageId, nodes, nextNodes);
      await refresh();
      setNotice("Composition saved and reloaded from the server.");
    } catch (reason) {
      setError(editorMessage(reason));
    } finally {
      pending.current = false;
    }
  }

  if (error && !data) return <StatusPanel>{error}</StatusPanel>;
  if (!authority || !data || !nodes)
    return <p>Loading the trusted composition editor…</p>;
  const required = [
    "composition:read",
    "component-structure:create",
    "component-content-props:write",
    "component-structure:move",
    "component-structure:delete",
  ];
  const authorized =
    authority.platform_administrator ||
    required.every((permission) =>
      authority.effective_permissions.includes(permission),
    );
  if (!authorized)
    return <StatusPanel>Editing authority is required for this page.</StatusPanel>;

  return (
    <section className="composition-editor" aria-labelledby="composition-editor-title">
      <div className="composition-editor__intro">
        <div>
          <p className="eyebrow">Trusted visual editor</p>
          <h1 id="composition-editor-title">Page composition</h1>
          <p>Changes are validated and saved through the human Editor API.</p>
        </div>
        <Button
          type="button"
          onClick={() => {
            if (latestData.current) void publish(latestData.current);
          }}
          disabled={pending.current}
        >
          Save composition
        </Button>
        <Button type="button" onClick={() => void refresh()} disabled={pending.current}>
          Reload server state
        </Button>
      </div>
      {notice && <StatusPanel>{notice}</StatusPanel>}
      {error && <StatusPanel>{error}</StatusPanel>}
      <Card>
        <Puck
          key={puckRenderKey}
          config={PUCK_CONFIG}
          data={data as Data}
          permissions={{
            drag: true,
            edit: true,
            delete: true,
            duplicate: true,
            insert: true,
          }}
          onChange={(next) => {
            latestData.current = next as Data;
          }}
          renderHeaderActions={({ state }) => {
            const hasMultipleRootComponents = state.data.content.length > 1;
            return (
              <button
                type="button"
                data-testid="puck-action:move-first-down"
                disabled={!hasMultipleRootComponents}
                onClick={() => {
                  const nextData = moveFirstRootComponent(state.data as PuckData);
                  latestData.current = nextData;
                  setData(nextData);
                  setPuckRenderKey((key) => key + 1);
                }}
              >
                Move first component down
              </button>
            );
          }}
          onPublish={(next) => void publish(next)}
          headerTitle="Page composition"
          iframe={{ enabled: false }}
        />
      </Card>
    </section>
  );
}
