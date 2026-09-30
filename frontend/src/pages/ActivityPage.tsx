import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { EmptyState, Notice, PageHeader, Panel } from '../components/ui';

type Movement = { id: string; batch_id: string; location_id: string; medicine_name: string; batch_number: string; location_name: string; change_qty: number; reason: string; created_at: string };

export default function ActivityPage({ pharmacyId }: { pharmacyId: string }) {
  const [rows, setRows] = useState<Movement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  useEffect(() => {
    api.transactions(pharmacyId).then(setRows).catch(err => setError(err instanceof Error ? err.message : 'Could not load stock history')).finally(() => setLoading(false));
  }, [pharmacyId]);

  return <>
    <PageHeader title="Stock activity" description="Auditable stock changes recorded by receiving, sales and transfers." />
    {error && <Notice>{error}</Notice>}
    <Panel title="Stock transaction history">
      {loading ? <p className="text-sm text-slate-500">Loading movement history…</p> : rows.length ? <div className="overflow-x-auto"><table className="w-full min-w-[560px] text-left text-sm"><thead className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-400"><tr><th className="pb-3 pr-4 font-medium">Time</th><th className="pb-3 pr-4 font-medium">Movement</th><th className="pb-3 pr-4 font-medium">Quantity</th><th className="pb-3 font-medium">Batch / location</th></tr></thead><tbody className="divide-y divide-slate-100">{rows.map(row => <tr key={row.id}><td className="whitespace-nowrap py-3 pr-4 text-slate-600">{new Date(row.created_at).toLocaleString()}</td><td className="py-3 pr-4"><span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700">{row.reason.replaceAll('_', ' ')}</span></td><td className={`py-3 pr-4 font-semibold ${row.change_qty < 0 ? 'text-red-700' : 'text-emerald-700'}`}>{row.change_qty > 0 ? '+' : ''}{row.change_qty}</td><td className="py-3 text-xs text-slate-600"><p className="font-medium text-slate-800">{row.medicine_name} · {row.batch_number}</p><p>{row.location_name}</p></td></tr>)}</tbody></table></div> : <EmptyState>No stock movements recorded yet.</EmptyState>}
    </Panel>
  </>;
}
