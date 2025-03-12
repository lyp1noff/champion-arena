import UploadPhoto from "@/components/upload-photo";

export default function TestPage() {
  return (
    <div className="container mx-auto py-10">
      <UploadPhoto uploadPath={`/champion/tournaments`} />
    </div>
  );
}
