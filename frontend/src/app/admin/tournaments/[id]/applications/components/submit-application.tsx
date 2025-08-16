"use client";

import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { Command, CommandInput, CommandList, CommandItem, CommandEmpty } from "@/components/ui/command";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { toast } from "sonner";
import { useCallback, useEffect, useState } from "react";
import { Coach, Athlete, Category, ApplicationResponse } from "@/lib/interfaces";
import { getApplications, createApplication, approveAllApplications } from "@/lib/api/applications";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import AthleteForm from "@/components/athlete-form";
import { useTranslations } from "next-intl";

interface Props {
  tournamentId: number;
  coaches: Coach[];
  athletes: Athlete[];
  categories: Category[];
}

export default function SubmitApplication({ tournamentId, coaches, athletes, categories }: Props) {
  const [selectedCoach, setSelectedCoach] = useState<Coach | null>(null);
  const [selectedAthlete, setSelectedAthlete] = useState<Athlete | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);

  const [openCoach, setOpenCoach] = useState(false);
  const [openAthlete, setOpenAthlete] = useState(false);
  const [openCategory, setOpenCategory] = useState(false);

  const [submitted, setSubmitted] = useState<ApplicationResponse[]>([]);

  const [athletesState, setAthletes] = useState<Athlete[]>(athletes);
  const [athleteDialogOpen, setAthleteDialogOpen] = useState(false);

  const t = useTranslations("AdminTournaments");

  // const getAge = (birthDate: string | null) => {
  //   if (!birthDate) return null;
  //   const dob = new Date(birthDate);
  //   const diff = Date.now() - dob.getTime();
  //   return Math.floor(diff / (1000 * 60 * 60 * 24 * 365.25));
  // };

  const fetchSubmitted = useCallback(async () => {
    try {
      const data = await getApplications(tournamentId);
      setSubmitted(data);
    } catch {
      toast.error("Failed to load submitted applications");
    }
  }, [tournamentId]);

  useEffect(() => {
    fetchSubmitted();
  }, [fetchSubmitted]);

  const filteredAthletes = selectedCoach ? athletesState.filter((a) => a.coaches_id?.includes(selectedCoach.id)) : [];

  const filteredCategories = categories;
  // const filteredCategories = selectedAthlete
  //   ? categories.filter((c) => {
  //       if (c.gender !== "any" && selectedAthlete.gender && c.gender !== selectedAthlete.gender) return false;
  //       const age = getAge(selectedAthlete.birth_date);
  //       return age === null || age === c.age;
  //     })
  //   : categories;

  const submitApplication = async () => {
    if (!selectedAthlete || !selectedCategory) {
      toast.error("Select athlete and category");
      return;
    }

    try {
      await createApplication({
        tournament_id: tournamentId,
        athlete_id: selectedAthlete.id,
        category_id: selectedCategory.id,
      });

      toast.success("Application submitted!");
      setSelectedCategory(null);
      fetchSubmitted();
    } catch (err) {
      if (err instanceof Error) toast.error(err.message);
    }
  };

  const approveAll = async () => {
    try {
      await approveAllApplications(tournamentId);
      toast.success("All applications approved and added to brackets");
      fetchSubmitted();
    } catch {
      toast.error("Failed to approve all applications");
    }
  };

  return (
    <div className="flex flex-col lg:flex-row gap-6 max-w-5xl mx-auto">
      <div className="flex-1 space-y-4">
        {/* Coach selector */}
        <Popover open={openCoach} onOpenChange={setOpenCoach}>
          <PopoverTrigger asChild>
            <Button variant="outline" className="w-full text-left min-h-10">
              {selectedCoach ? `${selectedCoach.last_name}` : t("selectCoach")}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-[--radix-popover-trigger-width] p-0">
            <Command>
              <CommandInput placeholder="Search coaches..." />
              <CommandList>
                <CommandEmpty>{t("noCoachesFound")}</CommandEmpty>
                {coaches.map((coach) => (
                  <CommandItem
                    key={coach.id}
                    value={coach.last_name}
                    onSelect={() => {
                      setSelectedCoach(coach);
                      setSelectedAthlete(null);
                      setSelectedCategory(null);
                      setOpenCoach(false);
                    }}
                  >
                    {coach.last_name}
                  </CommandItem>
                ))}
              </CommandList>
            </Command>
          </PopoverContent>
        </Popover>

        {/* Athlete selector */}
        <Popover open={openAthlete} onOpenChange={setOpenAthlete}>
          <PopoverTrigger asChild>
            <Button variant="outline" className="w-full text-left min-h-10">
              {selectedAthlete ? `${selectedAthlete.first_name} ${selectedAthlete.last_name}` : t("selectAthlete")}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-[--radix-popover-trigger-width] p-0">
            <Command>
              <CommandInput placeholder="Search athletes..." />
              <CommandList>
                <CommandEmpty>
                  {t("noAthletesFound")}
                  <div className="mt-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setOpenAthlete(false);
                        setAthleteDialogOpen(true);
                      }}
                    >
                      {t("createNewAthlete")}
                    </Button>
                  </div>
                </CommandEmpty>

                {filteredAthletes.map((athlete) => (
                  <CommandItem
                    key={athlete.id}
                    value={`${athlete.first_name} ${athlete.last_name}`}
                    onSelect={() => {
                      setSelectedAthlete(athlete);
                      setSelectedCategory(null);
                      setOpenAthlete(false);
                    }}
                  >
                    {athlete.first_name} {athlete.last_name}
                  </CommandItem>
                ))}
              </CommandList>
            </Command>
          </PopoverContent>
        </Popover>

        {/* Category selector */}
        <Popover open={openCategory} onOpenChange={setOpenCategory}>
          <PopoverTrigger asChild>
            <Button variant="outline" className="w-full text-left min-h-10">
              {selectedCategory ? selectedCategory.name : t("selectCategory")}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-[--radix-popover-trigger-width] p-0">
            <Command>
              <CommandInput placeholder="Search categories..." />
              <CommandList>
                <CommandEmpty>{t("noCategoriesFound")}</CommandEmpty>
                {filteredCategories.map((cat) => (
                  <CommandItem
                    key={cat.id}
                    value={cat.name}
                    onSelect={() => {
                      setSelectedCategory(cat);
                      setOpenCategory(false);
                    }}
                  >
                    {cat.name}
                  </CommandItem>
                ))}
              </CommandList>
            </Command>
          </PopoverContent>
        </Popover>

        <Button className="w-full" onClick={submitApplication} disabled={!selectedAthlete || !selectedCategory}>
          {t("submitApplication")}
        </Button>
      </div>

      <div className="flex flex-1 flex-col space-y-4">
        {/* Sidebar with submitted applications */}
        <Card className="w-full">
          <CardHeader>
            <CardTitle>{t("submittedApplications")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {submitted.length === 0 ? (
              <p className="text-sm text-muted-foreground">{t("noApplicationsYet")}</p>
            ) : (
              submitted.map((app) => (
                <div key={app.id} className="text-sm">
                  {app.athlete.first_name} {app.athlete.last_name} – {app.category.name} ({app.status})
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Button onClick={approveAll}>{t("approveAllApplications")}</Button>
      </div>

      <Dialog open={athleteDialogOpen} onOpenChange={setAthleteDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogTitle>{t("createNewAthlete")}</DialogTitle>
          <AthleteForm
            onSuccess={(newAthlete: Athlete) => {
              setAthletes((prev) => [...prev, newAthlete]);
              setSelectedAthlete(newAthlete);
              setAthleteDialogOpen(false);
              toast.success(t("athleteCreated"));
            }}
            onCancel={() => setAthleteDialogOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
