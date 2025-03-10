"use client";

import { useParams } from "next/navigation";

export default function TournamentPage() {
  const { id } = useParams();

  return (
    <div className="container py-10">
      <h1>Турнир: {id}</h1>
      <p>Здесь будет информация о турнире, сетки и прочее.</p>
    </div>
  );
}
