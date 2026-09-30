import type { ReactNode } from 'react';

export function PageHeader({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-end"><div><h1 className="text-2xl font-bold tracking-tight text-slate-900">{title}</h1><p className="mt-1 text-sm text-slate-500">{description}</p></div>{action}</div>;
}

export function Notice({ children, tone = 'error' }: { children: ReactNode; tone?: 'error' | 'success' | 'info' }) {
  const colors = { error: 'border-red-200 bg-red-50 text-red-800', success: 'border-emerald-200 bg-emerald-50 text-emerald-800', info: 'border-sky-200 bg-sky-50 text-sky-800' };
  return <div role={tone === 'error' ? 'alert' : 'status'} className={`mb-4 rounded-lg border px-3 py-2.5 text-sm ${colors[tone]}`}>{children}</div>;
}

export function Panel({ title, children, action }: { title: string; children: ReactNode; action?: ReactNode }) {
  return <section className="rounded-xl border border-slate-200 bg-white shadow-sm"><div className="flex items-center justify-between border-b border-slate-100 px-5 py-4"><h2 className="font-semibold text-slate-900">{title}</h2>{action}</div><div className="p-5">{children}</div></section>;
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<span className="mt-1 block">{children}</span></label>;
}

export const inputClass = 'w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-teal-600 focus:ring-2 focus:ring-teal-100';
export const buttonClass = 'inline-flex items-center justify-center rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-55';
export const secondaryButtonClass = 'inline-flex items-center justify-center rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-55';

export function EmptyState({ children }: { children: ReactNode }) {
  return <div className="rounded-lg border border-dashed border-slate-300 px-5 py-10 text-center text-sm text-slate-500">{children}</div>;
}
