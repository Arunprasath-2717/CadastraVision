import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Home, MapPin } from 'lucide-react';

export function NotFoundPage() {
  return (
    <main className="cv-not-found min-h-screen overflow-hidden px-5 py-8 text-[#292824] sm:px-8 lg:px-12">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-5xl flex-col">
        <header className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#292824] text-[#D9E2C9] shadow-[0_10px_24px_rgba(41,40,36,0.16)]">
            <MapPin className="h-5 w-5" />
          </div>
          <div>
            <p className="font-display text-sm font-bold tracking-[0.14em]">CADASTRA<span className="text-[#8A4F4A]">VISION</span></p>
            <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#6F6B5F]">Spatial operations platform</p>
          </div>
        </header>

        <section className="animate-page-enter relative flex flex-1 items-center justify-center py-16">
          <div className="cv-not-found-grid absolute inset-0 opacity-60" aria-hidden="true" />
          <div className="relative z-10 max-w-xl text-center">
            <p className="font-mono text-xs font-bold uppercase tracking-[0.24em] text-[#8A4F4A]">Coordinate unavailable</p>
            <div className="mt-5 font-display text-[7rem] font-bold leading-none tracking-[-0.04em] text-[#292824] sm:text-[9rem]">404</div>
            <h1 className="mt-2 text-2xl font-bold tracking-tight sm:text-3xl">Spatial page not found</h1>
            <p className="mx-auto mt-4 max-w-md font-serif text-base leading-7 text-[#6F6B5F]">
              The workspace you are looking for does not exist or may have moved to another coordinate.
            </p>
            <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Link to="/dashboard" className="cv-not-found-primary group inline-flex items-center justify-center gap-2 rounded-xl bg-[#292824] px-5 py-3 text-xs font-bold text-[#FBFAF6] transition-all duration-200 hover:-translate-y-0.5 hover:bg-[#4D6548] hover:shadow-[0_12px_24px_rgba(41,40,36,0.18)]">
                <ArrowLeft className="h-4 w-4 transition-transform duration-200 group-hover:-translate-x-1" />
                <span>Back to Command Center</span>
              </Link>
              <Link to="/" className="group inline-flex items-center justify-center gap-2 rounded-xl border border-[#C9C1B4] bg-[#FBFAF6]/80 px-5 py-3 text-xs font-bold text-[#292824] transition-all duration-200 hover:-translate-y-0.5 hover:border-[#A9B89A] hover:bg-[#E4E8D9]">
                <Home className="h-4 w-4 text-[#8A4F4A] transition-transform duration-200 group-hover:-translate-y-0.5" />
                <span>Go Home</span>
              </Link>
            </div>
          </div>
        </section>

        <footer className="flex items-center justify-between border-t border-[#D9D3C7] py-4 font-mono text-[10px] uppercase tracking-[0.14em] text-[#918B7E]">
          <span>CV / NAVIGATION</span>
          <span>Sector 04 / Live</span>
        </footer>
      </div>
    </main>
  );
}
