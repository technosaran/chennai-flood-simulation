'use client';
import { Menu } from 'lucide-react';
import type { PresetScenario } from '@/lib/types';
import type { DashboardView } from './Sidebar';

interface HeaderProps {
  realtimeEnabled: boolean;
  onToggleRealtime: () => void;
  isBackendLive: boolean;
  onHelp: () => void;
  onOpenAdvisor?: () => void;
  onOpenReservoirs?: () => void;
  onShortcuts?: () => void;
  advisorThreatLevel?: string;
  isSidebarCollapsed: boolean;
  onToggleSidebar: () => void;
  activeView: DashboardView;
  onSelectView: (view: DashboardView) => void;
  presets?: PresetScenario[];
  activePresetId?: string | null;
  onSelectPreset?: (preset: PresetScenario) => void;
  timeStepText?: string;
  isDirty?: boolean;
  isSimulating?: boolean;
  onRunSimulation: () => void;
}

const titles: Record<DashboardView, [string, string]> = {
  overview: ['Executive Dashboard', 'Unified emergency operations command center with dedicated module sections.'],
  results: ['Simulation Results', 'Exposure, shelter assignments, and response priorities.'],
  routes: ['Map & Routes', 'Flood layers, dynamic evacuation routes, and timeline playback.'],
  fleet: ['Rescue Fleet', 'Vehicle plans, rescue trips, and passenger commitments.'],
  reservoirs: ['Reservoir Hydrology', 'Storage levels, inflow/outflow telemetry, and river surge models.'],
  mcdm: ['TOPSIS Priority Dispatch', 'IEEE multi-criteria decision analysis and emergency rankings.'],
  advisor: ['AI Tactical Advisor', 'Incident commander recommendations, airdrop zones, and bilingual alerts.'],
  realtime: ['Live Weather & Alerts', 'Downloaded weather and recent official notices.'],
  weather: ['Weather ML Model', 'NASA POWER 25-yr dataset and rainfall classification.'],
  kaggle: ['Kaggle Model', 'Weather dataset and model results.'],
  scenario: ['Flood Simulation Planner', 'Choose an area and adjust flood parameters.'],
  logistics: ['Shelters & Supplies', 'Available stock, shelter capacity, and allocations.'],
  analytics: ['Impact Analytics', 'Explore how the scenario changes over time.'],
  experiments: ['Saved Analyses & Reports', 'Save, restore, compare, and export your simulations.'],
  wards: ['Ward Atlas', 'Explore 200 GCC ward profiles and shelter coverage.'],
  review: ['Models & Datasets', 'Datasets, measured results, and model limitations.'],
};

export default function Header({
  realtimeEnabled,
  onToggleRealtime,
  isBackendLive,
  onToggleSidebar,
  activeView,
  isDirty,
  isSimulating,
  onRunSimulation,
  onOpenReservoirs,
}: HeaderProps) {
  const [title, subtitle] = titles[activeView] || ['Dashboard', 'Chennai Disaster Operations'];
  return (
    <header className="clean-header">
      <div className="flex items-center gap-3 min-w-0">
        <button
          className="clean-menu-toggle"
          onClick={onToggleSidebar}
          aria-label="Toggle navigation"
        >
          <Menu size={19} />
        </button>
        <div className="min-w-0">
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
      </div>
      <div className="flex flex-wrap items-center justify-end gap-2 shrink-0 max-w-[60%]">
        <button
          type="button"
          role="switch"
          aria-label="Real-time data"
          aria-checked={realtimeEnabled}
          onClick={onToggleRealtime}
          className={`rounded-full border px-3 py-2 text-xs font-semibold ${
            realtimeEnabled
              ? 'bg-teal-700 border-teal-700 text-white'
              : 'bg-white border-slate-300 text-slate-700'
          }`}
          title="Optional internet updates. Off keeps the local simulator available."
        >
          Real-time {realtimeEnabled ? 'ON' : 'OFF'}
        </button>
        <span
          className={`clean-connection ${isBackendLive ? 'online' : ''}`}
          role="status"
        >
          <i />
          {isBackendLive ? 'Engine online' : 'Engine offline'}
        </span>
        {isDirty && (
          <span className="hidden lg:inline text-sm text-amber-800">
            Changes not run
          </span>
        )}
      </div>
    </header>
  );
}
