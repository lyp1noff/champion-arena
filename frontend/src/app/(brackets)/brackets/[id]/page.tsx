"use client";

import {useEffect, useState} from "react";
import {useParams} from "next/navigation";
import ScreenLoader from "@/components/loader";
import {BracketMatch} from "@/lib/interfaces";
import {getBracketMatchesById} from "@/lib/api/brackets";
import BracketContent from "@/components/bracket/bracket-content";
import {Card} from "@/components/ui/card";
// import { Button } from "@/components/ui/button";

export default function BracketPage() {
  const {id} = useParams();
  const [bracketMatches, setMatches] = useState<BracketMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // const [zoom, setZoom] = useState(1);
  // const [translate, setTranslate] = useState({ x: 0, y: 0 });

  useEffect(() => {
    if (!id) return;

    const fetchMatches = async () => {
      try {
        setLoading(true);
        const data = await getBracketMatchesById(Number(id));
        setMatches(data);
      } catch (err) {
        console.error(err);
        setError("Ошибка загрузки матчей");
      } finally {
        setLoading(false);
      }
    };

    fetchMatches();
  }, [id]);

  if (loading) return <ScreenLoader/>;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!bracketMatches.length) return <p className="text-gray-500">Нет данных</p>;

  return (
    <div className="container mx-auto flex flex-col gap-4 py-6">
      {/* Add h-screen if needed */}
      <h1 className="text-3xl font-bold text-center pb-2">🏆 Сетка турнира #{id}</h1>
      <div className="w-full flex justify-center overflow-auto">
        <Card className="flex flex-col w-max max-w-full p-6" id="bracket-fullscreen">
          <BracketContent bracketMatches={bracketMatches}/>
        </Card>
      </div>
    </div>

    // <div className="container py-10 mx-auto h-screen">
    //   <h1 className="text-3xl font-bold mb-6">🏆 Сетка турнира #{id}</h1>
    //   <Card className="flex flex-col h-full h-3/4 p-6" id="bracket-fullscreen">
    //     {/* <div className="flex justify-between items-center">
    //       <h2 className="text-xl font-semibold">Сетка</h2>

    //       <div className="flex gap-2">
    //         <Button
    //           className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300"
    //           onClick={() => setZoom((z) => Math.max(0.5, z - 0.1))}
    //         >
    //           -
    //         </Button>
    //         <Button
    //           className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300"
    //           onClick={() => setZoom((z) => Math.min(2, z + 0.1))}
    //         >
    //           +
    //         </Button>
    //         <Button
    //           className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300"
    //           onClick={() => {
    //             setZoom(1);
    //             setTranslate({ x: 0, y: 0 });
    //           }}
    //         >
    //           Reset
    //         </Button>
    //         <Button
    //           className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300"
    //           onClick={() => {
    //             const el = document.getElementById("bracket-fullscreen");
    //             if (el && el.requestFullscreen) el.requestFullscreen();
    //           }}
    //         >
    //           Fullscreen
    //         </Button>
    //       </div>
    //     </div> */}
    //     <ScrollArea className="flex-1">
    //       <div
    //       // style={{
    //       //   transform: `translate(${translate.x}px, ${translate.y}px) scale(${zoom})`,
    //       //   transformOrigin: "top left",
    //       // }}
    //       >
    //         <div className="flex gap-8 items-start">
    //           {sortedRounds.map(({ round, bracketMatches }) => {
    //             const firstWithLabel = bracketMatches.find((bm) => bm.match?.round_type);
    //             const title = firstWithLabel?.match.round_type ? firstWithLabel.match.round_type : `Раунд ${round}`;

    //             return (
    //               <ul
    //                 key={round}
    //                 className="flex flex-col items-stretch min-w-[220px]"
    //                 style={{ height: `${maxMatchesInRound * 120 + 22}px` }}
    //               >
    //                 <h2 className="text-lg font-semibold mb-2 text-center">{title}</h2>
    //                 {bracketMatches.map((bracketMatch, bracketMatchIdx) => (
    //                   <li
    //                     key={bracketMatch.id || `empty-${round}-${bracketMatchIdx}`}
    //                     className="flex-1 flex items-center justify-center"
    //                   >
    //                     {bracketMatch.round_number === 1 &&
    //                     (!bracketMatch.match?.athlete1 || !bracketMatch.match?.athlete2) ? (
    //                       <div className="w-full h-20 border border-dashed border-gray-300 rounded-md opacity-30" />
    //                     ) : (
    //                       <MatchCard bracketMatch={bracketMatch} />
    //                     )}
    //                   </li>
    //                 ))}
    //               </ul>
    //             );
    //           })}
    //         </div>
    //       </div>
    //       <ScrollBar orientation="horizontal" />
    //     </ScrollArea>
    //   </Card>
    // </div>
  );
}
