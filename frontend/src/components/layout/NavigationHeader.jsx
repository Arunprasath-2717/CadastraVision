import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useMapSelection } from '../../context/MapContext';
import { OfflineBanner } from '../common/OfflineBanner';
import { 
  Layers, 
  Search, 
  MapPin, 
  Menu, 
  ChevronDown
} from 'lucide-react';

export function NavigationHeader({ onOpenProfile, onOpenWorkspace }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { selectParcel } = useMapSelection();

  const [searchQuery, setSearchQuery] = useState('');

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (!searchQuery) return;
    const cleanId = searchQuery.trim().toUpperCase();
    const formattedId = cleanId.startsWith('P-') ? cleanId : `P-${cleanId}`;
    
    // Select parcel and navigate to dashboard if on another route
    selectParcel(formattedId, true);
    if (location.pathname !== '/dashboard') {
      navigate('/dashboard');
    }
  };

  return (
    <header className="relative z-30 h-[72px] shrink-0 border-b border-[#54ACBF]/20 bg-[#011C40]/95 px-4 text-white shadow-[0_12px_30px_rgba(1,28,64,0.22)] backdrop-blur-xl lg:px-6">
      <div className="flex h-full items-center justify-between text-pastel-text">
        <div className="flex items-center space-x-6 shrink-0">
          <Link to="/dashboard" className="flex items-center space-x-3 group">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-[#A7EBF2] bg-[linear-gradient(135deg,#023859,#266580)] text-white shadow-[0_10px_20px_rgba(2,56,89,0.25)] transition-all duration-300 group-hover:scale-105 group-hover:shadow-[0_16px_28px_rgba(38,101,128,0.26)]">
              <Layers className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="font-display text-base font-bold tracking-wider text-white lg:text-lg">
                  CADASTRA<span className="text-[#266580]">VISION</span>
                </span>
                <span className="hidden sm:inline-block rounded bg-[#54ACBF]/20 px-1.5 py-0.5 text-[10px] font-mono font-semibold text-[#A7EBF2]">
                  PRO
                </span>
              </div>
              <div className="hidden items-center space-x-1 text-[10px] font-mono text-pastel-muted sm:flex">
                <MapPin className="h-3 w-3 text-[#266580]" />
                <span>Bengaluru East / Sector 4</span>
              </div>
            </div>
          </Link>
        </div>

        <div className="flex items-center space-x-3">
          <form onSubmit={handleSearchSubmit} className="hidden w-full max-w-xs items-center md:flex">
            <div className="relative w-full">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search parcel ID (e.g. P-1024)..."
                className="w-full rounded-xl border border-white/15 bg-white/10 py-2 pl-8 pr-3 text-xs text-white placeholder-white/40 transition-all focus:border-[#A7EBF2] focus:ring-1 focus:ring-[#54ACBF]"
              />
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-[#6F8DA0]" />
            </div>
          </form>

          <div className="hidden sm:block">
            <OfflineBanner />
          </div>

          <button
            onClick={onOpenProfile}
            className="group flex items-center space-x-2 rounded-xl border border-white/15 bg-white/10 p-1.5 pl-2.5 pr-2 text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-[#A7EBF2] hover:bg-white/15"
            title="Open Profile Drawer"
          >
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[linear-gradient(135deg,#023859,#54ACBF)] text-xs font-bold text-white shadow-[0_8px_18px_rgba(2,56,89,0.25)]">
              {user?.name ? user.name.charAt(0) : 'M'}
            </div>
            <div className="hidden text-xs lg:block">
                <div className="font-semibold leading-tight text-white transition-colors group-hover:text-[#A7EBF2]">
                {user?.name || 'Muthulakshmi S.'}
              </div>
                <div className="font-mono text-[10px] leading-none text-white/45">
                {user?.role || 'Surveyor'}
              </div>
            </div>
            <ChevronDown className="h-3.5 w-3.5 text-pastel-subtle transition-colors group-hover:text-[#266580]" />
          </button>

          <button
            onClick={onOpenWorkspace}
            className="cv-icon-button lg:hidden"
            title="Toggle Navigation Menu"
          >
            <Menu className="h-5 w-5" />
          </button>
        </div>
      </div>

    </header>
  );
}
