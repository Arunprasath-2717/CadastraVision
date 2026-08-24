import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, ShieldCheck, Clock, Check, Ban } from 'lucide-react';

/**
 * Dual-Encoded Pastel Confidence Badge (PRD-CM-04 Section 17 & WCAG 2.1 AA)
 * Combines pastel backgrounds with high-contrast text and explicit icon indicators.
 */
export function ConfidenceBadge({ band, score }) {
  const percent = Math.round(score * 100);

  if (band === 'HIGH' || score >= 0.8) {
    return (
      <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-pastel-mint/40 border border-emerald-300 text-pastel-mint-text text-xs font-semibold">
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700 shrink-0" />
        <span>{percent}% High Confidence</span>
      </span>
    );
  }

  if (band === 'MEDIUM' || (score >= 0.5 && score < 0.8)) {
    return (
      <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-pastel-amber/40 border border-amber-300 text-pastel-amber-text text-xs font-semibold">
        <AlertTriangle className="w-3.5 h-3.5 text-amber-700 shrink-0" />
        <span>{percent}% Med Confidence</span>
      </span>
    );
  }

  return (
    <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-pastel-rose/40 border border-rose-300 text-pastel-rose-text text-xs font-semibold">
      <XCircle className="w-3.5 h-3.5 text-rose-700 shrink-0" />
      <span>{percent}% Low Confidence</span>
    </span>
  );
}

/**
 * Validation Status Badge (Pastel Palette)
 */
export function StatusBadge({ status }) {
  switch (status) {
    case 'approved':
      return (
        <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-pastel-mint/50 border border-emerald-300 text-pastel-mint-text text-[11px] font-semibold">
          <Check className="w-3 h-3 text-emerald-700" />
          <span>Approved</span>
        </span>
      );
    case 'needs_review':
      return (
        <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-pastel-amber/50 border border-amber-300 text-pastel-amber-text text-[11px] font-semibold">
          <Clock className="w-3 h-3 text-amber-700" />
          <span>Needs Review</span>
        </span>
      );
    case 'rejected':
      return (
        <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-pastel-rose/50 border border-rose-300 text-pastel-rose-text text-[11px] font-semibold">
          <Ban className="w-3 h-3 text-rose-700" />
          <span>Rejected</span>
        </span>
      );
    case 'validated':
      return (
        <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-blue-100 border border-blue-200 text-pastel-action text-[11px] font-semibold">
          <ShieldCheck className="w-3 h-3 text-pastel-action" />
          <span>Validated</span>
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[11px] font-medium uppercase">
          {status}
        </span>
      );
  }
}
