// import Link from "next/link";
// import {LinkIcon} from "lucide-react";
import { Bracket } from "@/lib/interfaces";

interface ParticipantsViewProps {
  bracket: Bracket;
}

export function ParticipantsView({ bracket }: ParticipantsViewProps) {
  return (
    <>
      {/*<Link*/}
      {/*  href={`/brackets/${bracket.id}`}*/}
      {/*  onClick={(e) => e.stopPropagation()}*/}
      {/*>*/}
      {/*  <LinkIcon className="w-4 h-4"/>*/}
      {/*</Link>*/}
      <ul className="list-decimal list-inside mt-2">
        {bracket.participants.map((p) => (
          <li key={p.seed} className="py-1">
            {p.last_name} {p.first_name} ({p.coaches_last_name?.join(", ")})
          </li>
        ))}
      </ul>
    </>
  );
}
