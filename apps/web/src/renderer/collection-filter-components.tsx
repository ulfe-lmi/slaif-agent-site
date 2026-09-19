"use client";

/**
 * Client-only renderers for the bounded in-memory collection components
 * (CollectionSearch, CollectionFilter). This is the single "use client"
 * boundary in the trusted renderer: useState lives here so the shared server
 * renderer (components.tsx), imported by server components, never touches a
 * hook. The filtering semantics themselves stay in the pure, server-safe
 * bounded-collection-filter module; the components only ever filter the
 * items the projection already delivered.
 */

import { useState } from "react";

import {
  capFacetInput,
  capSearchInput,
  itemTitle,
  itemValues,
  matchesAllFacets,
  matchesSearch,
  parseCollectionFacets,
  type FilterField,
} from "./bounded-collection-filter";

interface RenderProps {
  readonly props: Record<string, unknown>;
  readonly locale: string;
  readonly data?: readonly Record<string, unknown>[];
  readonly meta?: Readonly<{ readonly filter_fields: readonly FilterField[] }>;
}

function text(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function CollectionItemList({
  items,
}: Readonly<{ items: readonly Record<string, unknown>[] }>) {
  return (
    <ul className="renderer-collection-list">
      {items.map((item, index) => {
        const values = itemValues(item);
        return (
          <li key={text(item.id) || index}>
            <article>
              <h2>{itemTitle(item)}</h2>
              <p>{text(values.summary ?? values.description)}</p>
            </article>
          </li>
        );
      })}
    </ul>
  );
}
function CollectionSearch({ props, data, meta }: RenderProps) {
  const [query, setQuery] = useState("");
  const items: readonly Record<string, unknown>[] = Array.isArray(data) ? data : [];
  const filterFields = meta?.filter_fields ?? [];
  const visible = items.filter((item) => matchesSearch(item, filterFields, query));
  return (
    <div className="renderer-collection-search">
      <label className="renderer-collection-search-field">
        <span>{text(props.placeholder) || "Search"}</span>
        <input
          className="renderer-collection-search-input"
          type="search"
          value={query}
          maxLength={256}
          onChange={(event) => setQuery(capSearchInput(event.target.value))}
        />
      </label>
      {visible.length === 0 ? (
        <p className="renderer-collection-search-empty">No results</p>
      ) : (
        <CollectionItemList items={visible} />
      )}
    </div>
  );
}
function CollectionFilter({ props, data, meta }: RenderProps) {
  const facets = parseCollectionFacets(props);
  const [facetValues, setFacetValues] = useState<string[]>(() =>
    facets.map((facet) => facet.value),
  );
  const items: readonly Record<string, unknown>[] = Array.isArray(data) ? data : [];
  const filterFields = meta?.filter_fields ?? [];
  const active = facets.map((facet, index) => ({
    ...facet,
    value: facetValues[index] ?? "",
  }));
  const visible = items.filter((item) => matchesAllFacets(item, filterFields, active));
  return (
    <div className="renderer-collection-filter">
      {facets.length > 0 ? (
        <div className="renderer-collection-filter-facets">
          {facets.map((facet, index) => (
            <label
              key={`${facet.fieldKey}-${facet.operator}-${index}`}
              className="renderer-collection-filter-facet"
            >
              <span>{`${facet.fieldKey} ${facet.operator}`}</span>
              <input
                className="renderer-collection-filter-input"
                type="text"
                value={facetValues[index] ?? ""}
                maxLength={4096}
                onChange={(event) =>
                  setFacetValues((previous) =>
                    previous.map((value, i) =>
                      i === index ? capFacetInput(event.target.value) : value,
                    ),
                  )
                }
              />
            </label>
          ))}
        </div>
      ) : null}
      {visible.length === 0 ? (
        <p className="renderer-collection-filter-empty">No results</p>
      ) : (
        <CollectionItemList items={visible} />
      )}
    </div>
  );
}

export { CollectionFilter, CollectionSearch };
