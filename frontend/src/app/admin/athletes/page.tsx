import { Suspense } from "react";
import AthletesPageContent from "./components/athletes-page-content";
import FullScreenLoader from "@/components/loader";

export default function AthletesPage() {
  return (
    <Suspense fallback={<FullScreenLoader />}>
      <AthletesPageContent />
    </Suspense>
  );
}
