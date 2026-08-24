import React, { useState } from 'react';
import { MapProvider } from '../../context/MapContext';
import { OfflineProvider } from '../../context/OfflineContext';
import { NavigationHeader } from './NavigationHeader';
import { ProfileDrawer } from './ProfileDrawer';
import { PageTransition } from './PageTransition';

export function CommandCenterLayout({ page: PageComponent }) {
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  return (
    <OfflineProvider>
      <MapProvider>
        <div className="cv-page-shell h-screen w-screen overflow-hidden flex flex-col font-sans text-pastel-text">
          <NavigationHeader onOpenProfile={() => setIsProfileOpen(true)} />

          <main className="flex-1 overflow-hidden relative flex flex-col">
            <PageTransition>
              <PageComponent />
            </PageTransition>
          </main>

          <ProfileDrawer 
            isOpen={isProfileOpen} 
            onClose={() => setIsProfileOpen(false)} 
          />
        </div>
      </MapProvider>
    </OfflineProvider>
  );
}
