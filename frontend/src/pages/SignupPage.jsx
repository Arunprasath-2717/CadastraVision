import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Layers, ShieldAlert, ArrowLeft, CheckCircle } from 'lucide-react';

export function SignupPage() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    staffId: '',
    department: 'Survey & Land Records Dept',
    password: '',
    confirmPassword: '',
  });

  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (formData.password !== formData.confirmPassword) {
      alert('Passwords do not match.');
      return;
    }
    setSubmitted(true);
  };

  return (
    <div className="min-h-screen bg-pastel-bg flex flex-col justify-center items-center p-6 relative topo-grid-pastel">
      <div className="w-full max-w-2xl bg-white rounded-3xl border border-pastel-border shadow-pastel-lg p-8">
        
        <div className="flex items-center justify-between mb-6">
          <Link to="/login" className="inline-flex items-center space-x-2 text-xs text-pastel-muted hover:text-pastel-text transition-colors">
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Sign In</span>
          </Link>
          <div className="flex items-center space-x-2 text-pastel-action">
            <Layers className="w-5 h-5" />
            <span className="font-bold tracking-wider font-display text-pastel-text">CADASTRALMAP</span>
          </div>
        </div>

        <h2 className="text-xl font-bold text-pastel-text">Staff Account Registration</h2>
        <p className="text-xs text-pastel-muted mt-1">Register for district GIS Cadastral Portal access</p>

        {submitted ? (
          <div className="my-8 p-6 bg-pastel-mint/30 border border-emerald-300 rounded-2xl text-center">
            <CheckCircle className="w-12 h-12 text-emerald-600 mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-pastel-mint-text">Registration Submitted Successfully</h3>
            <p className="text-xs text-pastel-muted mt-2 max-w-md mx-auto">
              Your staff registration for <strong className="text-pastel-text">{formData.email}</strong> is pending authorization from your District GIS Administrator.
            </p>
            <button
              onClick={() => navigate('/login')}
              className="mt-6 px-6 py-2.5 bg-pastel-action hover:bg-pastel-action-hover text-white font-medium text-xs rounded-xl shadow-pastel-sm transition-all"
            >
              Return to Login
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            
            {/* Notice about Role assignment */}
            <div className="p-3.5 bg-pastel-amber/40 border border-amber-300 rounded-xl text-pastel-amber-text text-xs flex items-center space-x-2.5">
              <ShieldAlert className="w-4 h-4 shrink-0 text-amber-700" />
              <span>Role assignment is managed by the district administrator upon verification of Staff ID.</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-pastel-text mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={formData.fullName}
                  onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                  placeholder="Muthulakshmi S."
                  className="w-full px-3.5 py-2 bg-pastel-surface-soft border border-pastel-border rounded-xl text-xs text-pastel-text focus:border-pastel-action focus:ring-1 focus:ring-pastel-action"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-pastel-text mb-1">Official Email</label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="name@cadastral.gov.in"
                  className="w-full px-3.5 py-2 bg-pastel-surface-soft border border-pastel-border rounded-xl text-xs text-pastel-text focus:border-pastel-action focus:ring-1 focus:ring-pastel-action"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-pastel-text mb-1">Government Staff ID</label>
                <input
                  type="text"
                  required
                  value={formData.staffId}
                  onChange={(e) => setFormData({ ...formData, staffId: e.target.value })}
                  placeholder="STF-4092"
                  className="w-full px-3.5 py-2 bg-pastel-surface-soft border border-pastel-border rounded-xl text-xs text-pastel-text focus:border-pastel-action focus:ring-1 focus:ring-pastel-action"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-pastel-text mb-1">Organization / Department</label>
                <select
                  value={formData.department}
                  onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                  className="w-full px-3.5 py-2 bg-pastel-surface-soft border border-pastel-border rounded-xl text-xs text-pastel-text focus:border-pastel-action"
                >
                  <option value="Survey & Land Records Dept">Survey & Land Records Dept</option>
                  <option value="Municipal GIS Administration">Municipal GIS Administration</option>
                  <option value="Town Planning Authority">Town Planning Authority</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-pastel-text mb-1">Password</label>
                <input
                  type="password"
                  required
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  placeholder="••••••••••••"
                  className="w-full px-3.5 py-2 bg-pastel-surface-soft border border-pastel-border rounded-xl text-xs text-pastel-text focus:border-pastel-action"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-pastel-text mb-1">Confirm Password</label>
                <input
                  type="password"
                  required
                  value={formData.confirmPassword}
                  onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                  placeholder="••••••••••••"
                  className="w-full px-3.5 py-2 bg-pastel-surface-soft border border-pastel-border rounded-xl text-xs text-pastel-text focus:border-pastel-action"
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full mt-4 py-3 bg-pastel-action hover:bg-pastel-action-hover text-white font-medium text-sm rounded-xl shadow-pastel-md transition-all"
            >
              Submit Registration
            </button>
          </form>
        )}

      </div>
    </div>
  );
}
