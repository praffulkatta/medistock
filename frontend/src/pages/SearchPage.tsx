import { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api, type SearchResponse } from '../lib/api';
import { EmptyState, Notice, PageHeader, secondaryButtonClass } from '../components/ui';

const quantity = new Intl.NumberFormat(undefined, { maximumFractionDigits: 3 });

export default function SearchPage({ pharmacyId }: { pharmacyId: string }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [term, setTerm] = useState(searchParams.get('q') ?? '');
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const requestId = useRef(0);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const currentRequest = ++requestId.current;
      if (!term.trim()) { setData(null); setLoading(false); setError(''); return; }
      setLoading(true);
      setError('');
      api.search(pharmacyId, term.trim(), offset).then(result => { if (requestId.current === currentRequest) setData(result); }).catch(err => { if (requestId.current === currentRequest) setError(err instanceof Error ? err.message : 'Search could not be completed'); }).finally(() => { if (requestId.current === currentRequest) setLoading(false); });
    }, term.trim() ? 250 : 0);
    return () => { window.clearTimeout(timer); requestId.current += 1; };
  }, [pharmacyId, term, offset]);

  return <>
    <PageHeader title="Medicine search" description="Find stock by medicine, generic name, manufacturer or batch number." />
    <div className="mb-6 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
      <label htmlFor="medicine-search" className="mb-2 block text-sm font-semibold text-slate-700">Search the medicine catalog</label>
      <div className="relative"><span className="pointer-events-none absolute left-3 top-2.5 text-xl text-slate-400">⌕</span><input id="medicine-search" autoFocus value={term} onChange={event => { setTerm(event.target.value); setSearchParams(event.target.value ? { q: event.target.value } : {}); setOffset(0); }} placeholder="Try a name, generic, manufacturer or batch…" className="w-full rounded-lg border border-slate-300 py-3 pl-10 pr-4 text-base outline-none focus:border-teal-600 focus:ring-2 focus:ring-teal-100" /></div>
      <p className="mt-2 text-xs text-slate-500">Search results include current batch quantities, expiry status and physical bin locations.</p>
    </div>
    {loading && <p role="status" className="mb-4 text-sm text-slate-500">Searching the pharmacy catalog…</p>}
    {error && <Notice>{error}</Notice>}
    {!term.trim() && <EmptyState>Start typing to find medicines and exact stock locations.</EmptyState>}
    {data && term.trim() && !loading && data.results.length === 0 && <EmptyState>No medicine matched “{term}”. Try a generic name or batch number.</EmptyState>}
    {data && term.trim() && data.results.length > 0 && !loading && <>
      <p className="mb-3 text-sm text-slate-500">{data.total} {data.total === 1 ? 'medicine' : 'medicines'} found</p>
      <div className="space-y-4">{data.results.map(medicine => <article key={medicine.medicine_id} className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-col justify-between gap-4 border-b border-slate-100 p-5 sm:flex-row sm:items-center">
          <div><h2 className="text-lg font-bold text-slate-900">{medicine.name}</h2><p className="mt-0.5 text-sm text-slate-500">{medicine.generic_name}{medicine.manufacturer ? ` · ${medicine.manufacturer}` : ''}</p></div>
          <div className="flex items-center gap-2"><span className={`rounded-full px-3 py-1.5 text-sm font-bold ${medicine.total_quantity === 0 ? 'bg-slate-100 text-slate-600' : medicine.total_quantity <= medicine.min_stock_level ? 'bg-amber-50 text-amber-800' : 'bg-emerald-50 text-emerald-800'}`}>{quantity.format(medicine.total_quantity)} units</span>{medicine.total_quantity === 0 && <span className="text-xs text-slate-500">Out of stock</span>}</div>
        </div>
        {medicine.batches.length ? <div className="grid gap-3 p-4 sm:grid-cols-2">{medicine.batches.map(batch => <div key={batch.batch_id} className="rounded-lg border border-slate-200 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2"><p className="font-semibold text-slate-800">Batch {batch.batch_number}</p><ExpiryBadge status={batch.expiry_status} /></div>
          <p className="mt-1 text-sm text-slate-600">{quantity.format(batch.quantity)} units · Expires {new Date(`${batch.expiry_date}T00:00:00`).toLocaleDateString()}</p>
          {batch.locations.length ? <div className="mt-3 space-y-2">{batch.locations.map(location => <div key={location.location_id} className="flex items-start justify-between gap-3 rounded-md bg-slate-50 px-3 py-2"><div><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Physical location</p><p className="mt-0.5 text-sm text-slate-700">{location.location_path.join(' → ') || 'Location path unavailable'}</p></div><span className="whitespace-nowrap text-sm font-semibold text-slate-800">{quantity.format(location.quantity)} units</span></div>)}</div> : <p className="mt-3 text-sm text-slate-400">No stock currently assigned to a location.</p>}
        </div>)}</div> : <div className="p-5 text-sm text-slate-500">No batches have been recorded for this medicine.</div>}
      </article>)}</div>
      {data.total > data.limit && <div className="mt-5 flex items-center justify-between"><button className={secondaryButtonClass} disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - data.limit))}>Previous</button><span className="text-sm text-slate-500">Showing {offset + 1}–{Math.min(offset + data.results.length, data.total)} of {data.total}</span><button className={secondaryButtonClass} disabled={offset + data.limit >= data.total} onClick={() => setOffset(offset + data.limit)}>Next</button></div>}
    </>}
  </>;
}

function ExpiryBadge({ status }: { status: string }) {
  const classes = status === 'EXPIRED' ? 'bg-red-50 text-red-700' : status === 'EXPIRING_SOON' ? 'bg-amber-50 text-amber-800' : 'bg-emerald-50 text-emerald-700';
  const label = status === 'EXPIRING_SOON' ? 'Expiring soon' : status === 'EXPIRED' ? 'Expired' : 'Safe';
  return <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${classes}`}>{label}</span>;
}
