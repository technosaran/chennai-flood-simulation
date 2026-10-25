'use client';
import { useEffect, useState, ComponentType } from 'react';
import {
  Coordinates,
  FloodZoneInput,
  TimelineStep,
  ShelterEntity,
  WarehouseEntity,
  DistributionPointEntity,
  PopulationClusterEntity,
  StagingBaseEntity,
  RouteInspectionData,
} from '@/lib/types';
export interface ChennaiMapProps {
  center: Coordinates;
  bounds: [Coordinates, Coordinates];
  shelters: ShelterEntity[];
  warehouses: WarehouseEntity[];
  distributionPoints: DistributionPointEntity[];
  populationClusters: PopulationClusterEntity[];
  stagingBases?: StagingBaseEntity[];
  currentStep: TimelineStep | null;
  showRescuePlayback?: boolean;
  definedZones: FloodZoneInput[];
  activeDrawingMode: 'none' | 'circle' | 'polygon';
  circleRadiusMeters: number;
  draftPolygonPoints: Coordinates[];
  draftCircleCenter: Coordinates | null;
  onMapClick: (coords: Coordinates) => void;
  visibleLayers: {
    flood: boolean;
    evacuation: boolean;
    supply: boolean;
    shelters: boolean;
    warehouses: boolean;
    distributionPoints: boolean;
    populationHeatmap: boolean;
  };
  onSelectShelter?: (id: string) => void;
  onSelectDistributionPoint?: (id: string) => void;
  onSelectRoute?: (route: RouteInspectionData) => void;
}
export default function MapContainer(props: ChennaiMapProps) {
  const [MapComponent, setMapComponent] =
    useState<ComponentType<ChennaiMapProps> | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    let active = true;
    // Load Leaflet after mount without a Suspense boundary recreating its container.
    import('./ChennaiMap')
      .then((module) => {
        if (active) setMapComponent(() => module.default);
      })
      .catch(() => {
        if (active) setError(true);
      });
    return () => {
      active = false;
    };
  }, []);
  return MapComponent ? (
    <MapComponent {...props} />
  ) : (
    <div className="h-full flex items-center justify-center text-sm text-slate-700">
      {error
        ? 'Unable to load the map. Reload the page to try again.'
        : 'Loading Chennai map…'}
    </div>
  );
}
