'use client';

import { Droplets, Package, HeartPulse } from 'lucide-react';
import type { InventoryStatus, ShelterEntity, DistributionPointEntity, ShelterAllocation } from '@/lib/types';

interface ResourcePanelProps {
  inventory: InventoryStatus;
  shelters: ShelterEntity[];
  distributionPoints: DistributionPointEntity[];
  shelterAllocations: ShelterAllocation[];
  onOpenAllocateModal: (id: string, type: 'shelter' | 'point') => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  allocationDisabled?: boolean;
}

export default function ResourcePanel({ inventory, distributionPoints, onOpenAllocateModal, allocationDisabled = false }: ResourcePanelProps) {
  const stock = [
    { name: 'Drinking water', unit: 'litres', available: inventory.available_water_litres, allocated: inventory.allocated_water_litres, icon: Droplets },
    { name: 'Food', unit: 'rations', available: inventory.available_food_rations, allocated: inventory.allocated_food_rations, icon: Package },
    { name: 'Medical supplies', unit: 'kits', available: inventory.available_medical_kits, allocated: inventory.allocated_medical_kits, icon: HeartPulse },
  ];
  return <div className="space-y-5">
    <p className="text-sm text-slate-600">Available depot stock and cumulative allocations through the selected hour.</p>
    <dl className="space-y-3">{stock.map(item => <div key={item.name} className="rounded-xl border border-slate-200 bg-white p-4"><dt className="flex items-center gap-2 text-sm font-medium text-slate-700"><item.icon size={17} />{item.name}</dt><dd className="text-2xl font-semibold text-slate-900 mt-2">{item.available.toLocaleString()} <small className="text-sm font-normal">{item.unit} available</small></dd><p className="text-sm text-slate-600 mt-1">{item.allocated.toLocaleString()} allocated so far</p></div>)}</dl>
    <details className="border-t border-slate-200 pt-4"><summary className="cursor-pointer font-semibold text-sm">Distribution points ({distributionPoints.length})</summary><p className="text-sm text-slate-600 my-3">Manual allocations use the final-hour inventory. Open a point to choose a depot and quantities.</p><div className="space-y-3">{distributionPoints.map(point => <article key={point.id} className="rounded-lg border border-slate-200 p-3"><h3 className="font-semibold text-sm">{point.name}</h3><p className="text-sm text-slate-600 mt-1">{point.target_ward}</p><button className="planner-secondary mt-3" disabled={allocationDisabled} onClick={() => onOpenAllocateModal(point.id, 'point')}>Allocate supplies</button></article>)}</div></details>
    {allocationDisabled && <p className="text-sm text-slate-600">Allocations require a completed, current, editable analysis.</p>}
  </div>;
}
