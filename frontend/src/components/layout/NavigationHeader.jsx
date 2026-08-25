import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useMapSelection } from '../../context/MapContext';
import { OfflineBanner } from '../common/OfflineBanner';
import { 
  Layers, 
  Search, 
  MapPin, 
  Map, 
  Sparkles, 
  CheckSquare, 
  BarChart3, 
  History, 
  FileText, 
  Menu, 
  X,
  ChevronDown
} from 'lucide-react';

export function NavigationHeader({ onOpenProfile }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { selectParcel } = useMapSelection();

  const [searchQuery, setSearchQuery] = useState('');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

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

  const navItems = [
    { label: 'Command Center', path: '/dashboard', icon: Map },
    { label: 'AI Intelligence', path: '/ai-analysis', icon: Sparkles },
    { label: 'Surveyor Review', path: '/review', icon: CheckSquare },
    { label: 'Analytics', path: '/analytics', icon: BarChart3 },
    { label: 'History', path: '/history', icon: History },
    { label: 'Reports', path: '/reports', icon: FileText },
  ];

  return (
    <header className="relative z-30 h-16 shrink-0 border-b border-[#C9E5EE] bg-[linear-gradient(180deg,rgba(247,252,254,0.96),rgba(228,246,252,0.92))] px-4 backdrop-blur-xl lg:px-6 shadow-[0_10px_28px_rgba(1,28,64,0.08)]">
      <div className="flex h-full items-center justify-between text-pastel-text">
        <div className="flex items-center space-x-6 shrink-0">
          <Link to="/dashboard" className="flex items-center space-x-3 group">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-[#A7EBF2] bg-[linear-gradient(135deg,#023859,#266580)] text-white shadow-[0_10px_20px_rgba(2,56,89,0.25)] transition-all duration-300 group-hover:scale-105 group-hover:shadow-[0_16px_28px_rgba(38,101,128,0.26)]">
              <Layers className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="font-display text-base font-bold tracking-wider text-[#011C40] lg:text-lg">
                  CADASTRA<span className="text-[#266580]">VISION</span>
                </span>
                <span className="hidden sm:inline-block rounded bg-[#DFF9FD] px-1.5 py-0.5 text-[10px] font-mono font-semibold text-[#023859]">
                  PRO
                </span>
              </div>
              <div className="hidden items-center space-x-1 text-[10px] font-mono text-pastel-muted sm:flex">
                <MapPin className="h-3 w-3 text-[#266580]" />
                <span>Bengaluru East • Sector 4</span>
              </div>
            </div>
          </Link>
        </div>

        <nav className="hidden items-center space-x-1 xl:flex">
          {navItems.map((item) => {
            const ItemIcon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`group relative flex items-center space-x-2 rounded-xl px-3.5 py-2 text-xs font-semibold transition-all duration-200 ${
                  isActive
                    ? 'border border-[#A7EBF2] bg-[linear-gradient(135deg,rgba(167,235,242,0.30),rgba(84,172,191,0.12))] text-[#023859] shadow-[0_8px_24px_rgba(2,56,89,0.08)]'
                    : 'text-pastel-muted hover:bg-[linear-gradient(135deg,rgba(167,235,242,0.18),rgba(84,172,191,0.06))] hover:text-[#011C40]'
                }`}
              >
                <ItemIcon className={`h-4 w-4 transition-transform duration-200 ${isActive ? 'text-[#266580] group-hover:-translate-y-0.5' : 'text-pastel-subtle group-hover:-translate-y-0.5'}`} />
                <span>{item.label}</span>
                {isActive && (
                  <span className="absolute bottom-0 left-3 right-3 h-[2px] rounded-full bg-[linear-gradient(90deg,#54ACBF,#266580)]" />
                )}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center space-x-3">
          <form onSubmit={handleSearchSubmit} className="hidden w-full max-w-xs items-center md:flex">
            <div className="relative w-full">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search parcel ID (e.g. P-1024)..."
                className="w-full rounded-xl border border-[#C9E5EE] bg-[linear-gradient(180deg,rgba(247,252,254,0.98),rgba(233,246,252,0.92))] py-1.5 pl-8 pr-3 text-xs text-[#011C40] placeholder-[#6F8DA0] shadow-[0_8px_20px_rgba(2,56,89,0.06)] transition-all focus:border-[#54ACBF] focus:ring-1 focus:ring-[#54ACBF]"
              />
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-[#6F8DA0]" />
            </div>
          </form>

          <div className="hidden sm:block">
            <OfflineBanner />
          </div>

          <button
            onClick={onOpenProfile}
            className="group flex items-center space-x-2 rounded-xl border border-[#C9E5EE] bg-[linear-gradient(135deg,rgba(247,252,254,0.98),rgba(220,244,250,0.9))] p-1.5 pl-2.5 pr-2 text-left shadow-[0_8px_20px_rgba(2,56,89,0.06)] transition-all duration-200 hover:-translate-y-0.5 hover:border-[#54ACBF] hover:shadow-[0_12px_26px_rgba(2,56,89,0.12)]"
            title="Open Profile Drawer"
          >
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[linear-gradient(135deg,#023859,#54ACBF)] text-xs font-bold text-white shadow-[0_8px_18px_rgba(2,56,89,0.25)]">
              {user?.name ? user.name.charAt(0) : 'M'}
            </div>
            <div className="hidden text-xs lg:block">
              <div className="font-semibold leading-tight text-[#011C40] transition-colors group-hover:text-[#266580]">
                {user?.name || 'Muthulakshmi S.'}
              </div>
              <div className="font-mono text-[10px] leading-none text-pastel-muted">
                {user?.role || 'Surveyor'}
              </div>
            </div>
            <ChevronDown className="h-3.5 w-3.5 text-pastel-subtle transition-colors group-hover:text-[#266580]" />
          </button>

          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="rounded-xl border border-[#C9E5EE] bg-[linear-gradient(180deg,rgba(247,252,254,0.96),rgba(220,244,250,0.9))] p-2 text-pastel-muted transition-all hover:border-[#54ACBF] hover:text-[#023859] xl:hidden"
            title="Toggle Navigation Menu"
          >
            {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {isMobileMenuOpen && (
        <div className="absolute left-0 right-0 top-16 z-50 space-y-2 border-b border-[#C9E5EE] bg-[linear-gradient(180deg,rgba(247,252,254,0.98),rgba(232,246,252,0.96))] p-4 shadow-[0_18px_38px_rgba(1,28,64,0.12)] xl:hidden animate-fade-in">
          <form onSubmit={handleSearchSubmit} className="mb-3">
            <div className="relative w-full">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search parcel ID (e.g. P-1024)..."
                className="w-full rounded-xl border border-[#C9E5EE] bg-white/80 py-2 pl-8 pr-3 text-xs text-[#011C40]"
              />
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-pastel-subtle" />
            </div>
          </form>

          <div className="grid grid-cols-2 gap-2">
            {navItems.map((item) => {
              const ItemIcon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`flex items-center space-x-2 rounded-xl p-2.5 text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-[linear-gradient(135deg,#023859,#266580)] text-white shadow-[0_12px_24px_rgba(2,56,89,0.18)]'
                      : 'bg-[linear-gradient(180deg,rgba(247,252,254,0.95),rgba(226,240,248,0.9))] text-[#011C40] hover:border hover:border-[#A7EBF2]'
                  }`}
                >
                  <ItemIcon className="h-4 w-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </header>
  );
}
