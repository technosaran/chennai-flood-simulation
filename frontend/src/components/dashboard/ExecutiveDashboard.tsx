'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Waves,
  SlidersHorizontal,
  Map,
  Package,
  Truck,
  Droplets,
  Target,
  Building2,
  CloudRain,
  Sparkles,
  FolderOpen,
  ArrowRight,
  Play,
  RotateCcw,
  Download,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Layers,
  ChevronRight,
  RefreshCw,
  Compass,
  Tent,
  Activity,
  Shield,
  Radio,
  ExternalLink,
  Info,
} from 'lucide-react';

import type {
  Coordinates,
  DisasterParameters,
  FloodZoneInput,
  PresetScenario,
  SimulationResponse,
  MapInitResponse,
  InventoryStatus,
  TimelineStep,
  RouteInspectionData,
  AIAdvisorData,
  RescueFleetConfig,
} from '@/lib/types';
import type { DashboardView } from './Sidebar';
import MapContainer from '@/components/map/MapContainer';
import TimelinePlayer from '@/components/controls/TimelinePlayer';
import LayerToggle from '@/components/controls/LayerToggle';
import ScenarioReport from '@/components/dashboard/ScenarioReport';

interface ExecutiveDashboardProps {
  data: MapInitResponse;
  response: SimulationResponse | null;
  step: TimelineStep | null;
  currentStepIndex: number;
  onStepChange: (index: number) => void;
  isPlaying: boolean;
  onTogglePlay: () => void;
  playbackSpeed: number;
  onSpeedChange: (speed: number) => void;
  parameters: DisasterParameters;
  onChangeParameters: (p: DisasterParameters) => void;
  activePresetId: string | null;
  onSelectPreset: (preset: PresetScenario) => void;
  definedZones: FloodZoneInput[];
  isSimulating: boolean;
  elapsedSeconds: number;
  onRunSimulation: () => void;
  onResetScenario: () => void;
  onExportResults: () => void;
  isBackendLive: boolean;
  isDirty: boolean;
  savedView: string | null;
  rescueFleet: RescueFleetConfig;
  inventory: InventoryStatus;
  visibleLayers: {
    flood: boolean;
    evacuation: boolean;
    supply: boolean;
    shelters: boolean;
    warehouses: boolean;
    distributionPoints: boolean;
    populationHeatmap: boolean;
  };
  onToggleLayer: (layer: keyof ExecutiveDashboardProps['visibleLayers']) => void;
  onSelectView: (view: DashboardView) => void;
  onOpenAllocation: (id: string, type: 'shelter' | 'point') => void;
  onSelectRoute: (route: RouteInspectionData | null) => void;
  onOpenAdvisor: () => void;
  onOpenReservoirs: () => void;
  onOpenMCDM?: () => void;
  advisorData: AIAdvisorData | null;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function ExecutiveDashboard({
  data,
  response,
  step,
  currentStepIndex,
  onStepChange,
  isPlaying,
  onTogglePlay,
  playbackSpeed,
  onSpeedChange,
  parameters,
  onChangeParameters,
  activePresetId,
  onSelectPreset,
  definedZones,
  isSimulating,
  elapsedSeconds,
  onRunSimulation,
  onResetScenario,
  onExportResults,
  isBackendLive,
  isDirty,
  savedView,
  rescueFleet,
  inventory,
  visibleLayers,
  onToggleLayer,
  onSelectView,
  onOpenAllocation,
  onSelectRoute,
  onOpenAdvisor,
  onOpenReservoirs,
  advisorData,
}: ExecutiveDashboardProps) {
  // Local Reservoir Telemetry state for Section 5
  const [reservoirData, setReservoirData] = useState<any>(null);
  const [reservoirLoading, setReservoirLoading] = useState(false);

  // Local MCDM Rankings state for Section 6
  const [mcdmData, setMcdmData] = useState<any>(null);
  const [mcdmLoading, setMcdmLoading] = useState(false);

  // Active anchor tab highlight
  const [activeAnchor, setActiveAnchor] = useState('overview');

  const fetchReservoirs = useCallback(async () => {
    setReservoirLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/reservoirs`);
      if (res.ok) {
        const json = await res.json();
        setReservoirData(json.data);
      }
    } catch {
      // offline fallback
    } finally {
      setReservoirLoading(false);
    }
  }, []);

  const fetchMCDM = useCallback(async () => {
    if (!response) return;
    setMcdmLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/advisory/mcdm`);
      if (res.ok) {
        const json = await res.json();
        setMcdmData(json.mcdm_topsis_rankings);
      }
    } catch {
      // fallback
    } finally {
      setMcdmLoading(false);
    }
  }, [response]);

  useEffect(() => {
    fetchReservoirs();
  }, [fetchReservoirs]);

  useEffect(() => {
    if (response) {
      fetchMCDM();
    }
  }, [response, fetchMCDM]);

  const scrollToSection = (id: string) => {
    setActiveAnchor(id);
    const element = document.getElementById(id);
    if (element) {
      const yOffset = -100;
      const y = element.getBoundingClientRect().top + window.pageYOffset + yOffset;
      window.scrollTo({ top: y, behavior: 'smooth' });
    }
  };

  const metrics = step?.metrics;
  const currentPreset = data.presets.find((p) => p.id === activePresetId);

  // Fallback calculations for reservoirs if API not yet populated
  const totalReservoirStorage = reservoirData?.total_storage_mcft ?? 7850;
  const totalReservoirCap = reservoirData?.total_capacity_mcft ?? 11257;
  const reservoirPct = reservoirData?.overall_storage_pct ?? Math.round((totalReservoirStorage / totalReservoirCap) * 100);

  // Supply ledger percentages
  const waterPct = Math.round((inventory.available_water_litres / (inventory.total_water_litres || 1)) * 100);
  const foodPct = Math.round((inventory.available_food_rations / (inventory.total_food_rations || 1)) * 100);
  const medPct = Math.round((inventory.available_medical_kits / (inventory.total_medical_kits || 1)) * 100);

  // Fleet total seat capacity
  const totalFleetSeats =
    rescueFleet.trucks.count * rescueFleet.trucks.seats +
    rescueFleet.boats.count * rescueFleet.boats.seats +
    rescueFleet.helicopters.count * rescueFleet.helicopters.seats;

  const totalVehicles =
    rescueFleet.trucks.count + rescueFleet.boats.count + rescueFleet.helicopters.count;

  return (
    <div className="space-y-8 pb-16">
      {/* 1. EXECUTIVE HERO COMMAND BANNER */}
      <section id="module-overview" className="p-6 sm:p-8 bg-white border border-slate-200 rounded-2xl shadow-sm space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-slate-100">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-teal-50 text-teal-800 border border-teal-200 tracking-wide uppercase">
                OPERATIONAL COMMAND DASHBOARD
              </span>
              <span className="text-xs text-slate-500 font-medium">
                Greater Chennai Disaster Risk Management
              </span>
              {savedView && (
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-cyan-100 text-cyan-800">
                  SNAPSHOT: {savedView}
                </span>
              )}
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900">
              Chennai Natural Disaster (Flood) Simulation & Operations
            </h1>
            <p className="text-sm text-slate-600 max-w-3xl leading-relaxed">
              Unified multi-agency coordination dashboard across flood hydrodynamics, dynamic evacuation routing,
              relief logistics supply chain, and emergency rescue fleet deployment.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <button
              onClick={onRunSimulation}
              disabled={isSimulating}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm bg-teal-700 hover:bg-teal-800 text-white shadow-sm transition-all disabled:opacity-50"
            >
              {isSimulating ? (
                <>
                  <RefreshCw size={16} className="animate-spin" />
                  <span>Computing ({elapsedSeconds}s)…</span>
                </>
              ) : (
                <>
                  <Play size={16} fill="currentColor" />
                  <span>Run Scenario</span>
                </>
              )}
            </button>
            <button
              onClick={onResetScenario}
              disabled={isSimulating}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl font-semibold text-sm bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition-colors"
            >
              <RotateCcw size={15} />
              <span>Reset</span>
            </button>
            <button
              onClick={onExportResults}
              disabled={!response || isDirty || isSimulating}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl font-semibold text-sm bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition-colors disabled:opacity-40"
            >
              <Download size={15} />
              <span>Export</span>
            </button>
          </div>
        </div>

        {/* 6 EXECUTIVE TELEMETRY KPI CARDS */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
          <div className="p-4 bg-slate-50/70 border border-slate-200 rounded-xl space-y-1">
            <span className="text-xs font-semibold text-slate-500 block truncate">Affected Population</span>
            <strong className="text-xl font-bold text-slate-900 block">
              {metrics ? metrics.total_affected_population.toLocaleString() : '—'}
            </strong>
            <small className="text-[11px] text-slate-500 block">
              {step ? `Hour T+${step.hour}h exposure` : 'Baseline estimation'}
            </small>
          </div>

          <div className="p-4 bg-slate-50/70 border border-slate-200 rounded-xl space-y-1">
            <span className="text-xs font-semibold text-slate-500 block truncate">Sheltered Evacuees</span>
            <strong className="text-xl font-bold text-teal-700 block">
              {metrics ? metrics.total_evacuated_population.toLocaleString() : '—'}
            </strong>
            <small className="text-[11px] text-slate-500 block">
              {data.shelters.length} active public shelters
            </small>
          </div>

          <div className="p-4 bg-slate-50/70 border border-slate-200 rounded-xl space-y-1">
            <span className="text-xs font-semibold text-slate-500 block truncate">Awaiting Rescue</span>
            <strong className={`text-xl font-bold block ${metrics && metrics.unassigned_stranded_population > 0 ? 'text-amber-800 font-extrabold' : 'text-slate-900'}`}>
              {metrics ? metrics.unassigned_stranded_population.toLocaleString() : '—'}
            </strong>
            <small className="text-[11px] text-slate-500 block">
              {metrics && metrics.unassigned_stranded_population > 0 ? 'Urgent evacuation trap' : 'All secured'}
            </small>
          </div>

          <div className="p-4 bg-slate-50/70 border border-slate-200 rounded-xl space-y-1">
            <span className="text-xs font-semibold text-slate-500 block truncate">Flooded Footprint</span>
            <strong className="text-xl font-bold text-slate-900 block">
              {metrics ? `${metrics.total_flooded_area_sq_km.toFixed(1)} km²` : '—'}
            </strong>
            <small className="text-[11px] text-slate-500 block">
              Peak depth {parameters.flood_depth_meters}m
            </small>
          </div>

          <div className="p-4 bg-slate-50/70 border border-slate-200 rounded-xl space-y-1">
            <span className="text-xs font-semibold text-slate-500 block truncate">Rescue Fleet Seats</span>
            <strong className="text-xl font-bold text-slate-900 block">
              {totalFleetSeats}
            </strong>
            <small className="text-[11px] text-slate-500 block">
              {totalVehicles} vehicles deployed
            </small>
          </div>

          <div className="p-4 bg-slate-50/70 border border-slate-200 rounded-xl space-y-1">
            <span className="text-xs font-semibold text-slate-500 block truncate">Reservoir Storage</span>
            <strong className={`text-xl font-bold block ${reservoirPct >= 90 ? 'text-red-700' : reservoirPct >= 75 ? 'text-amber-800' : 'text-teal-700'}`}>
              {reservoirPct}%
            </strong>
            <small className="text-[11px] text-slate-500 block">
              {totalReservoirStorage.toLocaleString()} Mcft total
            </small>
          </div>
        </div>
      </section>

      {/* 2. STICKY QUICK-JUMP MODULE NAVIGATION BAR */}
      <nav
        aria-label="Module Quick Jump"
        className="sticky top-[86px] z-20 -my-2 py-2 bg-slate-50/90 backdrop-blur-md flex items-center gap-1.5 overflow-x-auto custom-scrollbar border-b border-slate-200"
      >
        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider px-2 shrink-0">
          Module Jump:
        </span>
        {[
          { id: 'module-simulation', label: 'Flood Simulation', icon: SlidersHorizontal },
          { id: 'module-map', label: 'Map & Routes', icon: Map },
          { id: 'module-logistics', label: 'Shelters & Supplies', icon: Package },
          { id: 'module-fleet', label: 'Rescue Fleet', icon: Truck },
          { id: 'module-reservoirs', label: 'Reservoirs & Dams', icon: Droplets },
          { id: 'module-mcdm', label: 'TOPSIS Dispatch', icon: Target },
          { id: 'module-wards', label: 'Ward Atlas', icon: Building2 },
          { id: 'module-weather', label: 'Weather & ML', icon: CloudRain },
          { id: 'module-advisor', label: 'AI Advisory', icon: Sparkles },
          { id: 'module-experiments', label: 'Saved Analyses', icon: FolderOpen },
        ].map((item) => (
          <button
            key={item.id}
            onClick={() => scrollToSection(item.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold shrink-0 transition-all ${
              activeAnchor === item.id
                ? 'bg-teal-700 text-white shadow-sm'
                : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'
            }`}
          >
            <item.icon size={13} />
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      {/* =========================================================================
          MODULE SECTION 1: SPATIO-TEMPORAL FLOOD SIMULATION ENGINE
          ========================================================================= */}
      <section
        id="module-simulation"
        className="p-6 bg-white border border-slate-200 rounded-2xl shadow-sm space-y-6"
        aria-labelledby="heading-sim-module"
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <span className="w-10 h-10 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center font-bold">
              <SlidersHorizontal size={20} />
            </span>
            <div>
              <span className="text-[11px] font-bold tracking-widest text-teal-700 uppercase">
                MODULE 01 · SPATIO-TEMPORAL FLOOD ENGINE
              </span>
              <h2 id="heading-sim-module" className="text-lg font-bold text-slate-900">
                Disaster Scenario Parameters & Hydrodynamic Modeling
              </h2>
            </div>
          </div>
          <button
            onClick={() => onSelectView('scenario')}
            className="flex items-center gap-1.5 text-xs font-bold text-teal-700 hover:text-teal-900 bg-teal-50 hover:bg-teal-100 px-3.5 py-1.5 rounded-lg transition-colors shrink-0"
          >
            <span>Open Advanced Planner</span>
            <ExternalLink size={13} />
          </button>
        </div>

        {/* Historical Scenario Presets */}
        <div className="space-y-2">
          <label className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Select Historical Disaster Preset
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
            {data.presets.map((preset) => (
              <button
                key={preset.id}
                onClick={() => onSelectPreset(preset)}
                className={`p-3 rounded-xl text-left border transition-all ${
                  activePresetId === preset.id
                    ? 'border-teal-700 bg-teal-50/50 shadow-sm'
                    : 'border-slate-200 bg-slate-50/50 hover:bg-slate-100'
                }`}
              >
                <span className="text-xs font-bold text-slate-900 block truncate">{preset.name}</span>
                <span className="text-[11px] text-slate-500 block mt-0.5">
                  {preset.default_rainfall} mm/h · {preset.default_depth}m depth
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Parameter Sliders */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 p-4 bg-slate-50 rounded-xl border border-slate-200">
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="font-semibold text-slate-700">Rainfall Intensity</span>
              <span className="font-mono font-bold text-teal-700">{parameters.rainfall_intensity_mm_hr} mm/hr</span>
            </div>
            <input
              type="range"
              min="10"
              max="250"
              step="5"
              value={parameters.rainfall_intensity_mm_hr}
              onChange={(e) => onChangeParameters({ ...parameters, rainfall_intensity_mm_hr: Number(e.target.value) })}
              className="w-full accent-teal-700"
            />
            <span className="text-[10px] text-slate-500">100+ mm/hr indicates severe torrential cloudburst</span>
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="font-semibold text-slate-700">Flood Inundation Depth</span>
              <span className="font-mono font-bold text-teal-700">{parameters.flood_depth_meters} m</span>
            </div>
            <input
              type="range"
              min="0.2"
              max="3.0"
              step="0.1"
              value={parameters.flood_depth_meters}
              onChange={(e) => onChangeParameters({ ...parameters, flood_depth_meters: Number(e.target.value) })}
              className="w-full accent-teal-700"
            />
            <span className="text-[10px] text-slate-500">&gt;0.5m severs standard vehicular transit</span>
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="font-semibold text-slate-700">Flood Spread Velocity</span>
              <span className="font-mono font-bold text-teal-700">{parameters.spread_rate_meters_hr} m/hr</span>
            </div>
            <input
              type="range"
              min="50"
              max="500"
              step="10"
              value={parameters.spread_rate_meters_hr}
              onChange={(e) => onChangeParameters({ ...parameters, spread_rate_meters_hr: Number(e.target.value) })}
              className="w-full accent-teal-700"
            />
            <span className="text-[10px] text-slate-500">Radial wave expansion rate</span>
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="font-semibold text-slate-700">Simulation Horizon</span>
              <span className="font-mono font-bold text-teal-700">{parameters.duration_hours} Hours</span>
            </div>
            <input
              type="range"
              min="1"
              max="24"
              step="1"
              value={parameters.duration_hours}
              onChange={(e) => onChangeParameters({ ...parameters, duration_hours: Number(e.target.value) })}
              className="w-full accent-teal-700"
            />
            <span className="text-[10px] text-slate-500">Hourly temporal steps (T=0 to T=T)</span>
          </div>
        </div>

        {/* Simulation Execution Status */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-50 border border-slate-200">
          <div className="flex items-center gap-3">
            {isSimulating ? (
              <RefreshCw size={18} className="animate-spin text-teal-600" />
            ) : isDirty ? (
              <AlertTriangle size={18} className="text-amber-800" />
            ) : response ? (
              <CheckCircle2 size={18} className="text-emerald-700" />
            ) : (
              <Info size={18} className="text-slate-400" />
            )}
            <div className="text-xs">
              <strong>
                {isSimulating
                  ? 'Computing multi-hour flood progression and dynamic routing…'
                  : isDirty
                  ? 'Parameters modified. Simulation results need recalculation.'
                  : response
                  ? `Scenario active: ${currentPreset?.name || 'Custom'} (${parameters.duration_hours}h horizon)`
                  : 'Ready to calculate scenario.'}
              </strong>
              <p className="text-slate-500 mt-0.5">
                {isBackendLive ? 'Simulation backend is online and ready.' : 'Simulation backend is currently offline.'}
              </p>
            </div>
          </div>

          <button
            onClick={onRunSimulation}
            disabled={isSimulating}
            className="flex items-center justify-center gap-2 px-6 py-2 rounded-xl text-sm font-bold bg-teal-700 hover:bg-teal-800 text-white shadow-sm transition-all disabled:opacity-50"
          >
            <Play size={14} fill="currentColor" />
            <span>{isSimulating ? 'Processing…' : 'Run Flood Simulation'}</span>
          </button>
        </div>
      </section>

      {/* =========================================================================
          MODULE SECTION 2: GEOSPATIAL COMMAND & EVACUATION ROUTING
          ========================================================================= */}
      <section
        id="module-map"
        className="p-6 bg-white border border-slate-200 rounded-2xl shadow-sm space-y-6"
        aria-labelledby="heading-map-module"
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <span className="w-10 h-10 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center font-bold">
              <Map size={20} />
            </span>
            <div>
              <span className="text-[11px] font-bold tracking-widest text-teal-700 uppercase">
                MODULE 02 · GEOSPATIAL COMMAND & EVACUATION ROUTING
              </span>
              <h2 id="heading-map-module" className="text-lg font-bold text-slate-900">
                Interactive Chennai Road Network & Safe Evacuation Corridors
              </h2>
            </div>
          </div>
          <button
            onClick={() => onSelectView('routes')}
            className="flex items-center gap-1.5 text-xs font-bold text-teal-700 hover:text-teal-900 bg-teal-50 hover:bg-teal-100 px-3.5 py-1.5 rounded-lg transition-colors shrink-0"
          >
            <span>Open Dedicated Map View</span>
            <ExternalLink size={13} />
          </button>
        </div>

        {/* Embedded Map Container */}
        <div className="relative rounded-2xl overflow-hidden border border-slate-200 bg-slate-100 min-h-[460px] h-[520px]">
          <MapContainer
            center={data.center}
            bounds={data.bounds}
            shelters={data.shelters}
            warehouses={data.warehouses}
            distributionPoints={data.distribution_points}
            populationClusters={data.population_clusters}
            stagingBases={[]}
            currentStep={step}
            showRescuePlayback={true}
            definedZones={definedZones}
            activeDrawingMode="none"
            circleRadiusMeters={2000}
            draftPolygonPoints={[]}
            draftCircleCenter={null}
            onMapClick={() => {}}
            visibleLayers={visibleLayers}
            onSelectShelter={(id) => onOpenAllocation(id, 'shelter')}
            onSelectDistributionPoint={(id) => onOpenAllocation(id, 'point')}
            onSelectRoute={onSelectRoute}
          />

          {/* Layer Filter Float Overlay */}
          <div className="absolute top-3 right-3 z-[500]">
            <LayerToggle
              layers={visibleLayers}
              onToggleLayer={(key) => onToggleLayer(key as any)}
            />
          </div>
        </div>

        {/* Timeline Player */}
        {response ? (
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
            <TimelinePlayer
              totalSteps={response.timeline.length}
              currentStepIndex={currentStepIndex}
              onStepChange={(index) => {
                onStepChange(index);
              }}
              isPlaying={isPlaying}
              onTogglePlay={onTogglePlay}
              playbackSpeed={playbackSpeed}
              onSpeedChange={onSpeedChange}
              stepDescription={`Simulated Hour T+${step?.hour}h · ${step?.evacuation_routes.features.length || 0} evacuation corridors · ${step?.supply_routes.features.length || 0} relief supply lines`}
            />
          </div>
        ) : (
          <div className="p-4 text-center bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-500">
            Timeline scrubber will activate after running a flood scenario.
          </div>
        )}

        <div className="text-xs text-slate-500 bg-teal-50/50 p-3 rounded-lg border border-teal-100 flex items-center gap-2">
          <Info size={14} className="text-teal-700 shrink-0" />
          <span>
            Click on any evacuation route or relief line on the map to inspect corridor clearance, flood depth, and travel impedance.
          </span>
        </div>
      </section>

      {/* =========================================================================
          MODULE SECTION 3: SHELTERS & RELIEF LOGISTICS NETWORK
          ========================================================================= */}
      <section
        id="module-logistics"
        className="p-6 bg-white border border-slate-200 rounded-2xl shadow-sm space-y-6"
        aria-labelledby="heading-logistics-module"
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <span className="w-10 h-10 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center font-bold">
              <Package size={20} />
            </span>
            <div>
              <span className="text-[11px] font-bold tracking-widest text-teal-700 uppercase">
                MODULE 03 · SHELTER NETWORK & RELIEF LOGISTICS
              </span>
              <h2 id="heading-logistics-module" className="text-lg font-bold text-slate-900">
                Strategic Supply Depots & Emergency Shelter Occupancy
              </h2>
            </div>
          </div>
          <button
            onClick={() => onSelectView('logistics')}
            className="flex items-center gap-1.5 text-xs font-bold text-teal-700 hover:text-teal-900 bg-teal-50 hover:bg-teal-100 px-3.5 py-1.5 rounded-lg transition-colors shrink-0"
          >
            <span>Open Logistics Workspace</span>
            <ExternalLink size={13} />
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Supply Depot Reserves */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Package size={16} className="text-amber-800" />
              Strategic Relief Depots (5 Warehouses)
            </h3>
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3.5">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-600 font-semibold">Potable Water Reserves</span>
                  <span className="font-mono font-bold text-slate-900">
                    {inventory.available_water_litres.toLocaleString()} / {inventory.total_water_litres.toLocaleString()} L ({waterPct}%)
                  </span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                  <div className="bg-cyan-500 h-2 rounded-full" style={{ width: `${waterPct}%` }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-600 font-semibold">Food Rations</span>
                  <span className="font-mono font-bold text-slate-900">
                    {inventory.available_food_rations.toLocaleString()} / {inventory.total_food_rations.toLocaleString()} packs ({foodPct}%)
                  </span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                  <div className="bg-amber-500 h-2 rounded-full" style={{ width: `${foodPct}%` }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-600 font-semibold">Emergency Medical Kits</span>
                  <span className="font-mono font-bold text-slate-900">
                    {inventory.available_medical_kits.toLocaleString()} / {inventory.total_medical_kits.toLocaleString()} kits ({medPct}%)
                  </span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                  <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${medPct}%` }} />
                </div>
              </div>

              <div className="pt-2 border-t border-slate-200">
                <span className="text-[11px] text-slate-500 block">
                  Depots: Ambattur, Guindy Industrial, Koyambedu Wholesale, Madhavaram, Tambaram
                </span>
              </div>
            </div>
          </div>

          {/* Shelters Directory */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Tent size={16} className="text-teal-700" />
                Greater Chennai Shelters ({data.shelters.length} Facilities)
              </h3>
              <span className="text-xs text-slate-500 font-mono">12 Designated Centers</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[380px] overflow-y-auto custom-scrollbar pr-1">
              {data.shelters.map((shelter) => {
                const alloc = step?.shelter_allocations.find((a) => a.shelter_id === shelter.id);
                const occ =
                  (alloc?.current_occupancy ?? shelter.current_occupancy ?? 0) +
                  (alloc?.allocated_evacuees ?? 0);
                const cap = alloc?.total_capacity || shelter.capacity;
                const pct = Math.round((occ / cap) * 100);
                const isFull = alloc?.status === 'full' || pct >= 100;
                const isCompromised = alloc?.status === 'compromised';

                return (
                  <div
                    key={shelter.id}
                    className="p-3.5 rounded-xl bg-slate-50/70 border border-slate-200 flex flex-col justify-between gap-2.5 hover:border-teal-500 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h4 className="text-xs font-bold text-slate-900">{shelter.name}</h4>
                        <span className="text-[11px] text-slate-500 font-mono">
                          {shelter.location[0].toFixed(3)}°N, {shelter.location[1].toFixed(3)}°E
                        </span>
                      </div>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                          isCompromised
                            ? 'bg-red-50 text-red-700 border-red-200'
                            : isFull
                            ? 'bg-amber-50 text-amber-800 border-amber-200'
                            : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        }`}
                      >
                        {isCompromised ? 'COMPROMISED' : isFull ? 'FULL' : 'ACTIVE'}
                      </span>
                    </div>

                    <div className="space-y-1">
                      <div className="flex justify-between text-[11px] font-mono">
                        <span className="text-slate-500">Occupancy:</span>
                        <span className="text-slate-800 font-semibold">
                          {occ.toLocaleString()} / {cap.toLocaleString()} ({pct}%)
                        </span>
                      </div>
                      <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                        <div
                          className={`h-full rounded-full ${pct >= 90 ? 'bg-amber-500' : 'bg-teal-600'}`}
                          style={{ width: `${Math.min(100, pct)}%` }}
                        />
                      </div>
                    </div>

                    <button
                      onClick={() => onOpenAllocation(shelter.id, 'shelter')}
                      disabled={!response || isDirty || !!savedView || isSimulating}
                      className="w-full py-1 text-xs font-semibold bg-white hover:bg-slate-100 text-teal-700 border border-slate-200 rounded-lg transition-colors disabled:opacity-40"
                    >
                      Allocate Supplies
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          MODULE SECTION 4: TACTICAL RESCUE FLEET COMMAND
          ========================================================================= */}
      <section
        id="module-fleet"
        className="p-6 bg-white border border-slate-200 rounded-2xl shadow-sm space-y-6"
        aria-labelledby="heading-fleet-module"
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <span className="w-10 h-10 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center font-bold">
              <Truck size={20} />
            </span>
            <div>
              <span className="text-[11px] font-bold tracking-widest text-teal-700 uppercase">
                MODULE 04 · RESCUE FLEET & TACTICAL SORTIES
              </span>
              <h2 id="heading-fleet-module" className="text-lg font-bold text-slate-900">
                Multi-Modal Rescue Fleet Deployment & Capacity Allocation
              </h2>
            </div>
          </div>
          <button
            onClick={() => onSelectView('fleet')}
            className="flex items-center gap-1.5 text-xs font-bold text-teal-700 hover:text-teal-900 bg-teal-50 hover:bg-teal-100 px-3.5 py-1.5 rounded-lg transition-colors shrink-0"
          >
            <span>Configure Rescue Fleet</span>
            <ExternalLink size={13} />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
            <div className="flex justify-between items-center">
              <h4 className="font-bold text-sm text-slate-900 flex items-center gap-2">
                <Truck size={16} className="text-teal-700" />
                Heavy Rescue Trucks (6x6)
              </h4>
              <span className="text-xs font-bold px-2 py-0.5 rounded bg-teal-100 text-teal-800">
                {rescueFleet.trucks.count} Vehicles
              </span>
            </div>
            <p className="text-xs text-slate-600">
              High-clearance emergency vehicles for accessible urban corridors where flood depth is under 0.5 meters.
            </p>
            <div className="pt-2 text-xs text-slate-500 space-y-1">
              <div>Capacity: <strong>{rescueFleet.trucks.seats} evacuees / truck</strong></div>
              <div>Speed: <strong>35 km/h</strong> · Readiness: <strong>15 mins</strong></div>
            </div>
          </div>

          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
            <div className="flex justify-between items-center">
              <h4 className="font-bold text-sm text-slate-900 flex items-center gap-2">
                <Waves size={16} className="text-cyan-600" />
                Inflatable Rescue Boats (Zodiac)
              </h4>
              <span className="text-xs font-bold px-2 py-0.5 rounded bg-cyan-100 text-cyan-800">
                {rescueFleet.boats.count} Boats
              </span>
            </div>
            <p className="text-xs text-slate-600">
              Shallow-draft powerboats for submerged residential wards (Velachery, Mudichur, Madipakkam) where roads are flooded.
            </p>
            <div className="pt-2 text-xs text-slate-500 space-y-1">
              <div>Capacity: <strong>{rescueFleet.boats.seats} evacuees / boat</strong></div>
              <div>Speed: <strong>15 km/h</strong> · Readiness: <strong>25 mins</strong></div>
            </div>
          </div>

          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
            <div className="flex justify-between items-center">
              <h4 className="font-bold text-sm text-slate-900 flex items-center gap-2">
                <Compass size={16} className="text-purple-600" />
                Helicopters (Chetak / ALH)
              </h4>
              <span className="text-xs font-bold px-2 py-0.5 rounded bg-purple-100 text-purple-800">
                {rescueFleet.helicopters.count} Aircraft
              </span>
            </div>
            <p className="text-xs text-slate-600">
              IAF & Coast Guard air-rescue sorties for rooftop winching in completely isolated, cut-off urban island clusters.
            </p>
            <div className="pt-2 text-xs text-slate-500 space-y-1">
              <div>Capacity: <strong>{rescueFleet.helicopters.seats} passengers / sortie</strong></div>
              <div>Speed: <strong>120 km/h</strong> · Readiness: <strong>35 mins</strong></div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          MODULE SECTION 5: RESERVOIRS & HYDROLOGY TELEMETRY
          ========================================================================= */}
      <section
        id="module-reservoirs"
        className="p-6 bg-white border border-slate-200 rounded-2xl shadow-sm space-y-6"
        aria-labelledby="heading-reservoir-module"
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <span className="w-10 h-10 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center font-bold">
              <Droplets size={20} />
            </span>
            <div>
              <span className="text-[11px] font-bold tracking-widest text-teal-700 uppercase">
                MODULE 05 · RESERVOIR HYDROLOGY & RIVER SURGE
              </span>
              <h2 id="heading-reservoir-module" className="text-lg font-bold text-slate-900">
                Major Chennai Reservoirs Storage & Downstream River Surges
              </h2>
            </div>
          </div>
          <button
            onClick={() => onSelectView('reservoirs')}
            className="flex items-center gap-1.5 text-xs font-bold text-teal-700 hover:text-teal-900 bg-teal-50 hover:bg-teal-100 px-3.5 py-1.5 rounded-lg transition-colors shrink-0"
          >
            <span>Open Reservoir Telemetry</span>
            <ExternalLink size={13} />
          </button>
        </div>

        {/* 4 Chennai Major Reservoirs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            {
              id: 'chembarambakkam',
              name: 'Chembarambakkam',
              cap: 3645,
              storage: 2950,
              river: 'Adyar River',
              inflow: 4500,
              outflow: 3800,
              gates: '4 / 19',
              alert: 'WARNING',
            },
            {
              id: 'poondi',
              name: 'Poondi',
              cap: 3231,
              storage: 2400,
              river: 'Kosasthalaiyar River',
              inflow: 3200,
              outflow: 2500,
              gates: '3 / 16',
              alert: 'ADVISORY',
            },
            {
              id: 'redhills',
              name: 'Red Hills (Puzhal)',
              cap: 3300,
              storage: 2700,
              river: 'Puzhal Surplus Canal',
              inflow: 2800,
              outflow: 1800,
              gates: '2 / 8',
              alert: 'NORMAL',
            },
            {
              id: 'cholavaram',
              name: 'Cholavaram',
              cap: 1081,
              storage: 750,
              river: 'North Surplus',
              inflow: 850,
              outflow: 500,
              gates: '1 / 4',
              alert: 'NORMAL',
            },
          ].map((res) => {
            const live = reservoirData?.reservoirs?.find((r: any) => r.id === res.id);
            const storage = live?.current_storage_mcft ?? res.storage;
            const cap = live?.total_capacity_mcft ?? res.cap;
            const pct = Math.round((storage / cap) * 100);
            const alertLevel = live?.alert_level ?? res.alert;

            return (
              <div key={res.id} className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-bold text-sm text-slate-900">{res.name}</h4>
                    <span className="text-[11px] text-slate-500">→ {res.river}</span>
                  </div>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                      alertLevel === 'CRITICAL_DISCHARGE'
                        ? 'bg-red-100 text-red-800 border-red-200'
                        : alertLevel === 'WARNING'
                        ? 'bg-orange-100 text-orange-800 border-orange-200'
                        : 'bg-emerald-100 text-emerald-800 border-emerald-200'
                    }`}
                  >
                    {alertLevel}
                  </span>
                </div>

                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-500 font-mono">Storage:</span>
                    <span className="font-bold text-slate-800">{pct}% ({storage.toLocaleString()} Mcft)</span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${pct >= 85 ? 'bg-red-500' : pct >= 70 ? 'bg-amber-500' : 'bg-teal-600'}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-200 text-[11px] text-slate-600">
                  <div>Inflow: <strong>{(live?.current_inflow_cusecs ?? res.inflow).toLocaleString()} cusecs</strong></div>
                  <div>Discharge: <strong>{(live?.current_discharge_cusecs ?? res.outflow).toLocaleString()} cusecs</strong></div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* =========================================================================
          MODULE SECTION 6: MULTI-CRITERIA DECISION MAKING (IEEE TOPSIS)
          ========================================================================= */}
      <section
        id="module-mcdm"
        className="p-6 bg-white border border-slate-200 rounded-2xl shadow-sm space-y-6"
        aria-labelledby="heading-mcdm-module"
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <span className="w-10 h-10 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center font-bold">
              <Target size={20} />
            </span>
            <div>
              <span className="text-[11px] font-bold tracking-widest text-teal-700 uppercase">
                MODULE 06 · MULTI-CRITERIA DECISION MAKING (IEEE TOPSIS)
              </span>
              <h2 id="heading-mcdm-module" className="text-lg font-bold text-slate-900">
                Algorithmic Emergency Relief Dispatch Prioritization
              </h2>
            </div>
          </div>
          <button
            onClick={() => onSelectView('mcdm')}
            className="flex items-center gap-1.5 text-xs font-bold text-teal-700 hover:text-teal-900 bg-teal-50 hover:bg-teal-100 px-3.5 py-1.5 rounded-lg transition-colors shrink-0"
          >
            <span>Open Full MCDM Matrix</span>
            <ExternalLink size={13} />
          </button>
        </div>

        {/* Priority Rankings Table Preview */}
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="font-bold text-slate-700">Weights Calibration:</span>
            <span className="bg-slate-100 px-2 py-0.5 rounded text-slate-600">Flood Depth (25%)</span>
            <span className="bg-slate-100 px-2 py-0.5 rounded text-slate-600">Affected Population (25%)</span>
            <span className="bg-slate-100 px-2 py-0.5 rounded text-slate-600">Isolation Factor (20%)</span>
            <span className="bg-slate-100 px-2 py-0.5 rounded text-slate-600">Elevation (15%)</span>
            <span className="bg-slate-100 px-2 py-0.5 rounded text-slate-600">Vulnerability (15%)</span>
          </div>

          <div className="border border-slate-200 rounded-xl overflow-hidden">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-50 border-b border-slate-200 font-bold text-slate-700">
                <tr>
                  <th className="p-3">Rank</th>
                  <th className="p-3">Zone / Wards</th>
                  <th className="p-3">Priority Tier</th>
                  <th className="p-3">TOPSIS Score</th>
                  <th className="p-3">Flood Depth</th>
                  <th className="p-3">Recommended Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {[
                  {
                    rank: 1,
                    zone: 'Zone 13 - Adyar / Velachery',
                    tier: 'P1 Immediate Dispatch',
                    tierClass: 'bg-red-100 text-red-800 border-red-200',
                    score: '94.2%',
                    depth: '2.1 m',
                    action: 'Deploy inflatable Zodiac rescue boats and dewatering teams',
                  },
                  {
                    rank: 2,
                    zone: 'Zone 9 - T. Nagar / Saidapet',
                    tier: 'P1 Immediate Dispatch',
                    tierClass: 'bg-red-100 text-red-800 border-red-200',
                    score: '88.5%',
                    depth: '1.7 m',
                    action: 'Initiate evacuation to elevated shelters via Maraimalai Adigal Bridge',
                  },
                  {
                    rank: 3,
                    zone: 'Zone 14 - Perungudi / Madipakkam',
                    tier: 'P2 High Priority',
                    tierClass: 'bg-orange-100 text-orange-800 border-orange-200',
                    score: '76.8%',
                    depth: '1.3 m',
                    action: 'Pre-position emergency water rations and mobile medical teams',
                  },
                  {
                    rank: 4,
                    zone: 'Zone 10 - Kodambakkam / Jafferkhanpet',
                    tier: 'P2 High Priority',
                    tierClass: 'bg-orange-100 text-orange-800 border-orange-200',
                    score: '69.4%',
                    depth: '1.0 m',
                    action: 'Monitor Adyar river crest level and clear stormwater sluices',
                  },
                ].map((row) => (
                  <tr key={row.rank} className="hover:bg-slate-50/70">
                    <td className="p-3 font-bold text-slate-900">#{row.rank}</td>
                    <td className="p-3 font-semibold text-slate-800">{row.zone}</td>
                    <td className="p-3">
                      <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full border ${row.tierClass}`}>
                        {row.tier}
                      </span>
                    </td>
                    <td className="p-3 font-mono font-bold text-slate-900">{row.score}</td>
                    <td className="p-3 font-mono text-slate-700">{row.depth}</td>
                    <td className="p-3 text-slate-600">{row.action}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* =========================================================================
          MODULE SECTION 7: WARD ATLAS & POPULATION VULNERABILITY
          ========================================================================= */}
      <section
        id="module-wards"
        className="p-6 bg-white border border-slate-200 rounded-2xl shadow-sm space-y-6"
        aria-labelledby="heading-wards-module"
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <span className="w-10 h-10 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center font-bold">
              <Building2 size={20} />
            </span>
            <div>
              <span className="text-[11px] font-bold tracking-widest text-teal-700 uppercase">
                MODULE 07 · WARD ATLAS & SOCIO-DEMOGRAPHICS
              </span>
              <h2 id="heading-wards-module" className="text-lg font-bold text-slate-900">
                200 GCC Municipal Wards Exposure & Spatial Vulnerability Index
              </h2>
            </div>
          </div>
          <button
            onClick={() => onSelectView('wards')}
            className="flex items-center gap-1.5 text-xs font-bold text-teal-700 hover:text-teal-900 bg-teal-50 hover:bg-teal-100 px-3.5 py-1.5 rounded-lg transition-colors shrink-0"
          >
            <span>Explore 200 GCC Wards</span>
            <ExternalLink size={13} />
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { ward: 'Ward 177 - Velachery West', pop: '42,500', density: 'High Density Basin', elev: '3.2 m', risk: 'Critical', riskClass: 'text-red-700' },
            { ward: 'Ward 142 - Saidapet South', pop: '38,200', density: 'Riverine Corridor', elev: '4.8 m', risk: 'High', riskClass: 'text-orange-600' },
            { ward: 'Ward 136 - T. Nagar Core', pop: '51,000', density: 'Commercial High-Density', elev: '7.1 m', risk: 'Moderate', riskClass: 'text-amber-700' },
            { ward: 'Ward 188 - Madipakkam Lake', pop: '35,900', density: 'Lowland Encroachment', elev: '2.9 m', risk: 'Critical', riskClass: 'text-red-700' },
          ].map((w, idx) => (
            <div key={idx} className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5">
              <div className="flex justify-between items-start">
                <h4 className="font-bold text-xs text-slate-900">{w.ward}</h4>
                <span className={`text-[11px] font-bold ${w.riskClass}`}>{w.risk} Risk</span>
              </div>
              <p className="text-[11px] text-slate-500">{w.density}</p>
              <div className="pt-2 border-t border-slate-200 text-xs text-slate-700 flex justify-between">
                <span>Population: <strong>{w.pop}</strong></span>
                <span>Elev: <strong>{w.elev}</strong></span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* =========================================================================
          MODULE SECTION 8: WEATHER INTELLIGENCE & AI/ML PREDICTION MODELS
          ========================================================================= */}
      <section
        id="module-weather"
        className="p-6 bg-white border border-slate-200 rounded-2xl shadow-sm space-y-6"
        aria-labelledby="heading-ml-module"
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <span className="w-10 h-10 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center font-bold">
              <CloudRain size={20} />
            </span>
            <div>
              <span className="text-[11px] font-bold tracking-widest text-teal-700 uppercase">
                MODULE 08 · WEATHER INTELLIGENCE & PREDICTIVE ML
              </span>
              <h2 id="heading-ml-module" className="text-lg font-bold text-slate-900">
                NASA POWER 25-Year Reanalysis & Next-Day Rainfall ML Classifier
              </h2>
            </div>
          </div>
          <button
            onClick={() => onSelectView('weather')}
            className="flex items-center gap-1.5 text-xs font-bold text-teal-700 hover:text-teal-900 bg-teal-50 hover:bg-teal-100 px-3.5 py-1.5 rounded-lg transition-colors shrink-0"
          >
            <span>Inspect Weather Models</span>
            <ExternalLink size={13} />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* NASA POWER Model Card */}
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
            <div className="flex justify-between items-center">
              <h4 className="font-bold text-sm text-slate-900 flex items-center gap-2">
                <CloudRain size={16} className="text-teal-700" />
                Rainfall Classification Model (180-Tree Random Forest)
              </h4>
              <span className="text-xs font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                ROC-AUC: 0.88
              </span>
            </div>
            <p className="text-xs text-slate-600">
              Trained on 9,131 daily gridded records from NASA POWER (1998-2023) across Greater Chennai coordinates.
              Predicts next-day extreme precipitation threshold exceeding 50 mm.
            </p>
            <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-200 text-xs">
              <div>Accuracy: <strong>83.5%</strong></div>
              <div>F1 Score: <strong>0.82</strong></div>
              <div>Test Split: <strong>Chronological</strong></div>
            </div>
          </div>

          {/* Relief Demand Predictor Card */}
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
            <div className="flex justify-between items-center">
              <h4 className="font-bold text-sm text-slate-900 flex items-center gap-2">
                <Package size={16} className="text-amber-700" />
                Relief Demand Estimator (RF + Ridge Blend)
              </h4>
              <span className="text-xs font-bold px-2 py-0.5 rounded bg-teal-100 text-teal-800">
                R² Score: 0.94
              </span>
            </div>
            <p className="text-xs text-slate-600">
              Blends 128 decision trees with L2 Ridge regression to predict potable water (litres), food packets,
              and trauma kits needed per cluster based on water depth and vulnerable population.
            </p>
            <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-200 text-xs">
              <div>Water: <strong>3.0 L/person</strong></div>
              <div>Food: <strong>2 packs/person</strong></div>
              <div>Medical: <strong>1 kit/25 people</strong></div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================================
          MODULE SECTION 9: AI TACTICAL ADVISOR & INCIDENT COMMAND
          ========================================================================= */}
      <section
        id="module-advisor"
        className="p-6 bg-white border border-slate-200 rounded-2xl shadow-sm space-y-6"
        aria-labelledby="heading-advisor-module"
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <span className="w-10 h-10 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center font-bold">
              <Sparkles size={20} />
            </span>
            <div>
              <span className="text-[11px] font-bold tracking-widest text-teal-700 uppercase">
                MODULE 09 · AI TACTICAL ADVISOR & INCIDENT COMMAND
              </span>
              <h2 id="heading-advisor-module" className="text-lg font-bold text-slate-900">
                Autonomous Situational Threat Assessment & Public Alerts
              </h2>
            </div>
          </div>
          <button
            onClick={() => onSelectView('advisor')}
            className="flex items-center gap-1.5 text-xs font-bold text-teal-700 hover:text-teal-900 bg-teal-50 hover:bg-teal-100 px-3.5 py-1.5 rounded-lg transition-colors shrink-0"
          >
            <span>Open AI Advisory</span>
            <ExternalLink size={13} />
          </button>
        </div>

        <div className="p-4 bg-teal-50/60 border border-teal-200 rounded-xl space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold px-2.5 py-0.5 rounded bg-teal-700 text-white">
                THREAT LEVEL
              </span>
              <strong className="text-sm text-teal-900">
                {advisorData?.risk_radar_level || 'DEFCON 3 (ELEVATED RISK)'}
              </strong>
            </div>
            <span className="text-xs font-mono text-teal-800">
              Score: {advisorData?.radar_score || 65}/100
            </span>
          </div>

          <p className="text-sm text-slate-700 leading-relaxed">
            {advisorData?.tactical_summary ||
              'Continuous hydrodynamic decision analysis active. Prepare designated elevated shelters in Saidapet and Velachery. Pre-position dewatering pumps near Maraimalai Adigal Bridge.'}
          </p>

          <div className="pt-2 border-t border-teal-200/60 flex flex-wrap items-center justify-between gap-2 text-xs">
            <span className="text-slate-600">
              Bilingual Public Siren Broadcast: <strong>Tamil & English Ready</strong>
            </span>
            <button
              onClick={onOpenAdvisor}
              className="text-xs font-bold text-teal-800 hover:text-teal-950 underline"
            >
              View Full Incident Directives →
            </button>
          </div>
        </div>
      </section>

      {/* =========================================================================
          MODULE SECTION 10: SIMULATION ARCHIVE, EXPERIMENTS & REPORTS
          ========================================================================= */}
      <section
        id="module-experiments"
        className="p-6 bg-white border border-slate-200 rounded-2xl shadow-sm space-y-6"
        aria-labelledby="heading-experiments-module"
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <span className="w-10 h-10 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center font-bold">
              <FolderOpen size={20} />
            </span>
            <div>
              <span className="text-[11px] font-bold tracking-widest text-teal-700 uppercase">
                MODULE 10 · SIMULATION ARCHIVE & REPORT AUDITING
              </span>
              <h2 id="heading-experiments-module" className="text-lg font-bold text-slate-900">
                Immutable SQLite Snapshots, Scenario Comparison & PDF Reports
              </h2>
            </div>
          </div>
          <button
            onClick={() => onSelectView('experiments')}
            className="flex items-center gap-1.5 text-xs font-bold text-teal-700 hover:text-teal-900 bg-teal-50 hover:bg-teal-100 px-3.5 py-1.5 rounded-lg transition-colors shrink-0"
          >
            <span>Open Saved Analyses</span>
            <ExternalLink size={13} />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
            <h4 className="font-bold text-sm text-slate-900 flex items-center gap-2">
              <Download size={16} className="text-teal-700" />
              Comprehensive Incident Audit Report
            </h4>
            <p className="text-xs text-slate-600">
              Generates self-contained HTML/PDF scenario reports including vector SVG maps, supply ledgers,
              evacuation corridors, and model evidence provenance.
            </p>
            <div className="pt-2">
              <ScenarioReport
                result={response}
                parameters={parameters}
                isDirty={isDirty}
                isSimulating={isSimulating}
              />
            </div>
          </div>

          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
            <h4 className="font-bold text-sm text-slate-900 flex items-center gap-2">
              <FolderOpen size={16} className="text-teal-700" />
              Snapshot Storage & Verification
            </h4>
            <p className="text-xs text-slate-600">
              Preserves archived parameters, timeline progression, and evidence verification without altering live engine state.
            </p>
            <div className="pt-2 flex gap-2">
              <button
                onClick={() => onSelectView('experiments')}
                className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-xs font-bold text-slate-700 hover:bg-slate-100 shadow-sm"
              >
                Browse Snapshot Library
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
