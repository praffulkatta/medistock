import { NavLink, Outlet } from 'react-router-dom';
import type { Pharmacy } from '../lib/api';

const navigation = [
  { to: '/', label: 'Dashboard', icon: '▦', end: true },
  { to: '/search', label: 'Medicine search', icon: '⌕' },
  { to: '/medicines', label: 'Medicines', icon: '◫' },
  { to: '/inventory', label: 'Inventory', icon: '▤' },
  { to: '/locations', label: 'Stock locations', icon: '⌖' },
  { to: '/purchases', label: 'Purchases', icon: '↓' },
  { to: '/sales', label: 'Sales', icon: '↑' },
  { to: '/catalog', label: 'Categories & suppliers', icon: '◇' },
  { to: '/activity', label: 'Stock activity', icon: '↻' },
];

type Props = { pharmacies: Pharmacy[]; selectedId: string; onSelect: (id: string) => void };

export default function MainLayout({ pharmacies, selectedId, onSelect }: Props) {
  const selected = pharmacies.find(pharmacy => pharmacy.id === selectedId);
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 lg:flex">
      <aside className="flex shrink-0 flex-col bg-slate-950 text-slate-300 lg:sticky lg:top-0 lg:h-screen lg:w-64">
        <div className="flex items-center gap-3 px-5 py-5">
          <span className="grid size-10 place-items-center rounded-xl bg-teal-500 font-bold text-white">M</span>
          <div><p className="font-bold tracking-wide text-white">MediStock</p><p className="text-xs text-slate-400">Pharmacy operations</p></div>
        </div>
        <nav aria-label="Main navigation" className="flex gap-1 overflow-x-auto px-3 pb-3 lg:block lg:flex-1 lg:overflow-y-auto lg:pb-5">
          <p className="hidden px-3 pb-2 pt-4 text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500 lg:block">Workspace</p>
          {navigation.map(item => <NavLink key={item.to} to={item.to} end={item.end} className={({ isActive }) => `flex shrink-0 items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition ${isActive ? 'bg-teal-600/20 font-semibold text-teal-300' : 'text-slate-400 hover:bg-slate-800 hover:text-white'}`}><span className="w-5 text-center text-base" aria-hidden="true">{item.icon}</span><span>{item.label}</span></NavLink>)}
        </nav>
        <div className="hidden border-t border-slate-800 p-4 text-xs text-slate-500 lg:block">Inventory, expiry and stock location</div>
      </aside>
      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-10 flex h-[72px] items-center justify-between border-b border-slate-200 bg-white/95 px-4 backdrop-blur sm:px-7">
          <div><p className="text-xs font-medium uppercase tracking-wider text-slate-400">Workspace</p><p className="font-semibold text-slate-800">{selected?.name ?? 'Pharmacy'}</p></div>
          <div className="flex items-center gap-2 sm:gap-4">
            <NavLink to="/search" className="hidden rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-500 hover:border-teal-500 hover:text-teal-700 sm:block">Search medicines <span className="ml-5 text-slate-400">⌕</span></NavLink>
            {pharmacies.length > 1 && <select aria-label="Select pharmacy" value={selectedId} onChange={event => onSelect(event.target.value)} className="max-w-36 rounded-lg border border-slate-200 bg-white px-2 py-2 text-sm sm:max-w-56 sm:px-3">{pharmacies.map(pharmacy => <option key={pharmacy.id} value={pharmacy.id}>{pharmacy.name}</option>)}</select>}
            <div className="grid size-9 place-items-center rounded-full bg-teal-50 text-sm font-bold text-teal-800" title="Pharmacy staff">PS</div>
          </div>
        </header>
        <main className="mx-auto w-full max-w-[1440px] p-4 sm:p-7"><Outlet /></main>
      </div>
    </div>
  );
}
