import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { api, type Medicine, type PharmacyLocation, type PurchaseRecord, type Supplier } from '../lib/api';
import { buttonClass, EmptyState, Field, inputClass, Notice, PageHeader, Panel } from '../components/ui';

function datePlus(days: number) { const date = new Date(); date.setDate(date.getDate() + days); return date.toISOString().slice(0, 10); }

export default function PurchasesPage({ pharmacyId }: { pharmacyId: string }) {
  const [medicines, setMedicines] = useState<Medicine[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [bins, setBins] = useState<PharmacyLocation[]>([]);
  const [purchases, setPurchases] = useState<PurchaseRecord[]>([]);
  const [supplierId, setSupplierId] = useState('');
  const [form, setForm] = useState({ medicine_id: '', batch_number: '', manufacturing_date: '', expiry_date: datePlus(365), cost_price: '', selling_price: '', quantity: '', location_id: '', invoice_number: '' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const load = useCallback(async () => {
    try {
      const [medRows, supplierRows, locationRows, purchaseRows] = await Promise.all([api.medicines(pharmacyId), api.suppliers(pharmacyId), api.locations(pharmacyId), api.purchases(pharmacyId)]);
      setMedicines(medRows); setSuppliers(supplierRows); setBins(locationRows.filter(location => location.type === 'Bin')); setPurchases(purchaseRows);
      setSupplierId(current => current || supplierRows[0]?.id || '');
      setForm(current => ({ ...current, medicine_id: current.medicine_id || medRows[0]?.id || '', location_id: current.location_id || locationRows.find(location => location.type === 'Bin')?.id || '' }));
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not load receiving data'); }
    finally { setLoading(false); }
  }, [pharmacyId]);
  useEffect(() => {
    let active = true;
    Promise.all([api.medicines(pharmacyId), api.suppliers(pharmacyId), api.locations(pharmacyId), api.purchases(pharmacyId)]).then(([medRows, supplierRows, locationRows, purchaseRows]) => {
      if (!active) return;
      setMedicines(medRows); setSuppliers(supplierRows); setBins(locationRows.filter(location => location.type === 'Bin')); setPurchases(purchaseRows);
      setSupplierId(current => current || supplierRows[0]?.id || '');
      setForm(current => ({ ...current, medicine_id: current.medicine_id || medRows[0]?.id || '', location_id: current.location_id || locationRows.find(location => location.type === 'Bin')?.id || '' }));
      setLoading(false);
    }).catch(err => { if (active) { setError(err instanceof Error ? err.message : 'Could not load receiving data'); setLoading(false); } });
    return () => { active = false; };
  }, [pharmacyId]);

  async function submit(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError(''); setMessage('');
    try {
      await api.receivePurchase({ pharmacy_id: pharmacyId, supplier_id: supplierId, invoice_number: form.invoice_number || undefined, items: [{ medicine_id: form.medicine_id, batch_number: form.batch_number, manufacturing_date: form.manufacturing_date || undefined, expiry_date: form.expiry_date, cost_price: Number(form.cost_price), selling_price: Number(form.selling_price), quantity: Number(form.quantity), location_id: form.location_id }] });
      setMessage('Purchase recorded and stock added to the selected bin.');
      setForm(current => ({ ...current, batch_number: '', quantity: '', invoice_number: '' })); await load();
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not receive purchase'); }
    finally { setSaving(false); }
  }

  const supplierName = (id: string) => suppliers.find(supplier => supplier.id === id)?.name ?? 'Supplier';
  return <>
    <PageHeader title="Purchases" description="Receive a supplier delivery into a specific bin. Stock and audit records update together." />
    {error && <Notice>{error}</Notice>}{message && <Notice tone="success">{message}</Notice>}
    <div className="grid items-start gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
      <Panel title="Purchase history">
        {loading ? <p className="text-sm text-slate-500">Loading purchases…</p> : purchases.length ? <div className="overflow-x-auto"><table className="w-full min-w-[520px] text-left text-sm"><thead className="border-b border-slate-100 text-xs uppercase text-slate-400"><tr><th className="pb-3 pr-4 font-medium">Date / invoice</th><th className="pb-3 pr-4 font-medium">Supplier</th><th className="pb-3 pr-4 font-medium">Received</th><th className="pb-3 font-medium">Value</th></tr></thead><tbody className="divide-y divide-slate-100">{purchases.map(purchase => <tr key={purchase.id}><td className="py-3 pr-4"><p className="font-medium text-slate-800">{new Date(purchase.purchase_date).toLocaleDateString()}</p><p className="text-xs text-slate-500">{purchase.invoice_number || 'No invoice number'}</p></td><td className="py-3 pr-4 text-slate-600">{supplierName(purchase.supplier_id)}</td><td className="py-3 pr-4 text-slate-600">{purchase.items.reduce((sum, item) => sum + item.quantity, 0)} units · {purchase.items.length} line(s)</td><td className="py-3 text-slate-700">₹{Number(purchase.total_amount).toFixed(2)}</td></tr>)}</tbody></table></div> : <EmptyState>No purchases received yet.</EmptyState>}
      </Panel>
      <Panel title="Receive stock">
        {!suppliers.length || !medicines.length || !bins.length ? <div className="space-y-3 text-sm text-slate-600"><p>Set up a supplier, medicine and Bin location before receiving stock.</p><p>Use <a className="font-semibold text-teal-700" href="/catalog">Categories & suppliers</a>, <a className="font-semibold text-teal-700" href="/medicines">Medicines</a> and <a className="font-semibold text-teal-700" href="/locations">Stock locations</a>.</p></div> : <form onSubmit={submit} className="space-y-4">
          <Field label="Supplier"><select required value={supplierId} onChange={event => setSupplierId(event.target.value)} className={inputClass}>{suppliers.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></Field>
          <Field label="Medicine"><select required value={form.medicine_id} onChange={event => setForm({ ...form, medicine_id: event.target.value })} className={inputClass}>{medicines.map(item => <option key={item.id} value={item.id}>{item.name} · {item.strength || item.generic_name}</option>)}</select></Field>
          <Field label="Batch number"><input required maxLength={100} value={form.batch_number} onChange={event => setForm({ ...form, batch_number: event.target.value })} className={inputClass} /></Field>
          <div className="grid grid-cols-2 gap-3"><Field label="Manufactured"><input type="date" value={form.manufacturing_date} onChange={event => setForm({ ...form, manufacturing_date: event.target.value })} className={inputClass} /></Field><Field label="Expires"><input required type="date" min={datePlus(1)} value={form.expiry_date} onChange={event => setForm({ ...form, expiry_date: event.target.value })} className={inputClass} /></Field></div>
          <div className="grid grid-cols-3 gap-2"><Field label="Quantity"><input required type="number" min="0.001" step="0.001" value={form.quantity} onChange={event => setForm({ ...form, quantity: event.target.value })} className={inputClass} /></Field><Field label="Cost ₹"><input required type="number" min="0" step="0.01" value={form.cost_price} onChange={event => setForm({ ...form, cost_price: event.target.value })} className={inputClass} /></Field><Field label="Sell ₹"><input required type="number" min="0" step="0.01" value={form.selling_price} onChange={event => setForm({ ...form, selling_price: event.target.value })} className={inputClass} /></Field></div>
          <Field label="Stock bin"><select required value={form.location_id} onChange={event => setForm({ ...form, location_id: event.target.value })} className={inputClass}>{bins.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></Field>
          <Field label="Invoice number"><input maxLength={100} value={form.invoice_number} onChange={event => setForm({ ...form, invoice_number: event.target.value })} className={inputClass} /></Field>
          <button disabled={saving} className={`${buttonClass} w-full`}>{saving ? 'Recording purchase…' : 'Receive stock'}</button>
        </form>}
      </Panel>
    </div>
  </>;
}
