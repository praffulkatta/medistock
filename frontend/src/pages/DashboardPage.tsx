import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, type Dashboard } from '../lib/api';
import { EmptyState, Notice, PageHeader, Panel } from '../components/ui';

const number = new Intl.NumberFormat(undefined, { maximumFractionDigits: 3 });
const money = new Intl.NumberFormat(undefined, { style: 'currency', currency: 'INR', maximumFractionDigits: 2 });

export default function DashboardPage({ pharmacyId }: { pharmacyId: string }) {
  const [data, setData] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  useEffect(() => {
    api.dashboard(pharmacyId).then(setData).catch(err => setError(err instanceof Error ? err.message : 'Dashboard could not be loaded')).finally(() => setLoading(false));
  }, [pharmacyId]);

  return <>
    <PageHeader title="Dashboard" description="A live view of your pharmacy inventory and daily operations." action={<Link to="/purchases" className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-800">Receive stock</Link>} />
    {error && <Notice>{error}</Notice>}
    {loading && <p className="mb-4 text-sm text-slate-500">Loading current pharmacy data…</p>}
    {data && <>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <Metric label="Medicines" value={number.format(data.medicine_count)} note="Active catalog" tone="teal" />
        <Metric label="Units in stock" value={number.format(data.total_stock)} note="Across all batches and locations" tone="blue" />
        <Metric label="Low stock" value={number.format(data.low_stock_count)} note="At or below minimum level" tone="amber" />
        <Metric label="Expiring soon" value={number.format(data.expiring_soon_quantity)} note="Units expiring within 30 days" tone="amber" />
        <Metric label="Expired stock" value={number.format(data.expired_quantity)} note="Units past expiry date" tone="red" />
        <Metric label="Sales today" value={money.format(data.sales_today)} note="Recorded sale value today" tone="green" />
      </div>
      <div className="mt-6 grid gap-5 xl:grid-cols-2">
        <Panel title="Low-stock medicines" action={<Link className="text-sm font-medium text-teal-700" to="/medicines">Manage medicines</Link>}>
          {data.low_stock_items.length ? <div className="divide-y divide-slate-100">{data.low_stock_items.map(item => <div key={item.medicine_id} className="flex items-center justify-between gap-4 py-3 first:pt-0 last:pb-0"><div><p className="font-medium text-slate-800">{item.name}</p><p className="text-xs text-slate-500">Minimum {number.format(item.minimum)} units</p></div><span className="rounded-full bg-amber-50 px-2.5 py-1 text-sm font-semibold text-amber-800">{number.format(item.quantity)} left</span></div>)}</div> : <EmptyState>No medicines are currently at or below their minimum stock level.</EmptyState>}
        </Panel>
        <Panel title="Expiry alerts" action={<Link className="text-sm font-medium text-teal-700" to="/inventory">View stock</Link>}>
          {data.expiry_alerts.length ? <div className="divide-y divide-slate-100">{data.expiry_alerts.map(item => <div key={item.batch_id} className="flex items-center justify-between gap-4 py-3 first:pt-0 last:pb-0"><div><p className="font-medium text-slate-800">{item.medicine_name}<span className="ml-2 text-xs font-normal text-slate-500">{item.batch_number}</span></p><p className="text-xs text-slate-500">Expires {new Date(`${item.expiry_date}T00:00:00`).toLocaleDateString()}</p></div><span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${item.status === 'EXPIRED' ? 'bg-red-50 text-red-700' : 'bg-amber-50 text-amber-800'}`}>{item.status === 'EXPIRED' ? 'Expired' : `${number.format(item.quantity)} units`}</span></div>)}</div> : <EmptyState>No expired or soon-to-expire stock found.</EmptyState>}
        </Panel>
        <Panel title="Recent stock movements" action={<Link className="text-sm font-medium text-teal-700" to="/activity">Full history</Link>}>
          {data.recent_movements.length ? <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="text-xs uppercase text-slate-400"><tr><th className="pb-3 pr-3 font-medium">Medicine</th><th className="pb-3 pr-3 font-medium">Movement</th><th className="pb-3 pr-3 font-medium">Location</th><th className="pb-3 font-medium">When</th></tr></thead><tbody className="divide-y divide-slate-100">{data.recent_movements.map(item => <tr key={item.id}><td className="py-3 pr-3"><p className="font-medium text-slate-800">{item.medicine_name}</p><p className="text-xs text-slate-500">{item.batch_number}</p></td><td className={`py-3 pr-3 font-semibold ${item.change_qty < 0 ? 'text-red-700' : 'text-emerald-700'}`}>{item.change_qty > 0 ? '+' : ''}{number.format(item.change_qty)} <span className="font-normal text-slate-500">{item.reason.replace('_', ' ')}</span></td><td className="py-3 pr-3 text-slate-600">{item.location_name}</td><td className="whitespace-nowrap py-3 text-xs text-slate-500">{new Date(item.created_at).toLocaleDateString()}</td></tr>)}</tbody></table></div> : <EmptyState>Stock movements will appear here after purchases, sales or transfers.</EmptyState>}
        </Panel>
      </div>
    </>}
  </>;
}

function Metric({ label, value, note, tone }: { label: string; value: string; note: string; tone: string }) {
  const accent: Record<string, string> = { teal: 'bg-teal-500', blue: 'bg-blue-500', amber: 'bg-amber-500', red: 'bg-red-500', green: 'bg-emerald-500' };
  return <div className="relative overflow-hidden rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><span className={`absolute inset-y-0 left-0 w-1 ${accent[tone]}`} /><p className="text-sm font-medium text-slate-500">{label}</p><p className="mt-2 text-3xl font-bold tracking-tight text-slate-900">{value}</p><p className="mt-1 text-xs text-slate-500">{note}</p></div>;
}
