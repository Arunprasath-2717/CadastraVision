import React from 'react';

/**
 * CadastraVision Reusable Glowing Button Component
 * Inspired by Uiverse neon border glow concept, adapted for CadastraVision's pastel + electric blue visual theme.
 */
export function GlowingButton({
  children,
  onClick,
  type = 'button',
  variant = 'primary-glow', // 'primary-glow' | 'secondary-pastel' | 'ghost' | 'danger' | 'accent' | 'icon'
  size = 'md', // 'sm' | 'md' | 'lg'
  icon: Icon,
  disabled = false,
  className = '',
  title = '',
  ...props
}) {
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-xs gap-1.5 rounded-lg font-medium',
    md: 'px-4 py-2 text-xs font-semibold gap-2 rounded-xl',
    lg: 'px-5 py-2.5 text-sm font-semibold gap-2.5 rounded-xl',
  }[size] || 'px-4 py-2 text-xs font-semibold gap-2 rounded-xl';

  if (variant === 'primary-glow' || variant === 'primary') {
    return (
      <button
        type={type}
        onClick={onClick}
        disabled={disabled}
        title={title}
        className={`group relative inline-flex items-center justify-center text-white transition-all duration-300 hover:-translate-y-0.5 hover:scale-[1.01] disabled:cursor-not-allowed disabled:opacity-50 ${sizeClasses} ${className}`}
        {...props}
      >
        <span className="pointer-events-none absolute inset-0 -z-10 rounded-xl bg-[radial-gradient(circle_at_center,rgba(167,235,242,0.9),rgba(84,172,191,0.5),rgba(2,56,89,0.9))] opacity-80 blur-md transition-all duration-500 group-hover:opacity-100 group-hover:blur-lg" />
        <span className="pointer-events-none absolute -inset-[1.5px] -z-10 rounded-[13px] bg-[linear-gradient(135deg,#A7EBF2,#54ACBF,#266580,#023859)] opacity-90 transition-transform duration-300 group-hover:scale-[1.02]" />
        <span className="pointer-events-none absolute inset-0 -z-10 rounded-xl bg-[linear-gradient(135deg,rgba(2,56,89,0.88),rgba(1,28,64,0.92))] backdrop-blur-sm transition-colors duration-300 group-hover:bg-[linear-gradient(135deg,rgba(1,28,64,0.9),rgba(2,56,89,0.88))]" />

        {Icon && <Icon className="h-4 w-4 shrink-0 text-[#A7EBF2] transition-transform duration-300 group-hover:translate-x-0.5 group-hover:rotate-12" />}
        <span className="relative z-10 tracking-wide text-slate-100 transition-colors group-hover:text-white">{children}</span>
      </button>
    );
  }

  if (variant === 'secondary-pastel' || variant === 'secondary') {
    return (
      <button
        type={type}
        onClick={onClick}
        disabled={disabled}
        title={title}
        className={`inline-flex items-center justify-center border border-[#C9E5EE] bg-[linear-gradient(135deg,rgba(167,235,242,0.18),rgba(255,255,255,0.8))] text-[#023859] shadow-[0_8px_20px_rgba(2,56,89,0.08)] transition-all duration-200 hover:-translate-y-0.5 hover:border-[#54ACBF] hover:bg-[linear-gradient(135deg,rgba(167,235,242,0.34),rgba(84,172,191,0.12))] disabled:cursor-not-allowed disabled:opacity-50 ${sizeClasses} ${className}`}
        {...props}
      >
        {Icon && <Icon className="h-4 w-4 shrink-0 text-[#266580] transition-transform duration-200 group-hover:translate-x-0.5" />}
        <span>{children}</span>
      </button>
    );
  }

  if (variant === 'accent') {
    return (
      <button
        type={type}
        onClick={onClick}
        disabled={disabled}
        title={title}
        className={`inline-flex items-center justify-center border border-[#A7EBF2] bg-[linear-gradient(135deg,rgba(247,252,254,0.98),rgba(167,235,242,0.18))] text-[#023859] shadow-[0_8px_20px_rgba(2,56,89,0.08)] transition-all duration-200 hover:-translate-y-0.5 hover:border-[#54ACBF] hover:shadow-[0_12px_22px_rgba(2,56,89,0.12)] disabled:cursor-not-allowed disabled:opacity-50 ${sizeClasses} ${className}`}
        {...props}
      >
        {Icon && <Icon className="h-4 w-4 shrink-0 text-[#266580] transition-transform duration-200 group-hover:translate-x-0.5" />}
        <span>{children}</span>
      </button>
    );
  }

  if (variant === 'danger' || variant === 'status') {
    return (
      <button
        type={type}
        onClick={onClick}
        disabled={disabled}
        title={title}
        className={`inline-flex items-center justify-center bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 shadow-pastel-sm transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed ${sizeClasses} ${className}`}
        {...props}
      >
        {Icon && <Icon className="w-4 h-4 shrink-0 text-rose-600" />}
        <span>{children}</span>
      </button>
    );
  }

  if (variant === 'icon') {
    return (
      <button
        type={type}
        onClick={onClick}
        disabled={disabled}
        title={title}
        className={`inline-flex items-center justify-center rounded-xl border border-pastel-border bg-white text-pastel-text hover:bg-pastel-surface-soft hover:text-pastel-action hover:border-pastel-action/40 shadow-pastel-sm transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed ${sizeClasses} ${className}`}
        {...props}
      >
        {Icon && <Icon className="w-4 h-4 shrink-0" />}
      </button>
    );
  }

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={`inline-flex items-center justify-center text-pastel-muted hover:text-pastel-text hover:bg-pastel-surface-soft border border-transparent rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed ${sizeClasses} ${className}`}
      {...props}
    >
      {Icon && <Icon className="w-4 h-4 shrink-0" />}
      <span>{children}</span>
    </button>
  );
}
