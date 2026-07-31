"use client";

import Link from "next/link";

type EmptyStateAction = { href: string; label: string };

export function EmptyState({
  title,
  description,
  actions = [],
  onRetry,
  retrying = false,
  retryLabel = "重新載入",
}: {
  title: string;
  description: string;
  actions?: EmptyStateAction[];
  onRetry?: () => void;
  retrying?: boolean;
  retryLabel?: string;
}) {
  return (
    <section className="emptyState" role="status">
      <span className="emptyStateMark" aria-hidden="true">i</span>
      <div>
        <h2>{title}</h2>
        <p>{description}</p>
        <div className="emptyStateActions">
          {onRetry && <button disabled={retrying} onClick={onRetry} type="button">{retrying ? "重新載入中" : retryLabel}</button>}
          {actions.map((action) => <Link href={action.href} key={action.href}>{action.label}</Link>)}
        </div>
      </div>
    </section>
  );
}
