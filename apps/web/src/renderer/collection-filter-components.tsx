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
  /**
   * Composition node identifier. On the canonical surface the visible
   * same-path form structure stays in markup parity with the flight-free
   * private surfaces (083/5-b); the identifier itself is unused there
   * because the canonical bounded local state filters live and the
   * submission is suppressed client-side.
   */
  readonly nodeId?: string;
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
      {/*
       * 083/5-b markup parity with the flight-free private surfaces: the
       * same same-path form structure. On the canonical RSC surface the
       * documented bounded local state already filters live, so the
       * submission is suppressed client-side (no network I/O, no state
       * change, no new authority).
       */}
      <form
        className="renderer-collection-search-form"
        method="POST"
        onSubmit={(event) => event.preventDefault()}
      >
        <label className="renderer-collection-search-field">
          <span>{text(props.placeholder) || "Search"}</span>
          <input
            className="renderer-collection-search-input"
            name="q"
            type="search"
            value={query}
            maxLength={256}
            onChange={(event) => setQuery(capSearchInput(event.target.value))}
          />
        </label>
        <button
          className="renderer-button renderer-button--secondary renderer-collection-search-submit"
          type="submit"
        >
          Search
        </button>
      </form>
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
      {/*
       * 083/5-b markup parity with the flight-free private surfaces:
       * same same-path form structure; bounded local state filters live,
       * so the submission is suppressed client-side.
       */}
      <form
        className="renderer-collection-filter-form"
        method="POST"
        onSubmit={(event) => event.preventDefault()}
      >
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
                  name={`f${index}`}
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
        <button
          className="renderer-button renderer-button--secondary renderer-collection-filter-submit"
          type="submit"
        >
          Filter
        </button>
      </form>
      {visible.length === 0 ? (
        <p className="renderer-collection-filter-empty">No results</p>
      ) : (
        <CollectionItemList items={visible} />
      )}
    </div>
  );
}

export { CollectionFilter, CollectionSearch };
