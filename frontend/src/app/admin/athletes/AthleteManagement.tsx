import SortableAthleteTable from "./components/SortableAthleteTable";

const AthleteManagement = () => {
  return (
    <div>
      <h1 className="text-4xl font-bold text-center text-secondary">Управление спортсменами</h1>
      <div className="p-4 pt-8">
        <SortableAthleteTable />
      </div>
    </div>
  );
};

export default AthleteManagement;
