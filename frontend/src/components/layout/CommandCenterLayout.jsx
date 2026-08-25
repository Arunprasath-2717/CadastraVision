import React, { useState } from 'react';
import { MapProvider } from '../../context/MapContext';
import { OfflineProvider } from '../../context/OfflineContext';
import { NavigationHeader } from './NavigationHeader';
import { ProfileDrawer } from './ProfileDrawer';
import { PageTransition } from './PageTransition';
import { WorkspaceRail } from './WorkspaceRail';

export function CommandCenterLayout({ page: PageComponent }) {
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isWorkspaceOpen, setIsWorkspaceOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <OfflineProvider>
      <MapProvider>
        <div className="cv-page-shell h-screen w-screen overflow-hidden flex flex-col font-sans text-pastel-text">
          <NavigationHeader onOpenProfile={() => setIsProfileOpen(true)} onOpenWorkspace={() => setIsWorkspaceOpen(true)} />

          <div className="flex min-h-0 flex-1">
            <WorkspaceRail
              isOpen={isWorkspaceOpen}
              collapsed={sidebarCollapsed}
              onToggleCollapse={() => setSidebarCollapsed((collapsed) => !collapsed)}
              onClose={() => setIsWorkspaceOpen(false)}
            />
            <main className="cv-main-surface relative flex min-w-0 flex-1 flex-col overflow-hidden">
              <PageTransition><PageComponent /></PageTransition>
            </main>
          </div>

          <ProfileDrawer 
            isOpen={isProfileOpen} 
            onClose={() => setIsProfileOpen(false)} 
          />
        </div>
      </MapProvider>
    </OfflineProvider>
  );
}
