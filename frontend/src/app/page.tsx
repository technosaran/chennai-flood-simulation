'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useDialogFocus } from '@/lib/use-dialog-focus';
import { PlannerSteps, ScenarioSetup, ScenarioReview, ResultsSummary, type PlannerStep } from '@/components/dashboard/GuidedPlanner';
import Sidebar, { DashboardView, moduleGroups } from '@/components/dashboard/Sidebar';
import WeatherModelPanel from '@/components/dashboard/WeatherModelPanel';
import KaggleModelPanel from '@/components/dashboard/KaggleModelPanel';
import Header from '@/components/dashboard/Header';
import RealtimePanel from '@/components/dashboard/RealtimePanel';
import { useRealtimeData } from '@/lib/use-realtime-data';
import { canApplyWeather } from '@/lib/realtime';
import MetricsOverview from '@/components/dashboard/MetricsOverview';
import ScenarioInsights from '@/components/dashboard/ScenarioInsights';
import ExperimentNotebook from '@/components/dashboard/ExperimentNotebook';
import ProjectReview from '@/components/dashboard/ProjectReview';
import WardProfiles from '@/components/dashboard/WardProfiles';
import ScenarioReport from '@/components/dashboard/ScenarioReport';
import RescueFleetControls, { DEFAULT_RESCUE_FLEET } from '@/components/controls/RescueFleetControls';
import RescueFleetPanel from '@/components/dashboard/RescueFleetPanel';
import SavedSimulationLibrary from '@/components/dashboard/SavedSimulationLibrary';
import MapContainer from '@/components/map/MapContainer';
import DisasterControls from '@/components/controls/DisasterControls';
import TimelinePlayer from '@/components/controls/TimelinePlayer';
import LayerToggle from '@/components/controls/LayerToggle';
import ResourcePanel from '@/components/dashboard/ResourcePanel';
import AllocationModal from '@/components/dashboard/AllocationModal';
import AIAdvisorPanel from '@/components/dashboard/AIAdvisorPanel';
import ReservoirPanel from '@/components/dashboard/ReservoirPanel';
import KeyboardShortcutsModal from '@/components/dashboard/KeyboardShortcutsModal';
import RouteInspectorModal from '@/components/map/RouteInspectorModal';
import ExecutiveDashboard from '@/components/dashboard/ExecutiveDashboard';
import MCDMPanel from '@/components/dashboard/MCDMPanel';
import {
  Coordinates,
  DisasterParameters,
  FloodZoneInput,
  PresetScenario,
  SimulationResponse,
  MapInitResponse,
  InventoryStatus,
  ResourceAllocateRequest,
  RouteInspectionData,
  AIAdvisorData,
} from '@/lib/types';
import {
  CHENNAI_CENTER,
  CHENNAI_BOUNDS,
  CHENNAI_SHELTERS,
  CHENNAI_WAREHOUSES,
  CHENNAI_DISTRIBUTION_POINTS,
  CHENNAI_POPULATION_CLUSTERS,
  HISTORICAL_PRESETS,
} from '@/lib/constants';
import {
  getMapInit,
  checkHealth,
  runSimulation,
  allocateResources,
  getResourceState,
  toSimulationParameters,
  getAdvisory,
  adaptBackendAdvisoryToClient,
} from '@/lib/api';
import {
  Map,
  Waves,
  SlidersHorizontal,
  Package,
  X,
  Download,
  RotateCcw,
  ArrowRight,
  AlertTriangle,
  CheckCircle2,
  Navigation,
  Loader2,
  Maximize2,
  Minimize2,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  TrendingUp,
  FlaskConical,
  Compass,
  Layers,
  Sparkles,
  ShieldCheck,
  Building2,
  Tent,
} from 'lucide-react';

const initialParameters: DisasterParameters = {
  rainfall_intensity_mm_hr: HISTORICAL_PRESETS[0].default_rainfall,
  flood_depth_meters: HISTORICAL_PRESETS[0].default_depth,
  spread_rate_meters_hr: HISTORICAL_PRESETS[0].default_spread,
  duration_hours: 6,
};

const initialZones: FloodZoneInput[] = [
  {
    id: HISTORICAL_PRESETS[0].id,
    type: 'polygon',
    coordinates: HISTORICAL_PRESETS[0].polygon_coordinates!,
    name: HISTORICAL_PRESETS[0].name,
  },
];

const baseline: MapInitResponse = {
  center: CHENNAI_CENTER,
  bounds: CHENNAI_BOUNDS,
  shelters: CHENNAI_SHELTERS,
  warehouses: CHENNAI_WAREHOUSES,
  distribution_points: CHENNAI_DISTRIBUTION_POINTS,
  population_clusters: CHENNAI_POPULATION_CLUSTERS,
  presets: HISTORICAL_PRESETS,
};

function stockInventory(data: MapInitResponse): InventoryStatus {
  const s = data.warehouses.reduce(
    (a, w) => ({
      water: a.water + w.supplies.water_litres,
      food: a.food + w.supplies.food_rations,
      medical: a.medical + w.supplies.medical_kits,
    }),
    { water: 0, food: 0, medical: 0 },
  );
  return {
    total_water_litres: s.water,
    available_water_litres: s.water,
    allocated_water_litres: 0,
    total_food_rations: s.food,
    available_food_rations: s.food,
    allocated_food_rations: 0,
    total_medical_kits: s.medical,
    available_medical_kits: s.medical,
    allocated_medical_kits: 0,
  };
}

export default function DashboardPage() {
  const realtime = useRealtimeData();
  const [data, setData] = useState(baseline);
  const [isBackendLive, setIsBackendLive] = useState(false);
  const [parameters, setParameters] = useState(initialParameters);
  const [rescueFleet, setRescueFleet] = useState(DEFAULT_RESCUE_FLEET);
  const [activePresetId, setActivePresetId] = useState<string | null>(
    HISTORICAL_PRESETS[0].id,
  );
  const [definedZones, setDefinedZones] = useState(initialZones);
  const [activeDrawingMode, setDrawingMode] = useState<
    'none' | 'circle' | 'polygon'
  >('none');
  const [circleRadiusMeters, setCircleRadiusMeters] = useState(2000);
  const [draftPolygonPoints, setDraftPolygonPoints] = useState<Coordinates[]>(
    [],
  );
  const [response, setResponse] = useState<SimulationResponse | null>(null);
  const [savedView, setSavedView] = useState<string | null>(null);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [isSimulating, setIsSimulating] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [isDirty, setIsDirty] = useState(false);
  const [autoRun, setAutoRun] = useState(false);

  // Modern UI/UX View State
  const [activeView, setActiveView] = useState<DashboardView>('overview');
  const [plannerStep, setPlannerStep] = useState<PlannerStep>(1);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [isMapMaximized, setIsMapMaximized] = useState(false);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' });
    const heading = document.querySelector<HTMLElement>('main h1') || document.querySelector<HTMLElement>('.clean-header h1');
    if (heading) { heading.tabIndex = -1; heading.focus({ preventScroll: true }); }
  }, [plannerStep, activeView]);

  useEffect(() => {
    if (activeDrawingMode !== 'none') {
      requestAnimationFrame(() => document.querySelector('.map-drawing')?.scrollIntoView({ block: 'center', behavior: 'smooth' }));
    }
  }, [activeDrawingMode]);

  const [visibleLayers, setVisibleLayers] = useState({
    flood: true,
    evacuation: true,
    supply: false,
    shelters: true,
    warehouses: false,
    distributionPoints: false,
    populationHeatmap: false,
  });

  const [helpOpen, setHelpOpen] = useState(false);
  const [isAdvisorOpen, setIsAdvisorOpen] = useState(false);
  const [isReservoirsOpen, setIsReservoirsOpen] = useState(false);
  const [advisorData, setAdvisorData] = useState<AIAdvisorData | null>(null);
  const [isShortcutsOpen, setIsShortcutsOpen] = useState(false);
  const [target, setTarget] = useState<{
    id: string;
    name: string;
    type: 'shelter' | 'point';
  } | null>(null);
  const [route, setRoute] = useState<RouteInspectionData | null>(null);
  const [finalInventory, setFinalInventory] = useState<InventoryStatus>(() =>
    stockInventory(baseline),
  );
  const running = useRef(false);
  useDialogFocus(helpOpen || !!route || !!target || isShortcutsOpen || isAdvisorOpen || isReservoirsOpen || isMobileSidebarOpen);

  const fetchAdvisory = useCallback(async () => {
    if (!response || isDirty) return;
    if (savedView) {
      setAdvisorData(response.ai_advisory ? adaptBackendAdvisoryToClient(response.ai_advisory) : null);
      if (!response.ai_advisory) setError('No advisory was included in this saved snapshot.');
      return;
    }
    const adv = await getAdvisory(response.simulation_id);
    setAdvisorData(adv);
    if (!adv) setError('Advice could not be loaded for this run. The engine may be offline or another browser may have replaced the scenario.');
  }, [response, isDirty, savedView]);

  useEffect(() => {
    let active = true;
    Promise.all([checkHealth(), getMapInit()]).then(
      ([health, map]) => {
        if (active) {
          setIsBackendLive(health.isLive);
          setData(map);
          setFinalInventory(stockInventory(map));
        }
      },
    );
    const refreshHealth = () =>
      checkHealth().then((health) => {
        if (active) setIsBackendLive(health.isLive);
      });
    const interval = setInterval(refreshHealth, 15000);
    window.addEventListener('focus', refreshHealth);
    return () => {
      active = false;
      clearInterval(interval);
      window.removeEventListener('focus', refreshHealth);
    };
  }, []);

  useEffect(() => {
    if (!isSimulating) return;
    const start = Date.now();
    setElapsedSeconds(0);
    const timer = setInterval(
      () => setElapsedSeconds(Math.floor((Date.now() - start) / 1000)),
      1000,
    );
    return () => clearInterval(timer);
  }, [isSimulating]);

  const clearDrawing = () => {
    setDraftPolygonPoints([]);
    setDrawingMode('none');
  };

  const changeParameters = (p: DisasterParameters) => {
    setParameters(p);
    setNotice('');
    setIsDirty(true);
    setSavedView(null);
    setIsPlaying(false);
  };

  const selectPreset = (p: PresetScenario) => {
    if (running.current) return;
    setActivePresetId(p.id);
    setNotice('');
    clearDrawing();
    setParameters({
      ...parameters,
      rainfall_intensity_mm_hr: p.default_rainfall,
      rainfall_input_unit: 'legacy_level',
      flood_depth_meters: p.default_depth,
      spread_rate_meters_hr: p.default_spread,
    });
    setDefinedZones([
      {
        id: p.id,
        type: p.polygon_coordinates ? 'polygon' : 'circle',
        coordinates: p.polygon_coordinates || [p.center],
        radius_meters: p.radius_meters,
        name: p.name,
      },
    ]);
    setIsDirty(true);
    setIsPlaying(false);
  };

  const mapClick = (coords: Coordinates) => {
    if (
      coords[0] < 12.8 ||
      coords[0] > 13.35 ||
      coords[1] < 80 ||
      coords[1] > 80.4
    ) {
      setError('Choose a flood zone within the Chennai study area.');
      return;
    }
    if (activeDrawingMode === 'circle') {
      setDefinedZones([
        {
          id: `circle-${Date.now()}`,
          type: 'circle',
          coordinates: [coords],
          radius_meters: circleRadiusMeters,
          name: 'Custom circular zone',
        },
      ]);
      setActivePresetId(null);
      setDrawingMode('none');
      setIsDirty(true);
      setIsPlaying(false);
    } else if (activeDrawingMode === 'polygon')
      setDraftPolygonPoints((p) => [...p, coords]);
  };

  const finishPolygon = () => {
    if (draftPolygonPoints.length < 3) return;
    setDefinedZones([
      {
        id: `polygon-${Date.now()}`,
        type: 'polygon',
        coordinates: [...draftPolygonPoints, draftPolygonPoints[0]],
        name: 'Custom polygon zone',
      },
    ]);
    setActivePresetId(null);
    clearDrawing();
    setIsDirty(true);
    setIsPlaying(false);
  };

  const run = async () => {
    if (running.current || !definedZones.length) return;
    if (activeDrawingMode !== 'none') {
      setError('Finish or cancel the zone drawing before running the simulation.');
      return;
    }
    running.current = true;
    setIsSimulating(true);
    setAdvisorData(null);
    setRoute(null);
    setTarget(null);
    setError('');
    setNotice('');
    setIsPlaying(false);
    try {
      const result = await runSimulation({
        flood_zones: definedZones,
        parameters,
        rescue_fleet: rescueFleet,
      });
      if (!result.timeline?.length)
        throw new Error(
          'The engine returned an empty timeline. Please try again.',
        );
      setResponse(result);
      setPlannerStep(3); setActiveView('results');
      setSavedView(null);
      setFinalInventory(
        result.timeline[result.timeline.length - 1].inventory_status,
      );
      // Open the most affected snapshot so a completed run immediately shows impact.
      setCurrentStepIndex(
        result.timeline.reduce(
          (best, s, i) =>
            s.metrics.total_affected_population >
            result.timeline[best].metrics.total_affected_population
              ? i
              : best,
          0,
        ),
      );
      setIsDirty(false);
      setIsBackendLive(true);
      clearDrawing();
      setNotice('Analysis complete. Start with the explanation below, then explore shelters, supplies, or routes.');
      const state = await getResourceState();
      if (state && state.simulation_id === result.simulation_id)
        setData((d) => ({
          ...d,
          warehouses: state.warehouses,
          distribution_points: state.distribution_points,
        }));
      if (result.ai_advisory) setAdvisorData(adaptBackendAdvisoryToClient({
        ...result.ai_advisory, snapshot_hour: result.timeline[result.timeline.length - 1].hour,
      }));
    } catch (e) {
      setError(
        e instanceof Error ? e.message : 'Simulation failed. Please try again.',
      );
      setIsBackendLive((await checkHealth()).isLive);
    } finally {
      running.current = false;
      setIsSimulating(false);
    }
  };

  const step = response?.timeline[currentStepIndex] ?? null;
  const finalIndex = response ? response.timeline.length - 1 : 0;
  const inventory =
    step && currentStepIndex !== finalIndex
      ? step.inventory_status
      : finalInventory;

  const togglePlay = useCallback(() => {
    if (!response || isDirty || isSimulating) return;
    if (
      !isPlaying &&
      response &&
      currentStepIndex >= response.timeline.length - 1
    )
      setCurrentStepIndex(0);
    setIsPlaying((p) => !p);
  }, [response, currentStepIndex, isPlaying, isDirty, isSimulating]);

  // Playback belongs to the dashboard, so it also works outside the map view.
  useEffect(() => {
    if (!isPlaying || !response || isDirty || isSimulating) return;
    if (currentStepIndex >= response.timeline.length - 1) {
      setIsPlaying(false);
      return;
    }
    const timer = setTimeout(() => setCurrentStepIndex((i) => i + 1), 1300 / playbackSpeed);
    return () => clearTimeout(timer);
  }, [isPlaying, response, isDirty, isSimulating, currentStepIndex, playbackSpeed]);

  const runRef = useRef(run);
  runRef.current = run;

  useEffect(() => {
    if (!autoRun || !isDirty || !isBackendLive || savedView || activeDrawingMode !== 'none' || !definedZones.length) return;
    const timer = setTimeout(() => { if (!running.current) void runRef.current(); }, 1500);
    return () => clearTimeout(timer);
  }, [autoRun, isDirty, isBackendLive, savedView, activeDrawingMode, definedZones, parameters, rescueFleet]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const targetTag = (e.target as HTMLElement)?.tagName?.toLowerCase();
      if (
        (e.target as HTMLElement)?.isContentEditable ||
        targetTag === 'input' ||
        targetTag === 'textarea' ||
        targetTag === 'select'
      ) {
        return;
      }

      if (e.key === 'Escape') {
        if (isMobileSidebarOpen) {
          setIsMobileSidebarOpen(false);
          return;
        }
        if (isShortcutsOpen) {
          setIsShortcutsOpen(false);
          return;
        }
        if (isAdvisorOpen) {
          setIsAdvisorOpen(false);
          return;
        }
        if (isReservoirsOpen) {
          setIsReservoirsOpen(false);
          return;
        }
        if (helpOpen) {
          setHelpOpen(false);
          return;
        }
        if (route) {
          setRoute(null);
          return;
        }
        if (target) {
          setTarget(null);
          return;
        }
        if (activeDrawingMode !== 'none') {
          clearDrawing();
          return;
        }
      }

      // Keep shortcuts inside the active dialog and preserve native controls.
      if (helpOpen || route || target || isShortcutsOpen || isAdvisorOpen || isReservoirsOpen || isMobileSidebarOpen) return;
      if (e.ctrlKey || e.metaKey || e.altKey || e.repeat) return;
      if ((e.target as HTMLElement)?.closest('button, a, [role="button"]')) return;

      if (e.key === ' ' || e.code === 'Space') {
        e.preventDefault();
        togglePlay();
      }

      if (e.key === 'ArrowRight') {
        e.preventDefault();
        if (response?.timeline?.length) {
          setCurrentStepIndex((prev) =>
            Math.min(response.timeline.length - 1, prev + 1),
          );
          setIsPlaying(false);
        }
      }

      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        if (response?.timeline?.length) {
          setCurrentStepIndex((prev) => Math.max(0, prev - 1));
          setIsPlaying(false);
        }
      }

      if (
        (e.key === 'a' || e.key === 'A') &&
        !e.ctrlKey &&
        !e.metaKey &&
        !e.altKey
      ) {
        e.preventDefault();
        setIsAdvisorOpen((prev) => !prev);
      }

      if (
        (e.key === 'r' || e.key === 'R') &&
        !e.ctrlKey &&
        !e.metaKey &&
        !e.altKey
      ) {
        if (!isSimulating && definedZones.length > 0) {
          e.preventDefault();
          setActiveView('scenario'); setPlannerStep(2);
        }
      }

      if (e.key === '?' || (e.key === '/' && e.shiftKey)) {
        e.preventDefault();
        setIsShortcutsOpen((prev) => !prev);
      }

      if (e.key === '1') { setActiveView('scenario'); setPlannerStep(1); }
      if (e.key === '2') setActiveView('experiments');
      if (e.key === '3') setActiveView('review');
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    isShortcutsOpen,
    isAdvisorOpen,
    isReservoirsOpen,
    isMobileSidebarOpen,
    helpOpen,
    route,
    target,
    activeDrawingMode,
    togglePlay,
    response,
    isSimulating,
    definedZones.length,
  ]);

  const openAllocation = (id: string, type: 'shelter' | 'point') => {
    if (savedView) { setError('This is a read-only saved simulation. Run its settings again before making new allocations.'); return; }
    if (activeDrawingMode !== 'none' || isSimulating) return;
    if (!response || isDirty) {
      setError('Run the current scenario before allocating supplies.');
      return;
    }
    setIsPlaying(false);
    setCurrentStepIndex(finalIndex);
    const entity = (
      type === 'shelter' ? data.shelters : data.distribution_points
    ).find((e) => e.id === id);
    setTarget({ id, name: entity?.name || id, type });
  };

  const confirmAllocation = async (request: ResourceAllocateRequest) => {
    if (savedView) throw new Error('Saved simulations are read-only. Rerun the settings before allocating.');
    const result = await allocateResources({
      ...request,
      simulation_id: response?.simulation_id,
    });
    if (!result.success) throw new Error(result.message || 'Allocation failed.');
    setFinalInventory(result.updated_inventory);
    setResponse((prev) =>
      prev
        ? {
            ...prev,
            inventory_ledger: result.ledger ?? prev.inventory_ledger,
            supply_routes: {
              type: 'FeatureCollection',
              features: [
                ...(prev.supply_routes?.features || []),
                ...(result.updated_supply_routes || []),
              ],
            },
            rescue_routes: {
              type: 'FeatureCollection',
              features: [
                ...(prev.rescue_routes?.features || []),
                ...(result.updated_rescue_routes || []),
              ],
            },
            timeline: prev.timeline.map((s, i) =>
              i === prev.timeline.length - 1
                ? {
                    ...s,
                    inventory_status: result.updated_inventory,
                    supply_routes: {
                      type: 'FeatureCollection',
                      features: [
                        ...s.supply_routes.features,
                        ...(result.updated_supply_routes || []),
                        ...(result.updated_rescue_routes || []),
                      ],
                    },
                  }
                : s,
            ),
          }
        : prev,
    );
    const state = await getResourceState();
    if (state && state.simulation_id === response?.simulation_id)
      setData((d) => ({
        ...d,
        warehouses: state.warehouses,
        distribution_points: state.distribution_points,
      }));
    setNotice('Allocation recorded in the final-step inventory.');
  };

  const reset = () => {
    if (running.current) return;
    setResponse(null);
    setActiveView('scenario');
    setPlannerStep(1); setIsMapMaximized(false); setAutoRun(false);
    setSavedView(null);
    setIsPlaying(false);
    setCurrentStepIndex(0);
    setParameters(initialParameters);
    setRescueFleet(DEFAULT_RESCUE_FLEET);
    setDefinedZones(initialZones);
    setActivePresetId(HISTORICAL_PRESETS[0].id);
    setIsDirty(false);
    setError('');
    setNotice('');
    setAdvisorData(null);
    setRoute(null);
    setTarget(null);
    clearDrawing();
    setFinalInventory(stockInventory(baseline));
    setData((d) => ({
      ...d,
      warehouses: baseline.warehouses,
      distribution_points: baseline.distribution_points,
    }));
  };

  const exportResults = () => {
    if (!response || isDirty || isSimulating) return;
    const blob = new Blob(
      [
        JSON.stringify(
          {
            ...response,
            parameters: response.archived_parameters || toSimulationParameters(parameters),
            flood_zones: definedZones,
            simulation_only: true,
          },
          null,
          2,
        ),
      ],
      { type: 'application/json' },
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${response.simulation_id}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
  };

  const plannerMap = (mode: 'setup' | 'summary' | 'routes') => <div className={`guided-map map-${mode} ${activeDrawingMode !== 'none' && mode === 'setup' ? 'map-drawing drawing-active' : ''} ${isMapMaximized && mode === 'routes' ? 'map-expanded' : ''}`}>
    <MapContainer center={data.center} bounds={data.bounds} shelters={data.shelters} warehouses={data.warehouses} distributionPoints={data.distribution_points} populationClusters={data.population_clusters} stagingBases={[]} currentStep={mode === 'setup' ? null : step} showRescuePlayback={mode === 'routes'} definedZones={definedZones} activeDrawingMode={mode === 'setup' ? activeDrawingMode : 'none'} circleRadiusMeters={circleRadiusMeters} draftPolygonPoints={draftPolygonPoints} draftCircleCenter={null} onMapClick={mapClick} visibleLayers={mode === 'setup' ? { ...visibleLayers, shelters: false, warehouses: false, distributionPoints: false } : visibleLayers} onSelectShelter={id => openAllocation(id, 'shelter')} onSelectDistributionPoint={id => openAllocation(id, 'point')} onSelectRoute={setRoute} />
    {mode === 'routes' && <div className="absolute top-3 right-3 z-[500]"><LayerToggle layers={visibleLayers} onToggleLayer={key => setVisibleLayers(previous => ({ ...previous, [key]: !previous[key] }))} /></div>}
    {mode === 'setup' && activeDrawingMode !== 'none' && <div className="drawing-instructions"><p>{activeDrawingMode === 'polygon' ? `${draftPolygonPoints.length} points placed. Click at least three map points, then Finish.` : 'Click the map to place a circular flood area.'}</p><div>{activeDrawingMode === 'polygon' && <><button disabled={draftPolygonPoints.length < 3} onClick={finishPolygon}>Finish</button><button disabled={!draftPolygonPoints.length} onClick={() => setDraftPolygonPoints(points => points.slice(0, -1))}>Undo</button></>}<button onClick={clearDrawing}>Cancel</button></div></div>}
  </div>;

  const supplyContent = <><div className="space-y-6">
              {/* Warehouse & Shelter Dedicated Panels */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-1 space-y-4">
                  <div className="p-5 rounded-2xl bg-slate-50/70 border border-slate-200 space-y-4">
                    <div className="flex items-center gap-2">
                      <Package className="w-5 h-5 text-amber-800" />
                      <h2 className="text-base font-bold text-slate-900">
                        Supply depots
                      </h2>
                    </div>
                    <p className="text-sm text-slate-700">
                      Current available stock across Greater Chennai
                      warehouses.
                    </p>
                    <ResourcePanel
                      inventory={inventory}
                      shelters={data.shelters}
                      distributionPoints={data.distribution_points}
                      shelterAllocations={step?.shelter_allocations || []}
                      onOpenAllocateModal={openAllocation} allocationDisabled={!response || isDirty || !!savedView || isSimulating}
                      isCollapsed={false}
                      onToggleCollapse={() => {}}
                    />
                  </div>
                </div>

                <div className="lg:col-span-2 space-y-4">
                  {/* Shelter Capacity Directory */}
                  <div className="p-5 rounded-2xl bg-slate-50/70 border border-slate-200 space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Tent className="w-5 h-5 text-blue-700" />
                        <h3 className="text-base font-bold text-slate-900">
                          Shelters
                        </h3>
                      </div>
                      <span className="text-sm font-mono text-slate-700">
                        {data.shelters.length} modeled facilities
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[500px] overflow-y-auto custom-scrollbar">
                      {data.shelters.map((shelter) => {
                        const alloc = step?.shelter_allocations.find(
                          (a) => a.shelter_id === shelter.id,
                        );
                        const occ = (alloc?.current_occupancy ?? shelter.current_occupancy ?? 0) + (alloc?.allocated_evacuees ?? 0);
                        const cap = alloc?.total_capacity || shelter.capacity;
                        const pct = Math.round((occ / cap) * 100);
                        const isFull = alloc?.status === 'full';
                        const isCompromised =
                          alloc?.status === 'compromised';

                        return (
                          <div
                            key={shelter.id}
                            className="p-3.5 rounded-xl bg-slate-50/70 border border-slate-200 flex flex-col justify-between gap-3 hover:border-slate-200 transition-colors"
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div>
                                <h4 className="text-sm font-bold text-slate-900">
                                  {shelter.name}
                                </h4>
                                <span className="text-sm text-slate-600 font-mono">
                                  Lat {shelter.location[0].toFixed(3)}, Lng{' '}
                                  {shelter.location[1].toFixed(3)}
                                </span>
                              </div>
                              <span
                                className={`text-sm font-mono px-2 py-0.5 rounded-full border ${
                                  isCompromised
                                    ? 'bg-red-50 text-red-700 border-red-200'
                                    : isFull
                                      ? 'bg-amber-50 text-amber-800 border-amber-200'
                                      : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                }`}
                              >
                                {isCompromised
                                  ? 'COMPROMISED'
                                  : isFull
                                    ? 'CAPACITY FULL'
                                    : 'ACTIVE'}
                              </span>
                            </div>

                            <div className="space-y-1">
                              <div className="flex justify-between text-sm font-mono">
                                <span className="text-slate-700">
                                  Occupancy:
                                </span>
                                <span className="text-slate-900 font-semibold">
                                  {occ.toLocaleString()} / {cap.toLocaleString()}{' '}
                                  ({pct}%)
                                </span>
                              </div>
                              <div className="w-full bg-slate-50 rounded-full h-1.5 overflow-hidden">
                                <div
                                  className={`h-full rounded-full ${
                                    pct >= 90
                                      ? 'bg-amber-400'
                                      : 'bg-cyan-400'
                                  }`}
                                  style={{ width: `${Math.min(100, pct)}%` }}
                                />
                              </div>
                            </div>

                            <button
                              onClick={() =>
                                openAllocation(shelter.id, 'shelter')
                              }
                              disabled={!response || isDirty || !!savedView || isSimulating}
                              className="w-full py-1.5 px-3 rounded-lg text-sm font-semibold bg-slate-50 hover:bg-slate-100 text-cyan-700 border border-slate-200 transition-colors disabled:opacity-40"
                            >
                              Allocate supplies
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            </div></>;

  const threatText = response && !isDirty ? 'READY' : 'RUN FIRST';

  const timeStepLabel = response ? `T+${step?.hour}h` : undefined;

  return (
    <div className="simulation-app min-h-screen bg-slate-50 text-slate-900 flex">
      {/* 1. Collapsible Modern Sidebar (Desktop) */}
      <div className="hidden md:block">
        <Sidebar
          activeView={activeView}
          onSelectView={view => { setActiveView(view); if (view === 'scenario') { setPlannerStep(1); setIsMapMaximized(false); } if (view === 'results') { setPlannerStep(3); } }}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
          isBackendLive={isBackendLive}
          isSimulating={isSimulating}
          hasSimulation={!!response}
          onRunSimulation={run}
          onReset={reset}
          onExport={exportResults}
          onOpenAdvisor={() => setIsAdvisorOpen((prev) => !prev)}
          onOpenReservoirs={() => setIsReservoirsOpen(true)}
          onHelp={() => setHelpOpen(true)}
          onShortcuts={() => setIsShortcutsOpen(true)}
          advisorThreatLevel={threatText}
          timeStepText={timeStepLabel}
          isDirty={isDirty}
        />
      </div>

      {/* Mobile Drawer Overlay */}
      {isMobileSidebarOpen && (
        <div
          className="fixed inset-0 z-50 bg-slate-50/80 backdrop-blur-md md:hidden"
          onClick={() => setIsMobileSidebarOpen(false)}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Navigation"
            className="w-64 h-full bg-slate-50 border-r border-slate-200"
            onClick={(e) => e.stopPropagation()}
          >
            <Sidebar
              activeView={activeView}
              onSelectView={(v) => {
                setActiveView(v); if (v === 'scenario') setPlannerStep(1); if (v === 'results') { setPlannerStep(3); }
                setIsMobileSidebarOpen(false);
              }}
              isCollapsed={false}
              onToggleCollapse={() => setIsMobileSidebarOpen(false)}
              isBackendLive={isBackendLive}
              isSimulating={isSimulating}
              hasSimulation={!!response}
              onRunSimulation={() => {
                setIsMobileSidebarOpen(false);
                run();
              }}
              onReset={reset}
              onExport={exportResults}
              onOpenAdvisor={() => {
                setIsMobileSidebarOpen(false);
                setIsAdvisorOpen(true);
              }}
              onOpenReservoirs={() => { setIsMobileSidebarOpen(false); setIsReservoirsOpen(true); }}
              onHelp={() => {
                setIsMobileSidebarOpen(false);
                setHelpOpen(true);
              }}
              onShortcuts={() => {
                setIsMobileSidebarOpen(false);
                setIsShortcutsOpen(true);
              }}
              advisorThreatLevel={threatText}
              timeStepText={timeStepLabel}
              isDirty={isDirty}
            />
          </div>
        </div>
      )}

      {/* 2. Main Content Canvas */}
      <div
        className={`flex-1 flex flex-col min-w-0 ${
          isSidebarCollapsed ? 'md:ml-[72px]' : 'md:ml-[224px]'
        }`}
      >
        {/* Sticky Unified Top Header */}
        <Header
          realtimeEnabled={realtime.enabled}
          onToggleRealtime={realtime.toggle}
          onRunSimulation={run}
          isBackendLive={isBackendLive}
          onHelp={() => setHelpOpen(true)}
          onOpenAdvisor={() => setIsAdvisorOpen((prev) => !prev)}
          onOpenReservoirs={() => setIsReservoirsOpen(true)}
          onShortcuts={() => setIsShortcutsOpen(true)}
          advisorThreatLevel={threatText}
          isSidebarCollapsed={isSidebarCollapsed}
          onToggleSidebar={() => {
            if (window.innerWidth < 768) {
              setIsMobileSidebarOpen((p) => !p);
            } else {
              setIsSidebarCollapsed((p) => !p);
            }
          }}
          activeView={activeView}
          onSelectView={view => { setActiveView(view); if (view === 'scenario') { setPlannerStep(1); setIsMapMaximized(false); } if (view === 'results') { setPlannerStep(3); } }}
          presets={data.presets}
          activePresetId={activePresetId}
          onSelectPreset={selectPreset}
          timeStepText={timeStepLabel}
          isDirty={isDirty}
          isSimulating={isSimulating}
        />

        {/* Global Notifications & Banners */}
        <div className={(!isBackendLive || isSimulating || error || notice) ? "px-4 sm:px-6 pt-3 space-y-2" : "hidden"}>
          {!isBackendLive && (
            <div
              className="flex items-center justify-between p-3 rounded-xl bg-amber-50/40 border border-amber-200/60 text-amber-800 text-sm"
              role="status"
            >
              <div className="flex items-center gap-2.5">
                <AlertTriangle className="w-4 h-4 text-amber-800 flex-shrink-0" />
                <span>
                  <strong>Python Simulation Engine offline:</strong> Start
                  services via <code>start_project.bat</code> to run scenarios.
                </span>
              </div>
              <button
                onClick={async () => {
                  const health = await checkHealth();
                  setIsBackendLive(health.isLive);
                  if (health.isLive) setData(await getMapInit());
                }}
                className="px-2.5 py-1 text-sm font-semibold bg-amber-50/70 hover:bg-amber-50 border border-amber-200 rounded-lg text-amber-800 transition-colors"
              >
                Reconnect
              </button>
            </div>
          )}

          {isSimulating && plannerStep !== 2 && (
            <div
              className="flex items-center gap-3 p-3 rounded-xl bg-cyan-50/40 border border-cyan-200/60 text-cyan-700 text-sm "
              role="status"
            >
              <Loader2 className="w-4 h-4 animate-spin text-cyan-700" />
              <span>
                <strong>Computing flood progression and route graph:</strong>{' '}
                {elapsedSeconds}s elapsed · {parameters.duration_hours}-hour
                scenario simulation
              </span>
            </div>
          )}

          {error && (
            <div
              className="flex items-center justify-between p-3 rounded-xl bg-red-50/50 border border-red-200/70 text-red-700 text-sm"
              role="alert"
            >
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-700 flex-shrink-0" />
                <span>{error}</span>
              </div>
              <button
                onClick={() => setError('')}
                className="p-1 text-red-700 hover:text-slate-900"
                aria-label="Dismiss error"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {notice && !error && (
            <div
              className="flex items-center justify-between p-3 rounded-xl bg-emerald-50/40 border border-emerald-200/60 text-emerald-700 text-sm shadow-glow-emerald"
              role="status"
            >
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-700 flex-shrink-0" />
                <span>{notice}</span>
              </div>
              <button
                onClick={() => setNotice('')}
                className="p-1 text-emerald-700 hover:text-slate-900"
                aria-label="Dismiss notification"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        {/* Main Work Area */}
        <main className="clean-workspace flex-1 p-4 sm:p-6 space-y-5 max-w-[1600px] w-full mx-auto">
          {activeView === 'realtime' && <RealtimePanel enabled={realtime.enabled} snapshot={realtime.snapshot} loading={realtime.loading} error={realtime.error} onRefresh={realtime.refresh} busy={isSimulating} savedView={!!savedView} onApplyRainfall={rate => {
            if (!realtime.enabled || realtime.error || !canApplyWeather(realtime.snapshot?.weather) || isSimulating || savedView) return;
            setParameters(previous => ({ ...previous, rainfall_intensity_mm_hr: rate, rainfall_input_unit: 'mm_per_hour' }));
            setAutoRun(false); setIsDirty(true); setIsPlaying(false); setActivePresetId(null);
            setNotice('Downloaded hourly rainfall applied. Review and run the scenario; automatic reruns are paused. Flood depth and spread remain your scenario settings.');
          }} />}
          {(activeView === 'scenario' || activeView === 'results') && <>
            <PlannerSteps step={plannerStep} hasResults={!!response} onSelect={value => { if (!isSimulating) { setPlannerStep(value); setActiveView(value === 3 ? 'results' : 'scenario'); setIsMapMaximized(false); } }} />
          {savedView && <p role="status" className="rounded-lg border border-cyan-200 bg-cyan-50/50 p-4 text-sm text-cyan-700">Saved view: {savedView}. Read-only snapshot; new allocations require rerunning the settings. Ground inventory on the engine has not been replaced.</p>}
            {response && isDirty && <div className="planner-warning" role="status">Settings have changed. Previous results are outdated. Review and run again before allocating supplies, saving, or exporting. <button className="underline" onClick={() => { setActiveView('scenario'); setPlannerStep(2); }}>Review changes</button></div>}
            {plannerStep === 1 && <ScenarioSetup presets={HISTORICAL_PRESETS} selected={activePresetId} onSelect={selectPreset} parameters={parameters} onChange={changeParameters} busy={isSimulating} drawing={activeDrawingMode !== 'none'} onReview={() => setPlannerStep(2)} map={plannerMap('setup')} advanced={<>
              <fieldset disabled={isSimulating}><DisasterControls parameters={parameters} onParametersChange={changeParameters} activeDrawingMode={activeDrawingMode} setActiveDrawingMode={mode => { setDrawingMode(mode); setDraftPolygonPoints([]); }} circleRadiusMeters={circleRadiusMeters} setCircleRadiusMeters={setCircleRadiusMeters} draftPolygonPoints={draftPolygonPoints} onFinishPolygon={finishPolygon} onClearDrawing={clearDrawing} onUndoLastPoint={() => setDraftPolygonPoints(points => points.slice(0, -1))} activePresetId={activePresetId} onSelectPreset={selectPreset} onRunSimulation={run} isSimulating={isSimulating} definedZonesCount={definedZones.length} advancedOnly /></fieldset>
              <button className="planner-secondary" onClick={() => setActiveView('fleet')}>Configure rescue fleet <ArrowRight size={16} /></button>
              <label className="flex items-center gap-3"><input type="checkbox" checked={autoRun} disabled={isSimulating || !!savedView} onChange={event => { setAutoRun(event.target.checked); if (event.target.checked) setIsDirty(true); }} />Automatically rerun after settings change</label><p className="muted">Automatic reruns are {autoRun ? 'enabled' : 'off'}. When enabled, the planner waits 1.5 seconds after edits.</p>
            </>} />}
            {plannerStep === 2 && <ScenarioReview name={HISTORICAL_PRESETS.find(p => p.id === activePresetId)?.name || 'Custom flood scenario'} parameters={parameters} fleet={rescueFleet.trucks.count + rescueFleet.boats.count + rescueFleet.helicopters.count} zones={definedZones.length} busy={isSimulating} online={isBackendLive} elapsed={elapsedSeconds} error={error} onBack={() => setPlannerStep(1)} onRun={run} />}
            {plannerStep === 3 && response && <div className="guided-screen">
              <div className="planner-heading results-heading"><div><span className="planner-eyebrow">YOUR RESPONSE PLAN</span><h1>Understand the impact.</h1><p>These results describe hour {step?.hour}. Explore a different hour to see how the plan changes.</p></div><button className="planner-secondary" disabled={isSimulating} onClick={() => { setPlannerStep(1); setActiveView('scenario'); setIsMapMaximized(false); }}>Edit scenario</button></div>
              <MetricsOverview currentStep={step} onCardClick={type => setActiveView(type === 'rescue' ? 'fleet' : type === 'evac' ? 'logistics' : 'routes')} />
              <ResultsSummary result={response} index={currentStepIndex} onSelect={index => { setCurrentStepIndex(index); setIsPlaying(false); }} map={plannerMap('summary')} />
              <div className="dashboard-support-grid"><button onClick={() => setActiveView('logistics')}><Package size={21} /><span><strong>Shelters & supplies</strong><small>Inspect capacity and allocate relief stock.</small></span><ArrowRight size={17} /></button><button onClick={() => setActiveView('routes')}><Map size={21} /><span><strong>Map & routes</strong><small>Explore layers, route details, and timeline playback.</small></span><ArrowRight size={17} /></button></div>
              <div className="results-actions"><button className="planner-secondary" disabled={isDirty || isSimulating} onClick={() => setActiveView('experiments')}>Save analysis</button><ScenarioReport compact result={response} parameters={parameters} isDirty={isDirty} isSimulating={isSimulating} /></div>
              {isDirty && <p className="muted">Saving and downloading are unavailable until the changed settings are rerun.</p>}
            </div>}
          </>}

          {activeView === 'overview' && (
            <ExecutiveDashboard
              data={data}
              response={response}
              step={step}
              currentStepIndex={currentStepIndex}
              onStepChange={(i) => {
                setCurrentStepIndex(i);
                setIsPlaying(false);
              }}
              isPlaying={isPlaying}
              onTogglePlay={togglePlay}
              playbackSpeed={playbackSpeed}
              onSpeedChange={setPlaybackSpeed}
              parameters={parameters}
              onChangeParameters={changeParameters}
              activePresetId={activePresetId}
              onSelectPreset={selectPreset}
              definedZones={definedZones}
              isSimulating={isSimulating}
              elapsedSeconds={elapsedSeconds}
              onRunSimulation={run}
              onResetScenario={reset}
              onExportResults={exportResults}
              isBackendLive={isBackendLive}
              isDirty={isDirty}
              savedView={savedView}
              rescueFleet={rescueFleet}
              inventory={finalInventory}
              visibleLayers={visibleLayers}
              onToggleLayer={(key) =>
                setVisibleLayers((prev) => ({ ...prev, [key]: !prev[key] }))
              }
              onSelectView={(v) => {
                setActiveView(v);
                if (v === 'scenario') {
                  setPlannerStep(1);
                  setIsMapMaximized(false);
                }
                if (v === 'results') {
                  setPlannerStep(3);
                }
              }}
              onOpenAllocation={openAllocation}
              onSelectRoute={setRoute}
              onOpenAdvisor={() => setIsAdvisorOpen(true)}
              onOpenReservoirs={() => setIsReservoirsOpen(true)}
              advisorData={advisorData}
            />
          )}
          {(activeView === 'results' || activeView === 'routes') && !response && <section className="module-empty"><Map size={30} /><h2>Start with a flood simulation</h2><p>Run a scenario to explore {activeView === 'routes' ? 'the map, routes, and playback' : 'impact and response results'} here.</p><button className="planner-primary" onClick={() => { setActiveView('scenario'); setPlannerStep(1); }}>Create a scenario <ArrowRight size={17} /></button></section>}
          {activeView === 'routes' && response && <section className="planner-card space-y-4" aria-label="Map and routes"><div><h2>Explore the response map</h2><p className="muted">Hour {step?.hour}. Select a route for details or use the layer controls.</p></div>{isDirty && <p className="planner-warning" role="status">These routes belong to the previous run. Rerun the changed settings to update them.</p>}{plannerMap('routes')}<TimelinePlayer totalSteps={response.timeline.length} currentStepIndex={currentStepIndex} onStepChange={index => { setCurrentStepIndex(index); setIsPlaying(false); }} isPlaying={isPlaying} onTogglePlay={togglePlay} playbackSpeed={playbackSpeed} onSpeedChange={setPlaybackSpeed} stepDescription={`Hour ${step?.hour} · ${step?.evacuation_routes.features.length} evacuation routes · ${step?.supply_routes.features.length} delivery routes`} /></section>}
          {activeView === 'logistics' && <div className="space-y-5"><p className="planner-note">{!response ? 'Baseline shelter capacity and relief stock. Run a flood simulation to calculate assignments and enable allocations.' : isDirty ? 'Settings have changed. Rerun the simulation to update assignments and enable allocations.' : `Shelter assignments at hour ${step?.hour}. Manual allocations apply to the final hour.${savedView ? ' This saved snapshot is read-only.' : ''}`}</p>{supplyContent}</div>}

          {/* VIEW 4: IMPACT & ANALYTICS */}
          {activeView === 'analytics' && (
            <div className="space-y-6">
              {response ? (
                <ScenarioInsights
                  result={response}
                  selected={currentStepIndex}
                  onSelect={(i) => {
                    setCurrentStepIndex(i);
                    setIsPlaying(false);
                  }}
                />
              ) : (
                <div className="p-12 text-center rounded-2xl bg-slate-50/60 border border-slate-200 space-y-3">
                  <TrendingUp className="w-8 h-8 text-cyan-700 mx-auto" />
                  <h3 className="text-base font-bold text-slate-900">
                    No Simulation Analytics Available
                  </h3>
                  <p className="text-sm text-slate-700 max-w-md mx-auto">
                    Please define a flood scenario and run the simulation engine
                    to generate temporal vulnerability graphs and ML demand
                    forecasts.
                  </p>
                  <button
                    onClick={() => { setActiveView('scenario'); setPlannerStep(1); }}
                    className="px-4 py-2 text-sm font-semibold rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-600 "
                  >
                    Open flood simulation
                  </button>
                </div>
              )}
            </div>
          )}

          {activeView === 'review' && <ProjectReview result={response} isDirty={isDirty} />}
          {activeView === 'wards' && <WardProfiles />}

          {activeView === 'fleet' && <div className="space-y-5"><section className="planner-card space-y-4"><h2>Fleet configuration</h2><p className="muted">Set available vehicles for the next simulation. Changes require a new run.</p><RescueFleetControls shelters={data.shelters} value={rescueFleet} disabled={isSimulating} onChange={value => { setRescueFleet(value); setSavedView(null); setIsDirty(true); setIsPlaying(false); }} /><button className="planner-primary" disabled={isSimulating} onClick={() => { setActiveView('scenario'); setPlannerStep(2); }}>Review and run <ArrowRight size={17} /></button></section><RescueFleetPanel step={step} isDirty={isDirty} />{response && <TimelinePlayer totalSteps={response.timeline.length} currentStepIndex={currentStepIndex} onStepChange={index => { setCurrentStepIndex(index); setIsPlaying(false); }} isPlaying={isPlaying} onTogglePlay={togglePlay} playbackSpeed={playbackSpeed} onSpeedChange={setPlaybackSpeed} stepDescription={`Rescue plan at hour ${step?.hour}`} />}</div>}
          {activeView === 'weather' && <WeatherModelPanel />}
          {activeView === 'reservoirs' && (
            <ReservoirPanel inline onClose={() => setActiveView('overview')} />
          )}
          {activeView === 'mcdm' && (
            <MCDMPanel inline onClose={() => setActiveView('overview')} />
          )}
          {activeView === 'advisor' && (
            <AIAdvisorPanel
              inline
              onClose={() => setActiveView('overview')}
              advisorData={advisorData}
              onRefresh={fetchAdvisory}
            />
          )}
          {activeView === 'kaggle' && <KaggleModelPanel />}

          {/* VIEW 5: EXPERIMENT LAB */}
          {/* Keep the recorder mounted so runs are saved while other views are open. */}
            <div hidden={activeView !== 'experiments'} className="space-y-6">
              <SavedSimulationLibrary result={response} running={isSimulating} disabled={isDirty || isSimulating} archived={!!savedView} onOpen={snapshot => {
                const loaded = { ...snapshot.result, archive_origin: snapshot.imported_from?.notice, archived_evidence: snapshot.evidence, archived_parameters: snapshot.result.scenario?.parameters };
                setResponse(loaded); setData(snapshot.map_data); setParameters({ ...snapshot.view.parameters, ...(snapshot.result.scenario?.parameters ? { rainfall_intensity_mm_hr: snapshot.result.scenario.parameters.rainfall_intensity_mm_hr, rainfall_input_unit: 'mm_per_hour' as const } : {}) }); setDefinedZones(snapshot.view.zones);
                setRescueFleet(loaded.scenario?.rescue_fleet || DEFAULT_RESCUE_FLEET); setSavedView(snapshot.name + (snapshot.imported_from ? ' (imported file; evidence not independently verified)' : ''));
                setCurrentStepIndex(loaded.timeline.reduce((best, step, i) => step.metrics.total_affected_population > loaded.timeline[best].metrics.total_affected_population ? i : best, 0));
                setFinalInventory(loaded.timeline[loaded.timeline.length-1].inventory_status);
                setIsDirty(false); setIsPlaying(false); setTarget(null); setRoute(null); setActivePresetId(null); clearDrawing(); setError('');
                setAdvisorData(loaded.ai_advisory ? adaptBackendAdvisoryToClient(loaded.ai_advisory) : null); setPlannerStep(3); setActiveView('results');
                setNotice(`Opened ${snapshot.name}.`);
              }} />
              <details className="clean-disclosure"><summary>Export a scenario report</summary><div className="pt-4"><ScenarioReport result={response} parameters={parameters} isDirty={isDirty} isSimulating={isSimulating} /></div></details>
              <details className="clean-disclosure"><summary>Compare runs</summary><ExperimentNotebook
                result={isDirty ? null : response}
                parameters={parameters}
                zones={definedZones}
                disabled={isSimulating}
                onRestore={(savedParameters, savedZones, savedFleet) => {
                  setParameters(savedParameters);
                  setSavedView(null);
                  setRescueFleet(savedFleet || DEFAULT_RESCUE_FLEET);
                  setDefinedZones(savedZones);
                  setActivePresetId(null);
                  setIsDirty(true);
                  setIsPlaying(false);
                  clearDrawing();
                  setPlannerStep(1); setActiveView('scenario');
                  setNotice(
                    'Experiment settings restored. Run the simulation to compute response.',
                  );
                }}
              /></details>
            </div>
        </main>

      </div>

      {/* 3. Global Dialogs & Modals */}
      {target && (
        <AllocationModal
          isOpen
          onClose={() => setTarget(null)}
          targetId={target.id}
          targetName={target.name}
          targetType={target.type}
          warehouses={data.warehouses}
          inventory={finalInventory}
          onConfirmAllocate={confirmAllocation}
        />
      )}

      <RouteInspectorModal
        route={route}
        isOpen={!!route}
        onClose={() => setRoute(null)}
      />

      <AIAdvisorPanel
        isOpen={isAdvisorOpen}
        onClose={() => setIsAdvisorOpen(false)}
        advisorData={response && !isDirty ? advisorData : null}
        onRefresh={fetchAdvisory}
      />

      <ReservoirPanel
        isOpen={isReservoirsOpen}
        onClose={() => setIsReservoirsOpen(false)}
      />

      <KeyboardShortcutsModal
        isOpen={isShortcutsOpen}
        onClose={() => setIsShortcutsOpen(false)}
      />

      {helpOpen && (
        <div className="dialog-backdrop" onClick={() => setHelpOpen(false)}>
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="help-title"
            className="simple-dialog"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="dialog-close"
              aria-label="Close instructions"
              onClick={() => setHelpOpen(false)}
              autoFocus
            >
              <X size={20} />
            </button>
            <span className="eyebrow">QUICK START GUIDE</span>
            <h2 id="help-title">How to use Flood Lab</h2>
            <ol className="help-steps">
              <li><strong>Choose a scenario:</strong> Select an example and set rainfall and duration. Optional custom areas and fleet controls are under Advanced settings.</li>
              <li><strong>Review and run:</strong> Check your settings, then choose Run analysis. Keep the backend running.</li>
              <li><strong>Understand results:</strong> Read the explanation and select an hour. Use Shelters & supplies for allocations, or Map & routes for detailed mapping.</li>
              <li><strong>Keep your work:</strong> Save the analysis or download a report. Rerun changed settings before allocating or exporting.</li>
            </ol>
            <p className="dialog-note">
              Chennai Flood Lab is a decision-support and scenario planning system
              designed for municipal disaster risk management and emergency response exercises.
            </p>
          </section>
        </div>
      )}
    </div>
  );
}
