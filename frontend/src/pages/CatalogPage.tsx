import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { api, type Category, type Supplier } from '../lib/api';
import { buttonClass, EmptyState, Field, inputClass, Notice, PageHeader, Panel } from '../components/ui';

export default function CatalogPage({ pharmacyId }: { pharmacyId: string }) {
  const [categories, setCategories] = useState<Category[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [categoryName, setCategoryName] = useState('');
  const [supplierName, setSupplierName] = useState('');
  const [contact, setContact] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try { const [categoryRows, supplierRows] = await Promise.all([api.categories(pharmacyId), api.suppliers(pharmacyId)]); setCategories(categoryRows); setSuppliers(supplierRows); }
    catch (err) { setError(err instanceof Error ? err.message : 'Could not load catalog'); }
  }, [pharmacyId]);
  useEffect(() => {
    let active = true;
    Promise.all([api.categories(pharmacyId), api.suppliers(pharmacyId)]).then(([categoryRows, supplierRows]) => {
      if (active) { setCategories(categoryRows); setSuppliers(supplierRows); }
    }).catch(err => { if (active) setError(err instanceof Error ? err.message : 'Could not load catalog'); });
    return () => { active = false; };
  }, [pharmacyId]);

  async function createCategory(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError(''); setMessage('');
    try { await api.createCategory({ pharmacy_id: pharmacyId, name: categoryName }); setCategoryName(''); setMessage('Category created.'); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : 'Could not create category'); }
    finally { setSaving(false); }
  }
  async function createSupplier(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError(''); setMessage('');
    try { await api.createSupplier({ pharmacy_id: pharmacyId, name: supplierName, contact_info: contact || undefined }); setSupplierName(''); setContact(''); setMessage('Supplier created.'); await load(); }
    catch (err) { setError(err instanceof Error ? err.message : 'Could not create supplier'); }
    finally { setSaving(false); }
  }

  return <>
    <PageHeader title="Categories & suppliers" description="Organize the medicine catalog and manage your purchasing partners." />
    {error && <Notice>{error}</Notice>}{message && <Notice tone="success">{message}</Notice>}
    <div className="grid items-start gap-5 xl:grid-cols-2">
      <Panel title="Medicine categories">
        <form onSubmit={createCategory} className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-end"><div className="flex-1"><Field label="Category name"><input required maxLength={100} value={categoryName} onChange={event => setCategoryName(event.target.value)} className={inputClass} placeholder="Pain relief" /></Field></div><button disabled={saving} className={buttonClass}>Add category</button></form>
        {categories.length ? <ul className="divide-y divide-slate-100">{categories.map(item => <li key={item.id} className="py-3 text-sm font-medium text-slate-700">{item.name}</li>)}</ul> : <EmptyState>No categories have been added.</EmptyState>}
      </Panel>
      <Panel title="Suppliers">
        <form onSubmit={createSupplier} className="mb-5 grid gap-3 sm:grid-cols-2"><Field label="Supplier name"><input required maxLength={255} value={supplierName} onChange={event => setSupplierName(event.target.value)} className={inputClass} placeholder="Supplier name" /></Field><Field label="Contact details"><input maxLength={500} value={contact} onChange={event => setContact(event.target.value)} className={inputClass} placeholder="Phone or email" /></Field><button disabled={saving} className={`${buttonClass} sm:col-span-2`}>Add supplier</button></form>
        {suppliers.length ? <ul className="divide-y divide-slate-100">{suppliers.map(item => <li key={item.id} className="py-3"><p className="text-sm font-medium text-slate-700">{item.name}</p>{item.contact_info && <p className="mt-0.5 text-xs text-slate-500">{item.contact_info}</p>}</li>)}</ul> : <EmptyState>No suppliers have been added.</EmptyState>}
      </Panel>
    </div>
  </>;
}
