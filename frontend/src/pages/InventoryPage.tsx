import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
import { api, type PharmacyLocation, type StockRow } from '../lib/api';
import { buttonClass, EmptyState, Field, inputClass, Notice, PageHeader, Panel } from '../components/ui';

export default function InventoryPage({ pharmacyId }: { pharmacyId: string }) {
  const [stock, setStock] = useState<StockRow[]>([]);
  const [bins, setBins] = useState<PharmacyLocation[]>([]);
  const [sourceKey, setSourceKey] = useState('');
  const [destinationId, setDestinationId] = useState('');
  const [quantity, setQuantity] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const source = useMemo(() => stock.find(row => `${row.batch_id}:${row.location_id}` === sourceKey), [stock, sourceKey]);

  const load = useCallback(async () => {
    try {
      const [stockRows, locationRows] = await Promise.all([api.stock(pharmacyId), api.locations(pharmacyId)]);
      setStock(stockRows); setBins(locationRows.filter(location => location.type === 'Bin'));
      setSourceKey(current => current || (stockRows[0] ? `${stockRows[0].batch_id}:${stockRows[0].location_id}` : ''));
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not load inventory'); }
    finally { setLoading(false); }
  }, [pharmacyId]);
  useEffect(() => {
    let active = true;
    Promise.all([api.stock(pharmacyId), api.locations(pharmacyId)]).then(([stockRows, locationRows]) => {
      if (!active) return;
      setStock(stockRows); setBins(locationRows.filter(location => location.type === 'Bin'));
      setSourceKey(current => current || (stockRows[0] ? `${stockRows[0].batch_id}:${stockRows[0].location_id}` : ''));
      setLoading(false);
    }).catch(err => { if (active) { setError(err instanceof Error ? err.message : 'Could not load inventory'); setLoading(false); } });
    return () => { active = false; };
  }, [pharmacyId]);

  async function submit(event: FormEvent) {
    event.preventDefault(); if (!source) return;
    setSaving(true); setError(''); setMessage('');
    try {
      await api.transferStock({ pharmacy_id: pharmacyId, batch_id: source.batch_id, source_location_id: source.location_id, destination_location_id: destinationId, quantity: Number(quantity) });
      setMessage(`Moved ${quantity} units of ${source.medicine_name} to the selected bin. Total pharmacy stock is unchanged.`);
      setQuantity(''); await load();
    } catch (err) { setError(err instanceof Error ? err.message : 'Transfer could not be completed'); }
    finally { setSaving(false); }
  }

  return <>
    <PageHeader title="Inventory" description="Review batch quantities by bin and transfer stock without changing the pharmacy total." />
    {error && <Notice>{error}</Notice>}{message && <Notice tone="success">{message}</Notice>}
    <div className="grid items-start gap-5 xl:grid-cols-[minmax(0,1fr)_350px]">
      <Panel title="Stock by batch and location">
        {loading ? <p className="text-sm text-slate-500">Loading stock…</p> : stock.length ? <div className="overflow-x-auto"><table className="w-full min-w-[650px] text-left text-sm"><thead className="border-b border-slate-100 text-xs uppercase text-slate-400"><tr><th className="pb-3 pr-4 font-medium">Medicine / batch</th><th className="pb-3 pr-4 font-medium">Expiry</th><th className="pb-3 pr-4 font-medium">Location</th><th className="pb-3 pr-4 font-medium">Quantity</th><th className="pb-3 font-medium">Transfer</th></tr></thead><tbody className="divide-y divide-slate-100">{stock.map(row => <tr key={`${row.batch_id}:${row.location_id}`} className={sourceKey === `${row.batch_id}:${row.location_id}` ? 'bg-teal-50/50' : ''}><td className="py-3 pr-4"><p className="font-semibold text-slate-800">{row.medicine_name}</p><p className="text-xs text-slate-500">{row.batch_number}</p></td><td className={`py-3 pr-4 ${row.expired ? 'font-semibold text-red-700' : 'text-slate-600'}`}>{new Date(`${row.expiry_date}T00:00:00`).toLocaleDateString()}{row.expired && <span className="ml-1 text-xs">Expired</span>}</td><td className="py-3 pr-4 text-slate-600">{row.location_name}</td><td className="py-3 pr-4 font-semibold text-slate-800">{row.quantity}</td><td className="py-3"><button onClick={() => setSourceKey(`${row.batch_id}:${row.location_id}`)} className="text-xs font-semibold text-teal-700 hover:text-teal-900">Select</button></td></tr>)}</tbody></table></div> : <EmptyState>No stock records yet. Receive a purchase to add stock to a bin.</EmptyState>}
      </Panel>
      <Panel title="Transfer between bins">
        {!bins.length || !stock.length ? <p className="text-sm text-slate-600">Add stock and at least two Bin locations before transferring.</p> : <form onSubmit={submit} className="space-y-4">
          <Field label="Batch at source"><select value={sourceKey} onChange={event => setSourceKey(event.target.value)} className={inputClass}>{stock.map(row => <option key={`${row.batch_id}:${row.location_id}`} value={`${row.batch_id}:${row.location_id}`}>{row.medicine_name} · {row.batch_number} · {row.location_name} ({row.quantity})</option>)}</select></Field>
          {source && <div className="rounded-lg bg-slate-50 p-3 text-sm"><p className="font-medium text-slate-700">Available at source</p><p className="mt-1 text-xl font-bold text-slate-900">{source.quantity} units</p></div>}
          <Field label="Destination bin"><select required value={destinationId} onChange={event => setDestinationId(event.target.value)} className={inputClass}><option value="">Select destination</option>{bins.filter(bin => bin.id !== source?.location_id).map(bin => <option key={bin.id} value={bin.id}>{bin.name}</option>)}</select></Field>
          <Field label="Quantity to move"><input required type="number" min="0.001" step="0.001" max={source?.quantity ?? undefined} value={quantity} onChange={event => setQuantity(event.target.value)} className={inputClass} /></Field>
          <button disabled={saving || !source || !destinationId} className={`${buttonClass} w-full`}>{saving ? 'Transferring…' : 'Transfer stock'}</button>
        </form>}
      </Panel>
    </div>
  </>;
}
