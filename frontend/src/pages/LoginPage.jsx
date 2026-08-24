import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Layers, ShieldCheck, Lock, Mail, AlertCircle, Loader2 } from 'lucide-react';

export function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [username, setUsername] = useState('muthulakshmi@cadastral.gov.in');
  const [password, setPassword] = useState('••••••••••••');
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username || !password) {
      setError('Please enter your Email / Staff ID and password.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await login({ username, password });
      navigate('/dashboard');
    } catch (err) {
      setError(err.detail || 'Invalid staff credentials. Please check your credentials and retry.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-pastel-bg flex flex-col justify-center items-center p-6 relative topo-grid-pastel">
      <div className="w-full max-w-4xl bg-white rounded-3xl border border-pastel-border shadow-pastel-lg overflow-hidden grid grid-cols-1 md:grid-cols-2">
        
        {/* Left Side — Branding & Trust Context */}
        <div className="p-8 bg-pastel-lavender/60 flex flex-col justify-between border-b md:border-b-0 md:border-r border-pastel-border">
          <div>
            <Link to="/" className="flex items-center space-x-3 group mb-8">
              <div className="w-10 h-10 rounded-xl bg-white border border-pastel-border flex items-center justify-center text-pastel-action shadow-pastel-sm">
                <Layers className="w-5 h-5" />
              </div>
              <div>
                <span className="text-xl font-bold tracking-wider text-pastel-text font-display">CADASTRALMAP</span>
                <div className="text-[10px] text-pastel-muted tracking-widest uppercase">Surveyor Portal</div>
              </div>
            </Link>

            <h2 className="text-2xl font-bold text-pastel-text leading-snug">
              Official Government Land-Record GIS Workstation
            </h2>

            <p className="mt-3 text-sm text-pastel-muted leading-relaxed">
              Secure staff access for AI feature extraction, topology review, parcel boundary editing, and export authorization.
            </p>
          </div>

          <div className="mt-8 pt-6 border-t border-pastel-border space-y-3 text-xs text-pastel-muted">
            <div className="flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Role-Scoped JWT Authentication (FastAPI backend ready)</span>
            </div>
            <div className="flex items-center space-x-2">
              <Lock className="w-4 h-4 text-pastel-action" />
              <span>Immutable Hash-Chain Audit Logging</span>
            </div>
          </div>
        </div>

        {/* Right Side — Login Form */}
        <div className="p-8 flex flex-col justify-center bg-white">
          <div className="mb-6">
            <h3 className="text-xl font-semibold text-pastel-text">Sign in to your workspace</h3>
            <p className="text-xs text-pastel-muted mt-1">Enter your government staff email or ID</p>
          </div>

          {error && (
            <div className="mb-5 p-3 rounded-xl bg-pastel-rose/40 border border-rose-300 text-pastel-rose-text text-xs flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 text-rose-700 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-pastel-text mb-1.5" htmlFor="email-field">
                Official Email / Staff ID
              </label>
              <div className="relative">
                <input
                  id="email-field"
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="name@cadastral.gov.in"
                  className="w-full px-3.5 py-2.5 bg-pastel-surface-soft border border-pastel-border rounded-xl text-sm text-pastel-text placeholder-pastel-subtle focus:border-pastel-action focus:ring-1 focus:ring-pastel-action transition-colors"
                />
                <Mail className="w-4 h-4 text-pastel-subtle absolute right-3 top-3" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-pastel-text mb-1.5" htmlFor="password-field">
                Password
              </label>
              <div className="relative">
                <input
                  id="password-field"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full px-3.5 py-2.5 bg-pastel-surface-soft border border-pastel-border rounded-xl text-sm text-pastel-text placeholder-pastel-subtle focus:border-pastel-action focus:ring-1 focus:ring-pastel-action transition-colors"
                />
                <Lock className="w-4 h-4 text-pastel-subtle absolute right-3 top-3" />
              </div>
            </div>

            <div className="flex items-center justify-between text-xs">
              <label className="flex items-center space-x-2 text-pastel-muted cursor-pointer">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="rounded border-pastel-border bg-pastel-surface-soft text-pastel-action focus:ring-pastel-action"
                />
                <span>Remember me</span>
              </label>
              <a href="#forgot" onClick={(e) => { e.preventDefault(); alert('Please contact your district GIS Administrator to reset staff passwords.'); }} className="text-pastel-action hover:underline">
                Forgot password?
              </a>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-3 bg-pastel-action hover:bg-pastel-action-hover disabled:bg-slate-300 text-white font-medium text-sm rounded-xl shadow-pastel-md transition-all flex items-center justify-center space-x-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-white" />
                  <span>Authenticating...</span>
                </>
              ) : (
                <span>Sign In</span>
              )}
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-pastel-border text-center text-xs text-pastel-muted">
            <span>Don't have a staff account? </span>
            <Link to="/signup" className="text-pastel-action hover:underline font-medium">
              Create account
            </Link>
          </div>
        </div>

      </div>
    </div>
  );
}
