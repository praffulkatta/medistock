import { useEffect, useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { api, type Pharmacy } from './lib/api';
import MainLayout from './layouts/MainLayout';
import DashboardPage from './pages/DashboardPage';
import SearchPage from './pages/SearchPage';
import MedicinesPage from './pages/MedicinesPage';
import CatalogPage from './pages/CatalogPage';
import LocationsPage from './pages/LocationsPage';
import PurchasesPage from './pages/PurchasesPage';
import SalesPage from './pages/SalesPage';
import InventoryPage from './pages/InventoryPage';
import ActivityPage from './pages/ActivityPage';

function SetupPage({ onCreated }: { onCreated: (pharmacy: Pharmacy) => void }) {
  const [name, setName] = useState('');
  const [address, setAddress] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError('');
    try {
      onCreated(await api.createPharmacy({ name, address: address || undefined }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create pharmacy');
    } finally {
      setSaving(false);
    }
  }
  return (
    <main className="grid min-h-screen place-items-center bg-slate-100 px-4">
      <form onSubmit={submit} className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="mb-6 flex items-center gap-3"><span className="grid size-11 place-items-center rounded-xl bg-teal-700 font-bold text-white">M</span><div><p className="text-sm font-semibold text-teal-700">MediStock</p><h1 className="text-xl font-bold text-slate-900">Set up your pharmacy</h1></div></div>
        <p className="mb-6 text-sm text-slate-600">Create the workspace where your medicine, stock and sales records will live.</p>
        <label className="mb-4 block text-sm font-medium text-slate-700">Pharmacy name<input required maxLength={255} value={name} onChange={event => setName(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-teal-600 focus:ring-2 focus:ring-teal-100" /></label>
        <label className="mb-5 block text-sm font-medium text-slate-700">Address <span className="font-normal text-slate-400">(optional)</span><input maxLength={500} value={address} onChange={event => setAddress(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-teal-600 focus:ring-2 focus:ring-teal-100" /></label>
        {error && <p role="alert" className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
        <button disabled={saving} className="w-full rounded-lg bg-teal-700 px-4 py-2.5 font-semibold text-white hover:bg-teal-800 disabled:opacity-60">{saving ? 'Creating…' : 'Create pharmacy'}</button>
      </form>
    </main>
  );
}

function AppContent() {
  const [pharmacies, setPharmacies] = useState<Pharmacy[]>([]);
  const [selectedId, setSelectedId] = useState(localStorage.getItem('medistock.pharmacyId') ?? '');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.pharmacies().then(rows => {
      setPharmacies(rows);
      const savedId = localStorage.getItem('medistock.pharmacyId') ?? '';
      const saved = rows.find(row => row.id === savedId);
      const selected = saved?.id ?? rows[0]?.id ?? '';
      setSelectedId(selected);
      if (selected) localStorage.setItem('medistock.pharmacyId', selected);
    }).catch(err => setError(err instanceof Error ? err.message : 'Could not load pharmacies')).finally(() => setLoading(false));
  }, []);

  function selectPharmacy(id: string) {
    setSelectedId(id);
    localStorage.setItem('medistock.pharmacyId', id);
  }

  if (loading) return <div className="grid min-h-screen place-items-center text-sm text-slate-500">Connecting to MediStock…</div>;
  if (error) return <div className="grid min-h-screen place-items-center bg-slate-50 p-6"><div className="max-w-lg rounded-xl border border-red-200 bg-white p-6"><h1 className="font-semibold text-slate-900">Could not connect to MediStock</h1><p className="mt-2 text-sm text-red-700">{error}</p><button onClick={() => location.reload()} className="mt-4 rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white">Try again</button></div></div>;
  if (!pharmacies.length) return <SetupPage onCreated={pharmacy => { setPharmacies([pharmacy]); selectPharmacy(pharmacy.id); }} />;

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout key={selectedId} pharmacies={pharmacies} selectedId={selectedId} onSelect={selectPharmacy} />}>
          <Route path="/" element={<DashboardPage pharmacyId={selectedId} />} />
          <Route path="/search" element={<SearchPage pharmacyId={selectedId} />} />
          <Route path="/medicines" element={<MedicinesPage pharmacyId={selectedId} />} />
          <Route path="/catalog" element={<CatalogPage pharmacyId={selectedId} />} />
          <Route path="/locations" element={<LocationsPage pharmacyId={selectedId} />} />
          <Route path="/purchases" element={<PurchasesPage pharmacyId={selectedId} />} />
          <Route path="/sales" element={<SalesPage pharmacyId={selectedId} />} />
          <Route path="/inventory" element={<InventoryPage pharmacyId={selectedId} />} />
          <Route path="/activity" element={<ActivityPage pharmacyId={selectedId} />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

function App() {
  return <AppContent />;
}

export default App;
