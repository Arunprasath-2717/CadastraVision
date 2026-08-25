import React, { useState } from 'react';
import { FileText, Download, Sparkles, CheckCircle2, ShieldCheck, MapPinned, ChevronDown } from 'lucide-react';
import { GlowingButton } from '../components/common/GlowingButton';

const reportTypes = ['Parcel Summary', 'AI Analysis Summary', 'Validation Summary', 'Compliance Review'];

const parcelList = ['P-1024', 'P-1025', 'P-1026', 'P-1027'];

export function ReportsPage() {
  const [selectedType, setSelectedType] = useState(reportTypes[0]);
  const [selectedParcel, setSelectedParcel] = useState(parcelList[0]);

  return (
    <div className="h-full w-full overflow-y-auto bg-pastel-bg p-4 lg:p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="rounded-3xl border border-pastel-border bg-white/90 p-5 shadow-pastel-md backdrop-blur-sm">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-2xl bg-cyan-100 p-3 text-cyan-700">
                <FileText className="h-5 w-5" />
              </div>
              <div>
                <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-pastel-muted">Documentation</p>
                <h1 className="text-xl font-bold text-pastel-text">Reports & Export</h1>
              </div>
            </div>
            <GlowingButton variant="primary-glow" size="sm" icon={Download}>Export PDF</GlowingButton>
          </div>
        </header>

        <section className="grid grid-cols-12 gap-4 lg:gap-6">
          <div className="col-span-12 lg:col-span-4 rounded-3xl border border-pastel-border bg-white p-5 shadow-pastel-sm">
            <div className="space-y-4">
              <div>
                <label className="mb-2 block text-[10px] font-mono uppercase tracking-[0.18em] text-pastel-muted">Report Type</label>
                <div className="relative">
                  <select
                    value={selectedType}
                    onChange={(e) => setSelectedType(e.target.value)}
                    className="w-full appearance-none rounded-xl border border-pastel-border bg-pastel-surface-soft px-3 py-2.5 text-sm text-pastel-text outline-none"
                  >
                    {reportTypes.map((type) => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                  <ChevronDown className="pointer-events-none absolute right-3 top-3.5 h-4 w-4 text-pastel-muted" />
                </div>
              </div>

              <div>
                <label className="mb-2 block text-[10px] font-mono uppercase tracking-[0.18em] text-pastel-muted">Parcel Selection</label>
                <div className="relative">
                  <select
                    value={selectedParcel}
                    onChange={(e) => setSelectedParcel(e.target.value)}
                    className="w-full appearance-none rounded-xl border border-pastel-border bg-pastel-surface-soft px-3 py-2.5 text-sm text-pastel-text outline-none"
                  >
                    {parcelList.map((parcel) => (
                      <option key={parcel} value={parcel}>{parcel}</option>
                    ))}
                  </select>
                  <ChevronDown className="pointer-events-none absolute right-3 top-3.5 h-4 w-4 text-pastel-muted" />
                </div>
              </div>

              <div className="rounded-2xl border border-pastel-border bg-pastel-surface-soft p-4">
                <p className="text-[10px] font-mono uppercase tracking-[0.18em] text-pastel-muted">Current selection</p>
                <div className="mt-2 flex items-center gap-2 text-pastel-text">
                  <MapPinned className="h-4 w-4 text-pastel-action" />
                  <span className="font-semibold">{selectedParcel}</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-2xl border border-pastel-border bg-blue-50 p-3">
                  <p className="text-[10px] font-mono uppercase tracking-[0.16em] text-blue-700">AI score</p>
                  <p className="mt-2 text-xl font-bold text-blue-800">94%</p>
                </div>
                <div className="rounded-2xl border border-pastel-border bg-emerald-50 p-3">
                  <p className="text-[10px] font-mono uppercase tracking-[0.16em] text-emerald-700">Validation</p>
                  <p className="mt-2 text-xl font-bold text-emerald-800">Pass</p>
                </div>
              </div>
            </div>
          </div>

          <div className="col-span-12 lg:col-span-8 rounded-3xl border border-pastel-border bg-white p-5 shadow-pastel-sm">
            <div className="mb-4 flex items-center gap-2">
              <div className="rounded-xl bg-violet-100 p-2 text-violet-700">
                <Sparkles className="h-4 w-4" />
              </div>
              <h2 className="text-lg font-bold text-pastel-text">Report preview</h2>
            </div>

            <div className="rounded-3xl border border-pastel-border bg-gradient-to-br from-slate-50 to-white p-5">
              <div className="flex items-start justify-between gap-4 border-b border-pastel-border pb-4">
                <div>
                  <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-pastel-muted">CadastraVision</p>
                  <h3 className="mt-2 text-xl font-bold text-pastel-text">{selectedType}</h3>
                </div>
                <div className="rounded-full bg-emerald-100 px-2.5 py-1 text-[10px] font-semibold text-emerald-800">Approved</div>
              </div>

              <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-3">
                <div className="rounded-2xl border border-pastel-border bg-white p-3">
                  <div className="flex items-center gap-2 text-pastel-muted"><MapPinned className="h-4 w-4 text-blue-600" /> Parcel</div>
                  <p className="mt-2 text-lg font-bold text-pastel-text">{selectedParcel}</p>
                </div>
                <div className="rounded-2xl border border-pastel-border bg-white p-3">
                  <div className="flex items-center gap-2 text-pastel-muted"><Sparkles className="h-4 w-4 text-violet-600" /> AI Summary</div>
                  <p className="mt-2 text-lg font-bold text-pastel-text">3 anomalies</p>
                </div>
                <div className="rounded-2xl border border-pastel-border bg-white p-3">
                  <div className="flex items-center gap-2 text-pastel-muted"><ShieldCheck className="h-4 w-4 text-emerald-600" /> Validation</div>
                  <p className="mt-2 text-lg font-bold text-pastel-text">Passed</p>
                </div>
              </div>

              <div className="mt-5 space-y-3 text-sm text-pastel-text">
                <p>Boundary geometry remains within tolerance for the selected parcel segment.</p>
                <p>AI-detected anomalies were reviewed and no critical topological conflicts remain unresolved.</p>
                <p>Survey recommendations were logged and marked as non-blocking in the current review cycle.</p>
              </div>

              <div className="mt-6 flex items-center justify-between gap-3 border-t border-pastel-border pt-4">
                <div className="flex items-center gap-2 text-xs text-pastel-muted">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" /> Ready for export
                </div>
                <GlowingButton variant="secondary-pastel" size="sm" icon={Download}>Prepare Export</GlowingButton>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
