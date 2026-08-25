import React from 'react';
import { TrendingUp, MapPinned, Building2, Route, CheckCircle2, BrainCircuit, BarChart3, ShieldCheck, Sparkles } from 'lucide-react';
import { GlowingButton } from '../components/common/GlowingButton';

const kpis = [
  { label: 'Parcels', value: '1,284', delta: '+4.2%', tone: 'bg-blue-50 text-blue-700 border-blue-200' },
  { label: 'Buildings', value: '3,902', delta: '+6.8%', tone: 'bg-violet-50 text-violet-700 border-violet-200' },
  { label: 'Roads', value: '116 km', delta: '+2.1%', tone: 'bg-cyan-50 text-cyan-700 border-cyan-200' },
  { label: 'Validation', value: '94.6%', delta: '+1.4%', tone: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
];

const confidence = [
  { label: 'High', value: 68, color: 'bg-emerald-500' },
  { label: 'Medium', value: 22, color: 'bg-amber-500' },
  { label: 'Low', value: 10, color: 'bg-rose-500' },
];

const trends = [
  { label: 'Boundary', value: 82 },
  { label: 'Roads', value: 73 },
  { label: 'Buildings', value: 91 },
  { label: 'Risk', value: 64 },
  { label: 'Review', value: 87 },
];

const insights = [
  { title: 'Parcel confidence improved', detail: 'Validation precision rose 1.4% over the last 7 days.', meta: 'Updated 3h ago' },
  { title: 'Road network drift detected', detail: '3 new access corridors require survey verification.', meta: '2 flagged parcels' },
  { title: 'AI detection stability', detail: 'Anomaly classification remains stable across Sector 4 and 6.', meta: '92.4% confidence' },
];

export function AnalyticsPage() {
  return (
    <div className="h-full w-full overflow-y-auto bg-pastel-bg p-4 lg:p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="rounded-3xl border border-pastel-border bg-white/90 p-5 shadow-pastel-md backdrop-blur-sm">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-2xl bg-blue-100 p-3 text-blue-700">
                <BarChart3 className="h-5 w-5" />
              </div>
              <div>
                <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-pastel-muted">Operational Metrics</p>
                <h1 className="text-xl font-bold text-pastel-text">Analytics & Insights</h1>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <GlowingButton variant="secondary-pastel" size="sm" icon={Sparkles}>Refresh</GlowingButton>
              <GlowingButton variant="primary-glow" size="sm" icon={TrendingUp}>Export Snapshot</GlowingButton>
            </div>
          </div>
        </header>

        <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          {kpis.map((item) => (
            <div key={item.label} className={`rounded-2xl border p-4 shadow-pastel-sm ${item.tone}`}>
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono uppercase tracking-[0.16em]">{item.label}</span>
                <span className="text-[11px] font-semibold">{item.delta}</span>
              </div>
              <div className="mt-4 text-3xl font-bold text-pastel-text">{item.value}</div>
            </div>
          ))}
        </section>

        <section className="grid grid-cols-12 gap-4 lg:gap-6">
          <div className="col-span-12 xl:col-span-8 rounded-3xl border border-pastel-border bg-white p-5 shadow-pastel-sm">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-pastel-muted">Spatial Trends</p>
                <h2 className="text-lg font-bold text-pastel-text">Validation momentum</h2>
              </div>
              <span className="rounded-full bg-blue-100 px-2.5 py-1 text-[10px] font-semibold text-blue-700">Last 30 days</span>
            </div>

            <div className="flex h-56 items-end gap-3 rounded-2xl border border-pastel-border bg-pastel-surface-soft p-4">
              {trends.map((item) => (
                <div key={item.label} className="flex flex-1 flex-col items-center gap-3">
                  <div className="flex h-full w-full items-end justify-center">
                    <div
                      className="w-full rounded-t-2xl bg-gradient-to-t from-blue-400 via-sky-400 to-violet-300 shadow-[0_8px_18px_rgba(88,118,201,0.2)]"
                      style={{ height: `${item.value}%` }}
                    />
                  </div>
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-pastel-muted">{item.label}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="col-span-12 xl:col-span-4 rounded-3xl border border-pastel-border bg-white p-5 shadow-pastel-sm">
            <div className="mb-4 flex items-center gap-2">
              <div className="rounded-xl bg-violet-100 p-2 text-violet-700">
                <CheckCircle2 className="h-4 w-4" />
              </div>
              <h2 className="text-lg font-bold text-pastel-text">Confidence distribution</h2>
            </div>

            <div className="space-y-4">
              {confidence.map((item) => (
                <div key={item.label}>
                  <div className="mb-1 flex items-center justify-between text-xs font-semibold text-pastel-muted">
                    <span>{item.label}</span>
                    <span>{item.value}%</span>
                  </div>
                  <div className="h-2.5 overflow-hidden rounded-full bg-slate-100">
                    <div className={`h-full rounded-full ${item.color}`} style={{ width: `${item.value}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="grid grid-cols-12 gap-4 lg:gap-6">
          <div className="col-span-12 lg:col-span-7 rounded-3xl border border-pastel-border bg-white p-5 shadow-pastel-sm">
            <div className="mb-4 flex items-center gap-2">
              <div className="rounded-xl bg-cyan-100 p-2 text-cyan-700">
                <BrainCircuit className="h-4 w-4" />
              </div>
              <h2 className="text-lg font-bold text-pastel-text">AI detection statistics</h2>
            </div>

            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              <div className="rounded-2xl border border-pastel-border bg-pastel-surface-soft p-4">
                <div className="flex items-center gap-2 text-pastel-muted"><ShieldCheck className="h-4 w-4 text-emerald-600" /> Validated</div>
                <div className="mt-4 text-2xl font-bold text-pastel-text">876</div>
                <p className="text-[11px] text-pastel-muted">Autonomous approvals</p>
              </div>
              <div className="rounded-2xl border border-pastel-border bg-pastel-surface-soft p-4">
                <div className="flex items-center gap-2 text-pastel-muted"><MapPinned className="h-4 w-4 text-blue-600" /> Anomalies</div>
                <div className="mt-4 text-2xl font-bold text-pastel-text">42</div>
                <p className="text-[11px] text-pastel-muted">Flagged area insights</p>
              </div>
              <div className="rounded-2xl border border-pastel-border bg-pastel-surface-soft p-4">
                <div className="flex items-center gap-2 text-pastel-muted"><Route className="h-4 w-4 text-violet-600" /> Risk score</div>
                <div className="mt-4 text-2xl font-bold text-pastel-text">7.8</div>
                <p className="text-[11px] text-pastel-muted">Average sector severity</p>
              </div>
            </div>
          </div>

          <div className="col-span-12 lg:col-span-5 rounded-3xl border border-pastel-border bg-white p-5 shadow-pastel-sm">
            <div className="mb-4 flex items-center gap-2">
              <div className="rounded-xl bg-emerald-100 p-2 text-emerald-700">
                <TrendingUp className="h-4 w-4" />
              </div>
              <h2 className="text-lg font-bold text-pastel-text">Spatial insights</h2>
            </div>
            <div className="space-y-3">
              {insights.map((insight) => (
                <div key={insight.title} className="rounded-2xl border border-pastel-border bg-pastel-surface-soft p-3">
                  <p className="font-semibold text-pastel-text">{insight.title}</p>
                  <p className="mt-1 text-xs text-pastel-muted">{insight.detail}</p>
                  <p className="mt-2 text-[10px] font-mono uppercase tracking-[0.16em] text-pastel-action">{insight.meta}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
