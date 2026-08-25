import React from 'react';
import { useLocation } from 'react-router-dom';

/**
 * PageTransition Component
 * Provides subtle slide + fade animation between routes in CadastraVision
 */
export function PageTransition({ children }) {
  const location = useLocation();

  return (
    <div
      key={location.pathname}
      className="w-full h-full flex-1 overflow-hidden animate-page-enter"
    >
      {children}
    </div>
  );
}
