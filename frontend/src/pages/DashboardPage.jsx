import React from 'react';
import { MapProvider } from '../context/MapContext';
import { OfflineProvider } from '../context/OfflineContext';
import { AppShell } from '../components/layout/AppShell';

export function DashboardPage() {
  return (
    <OfflineProvider>
      <MapProvider>
        <AppShell />
      </MapProvider>
    </OfflineProvider>
  );
}
