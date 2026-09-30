import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { api, type Category, type Medicine } from '../lib/api';
import { buttonClass, EmptyState, Field, inputClass, Notice, PageHeader, Panel } from '../components/ui';

export default function MedicinesPage({ pharmacyId }: { pharmacyId: string }) {
  const [medicines, setMedicines] = useState<Medicine[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ name: '', generic_name: '', manufacturer: '', strength: '', category_id: '', min_stock_level: '0' });

  const load = useCallback(async () => {
    try {
      const [medicineRows, categoryRows] = await Promise.all([api.medicines(pharmacyId), api.categories(pharmacyId)]);
      setMedicines(medicineRows); setCategories(categoryRows);
      setForm(current => ({ ...current, category_id: current.category_id || categoryRows[0]?.id || '' }));
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not load medicine catalog'); }
    finally { setLoading(false); }
  }, [pharmacyId]);
  useEffect(() => {
    let active = true;
    Promise.all([api.medicines(pharmacyId), api.categories(pharmacyId)]).then(([medicineRows, categoryRows]) => {
      if (!active) return;
      setMedicines(medicineRows); setCategories(categoryRows);
      setForm(current => ({ ...current, category_id: current.category_id || categoryRows[0]?.id || '' }));
      setLoading(false);
    }).catch(err => { if (active) { setError(err instanceof Error ? err.message : 'Could not load medicine catalog'); setLoading(false); } });
    return () => { active = false; };
  }, [pharmacyId]);

  async function submit(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError(''); setMessage('');
    try {
      await api.createMedicine({ ...form, pharmacy_id: pharmacyId, min_stock_level: Number(form.min_stock_level), manufacturer: form.manufacturer || null, strength: form.strength || null });
      setForm(current => ({ ...current, name: '', generic_name: '', manufacturer: '', strength: '', min_stock_level: '0' }));
      setMessage('Medicine added to the pharmacy catalog.'); await load();
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not create medicine'); }
    finally { setSaving(false); }
  }

  return <>
    <PageHeader title="Medicines" description="Maintain the pharmacy catalog and set a low-stock threshold for each medicine." />
    {error && <Notice>{error}</Notice>}{message && <Notice tone="success">{message}</Notice>}
    <div className="grid items-start gap-5 xl:grid-cols-[minmax(0,1fr)_340px]">
      <Panel title="Medicine catalog">
        {loading ? <p className="text-sm text-slate-500">Loading medicines…</p> : medicines.length === 0 ? <EmptyState>No medicines yet. Add one here, then receive stock through Purchases.</EmptyState> : <div className="overflow-x-auto"><table className="w-full min-w-[560px] text-left text-sm"><thead className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-400"><tr><th className="pb-3 pr-4 font-medium">Medicine</th><th className="pb-3 pr-4 font-medium">Generic name</th><th className="pb-3 pr-4 font-medium">Strength</th><th className="pb-3 pr-4 font-medium">Manufacturer</th><th className="pb-3 font-medium">Min stock</th></tr></thead><tbody className="divide-y divide-slate-100">{medicines.map(item => <tr key={item.id}><td className="py-3 pr-4 font-semibold text-slate-800"><Link className="hover:text-teal-700" to={`/search?q=${encodeURIComponent(item.name)}`}>{item.name}</Link></td><td className="py-3 pr-4 text-slate-600">{item.generic_name}</td><td className="py-3 pr-4 text-slate-600">{item.strength || '—'}</td><td className="py-3 pr-4 text-slate-600">{item.manufacturer || '—'}</td><td className="py-3 text-slate-600">{item.min_stock_level}</td></tr>)}</tbody></table></div>}
      </Panel>
      <Panel title="Add medicine">
        {categories.length === 0 ? <div className="space-y-3 text-sm text-slate-600"><p>Create a category before adding medicines.</p><Link to="/catalog" className="font-semibold text-teal-700 hover:text-teal-900">Go to categories & suppliers →</Link></div> : <form onSubmit={submit} className="space-y-4">
          <Field label="Medicine name"><input required maxLength={255} value={form.name} onChange={event => setForm({ ...form, name: event.target.value })} className={inputClass} placeholder="Dolo 650" /></Field>
          <Field label="Generic name"><input required maxLength={255} value={form.generic_name} onChange={event => setForm({ ...form, generic_name: event.target.value })} className={inputClass} placeholder="Paracetamol" /></Field>
          <div className="grid grid-cols-2 gap-3"><Field label="Strength"><input value={form.strength} onChange={event => setForm({ ...form, strength: event.target.value })} className={inputClass} placeholder="650 mg" /></Field><Field label="Manufacturer"><input value={form.manufacturer} onChange={event => setForm({ ...form, manufacturer: event.target.value })} className={inputClass} placeholder="Manufacturer" /></Field></div>
          <Field label="Category"><select required value={form.category_id} onChange={event => setForm({ ...form, category_id: event.target.value })} className={inputClass}>{categories.map(category => <option key={category.id} value={category.id}>{category.name}</option>)}</select></Field>
          <Field label="Low-stock threshold (units)"><input type="number" min="0" step="0.001" value={form.min_stock_level} onChange={event => setForm({ ...form, min_stock_level: event.target.value })} className={inputClass} /></Field>
          <button disabled={saving} className={`${buttonClass} w-full`}>{saving ? 'Saving…' : 'Add medicine'}</button>
        </form>}
      </Panel>
    </div>
  </>;
}
