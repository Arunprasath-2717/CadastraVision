import React, { useMemo, useState } from 'react';
import { Clock3, MapPinned, Building2, Route, Landmark, ArrowRight, History as HistoryIcon } from 'lucide-react';

const timeline = [
  {
    id: 'evt-201',
    date: '12 Mar 2024',
    type: 'Boundary change',
    title: 'Parcel P-1024 boundary realignment',
    description: 'Northern edge adjusted by 2.4 m to align with the latest surveyed road reserve.',
    impact: 'Low',
    category: 'boundary',
    metadata: 'Surveyor update • Zone B',
  },
  {
    id: 'evt-202',
    date: '27 Jan 2024',
    type: 'Building change',
    title: 'Warehouse expansion recorded',
    description: 'Commercial structure added 128 m² in the southeastern corridor, requiring validation.',
    impact: 'Medium',
    category: 'building',
    metadata: 'AI classification • Sector 4',
  },
  {
    id: 'evt-203',
    date: '18 Dec 2023',
    type: 'Road change',
    title: 'Access lane alignment updated',
    description: 'Municipal service road widened and repositioned adjacent to parcel cluster C12.',
    impact: 'Medium',
    category: 'road',
    metadata: 'GIS team • Utility review',
  },
  {
    id: 'evt-204',
    date: '06 Nov 2023',
    type: 'Parcel change',
    title: 'Land use record updated',
    description: 'Agricultural parcel reclassified to mixed-use with updated tax documentation.',
    impact: 'High',
    category: 'parcel',
    metadata: 'Registry sync • East block',
  },
];

const categoryMeta = {
  parcel: { label: 'Parcel', icon: Landmark },
  boundary: { label: 'Boundary', icon: MapPinned },
  building: { label: 'Building', icon: Building2 },
  road: { label: 'Road', icon: Route },
};

export function HistoryPage() {
  const [selectedEvent, setSelectedEvent] = useState(timeline[0]);

  const selectedDetails = useMemo(() => {
    return categoryMeta[selectedEvent.category] || categoryMeta.parcel;
  }, [selectedEvent]);

  return (
    <div className="h-full w-full overflow-y-auto bg-pastel-bg p-4 lg:p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="rounded-3xl border border-pastel-border bg-white/90 p-5 shadow-pastel-md backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl bg-violet-100 p-3 text-violet-700">
              <HistoryIcon className="h-5 w-5" />
            </div>
            <div>
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-pastel-muted">Registry Timeline</p>
              <h1 className="text-xl font-bold text-pastel-text">Cadastral History</h1>
            </div>
          </div>
        </header>

        <section className="grid grid-cols-12 gap-4 lg:gap-6">
          <div className="col-span-12 lg:col-span-5 rounded-3xl border border-pastel-border bg-white p-4 shadow-pastel-sm">
            <div className="mb-4 flex items-center gap-2">
              <Clock3 className="h-4 w-4 text-pastel-action" />
              <h2 className="text-base font-bold text-pastel-text">Change timeline</h2>
            </div>

            <div className="space-y-3">
              {timeline.map((event) => {
                const Icon = categoryMeta[event.category].icon;
                const isActive = selectedEvent.id === event.id;
                return (
                  <button
                    key={event.id}
                    onClick={() => setSelectedEvent(event)}
                    className={`w-full rounded-2xl border p-3 text-left transition-all ${
                      isActive
                        ? 'border-pastel-action bg-pastel-lavender/70 shadow-pastel-sm'
                        : 'border-pastel-border bg-pastel-surface-soft hover:bg-white'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3">
                        <div className="rounded-xl bg-white p-2 text-pastel-action shadow-pastel-sm">
                          <Icon className="h-4 w-4" />
                        </div>
                        <div>
                          <p className="text-[10px] font-mono uppercase tracking-[0.16em] text-pastel-muted">{event.date}</p>
                          <p className="mt-1 font-semibold text-pastel-text">{event.title}</p>
                        </div>
                      </div>
                      <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-semibold text-pastel-action">{event.impact}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="col-span-12 lg:col-span-7 rounded-3xl border border-pastel-border bg-white p-5 shadow-pastel-sm">
            <div className="flex items-center justify-between gap-3 border-b border-pastel-border pb-4">
              <div>
                <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-pastel-muted">Selected Event</p>
                <h2 className="mt-1 text-xl font-bold text-pastel-text">{selectedEvent.title}</h2>
              </div>
              <div className="rounded-full border border-pastel-border bg-pastel-surface-soft px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-pastel-muted">
                {selectedEvent.type}
              </div>
            </div>

            <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="rounded-2xl border border-pastel-border bg-pastel-surface-soft p-4">
                <div className="flex items-center gap-2 text-pastel-action">
                  <selectedDetails.icon className="h-4 w-4" />
                  <span className="text-xs font-semibold uppercase tracking-[0.14em]">{selectedDetails.label}</span>
                </div>
                <p className="mt-3 text-sm leading-relaxed text-pastel-text">{selectedEvent.description}</p>
              </div>

              <div className="rounded-2xl border border-pastel-border bg-white p-4">
                <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-pastel-muted">Metadata</p>
                <ul className="mt-3 space-y-2 text-sm text-pastel-text">
                  <li><span className="text-pastel-muted">Date:</span> {selectedEvent.date}</li>
                  <li><span className="text-pastel-muted">Impact:</span> {selectedEvent.impact}</li>
                  <li><span className="text-pastel-muted">Source:</span> {selectedEvent.metadata}</li>
                </ul>
              </div>
            </div>

            <div className="mt-6 rounded-2xl bg-gradient-to-r from-sky-50 via-white to-violet-50 p-4 border border-sky-200">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-pastel-muted">Historical snapshot</p>
                  <p className="mt-1 font-semibold text-pastel-text">Before/after comparison available</p>
                </div>
                <button className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-3 py-2 text-[11px] font-semibold text-white">
                  View snapshot <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
