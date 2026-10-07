"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { useTranslations } from "next-intl";
import Link from "next/link";

import { Pencil, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import { createCoach, deleteCoach, getCoaches, updateCoach } from "@/lib/api/api";
import { Coach } from "@/lib/interfaces";

export default function CoachesPage() {
  const t = useTranslations("AdminCoaches");
  const [coaches, setCoaches] = useState<Coach[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState("");
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingCoach, setEditingCoach] = useState<Coach | null>(null);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<Coach | null>(null);

  const loadCoaches = useCallback(async () => {
    try {
      setLoading(true);
      setCoaches(await getCoaches());
    } catch (error) {
      toast.error(error instanceof Error ? error.message : t("loadError"));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    void loadCoaches();
  }, [loadCoaches]);

  const filteredCoaches = useMemo(() => {
    const query = search.trim().toLocaleLowerCase();
    if (!query) return coaches;
    return coaches.filter((coach) => `${coach.last_name} ${coach.first_name}`.toLocaleLowerCase().includes(query));
  }, [coaches, search]);

  const openCreate = () => {
    setEditingCoach(null);
    setFirstName("");
    setLastName("");
    setEditorOpen(true);
  };

  const openEdit = (coach: Coach) => {
    setEditingCoach(coach);
    setFirstName(coach.first_name);
    setLastName(coach.last_name);
    setEditorOpen(true);
  };

  const saveCoach = async () => {
    const payload = { first_name: firstName.trim(), last_name: lastName.trim() };
    if (!payload.last_name) {
      toast.error(t("nameRequired"));
      return;
    }

    try {
      setSaving(true);
      if (editingCoach) {
        await updateCoach(editingCoach.id, payload);
        toast.success(t("updated"));
      } else {
        await createCoach(payload);
        toast.success(t("created"));
      }
      setEditorOpen(false);
      await loadCoaches();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : t("saveError"));
    } finally {
      setSaving(false);
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      setSaving(true);
      await deleteCoach(deleteTarget.id);
      toast.success(t("deleted"));
      setDeleteTarget(null);
      await loadCoaches();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : t("deleteError"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="container mx-auto max-w-5xl p-6 md:p-8">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <Link href="/admin" className="mb-2 inline-block text-sm text-muted-foreground hover:underline">
            {t("back")}
          </Link>
          <h1 className="text-3xl font-bold tracking-tight">{t("title")}</h1>
          <p className="mt-1 text-sm text-muted-foreground">{t("description")}</p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="mr-2 h-4 w-4" />
          {t("create")}
        </Button>
      </div>

      <div className="mb-4">
        <Input
          className="max-w-sm"
          placeholder={t("search")}
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
      </div>

      <div className="overflow-hidden rounded-lg border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("lastName")}</TableHead>
              <TableHead>{t("firstName")}</TableHead>
              <TableHead className="w-36">{t("athletes")}</TableHead>
              <TableHead className="w-32 text-right">{t("actions")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={4} className="h-28 text-center text-muted-foreground">
                  {t("loading")}
                </TableCell>
              </TableRow>
            ) : filteredCoaches.length ? (
              filteredCoaches.map((coach) => (
                <TableRow key={coach.id}>
                  <TableCell className="font-medium">{coach.last_name}</TableCell>
                  <TableCell>{coach.first_name}</TableCell>
                  <TableCell>{coach.athlete_count}</TableCell>
                  <TableCell>
                    <div className="flex justify-end gap-1">
                      <Button variant="ghost" size="icon" onClick={() => openEdit(coach)} aria-label={t("edit")}>
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        disabled={coach.athlete_count > 0}
                        onClick={() => setDeleteTarget(coach)}
                        aria-label={coach.athlete_count > 0 ? t("deleteBlocked") : t("delete")}
                        title={coach.athlete_count > 0 ? t("deleteBlocked") : t("delete")}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={4} className="h-28 text-center text-muted-foreground">
                  {t("empty")}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <Dialog open={editorOpen} onOpenChange={(open) => !saving && setEditorOpen(open)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{editingCoach ? t("editTitle") : t("createTitle")}</DialogTitle>
            <DialogDescription>{t("formDescription")}</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-2">
            <div className="grid gap-2">
              <Label htmlFor="coach-last-name">{t("lastName")}</Label>
              <Input
                id="coach-last-name"
                autoFocus
                value={lastName}
                onChange={(event) => setLastName(event.target.value)}
                maxLength={100}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="coach-first-name">{t("firstNameOptional")}</Label>
              <Input
                id="coach-first-name"
                value={firstName}
                onChange={(event) => setFirstName(event.target.value)}
                maxLength={100}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditorOpen(false)} disabled={saving}>
              {t("cancel")}
            </Button>
            <Button onClick={saveCoach} disabled={saving}>
              {saving ? t("saving") : t("save")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={deleteTarget !== null} onOpenChange={(open) => !saving && !open && setDeleteTarget(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t("deleteTitle")}</DialogTitle>
            <DialogDescription>
              {t("deleteDescription", {
                name: deleteTarget ? `${deleteTarget.last_name} ${deleteTarget.first_name}` : "",
              })}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)} disabled={saving}>
              {t("cancel")}
            </Button>
            <Button variant="destructive" onClick={confirmDelete} disabled={saving}>
              {saving ? t("deleting") : t("delete")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
