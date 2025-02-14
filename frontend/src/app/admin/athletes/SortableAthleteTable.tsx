"use client";

import { useState, useEffect } from "react";
import { getAthletes } from "@/app/api/api";

interface Athlete {
  id: number;
  first_name: string;
  last_name: string;
  gender: string;
  birth_date: string;
}

const SortableAthleteTable = () => {
  const [athletes, setAthletes] = useState<Athlete[]>([]);
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: string }>({
    key: "first_name",
    direction: "asc",
  });

  useEffect(() => {
    const fetchAthletes = async () => {
      try {
        const data = await getAthletes();
        setAthletes(data);
      } catch (error) {
        console.error("Ошибка при загрузке атлетов:", error);
      }
    };
    fetchAthletes();
  }, []);

  const sortedData = [...athletes].sort((a, b) => {
    if (a[sortConfig.key as keyof Athlete] < b[sortConfig.key as keyof Athlete]) {
      return sortConfig.direction === "asc" ? -1 : 1;
    }
    if (a[sortConfig.key as keyof Athlete] > b[sortConfig.key as keyof Athlete]) {
      return sortConfig.direction === "asc" ? 1 : -1;
    }
    return 0;
  });

  const requestSort = (key: string) => {
    let direction: "asc" | "desc" = "asc";
    if (sortConfig.key === key && sortConfig.direction === "asc") {
      direction = "desc";
    }
    setSortConfig({ key, direction });
  };

  return (
    <div className="overflow-auto">
      <table className="min-w-full table-auto border-collapse border border-gray-200">
        <thead>
          <tr>
            <th className="text-left cursor-pointer p-2 border-b" onClick={() => requestSort("first_name")}>
              Name
            </th>
            <th className="text-left cursor-pointer p-2 border-b" onClick={() => requestSort("gender")}>
              Gender
            </th>
            <th className="text-left cursor-pointer p-2 border-b" onClick={() => requestSort("birth_date")}>
              Birth Date
            </th>
          </tr>
        </thead>
        <tbody>
          {sortedData.map((row) => (
            <tr key={row.id} className="hover:bg-gray-700">
              <td className="p-2 border-b">
                {row.first_name} {row.last_name}
              </td>
              <td className="p-2 border-b">{row.gender}</td>
              <td className="p-2 border-b">{row.birth_date}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default SortableAthleteTable;
