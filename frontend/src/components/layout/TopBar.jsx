import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useMapSelection } from '../../context/MapContext';
import { OfflineBanner } from '../common/OfflineBanner';
import { Layers, Search, LogOut, ShieldCheck, MapPin, BarChart3, Sparkles } from 'lucide-react';

export function TopBar({ onToggleAnalytics }) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { selectParcel } = useMapSelection();

  const [searchQuery, setSearchQuery] = useState('');
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (!searchQuery) return;
    const cleanId = searchQuery.trim().toUpperCase();
    const formattedId = cleanId.startsWith('P-') ? cleanId : `P-${cleanId}`;
    selectParcel(formattedId, true);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="h-16 bg-white border-b border-pastel-border px-6 flex items-center justify-between text-pastel-text shrink-0 relative z-30 shadow-pastel-sm">
      
      {/* Left: Brand Logo & Title */}
      <div className="flex items-center space-x-6">
        <Link to="/" className="flex items-center space-x-3 group">
          <div className="w-9 h-9 rounded-xl bg-pastel-lavender border border-pastel-border flex items-center justify-center text-pastel-action group-hover:border-pastel-action transition-all duration-300">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <span className="text-lg font-bold tracking-wider font-display text-pastel-text">CADASTRALMAP</span>
            <div className="flex items-center space-x-1 text-[10px] text-pastel-muted font-mono">
              <MapPin className="w-3 h-3 text-pastel-action" />
              <span>Bengaluru East • Sector 4</span>
            </div>
          </div>
        </Link>
      </div>

      {/* Center: Search Input Bar */}
      <form onSubmit={handleSearchSubmit} className="hidden md:flex items-center max-w-md w-full mx-6">
        <div className="relative w-full">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search parcel ID, zone, location..."
            className="w-full pl-9 pr-4 py-2 bg-pastel-surface-soft border border-pastel-border rounded-xl text-xs text-pastel-text placeholder-pastel-subtle focus:border-pastel-action focus:ring-1 focus:ring-pastel-action transition-all shadow-pastel-sm"
          />
          <Search className="w-4 h-4 text-pastel-subtle absolute left-3 top-2.5" />
        </div>
      </form>

      {/* Right Controls: Analytics Drawer Toggle, Offline Banner, Profile Menu */}
      <div className="flex items-center space-x-3">
        
        {/* Analytics Drawer Button */}
        {onToggleAnalytics && (
          <button
            onClick={onToggleAnalytics}
            className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 bg-pastel-lavender hover:bg-slate-200/60 text-pastel-action rounded-xl border border-pastel-border text-xs font-semibold transition-all shadow-pastel-sm"
            title="Cadastral Analytics Drawer"
          >
            <BarChart3 className="w-4 h-4" />
            <span>Analytics</span>
          </button>
        )}

        {/* Offline Status Banner */}
        <OfflineBanner />

        {/* User Profile Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            className="flex items-center space-x-2.5 p-1 rounded-xl hover:bg-pastel-surface-soft transition-colors text-left"
          >
            <div className="w-8 h-8 rounded-full bg-pastel-action text-white flex items-center justify-center font-bold text-xs shadow-pastel-sm">
              {user?.name ? user.name.charAt(0) : 'M'}
            </div>
            <div className="hidden sm:block text-xs">
              <div className="font-semibold text-pastel-text leading-tight">{user?.name || 'Muthulakshmi S.'}</div>
              <div className="text-[10px] text-pastel-muted font-mono">{user?.role || 'Surveyor'}</div>
            </div>
          </button>

          {showProfileMenu && (
            <div className="absolute right-0 mt-2 w-64 bg-white rounded-2xl border border-pastel-border p-3.5 shadow-pastel-lg text-xs text-pastel-muted z-50 animate-fade-in">
              <div className="border-b border-pastel-border pb-2.5 mb-2">
                <p className="font-semibold text-pastel-text">{user?.name}</p>
                <p className="text-[11px] text-pastel-muted">{user?.email}</p>
                <div className="mt-2 inline-flex items-center space-x-1 text-[10px] px-2 py-0.5 rounded-full bg-pastel-lavender text-pastel-action font-semibold">
                  <ShieldCheck className="w-3 h-3" />
                  <span>{user?.jurisdiction}</span>
                </div>
              </div>

              <button
                onClick={handleLogout}
                className="w-full text-left py-2 px-2.5 rounded-xl text-rose-600 hover:bg-rose-50 flex items-center space-x-2 transition-colors font-medium"
              >
                <LogOut className="w-4 h-4" />
                <span>Logout Session</span>
              </button>
            </div>
          )}
        </div>
      </div>

    </header>
  );
}
