import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { 
  X, 
  User, 
  MapPin, 
  ShieldCheck, 
  Sliders, 
  HelpCircle, 
  LogOut, 
  Map, 
  Sparkles, 
  CheckSquare, 
  BarChart3, 
  History, 
  FileText, 
  ChevronRight
} from 'lucide-react';

export function ProfileDrawer({ isOpen, onClose }) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleLogout = () => {
    logout();
    onClose();
    navigate('/login');
  };

  const handleNav = (path) => {
    navigate(path);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden animate-fade-in">
      <div 
        onClick={onClose}
        className="absolute inset-0 bg-[rgba(1,28,64,0.5)] backdrop-blur-sm transition-opacity duration-300"
      />

      <div className="absolute inset-y-0 right-0 flex max-w-full pl-10">
        <div className="flex w-screen max-w-md flex-col justify-between overflow-y-auto border-l border-[#A7EBF2]/60 bg-[linear-gradient(180deg,rgba(247,252,254,0.98),rgba(228,244,250,0.96))] shadow-[0_25px_70px_rgba(1,28,64,0.28)] transition-transform duration-300">
          <div className="flex items-center justify-between border-b border-[#C9E5EE] bg-[linear-gradient(135deg,rgba(2,56,89,0.96),rgba(1,28,64,0.96))] p-6 text-white">
            <div className="flex items-center space-x-2">
              <div className="h-2.5 w-2.5 animate-pulse rounded-full bg-[#A7EBF2]" />
              <span className="font-mono text-[11px] font-semibold uppercase tracking-[0.22em] text-[#D7F7FF]">
                CADASTRAVISION SESSION
              </span>
            </div>
            <button 
              onClick={onClose}
              className="rounded-xl p-2 text-[#D7F7FF] transition-colors hover:bg-white/10 hover:text-white"
              title="Close Drawer (Esc)"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="flex-1 space-y-6 p-6">
            <div className="rounded-2xl border border-[#A7EBF2]/60 bg-[linear-gradient(135deg,rgba(167,235,242,0.24),rgba(84,172,191,0.08),rgba(255,255,255,0.78))] p-5 shadow-[0_14px_32px_rgba(2,56,89,0.08)]">
              <div className="flex items-center space-x-4">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#023859,#54ACBF)] text-xl font-bold text-white shadow-[0_10px_22px_rgba(2,56,89,0.22)] ring-4 ring-white/60">
                  {user?.name ? user.name.charAt(0) : 'M'}
                </div>
                <div>
                  <h3 className="font-display text-base font-bold text-[#011C40]">
                    {user?.name || 'Muthulakshmi S.'}
                  </h3>
                  <p className="text-xs font-medium text-[#4F7285]">
                    {user?.role || 'Senior Cadastral Surveyor'}
                  </p>
                  <div className="mt-2 flex items-center space-x-2 text-[11px]">
                    <span className="inline-flex items-center rounded-full border border-[#A7EBF2] bg-white/80 px-2.5 py-0.5 font-medium text-[#266580] shadow-[0_6px_18px_rgba(2,56,89,0.08)]">
                      <ShieldCheck className="mr-1 h-3 w-3" />
                      {user?.jurisdiction || 'Bengaluru East'}
                    </span>
                    <span className="inline-flex items-center rounded-full bg-emerald-100 px-2 py-0.5 font-mono text-[10px] font-semibold text-emerald-800">
                      ● Online
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between border-t border-[#C9E5EE]/80 pt-3 text-xs text-[#4F7285]">
                <span className="flex items-center space-x-1 font-mono text-[11px]">
                  <MapPin className="h-3.5 w-3.5 text-[#266580]" />
                  <span>Sector 4 • Zone B</span>
                </span>
                <span className="rounded border border-[#C9E5EE] bg-white/75 px-2 py-0.5 font-mono text-[10px] text-[#6F8DA0]">
                  ID: USR-4092
                </span>
              </div>
            </div>

            <div>
              <h4 className="mb-2 px-1 font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-[#4F7285]">
                WORKSPACES
              </h4>
              <div className="space-y-1">
                {[
                  { label: 'Command Center', path: '/dashboard', icon: Map },
                  { label: 'AI Intelligence', path: '/ai-analysis', icon: Sparkles },
                  { label: 'Surveyor Review Queue', path: '/review', icon: CheckSquare },
                  { label: 'Spatial Analytics', path: '/analytics', icon: BarChart3 },
                  { label: 'Property History Timeline', path: '/history', icon: History },
                  { label: 'Cadastral Reports', path: '/reports', icon: FileText },
                ].map((item) => {
                  const ItemIcon = item.icon;
                  return (
                    <button
                      key={item.path}
                      onClick={() => handleNav(item.path)}
                      className="group flex w-full items-center justify-between rounded-xl p-3 text-left transition-all duration-200 hover:-translate-x-0.5 hover:bg-[linear-gradient(135deg,rgba(167,235,242,0.18),rgba(84,172,191,0.08))]"
                    >
                      <div className="flex items-center space-x-3 text-xs font-semibold text-[#011C40]">
                        <div className="rounded-lg bg-[linear-gradient(135deg,rgba(167,235,242,0.42),rgba(84,172,191,0.12))] p-1.5 text-[#266580] transition-colors group-hover:bg-[linear-gradient(135deg,#023859,#266580)] group-hover:text-white">
                          <ItemIcon className="h-4 w-4" />
                        </div>
                        <span>{item.label}</span>
                      </div>
                      <ChevronRight className="h-4 w-4 text-[#6F8DA0] transition-transform group-hover:translate-x-1" />
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <h4 className="mb-2 px-1 font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-[#4F7285]">
                ACCOUNT & SUPPORT
              </h4>
              <div className="space-y-1">
                <button className="flex w-full items-center space-x-3 rounded-xl p-3 text-left text-xs font-medium text-[#011C40] transition-all duration-200 hover:bg-[linear-gradient(135deg,rgba(167,235,242,0.18),rgba(84,172,191,0.08))]">
                  <User className="h-4 w-4 text-[#4F7285]" />
                  <span>Profile Settings</span>
                </button>
                <button className="flex w-full items-center space-x-3 rounded-xl p-3 text-left text-xs font-medium text-[#011C40] transition-all duration-200 hover:bg-[linear-gradient(135deg,rgba(167,235,242,0.18),rgba(84,172,191,0.08))]">
                  <Sliders className="h-4 w-4 text-[#4F7285]" />
                  <span>GIS Map Preferences</span>
                </button>
                <button className="flex w-full items-center space-x-3 rounded-xl p-3 text-left text-xs font-medium text-[#011C40] transition-all duration-200 hover:bg-[linear-gradient(135deg,rgba(167,235,242,0.18),rgba(84,172,191,0.08))]">
                  <HelpCircle className="h-4 w-4 text-[#4F7285]" />
                  <span>CadastraVision Help & Docs</span>
                </button>
              </div>
            </div>
          </div>

          <div className="border-t border-[#C9E5EE] bg-[linear-gradient(180deg,rgba(238,249,251,0.8),rgba(247,252,254,0.95))] p-6">
            <button
              onClick={handleLogout}
              className="flex w-full items-center justify-center space-x-2 rounded-xl border border-rose-200 bg-rose-50 px-4 py-2.5 text-xs font-semibold text-rose-700 transition-all duration-200 hover:-translate-y-0.5 hover:bg-rose-100"
            >
              <LogOut className="h-4 w-4" />
              <span>Sign Out of Session</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
