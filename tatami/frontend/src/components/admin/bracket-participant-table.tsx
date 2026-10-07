"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { SearchablePicker } from "@/components/admin/searchable-picker";
import { Bracket, BracketParticipant } from "@/lib/interfaces";
import { useI18n } from "@/lib/i18n";

interface BracketParticipantTableProps {
  participants: BracketParticipant[];
  brackets: Bracket[];
  selectedBracketId: number;
  loading: boolean;
  moveTargets: Record<number, string>;
  seedEdits: Record<number, string>;
  onMoveTargetChange: (participantId: number, value: string) => void;
  onSeedEditChange: (participantId: number, value: string) => void;
  onSeedSave: (participantId: number) => void;
  onReorder: (participantId: number, targetSeed: number) => void;
  onMove: (participantId: number) => void;
  onRemove: (participantId: number) => void;
}

export function BracketParticipantTable({
  participants,
  brackets,
  selectedBracketId,
  loading,
  moveTargets,
  seedEdits,
  onMoveTargetChange,
  onSeedEditChange,
  onSeedSave,
  onReorder,
  onMove,
  onRemove,
}: BracketParticipantTableProps) {
  const { t } = useI18n();
  const [draggedParticipantId, setDraggedParticipantId] = useState<number | null>(null);
  const [dragOverParticipantId, setDragOverParticipantId] = useState<number | null>(null);
  const [movingParticipantId, setMovingParticipantId] = useState<number | null>(null);

  return (
    <div className="participant-table">
      <div className="participant-table__header">
        <div>{t("brackets.seed")}</div>
        <div>{t("common.athlete")}</div>
        <div>{t("brackets.actions")}</div>
      </div>

      {participants.length === 0 ? (
        <div className="participant-table__empty">{t("brackets.noParticipants")}</div>
      ) : (
        participants.map((participant) => {
          const isMoving = movingParticipantId === participant.id;
          const seedValue = seedEdits[participant.id] ?? String(participant.seed);
          return (
            <div
              key={participant.id}
              className={`participant-table__entry ${dragOverParticipantId === participant.id ? "is-drag-over" : ""}`}
              onDragOver={(event) => {
                if (draggedParticipantId === null || draggedParticipantId === participant.id) return;
                event.preventDefault();
                setDragOverParticipantId(participant.id);
              }}
              onDragLeave={() => setDragOverParticipantId(null)}
              onDrop={(event) => {
                event.preventDefault();
                if (draggedParticipantId !== null && draggedParticipantId !== participant.id) {
                  onReorder(draggedParticipantId, participant.seed);
                }
                setDraggedParticipantId(null);
                setDragOverParticipantId(null);
              }}
            >
              <div className="participant-table__row">
                <div className="participant-seed">
                  <button
                    type="button"
                    className="participant-drag-handle"
                    draggable={!loading}
                    aria-label={t("brackets.dragSeed")}
                    title={t("brackets.dragSeed")}
                    onDragStart={(event) => {
                      event.dataTransfer.effectAllowed = "move";
                      event.dataTransfer.setData("text/plain", String(participant.id));
                      setDraggedParticipantId(participant.id);
                    }}
                    onDragEnd={() => {
                      setDraggedParticipantId(null);
                      setDragOverParticipantId(null);
                    }}
                  >
                    ⠿
                  </button>
                  <input
                    className="participant-seed__input"
                    aria-label={t("brackets.seedFor", { name: participant.athlete?.last_name ?? t("common.athlete") })}
                    inputMode="numeric"
                    value={seedValue}
                    onChange={(event) => onSeedEditChange(participant.id, event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") onSeedSave(participant.id);
                    }}
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onSeedSave(participant.id)}
                    disabled={loading || seedValue === String(participant.seed)}
                  >
                    {t("common.save")}
                  </Button>
                </div>

                <div className="participant-name">
                  {participant.athlete ? `${participant.athlete.last_name} ${participant.athlete.first_name}` : t("common.empty")}
                </div>

                <div className="participant-actions">
                  <Button
                    variant="outline"
                    onClick={() => setMovingParticipantId(isMoving ? null : participant.id)}
                    disabled={loading}
                  >
                    {isMoving ? t("common.cancel") : t("brackets.move")}
                  </Button>
                  <Button variant="destructive" onClick={() => onRemove(participant.id)} disabled={loading}>
                    {t("common.remove")}
                  </Button>
                </div>
              </div>

              {isMoving ? (
                <div className="participant-move-panel">
                  <div className="participant-move-panel__picker">
                    <label className="participant-move-panel__label">{t("brackets.target")}</label>
                    <SearchablePicker
                      options={brackets
                        .filter((bracket) => bracket.external_id !== selectedBracketId)
                        .map((bracket) => ({
                          value: bracket.external_id.toString(),
                          label: bracket.display_name || bracket.category,
                          keywords: `${bracket.display_name || bracket.category} ${bracket.category}`,
                        }))}
                      value={moveTargets[participant.id]}
                      placeholder={t("brackets.selectTarget")}
                      searchPlaceholder={t("brackets.search")}
                      emptyText={t("brackets.none")}
                      onChange={(value) => onMoveTargetChange(participant.id, value)}
                    />
                  </div>
                  <Button
                    onClick={() => onMove(participant.id)}
                    disabled={loading || !moveTargets[participant.id]}
                  >
                    {t("brackets.moveAthlete")}
                  </Button>
                </div>
              ) : null}
            </div>
          );
        })
      )}
    </div>
  );
}
