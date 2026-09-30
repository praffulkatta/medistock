import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
import { api, type PharmacyLocation } from '../lib/api';
import { buttonClass, EmptyState, Field, inputClass, Notice, PageHeader, Panel } from '../components/ui';

const levels = { Block: 1, Rack: 2, Shelf: 3, Bin: 4 } as const;

export default function LocationsPage({ pharmacyId }: { pharmacyId: string }) {
  const [locations, setLocations] = useState<PharmacyLocation[]>([]);
  const [type, setType] = useState<keyof typeof levels>('Block');
  const [name, setName] = useState('');
  const [parentId, setParentId] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [saving, setSaving] = useState(false);
  const parents = useMemo(() => locations.filter(item => item.level === levels[type] - 1), [locations, type]);

  const load = useCallback(async () => {
    try { setLocations(await api.locations(pharmacyId)); }
    catch (err) { setError(err instanceof Error ? err.message : 'Could not load locations'); }
  }, [pharmacyId]);
  useEffect(() => {
    let active = true;
    api.locations(pharmacyId).then(rows => { if (active) setLocations(rows); }).catch(err => { if (active) setError(err instanceof Error ? err.message : 'Could not load locations'); });
    return () => { active = false; };
  }, [pharmacyId]);

  async function submit(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError(''); setMessage('');
    try {
      await api.createLocation({ pharmacy_id: pharmacyId, name, type, level: levels[type], parent_id: parentId || null });
      setName(''); setParentId(''); setMessage('Stock location created.'); await load();
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not create stock location'); }
    finally { setSaving(false); }
  }

  const byId = new Map(locations.map(location => [location.id, location]));
  function path(location: PharmacyLocation) {
    const items = [location.name]; let parent = location.parent_id ? byId.get(location.parent_id) : undefined;
    while (parent) { items.unshift(parent.name); parent = parent.parent_id ? byId.get(parent.parent_id) : undefined; }
    return items.join(' → ');
  }

  return <>
    <PageHeader title="Stock locations" description="Build the physical path from block to rack, shelf and bin." />
    {error && <Notice>{error}</Notice>}{message && <Notice tone="success">{message}</Notice>}
    <div className="grid items-start gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
      <Panel title="Location hierarchy">
        {locations.length ? <div className="divide-y divide-slate-100">{locations.map(item => <div key={item.id} className="flex items-center justify-between gap-4 py-3 first:pt-0 last:pb-0"><div><p className="text-sm font-semibold text-slate-800">{item.name}<span className="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-500">{item.type}</span></p><p className="mt-1 text-xs text-slate-500">{path(item)}</p></div>{item.type === 'Bin' && <span className="text-xs font-medium text-teal-700">Stockable</span>}</div>)}</div> : <EmptyState>Create your first Block, then add its Rack, Shelf and Bin.</EmptyState>}
      </Panel>
      <Panel title="Add location">
        <form onSubmit={submit} className="space-y-4">
          <Field label="Level"><select value={type} onChange={event => { const next = event.target.value as keyof typeof levels; setType(next); setParentId(''); }} className={inputClass}>{Object.keys(levels).map(option => <option key={option}>{option}</option>)}</select></Field>
          <Field label="Location name"><input required maxLength={50} value={name} onChange={event => setName(event.target.value)} className={inputClass} placeholder={type === 'Block' ? 'Block A' : type === 'Rack' ? 'Rack 03' : type === 'Shelf' ? 'Shelf 02' : 'Bin 04'} /></Field>
          {type !== 'Block' && <Field label={`Parent ${type === 'Rack' ? 'Block' : type === 'Shelf' ? 'Rack' : 'Shelf'}`}><select required value={parentId} onChange={event => setParentId(event.target.value)} className={inputClass}><option value="">Select parent</option>{parents.map(parent => <option key={parent.id} value={parent.id}>{path(parent)}</option>)}</select></Field>}
          <p className="text-xs leading-5 text-slate-500">Only Bin locations can hold stock. Each child must belong to the same pharmacy as its parent.</p>
          <button disabled={saving || (type !== 'Block' && !parents.length)} className={`${buttonClass} w-full`}>{saving ? 'Saving…' : 'Create location'}</button>
        </form>
      </Panel>
    </div>
  </>;
}
