// "use client";

// import { useState, useEffect } from "react";
// import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
// // import { getAthleteById, updateAthlete } from "@/lib/api/athletes";
// import AthleteForm from "./athlete-form";
// import { Athlete, AthleteUpdate } from "@/lib/interfaces";
// import { Button } from "@/components/ui/button";
// import ScreenLoader from "./loader";

// interface AthleteDialogProps {
//   athleteId: number;
// }

// export default function AthleteDialog({ athleteId }: AthleteDialogProps) {
//   const [athlete, setAthlete] = useState<Athlete | null>(null);
//   const [isLoading, setIsLoading] = useState(true);
//   const [isSubmitting, setIsSubmitting] = useState(false);
//   const [open, setOpen] = useState(false);

//   useEffect(() => {
//     if (!open) return;

//     async function fetchAthlete() {
//       try {
//         // const data = await getAthleteById(athleteId);
//         // setAthlete(data);
//       } catch (error) {
//         console.error("Error loading athlete:", error);
//       } finally {
//         setIsLoading(false);
//       }
//     }

//     fetchAthlete();
//   }, [athleteId, open]);

//   async function handleModify(values: AthleteUpdate) {
//     setIsSubmitting(true);
//     try {
//       //   await updateAthlete(athleteId, values);
//       setOpen(false);
//     } catch (error) {
//       console.error("Error updating athlete:", error);
//     } finally {
//       setIsSubmitting(false);
//     }
//   }

//   return (
//     <Dialog open={open} onOpenChange={setOpen}>
//       <DialogTrigger asChild>
//         <Button variant="outline">Edit</Button>
//       </DialogTrigger>
//       <DialogContent className="max-w-lg">
//         <DialogHeader>
//           <DialogTitle>Edit Athlete</DialogTitle>
//         </DialogHeader>
//         {isLoading ? (
//           <ScreenLoader />
//         ) : (
//           athlete && <AthleteForm defaultValues={athlete} onSubmit={handleModify} isSubmitting={isSubmitting} />
//         )}
//       </DialogContent>
//     </Dialog>
//   );
// }
