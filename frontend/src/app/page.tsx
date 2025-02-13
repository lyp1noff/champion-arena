import Header from '@/app/components/Header';

const Home = () => {
  return (
    <div className="text-white min-h-screen">
      <Header />

      <main className="p-8">
        <h1 className="text-4xl font-bold text-center text-secondary">
          Добро пожаловать в Champion!
        </h1>
        <p className="mt-4 text-xl text-center">
          Здесь проходят турниры. Выберите один из пунктов меню для продолжения.
        </p>
      </main>
    </div>
  );
};

export default Home;
