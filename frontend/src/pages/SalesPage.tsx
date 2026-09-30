import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
import { api, type Medicine, type StockRow } from '../lib/api';
import { buttonClass, EmptyState, Field, inputClass, Notice, PageHeader, Panel } from '../components/ui';

export default function SalesPage({ pharmacyId }: { pharmacyId: string }) {
  const [medicines, setMedicines] = useState<Medicine[]>([]);
  const [stock, setStock] = useState<StockRow[]>([]);
  const [medicineId, setMedicineId] = useState('');
  const [quantity, setQuantity] = useState('1');
  const [unitPrice, setUnitPrice] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const available = useMemo(() => stock.filter(row => row.medicine_id === medicineId && !row.expired).reduce((sum, row) => sum + row.quantity, 0), [stock, medicineId]);
  const selected = medicines.find(item => item.id === medicineId);

  const load = useCallback(async () => {
    try { const [medicineRows, stockRows] = await Promise.all([api.medicines(pharmacyId), api.stock(pharmacyId)]); setMedicines(medicineRows); setStock(stockRows); setMedicineId(current => current || medicineRows[0]?.id || ''); }
    catch (err) { setError(err instanceof Error ? err.message : 'Could not load sale data'); }
    finally { setLoading(false); }
  }, [pharmacyId]);
  useEffect(() => {
    let active = true;
    Promise.all([api.medicines(pharmacyId), api.stock(pharmacyId)]).then(([medicineRows, stockRows]) => {
      if (!active) return;
      setMedicines(medicineRows); setStock(stockRows); setMedicineId(current => current || medicineRows[0]?.id || ''); setLoading(false);
    }).catch(err => { if (active) { setError(err instanceof Error ? err.message : 'Could not load sale data'); setLoading(false); } });
    return () => { active = false; };
  }, [pharmacyId]);

  async function submit(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError(''); setMessage('');
    try {
      const sale = await api.createSale({ pharmacy_id: pharmacyId, items: [{ medicine_id: medicineId, quantity: Number(quantity), unit_price: Number(unitPrice) }] }) as { id: string; total_amount: number; items: { batch_id: string; quantity: number }[] };
      setMessage(`Sale recorded for ₹${Number(sale.total_amount).toFixed(2)}. Stock was allocated FEFO across ${sale.items.length} batch line(s).`);
      await load();
    } catch (err) { setError(err instanceof Error ? err.message : 'Sale could not be recorded'); }
    finally { setSaving(false); }
  }

  return <>
    <PageHeader title="Sales" description="Record a sale. Available, unexpired stock is deducted in first-expiry-first-out order." />
    {error && <Notice>{error}</Notice>}{message && <Notice tone="success">{message}</Notice>}
    <div className="grid items-start gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
      <Panel title="Current sellable stock">
        {loading ? <p className="text-sm text-slate-500">Loading inventory…</p> : stock.length ? <div className="overflow-x-auto"><table className="w-full min-w-[560px] text-left text-sm"><thead className="border-b border-slate-100 text-xs uppercase text-slate-400"><tr><th className="pb-3 pr-4 font-medium">Medicine / batch</th><th className="pb-3 pr-4 font-medium">Expiry</th><th className="pb-3 pr-4 font-medium">Location</th><th className="pb-3 font-medium">Units</th></tr></thead><tbody className="divide-y divide-slate-100">{stock.map((item, index) => <tr key={`${item.batch_id}-${item.location_id}-${index}`}><td className="py-3 pr-4"><p className="font-medium text-slate-800">{item.medicine_name}</p><p className="text-xs text-slate-500">{item.batch_number}</p></td><td className="py-3 pr-4 text-slate-600">{new Date(`${item.expiry_date}T00:00:00`).toLocaleDateString()}</td><td className="py-3 pr-4 text-slate-600">{item.location_name}</td><td className="py-3 font-semibold text-slate-800">{item.quantity}</td></tr>)}</tbody></table></div> : <EmptyState>No stock received yet. Receive a purchase before recording a sale.</EmptyState>}
      </Panel>
      <Panel title="Record sale">
        {medicines.length === 0 ? <EmptyState>Add a medicine to begin.</EmptyState> : <form onSubmit={submit} className="space-y-4">
          <Field label="Medicine"><select required value={medicineId} onChange={event => setMedicineId(event.target.value)} className={inputClass}>{medicines.map(item => <option key={item.id} value={item.id}>{item.name} · {item.strength || item.generic_name}</option>)}</select></Field>
          <div className="rounded-lg bg-teal-50 px-4 py-3"><p className="text-xs font-medium uppercase tracking-wide text-teal-700">Unexpired stock available</p><p className="mt-1 text-2xl font-bold text-teal-900">{available} <span className="text-sm font-medium">units</span></p>{selected && <p className="mt-1 text-xs text-teal-800">Low-stock threshold: {selected.min_stock_level}</p>}</div>
          <Field label="Quantity"><input required type="number" min="0.001" step="0.001" value={quantity} onChange={event => setQuantity(event.target.value)} className={inputClass} /></Field>
          <Field label="Selling price per unit (₹)"><input required type="number" min="0" step="0.01" value={unitPrice} onChange={event => setUnitPrice(event.target.value)} className={inputClass} /></Field>
          <p className="text-xs leading-5 text-slate-500">The server allocates the sale to the earliest-expiring available batches and records one stock movement per location used.</p>
          <button disabled={saving || loading} className={`${buttonClass} w-full`}>{saving ? 'Recording sale…' : 'Complete sale'}</button>
        </form>}
      </Panel>
    </div>
  </>;
}
