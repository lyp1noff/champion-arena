"use client";

import { useTranslations } from "next-intl";

import { toast } from "sonner";

import { Button } from "@/components/ui/button";

function canShareFile(file: File): boolean {
  return typeof navigator !== "undefined" && !!navigator.canShare && navigator.canShare({ files: [file] });
}

function saveFile(file: File) {
  const url = URL.createObjectURL(file);
  const link = document.createElement("a");
  link.href = url;
  link.download = file.name;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
}

async function shareFile(file: File) {
  try {
    await navigator.share({ files: [file], title: file.name });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") return;
    toast.error(`${error}`);
  }
}

/**
 * Share/Download buttons for a generated file. Sharing has to be its own click:
 * iOS only allows navigator.share() directly from a user gesture, not after the
 * seconds it takes to generate the file. On iPhone this shares the PDF itself.
 */
export function ExportedFileActions({ file }: { file: File }) {
  const t = useTranslations("AdminTournaments");

  return (
    <div className="space-y-2 rounded-md border p-3">
      <p className="text-sm text-muted-foreground">
        {t("exportReady")}: <span className="break-all">{file.name}</span>
      </p>
      {canShareFile(file) && (
        <Button className="w-full" onClick={() => shareFile(file)}>
          {t("exportShare")}
        </Button>
      )}
      <Button className="w-full" variant="outline" onClick={() => saveFile(file)}>
        {t("exportDownload")}
      </Button>
    </div>
  );
}
