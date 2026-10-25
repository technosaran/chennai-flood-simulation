'use client';

import React from 'react';
import {
  Layers,
  Waves,
  Footprints,
  Truck,
  Warehouse,
  Tent,
  Flame,
} from 'lucide-react';

interface LayerToggleProps {
  layers: {
    flood: boolean;
    evacuation: boolean;
    supply: boolean;
    shelters: boolean;
    warehouses: boolean;
    distributionPoints: boolean;
    populationHeatmap: boolean;
  };
  onToggleLayer: (layerName: keyof LayerToggleProps['layers']) => void;
}

export default function LayerToggle({
  layers,
  onToggleLayer,
}: LayerToggleProps) {
  const layerDefs: {
    key: keyof LayerToggleProps['layers'];
    label: string;
    icon: React.ReactNode;
    colorClass: string;
    dotClass: string;
    glowClass: string;
  }[] = [
    {
      key: 'flood',
      label: 'Flood',
      icon: <Waves className="w-3.5 h-3.5" />,
      colorClass: 'text-cyan-700',
      dotClass: 'bg-cyan-400',
      glowClass: '',
    },
    {
      key: 'evacuation',
      label: 'Evacuation & rescue',
      icon: <Footprints className="w-3.5 h-3.5" />,
      colorClass: 'text-emerald-700',
      dotClass: 'bg-emerald-400',
      glowClass: 'shadow-glow-emerald',
    },
    {
      key: 'supply',
      label: 'Supply',
      icon: <Truck className="w-3.5 h-3.5" />,
      colorClass: 'text-orange-400',
      dotClass: 'bg-orange-400',
      glowClass: 'shadow-glow-orange',
    },
    {
      key: 'shelters',
      label: 'Shelters',
      icon: <Warehouse className="w-3.5 h-3.5" />,
      colorClass: 'text-blue-700',
      dotClass: 'bg-blue-400',
      glowClass: 'shadow-glow-blue',
    },
    {
      key: 'warehouses',
      label: 'Depots',
      icon: <Warehouse className="w-3.5 h-3.5" />,
      colorClass: 'text-indigo-400',
      dotClass: 'bg-indigo-400',
      glowClass: 'shadow-glow-indigo',
    },
    {
      key: 'distributionPoints',
      label: 'Relief points',
      icon: <Tent className="w-3.5 h-3.5" />,
      colorClass: 'text-amber-800',
      dotClass: 'bg-amber-400',
      glowClass: 'shadow-glow-amber',
    },
    {
      key: 'populationHeatmap',
      label: 'Population',
      icon: <Flame className="w-3.5 h-3.5" />,
      colorClass: 'text-red-700',
      dotClass: 'bg-red-400',
      glowClass: 'shadow-glow-red',
    },
  ];

  return (
    <details className="glass-panel p-2.5 rounded-xl shadow-xl">
      <summary className="flex items-center gap-1.5 text-sm font-medium text-slate-700 px-1 cursor-pointer">
        <Layers className="w-3 h-3 text-cyan-700" />
        Map Layers
      </summary>
      <div className="flex flex-wrap gap-2 max-w-[300px] mt-3">
        {layerDefs.map((l) => {
          const isActive = layers[l.key];
          return (
            <button
              key={l.key}
              onClick={() => onToggleLayer(l.key)}
              aria-pressed={isActive}
              className={`group flex items-center gap-2 py-1.5 px-3 rounded-full text-sm font-medium border transition-all duration-300 ${
                isActive
                  ? 'bg-slate-50 text-slate-900 border-slate-200 shadow-md'
                  : 'bg-slate-50/40 text-slate-600 border-slate-200 hover:bg-slate-50/60'
              }`}
            >
              {/* Colored Dot Toggle indicator */}
              <div
                className={`w-2 h-2 rounded-full transition-all duration-300 ${
                  isActive ? `${l.dotClass} ${l.glowClass}` : 'bg-slate-100'
                }`}
              />
              <div
                className={`transition-colors ${isActive ? l.colorClass : 'text-slate-600 group-hover:text-slate-700'}`}
              >
                {l.icon}
              </div>
              <span className="text-sm whitespace-nowrap">{l.label}</span>
            </button>
          );
        })}
      </div>
    </details>
  );
}
