// WelcomePage.tsx

const WelcomePage = () => {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="text-center max-w-2xl">
        <h2 className="text-4xl font-extrabold text-gray-900 mb-4">
          Welcome to MediStock
        </h2>
        <p className="text-lg text-gray-600 mb la">
          The modern solution for pharmacy inventory and stock-location management.
        </p>
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4 text-left">
          <div className="p-4 bg-white rounded-lg shadow-sm border">
            <h3 className="font-bold text-blue-600">Inventory</h3>
            <p className="text-sm text-gray-500">Manage medicines and stocks across locations.</p>
          </div>
          <div className="p-4 bg-white rounded-lg shadow-sm border">
            <h3 className="font-bold text-blue-600">Tracking</h3>
            <p className="text-sm text-gray-500">Precise stock-location tracking.</p>
          </div>
          <div className="p-4 bg-white rounded-lg shadow-sm border">
            <h3 className="font-bold text-blue-600">Management</h3>
            <p className="text-sm text-gray-500">Efficient pharmacy operations.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WelcomePage;
