import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  BarChart3,
  CheckSquare,
  FileText,
  History,
  Layers,
  Map,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  X,
} from 'lucide-react';

const workspaces = [
  { label: 'Command Center', detail: 'Interactive GIS overview', path: '/dashboard', icon: Map },
  { label: 'AI Intelligence', detail: 'Spatial analysis', path: '/ai-analysis', icon: Sparkles },
  { label: 'Surveyor Review', detail: 'Validation queue', path: '/review', icon: CheckSquare },
  { label: 'Spatial Analytics', detail: 'Metrics & patterns', path: '/analytics', icon: BarChart3 },
  { label: 'Property History', detail: 'Parcel timeline', path: '/history', icon: History },
  { label: 'Cadastral Reports', detail: 'Generate reports', path: '/reports', icon: FileText },
];

export function WorkspaceRail({ isOpen, collapsed, onToggleCollapse, onClose }) {
  const location = useLocation();

  return (
    <aside className={`cv-workspace-rail ${isOpen ? 'is-open' : ''} ${collapsed ? 'is-collapsed' : ''}`} aria-label="Workspace navigation">
      <div className="border-b border-white/10 px-5 py-5 lg:px-6">
          <div className="cv-workspace-brand flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#A7EBF2] text-[#011C40]">
            <Layers className="h-5 w-5" />
          </div>
          <div>
            <p className="font-display text-sm font-bold tracking-wider text-white">CADASTRA<span className="text-[#A7EBF2]">VISION</span></p>
            <p className="mt-1 text-[10px] text-white/45">Bengaluru East / Sector 4</p>
          </div>
        </div>
        <div className="cv-workspace-heading mt-5 flex items-center justify-between">
          <div>
            <p className="cv-kicker text-[#D4C7A1]">Workspaces</p>
            <p className="mt-1 text-xs text-white/45">Spatial operations</p>
          </div>
          <button onClick={onClose} className="cv-icon-button lg:hidden" aria-label="Close workspace navigation">
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      <button
        type="button"
        onClick={onToggleCollapse}
        className="cv-sidebar-toggle"
        aria-label={collapsed ? 'Expand workspace sidebar' : 'Collapse workspace sidebar'}
        title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
      </button>

      <nav className="cv-workspace-nav flex-1 space-y-1.5 overflow-y-auto px-3 py-5" aria-label="CadastraVision workspaces">
        {workspaces.map(({ label, detail, path, icon: Icon }) => {
          const active = location.pathname === path;
          return (
            <NavLink
              key={path}
              to={path}
              onClick={onClose}
              className={`cv-workspace-item ${active ? 'is-active' : ''}`}
              aria-current={active ? 'page' : undefined}
            >
              <span className="cv-workspace-icon"><Icon className="h-4 w-4" /></span>
              <span className="cv-workspace-copy min-w-0">
                <span className="block truncate text-[11px] font-bold tracking-wide">{label}</span>
                <span className="mt-0.5 block truncate text-[10px] text-white/40">{detail}</span>
              </span>
              <span className="cv-workspace-dot" aria-hidden="true" />
            </NavLink>
          );
        })}
      </nav>

      <div className="cv-workspace-project border-t border-white/10 p-4">
        <div className="rounded-xl border border-[#54ACBF]/25 bg-[#023859]/50 p-3">
          <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.16em] text-[#A7EBF2]">
            <Layers className="h-3.5 w-3.5" />
            <span>Active Project</span>
          </div>
          <p className="mt-2 text-xs font-semibold text-white">Bengaluru East</p>
          <p className="mt-0.5 font-mono text-[10px] text-white/45">SECTOR 04 / LIVE</p>
        </div>
      </div>
    </aside>
  );
}
