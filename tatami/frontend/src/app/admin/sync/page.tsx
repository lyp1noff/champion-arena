"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { getSyncBrackets, getSyncStatus, resendBracket, retrySyncNow } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import {
  BRACKET_SYNC_STATE,
  SYNC_WORKER_PHASE,
  type BracketSyncItem,
  type SyncStatus,
} from "@/lib/interfaces";

const PAGE_SIZE = 50;
const filters = ["pending", "attention", "all"] as const;
type Translate = (key: string, params?: Record<string, string | number>) => string;

function formatDate(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function statusTone(status: SyncStatus | null): string {
  if (!status?.worker.alive) return "sync-banner--danger";
  if (status.attention > 0) return "sync-banner--danger";
  if (status.worker.phase === SYNC_WORKER_PHASE.OFFLINE) return "sync-banner--warning";
  if (status.pending > 0) return "sync-banner--info";
  return "sync-banner--success";
}

function statusLabel(status: SyncStatus | null, t: Translate): string {
  if (!status?.worker.alive) return t("sync.workerStopped");
  if (status.attention > 0) return t("sync.actionRequired", { count: status.attention });
  if (status.worker.phase === SYNC_WORKER_PHASE.OFFLINE) return t("sync.offline", { count: status.pending });
  if (status.pending > 0) return t("sync.synchronizing", { count: status.pending });
  return t("sync.upToDate");
}

export default function SyncAdminPage() {
  const { t } = useI18n();
  const [status, setStatus] = useState<SyncStatus | null>(null);
  const [items, setItems] = useState<BracketSyncItem[]>([]);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState<(typeof filters)[number]>("pending");
  const [offset, setOffset] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [summary, page] = await Promise.all([getSyncStatus(), getSyncBrackets(filter, PAGE_SIZE, offset)]);
      setStatus(summary);
      setItems(page.items);
      setTotal(page.total);
      setError(null);
    } catch (refreshError) {
      console.error("Could not refresh synchronization state", refreshError);
      setError(t("sync.loadError"));
    }
  }, [filter, offset, t]);

  useEffect(() => {
    refresh();
    const interval = window.setInterval(refresh, 3000);
    return () => window.clearInterval(interval);
  }, [refresh]);

  const run = async (action: () => Promise<void>) => {
    try {
      setBusy(true);
      await action();
      await refresh();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : t("sync.actionError"));
    } finally {
      setBusy(false);
    }
  };

  const resend = (item: BracketSyncItem) => {
    if (item.remote_version != null && !window.confirm(t("sync.overwriteConfirm"))) return;
    void run(() => resendBracket(item.bracket_id));
  };

  const showRetry = status?.worker.phase === SYNC_WORKER_PHASE.OFFLINE;

  return (
    <main className="sync-page">
      <div className="sync-page__header">
        <div>
          <a className="text-sm underline" href="/admin/setup">{t("sync.back")}</a>
          <h1 className="text-3xl font-bold mt-2 mb-2">{t("sync.title")}</h1>
          <p className="text-gray-600">{t("sync.description")}</p>
        </div>
        <Button variant="outline" onClick={refresh}>{t("sync.refresh")}</Button>
      </div>

      <section className={`sync-banner ${statusTone(status)}`}>
        <div>
          <strong>{statusLabel(status, t)}</strong>
          <p className="text-sm mb-0">
            {t("sync.lastSuccess")}: {formatDate(status?.worker.last_success_at)}
            {showRetry && <> · {t("sync.nextAttempt")}: {formatDate(status?.worker.next_attempt_at)}</>}
          </p>
          {status?.worker.last_error && (
            <p className="text-sm mb-0">{t("sync.lastError")}: <span className="font-mono">{status.worker.last_error}</span></p>
          )}
        </div>
        {showRetry && (
          <Button variant="outline" disabled={busy} onClick={() => run(retrySyncNow)}>{t("sync.retryNow")}</Button>
        )}
      </section>

      {error && <div className="sync-error">{error}</div>}

      <section className="sync-cards">
        <div><strong>{status?.pending ?? 0}</strong><span>{t("sync.pending")}</span></div>
        <div><strong>{status?.attention ?? 0}</strong><span>{t("sync.attention")}</span></div>
        <div><strong>{status?.synced ?? 0}</strong><span>{t("sync.synced")}</span></div>
        <div><strong>{status?.total ?? 0}</strong><span>{t("sync.totalBrackets")}</span></div>
      </section>

      <section className="sync-list">
        <div className="sync-toolbar">
          <div className="sync-filters">
            {filters.map((value) => (
              <Button
                key={value}
                size="sm"
                variant={filter === value ? "default" : "outline"}
                onClick={() => {
                  setFilter(value);
                  setOffset(0);
                }}
              >
                {t(`sync.filter.${value}`)}
              </Button>
            ))}
          </div>
          <span className="text-sm text-gray-600">{t("sync.total", { count: total })}</span>
        </div>

        <div className="sync-table-wrap">
          <table className="sync-table">
            <thead><tr>
              <th>{t("sync.bracket")}</th><th>{t("sync.tournament")}</th><th>{t("sync.state")}</th>
              <th>{t("sync.versions")}</th><th>{t("sync.changed")}</th><th>{t("sync.error")}</th><th />
            </tr></thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.bracket_id}>
                  <td>{item.name}<br /><span className="font-mono text-xs">#{item.bracket_id}</span></td>
                  <td>{item.tournament_name}</td>
                  <td><span className={`sync-state sync-state--${item.state}`}>{t(`sync.stateLabel.${item.state}`)}</span></td>
                  <td className="font-mono text-xs">v{item.version} / {item.synced_version != null ? `v${item.synced_version}` : "—"}</td>
                  <td>{formatDate(item.updated_at)}</td>
                  <td className="text-sm">{item.error ?? "—"}</td>
                  <td><div className="sync-actions">
                    {item.state !== BRACKET_SYNC_STATE.PENDING && (
                      <Button size="sm" variant={item.state === BRACKET_SYNC_STATE.ATTENTION ? "default" : "outline"} disabled={busy} onClick={() => resend(item)}>
                        {item.remote_version != null ? t("sync.overwrite") : t("sync.resend")}
                      </Button>
                    )}
                  </div></td>
                </tr>
              ))}
              {items.length === 0 && <tr><td colSpan={7} className="sync-empty">{t("sync.empty")}</td></tr>}
            </tbody>
          </table>
        </div>

        <div className="sync-pagination">
          <Button variant="outline" size="sm" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>{t("sync.previous")}</Button>
          <Button variant="outline" size="sm" disabled={offset + PAGE_SIZE >= total} onClick={() => setOffset(offset + PAGE_SIZE)}>{t("sync.next")}</Button>
        </div>
      </section>
    </main>
  );
}
