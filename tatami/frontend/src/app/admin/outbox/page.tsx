"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  getOutboxItem,
  getOutboxItems,
  getOutboxStatus,
  reconcileOutboxItem,
  retryAllOutboxItems,
  retryOutboxItem,
} from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import type { OutboxItem, OutboxStatus } from "@/lib/interfaces";

const PAGE_SIZE = 50;
const filters = ["active", "attention", "success", "all"] as const;

function formatDate(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function statusTone(status: OutboxStatus | null): string {
  if (!status?.worker.alive) return "sync-banner--danger";
  if (status.dead_letter > 0) return "sync-banner--danger";
  if (status.worker.status === "offline_wait") return "sync-banner--warning";
  if (status.outstanding > 0) return "sync-banner--info";
  return "sync-banner--success";
}

function statusLabel(status: OutboxStatus | null, t: (key: string, params?: Record<string, string | number>) => string) {
  if (!status?.worker.alive) return t("outbox.workerStopped");
  if (status.dead_letter > 0) return t("outbox.actionRequired", { count: status.dead_letter });
  if (status.worker.status === "offline_wait") return t("outbox.offline", { count: status.outstanding });
  if (status.outstanding > 0) return t("outbox.synchronizing", { count: status.outstanding });
  return t("outbox.upToDate");
}

export default function OutboxAdminPage() {
  const { t } = useI18n();
  const [status, setStatus] = useState<OutboxStatus | null>(null);
  const [items, setItems] = useState<OutboxItem[]>([]);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState<(typeof filters)[number]>("active");
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState<OutboxItem | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [summary, page] = await Promise.all([
        getOutboxStatus(),
        getOutboxItems(filter, PAGE_SIZE, offset),
      ]);
      setStatus(summary);
      setItems(page.items);
      setTotal(page.total);
      setError(null);
    } catch (refreshError) {
      console.error("Could not refresh synchronization state", refreshError);
      setError(t("outbox.loadError"));
    }
  }, [filter, offset, t]);

  useEffect(() => {
    refresh();
    const interval = window.setInterval(refresh, 5000);
    return () => window.clearInterval(interval);
  }, [refresh]);

  const selectFilter = (value: (typeof filters)[number]) => {
    setFilter(value);
    setOffset(0);
  };

  const showDetails = async (id: number) => {
    try {
      setSelected(await getOutboxItem(id));
    } catch (detailsError) {
      console.error("Could not load synchronization item", detailsError);
      setError(t("outbox.loadError"));
    }
  };

  const retryOne = async (item: OutboxItem) => {
    try {
      setBusyId(item.id);
      await retryOutboxItem(item.id);
      await refresh();
    } catch (retryError) {
      console.error("Could not retry synchronization item", retryError);
      setError(t("outbox.retryError"));
    } finally {
      setBusyId(null);
    }
  };

  const retryAll = async () => {
    try {
      setBusyId(-1);
      await retryAllOutboxItems();
      await refresh();
    } catch (retryError) {
      console.error("Could not retry synchronization items", retryError);
      setError(t("outbox.retryError"));
    } finally {
      setBusyId(null);
    }
  };

  const reconcile = async (item: OutboxItem) => {
    if (!window.confirm(t("outbox.reconcileConfirm"))) return;
    try {
      setBusyId(item.id);
      await reconcileOutboxItem(item.id);
      setSelected(null);
      await refresh();
    } catch (reconcileError) {
      setError(reconcileError instanceof Error ? reconcileError.message : t("outbox.reconcileError"));
    } finally {
      setBusyId(null);
    }
  };

  return (
    <main className="sync-page">
      <div className="sync-page__header">
        <div>
          <a className="text-sm underline" href="/admin/setup">{t("outbox.back")}</a>
          <h1 className="text-3xl font-bold mt-2 mb-2">{t("outbox.title")}</h1>
          <p className="text-gray-600">{t("outbox.description")}</p>
        </div>
        <Button variant="outline" onClick={refresh}>{t("outbox.refresh")}</Button>
      </div>

      <section className={`sync-banner ${statusTone(status)}`}>
        <div>
          <strong>{statusLabel(status, t)}</strong>
          <p className="text-sm mb-0">
            {t("outbox.lastSuccess")}: {formatDate(status?.worker.last_success_at)} · {t("outbox.oldest")}: {formatDate(status?.oldest_pending_at)}
          </p>
        </div>
        {status && status.retry_wait > 0 && (
          <Button variant="outline" disabled={busyId !== null} onClick={retryAll}>
            {t("outbox.retryAll")}
          </Button>
        )}
      </section>

      {error && <div className="sync-error">{error}</div>}

      <section className="sync-cards">
        <div><strong>{status?.outstanding ?? 0}</strong><span>{t("outbox.outstanding")}</span></div>
        <div><strong>{status?.retry_wait ?? 0}</strong><span>{t("outbox.waiting")}</span></div>
        <div><strong>{status?.dead_letter ?? 0}</strong><span>{t("outbox.deadLetter")}</span></div>
        <div><strong>{status?.succeeded ?? 0}</strong><span>{t("outbox.delivered")}</span></div>
      </section>

      <section className="sync-list">
        <div className="sync-toolbar">
          <div className="sync-filters">
            {filters.map((value) => (
              <Button
                key={value}
                size="sm"
                variant={filter === value ? "default" : "outline"}
                onClick={() => selectFilter(value)}
              >
                {t(`outbox.filter.${value}`)}
              </Button>
            ))}
          </div>
          <span className="text-sm text-gray-600">{t("outbox.total", { count: total })}</span>
        </div>

        <div className="sync-table-wrap">
          <table className="sync-table">
            <thead><tr>
              <th>{t("outbox.created")}</th><th>{t("outbox.tournament")}</th><th>{t("outbox.aggregate")}</th>
              <th>{t("outbox.state")}</th><th>{t("outbox.attempts")}</th><th>{t("outbox.nextAttempt")}</th><th />
            </tr></thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>{formatDate(item.created_at)}</td>
                  <td>{item.tournament_name ?? item.external_tournament_id ?? "—"}</td>
                  <td><span className="font-mono text-xs">{item.item_type ?? "—"}<br />{item.aggregate_id ?? "—"} · v{item.aggregate_version ?? "—"}</span></td>
                  <td><span className={`sync-state sync-state--${item.status}`}>{t(`outbox.status.${item.status}`)}</span></td>
                  <td>{item.retry_count}</td>
                  <td>{formatDate(item.next_attempt_at)}</td>
                  <td><div className="sync-actions">
                    <Button size="sm" variant="outline" onClick={() => showDetails(item.id)}>{t("outbox.details")}</Button>
                    {item.status === "retry_wait" && <Button size="sm" disabled={busyId !== null} onClick={() => retryOne(item)}>{t("outbox.retry")}</Button>}
                    {item.status === "dead_letter" && !item.resolved_at && <Button size="sm" disabled={busyId !== null} onClick={() => reconcile(item)}>{t("outbox.reconcile")}</Button>}
                  </div></td>
                </tr>
              ))}
              {items.length === 0 && <tr><td colSpan={7} className="sync-empty">{t("outbox.empty")}</td></tr>}
            </tbody>
          </table>
        </div>

        <div className="sync-pagination">
          <Button variant="outline" size="sm" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>{t("outbox.previous")}</Button>
          <Button variant="outline" size="sm" disabled={offset + PAGE_SIZE >= total} onClick={() => setOffset(offset + PAGE_SIZE)}>{t("outbox.next")}</Button>
        </div>
      </section>

      <Dialog open={selected !== null} onOpenChange={(open) => !open && setSelected(null)}>
        <DialogContent className="sync-details">
          <DialogHeader>
            <DialogTitle>{t("outbox.itemTitle", { id: selected?.id ?? "" })}</DialogTitle>
            <DialogDescription>{selected?.event_id ?? ""}</DialogDescription>
          </DialogHeader>
          {selected && <div className="space-y-3">
            <p><strong>{t("outbox.state")}:</strong> {t(`outbox.status.${selected.status}`)}</p>
            <p><strong>{t("outbox.failureKind")}:</strong> {selected.failure_kind ?? "—"}</p>
            <p><strong>{t("outbox.lastError")}:</strong> {selected.error ?? "—"}</p>
            <pre className="sync-payload">{JSON.stringify(selected.payload, null, 2)}</pre>
          </div>}
          <DialogFooter>
            {selected?.status === "retry_wait" && <Button disabled={busyId !== null} onClick={() => retryOne(selected)}>{t("outbox.retry")}</Button>}
            {selected?.status === "dead_letter" && !selected.resolved_at && <Button disabled={busyId !== null} onClick={() => reconcile(selected)}>{t("outbox.reconcile")}</Button>}
            <Button variant="outline" onClick={() => setSelected(null)}>{t("common.close")}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </main>
  );
}
