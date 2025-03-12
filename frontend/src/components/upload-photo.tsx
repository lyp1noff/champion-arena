"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { LoaderCircle, Upload } from "lucide-react";
import Image from "next/image";
import { uploadPhoto } from "@/lib/api/api";

export default function UploadPhoto({ uploadPath }: { uploadPath: string }) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);
  const [error, setError] = useState("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Выберите изображение");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const url = await uploadPhoto(file, uploadPath);
      if (url) {
        setPhotoUrl(url);
      } else {
        setError("Ошибка загрузки");
      }
    } catch {
      setError("Ошибка при загрузке файла");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-lg">
      <CardContent className="p-4 flex flex-col gap-4">
        <h2 className="text-xl font-bold">Загрузка фото</h2>

        <Input type="file" accept="image/*" onChange={handleFileChange} />

        <Button onClick={handleUpload} disabled={loading}>
          {loading ? <LoaderCircle className="animate-spin" /> : <Upload className="mr-2" />}
          {loading ? "Загрузка..." : "Загрузить"}
        </Button>

        {error && <p className="text-red-500">{error}</p>}

        {photoUrl && (
          <div className="mt-4">
            <Image
              src={photoUrl}
              alt="Uploaded"
              className="mt-2 w-full rounded-lg shadow-md"
              width={1000}
              height={1000}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
