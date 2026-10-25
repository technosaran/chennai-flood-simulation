'use client';
import {
  LayoutDashboard,
  Truck,
  Radio,
  CloudRain,
  Database,
  Compass,
  SlidersHorizontal,
  Package,
  TrendingUp,
  FolderOpen,
  Map,
  ChartNoAxesCombined,
  Waves,
  PanelLeftClose,
  PanelLeftOpen,
  CircleHelp,
  MoreHorizontal,
  Download,
  RotateCcw,
  Keyboard,
  MessageSquare,
  Droplets,
  Target,
  Sparkles,
} from 'lucide-react';

export type DashboardView =
  | 'overview'
  | 'scenario'
  | 'logistics'
  | 'analytics'
  | 'experiments'
  | 'wards'
  | 'review'
  | 'results'
  | 'routes'
  | 'fleet'
  | 'realtime'
  | 'weather'
  | 'kaggle'
  | 'reservoirs'
  | 'mcdm'
  | 'advisor';

interface SidebarProps {
  activeView: DashboardView;
  onSelectView: (view: DashboardView) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  isBackendLive: boolean;
  isSimulating: boolean;
  hasSimulation: boolean;
  onRunSimulation: () => void;
  onReset: () => void;
  onExport: () => void;
  onOpenAdvisor: () => void;
  onOpenReservoirs?: () => void;
  onHelp: () => void;
  onShortcuts: () => void;
  advisorThreatLevel?: string;
  timeStepText?: string;
  isDirty?: boolean;
}

export const moduleGroups = [
  {
    label: 'Workspace',
    items: [
      {
        id: 'overview' as const,
        label: 'Dashboard',
        description: 'Executive command center with dedicated sections for each module.',
        icon: LayoutDashboard,
      },
      {
        id: 'scenario' as const,
        label: 'Flood simulation',
        description: 'Choose a flood area, set rainfall/depth, and run a scenario.',
        icon: SlidersHorizontal,
      },
      {
        id: 'results' as const,
        label: 'Simulation results',
        description: 'Review exposure, shelter assignments, and response priorities.',
        icon: Compass,
      },
      {
        id: 'routes' as const,
        label: 'Map & routes',
        description: 'Explore flood layers, dynamic evacuation routes, and playback.',
        icon: Map,
      },
    ],
  },
  {
    label: 'Operations & Logistics',
    items: [
      {
        id: 'logistics' as const,
        label: 'Shelters & supplies',
        description: 'Check shelter capacity, relief stock, and allocations.',
        icon: Package,
      },
      {
        id: 'fleet' as const,
        label: 'Rescue fleet',
        description: 'Review rescue vehicles, trips, and passenger commitments.',
        icon: Truck,
      },
      {
        id: 'reservoirs' as const,
        label: 'Reservoir hydrology',
        description: 'Live storage, inflow/outflow, and river surge models.',
        icon: Droplets,
      },
      {
        id: 'wards' as const,
        label: 'Ward atlas',
        description: 'Explore 200 GCC ward profiles and local shelter coverage.',
        icon: Map,
      },
    ],
  },
  {
    label: 'Decision Intelligence',
    items: [
      {
        id: 'mcdm' as const,
        label: 'TOPSIS dispatch',
        description: 'IEEE multi-criteria decision analysis and emergency rankings.',
        icon: Target,
      },
      {
        id: 'advisor' as const,
        label: 'AI Tactical advisor',
        description: 'Incident command guidance, airdrops, and bilingual alerts.',
        icon: Sparkles,
      },
      {
        id: 'analytics' as const,
        label: 'Impact analytics',
        description: 'Inspect hourly impact and relief-demand estimates.',
        icon: TrendingUp,
      },
    ],
  },
  {
    label: 'Data & Model Science',
    items: [
      {
        id: 'realtime' as const,
        label: 'Live weather & alerts',
        description: 'View downloaded weather and recent official notices.',
        icon: Radio,
      },
      {
        id: 'weather' as const,
        label: 'Weather ML model',
        description: 'Explore NASA POWER 25-yr dataset and rainfall classification.',
        icon: CloudRain,
      },
      {
        id: 'kaggle' as const,
        label: 'Kaggle dataset model',
        description: 'Inspect the weather dataset and trained model results.',
        icon: Database,
      },
      {
        id: 'review' as const,
        label: 'Model evaluation',
        description: 'Review evaluation evidence and system limitations.',
        icon: ChartNoAxesCombined,
      },
      {
        id: 'experiments' as const,
        label: 'Saved analyses & reports',
        description: 'Save, restore, compare, and export your simulations.',
        icon: FolderOpen,
      },
    ],
  },
] as const;

export default function Sidebar({
  activeView,
  onSelectView,
  isCollapsed,
  onToggleCollapse,
  isSimulating,
  hasSimulation,
  onReset,
  onExport,
  onOpenAdvisor,
  onOpenReservoirs,
  onHelp,
  onShortcuts,
  isDirty,
}: SidebarProps) {
  const navButton = (item: (typeof moduleGroups)[number]['items'][number]) => (
    <button
      key={item.id}
      onClick={() => onSelectView(item.id)}
      aria-current={activeView === item.id ? 'page' : undefined}
      aria-label={item.label}
      title={isCollapsed ? item.label : undefined}
      className={`clean-nav-link ${isCollapsed ? 'justify-center' : ''}`}
    >
      <item.icon size={18} strokeWidth={1.7} aria-hidden="true" />
      {!isCollapsed && <span>{item.label}</span>}
    </button>
  );

  return (
    <aside
      aria-label="Application Sidebar"
      className={`clean-sidebar ${isCollapsed ? 'is-collapsed' : ''}`}
    >
      <div className="clean-brand">
        <span className="clean-brand-icon">
          <Waves size={22} />
        </span>
        {!isCollapsed && (
          <div>
            <strong>Chennai Flood Lab</strong>
            <span>Simulation workspace</span>
          </div>
        )}
      </div>

      <nav aria-label="Main navigation" className="clean-navigation">
        {moduleGroups.map((group) => (
          <div className="module-nav-group" key={group.label}>
            {!isCollapsed && <p className="module-nav-label">{group.label}</p>}
            {group.items.map(navButton)}
          </div>
        ))}

        <div className="module-nav-group">
          {!isCollapsed && <p className="module-nav-label">Quick Modals</p>}
          {onOpenReservoirs && (
            <button
              className="clean-nav-link"
              onClick={onOpenReservoirs}
              title="Reservoirs dialog"
              aria-label="Reservoirs dialog"
            >
              <Droplets size={18} />
              {!isCollapsed && <span>Reservoirs modal</span>}
            </button>
          )}
          <button
            className="clean-nav-link"
            onClick={onOpenAdvisor}
            title="Scenario advice dialog"
            aria-label="Scenario advice dialog"
          >
            <MessageSquare size={18} />
            {!isCollapsed && <span>Scenario advice modal</span>}
          </button>
        </div>
      </nav>

      <div className="clean-sidebar-footer">
        <details className="clean-more">
          <summary aria-label="More options">
            <MoreHorizontal size={18} />
            {!isCollapsed && <span>More options</span>}
          </summary>
          <div className="clean-more-menu">
            <button
              disabled={!hasSimulation || isDirty || isSimulating}
              onClick={onExport}
            >
              <Download size={15} />
              Export results
            </button>
            <button disabled={isSimulating} onClick={onReset}>
              <RotateCcw size={15} />
              Reset scenario
            </button>
            <button onClick={onShortcuts}>
              <Keyboard size={15} />
              Keyboard shortcuts
            </button>
          </div>
        </details>
        <div className="clean-sidebar-bottom">
          <button
            onClick={onHelp}
            aria-label="Help and documentation"
            title="Help and documentation"
          >
            <CircleHelp size={17} />
            {!isCollapsed && <span>Help</span>}
          </button>
          <button
            onClick={onToggleCollapse}
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? <PanelLeftOpen size={17} /> : <PanelLeftClose size={17} />}
          </button>
        </div>
        {!isCollapsed && (
          <p className="clean-academic-note">Academic simulation · Chennai</p>
        )}
      </div>
    </aside>
  );
}
