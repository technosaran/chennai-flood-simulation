'use client';

import React from 'react';
import {
  DisasterParameters,
  PresetScenario,
  FloodZoneInput,
  Coordinates,
} from '@/lib/types';
import { HISTORICAL_PRESETS } from '@/lib/constants';
import {
  CloudRain,
  Waves,
  Wind,
  Layers,
  CircleDot,
  PenTool,
  Play,
  RotateCcw,
  CheckCircle2,
  Undo2,
  History,
} from 'lucide-react';

interface DisasterControlsProps {
  parameters: DisasterParameters;
  onParametersChange: (params: DisasterParameters) => void;
  activeDrawingMode: 'none' | 'circle' | 'polygon';
  setActiveDrawingMode: (mode: 'none' | 'circle' | 'polygon') => void;
  circleRadiusMeters: number;
  setCircleRadiusMeters: (radius: number) => void;
  draftPolygonPoints: Coordinates[];
  onFinishPolygon: () => void;
  onClearDrawing: () => void;
  onUndoLastPoint: () => void;
  activePresetId: string | null;
  onSelectPreset: (preset: PresetScenario) => void;
  onRunSimulation: () => void;
  isSimulating: boolean;
  definedZonesCount: number;
  advancedOnly?: boolean;
}

export default function DisasterControls({
  parameters,
  onParametersChange,
  activeDrawingMode,
  setActiveDrawingMode,
  circleRadiusMeters,
  setCircleRadiusMeters,
  draftPolygonPoints,
  onFinishPolygon,
  onClearDrawing,
  onUndoLastPoint,
  activePresetId,
  onSelectPreset,
  onRunSimulation,
  isSimulating,
  definedZonesCount,
  advancedOnly = false,
}: DisasterControlsProps) {
  const intensityLabels: Record<number, string> = {
    1: 'Advisory (25 mm/h)',
    2: 'Moderate (50 mm/h)',
    3: 'Heavy (90 mm/h)',
    4: 'Very Heavy (140 mm/h)',
    5: 'Catastrophic (220+ mm/h)',
  };

  return (
    <div className="glass-panel animate-slide-right flex flex-col gap-5 p-4 rounded-xl text-slate-900  overflow-y-auto custom-scrollbar">
      {!advancedOnly && <div className="space-y-2">
        <label htmlFor="scenario-preset" className="text-sm font-medium text-slate-700">Scenario preset</label>
        <select id="scenario-preset" value={activePresetId || ''} disabled={isSimulating} onChange={event => { const preset = HISTORICAL_PRESETS.find(item => item.id === event.target.value); if (preset) onSelectPreset(preset); }} className="w-full rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm text-slate-900">
          <option value="" disabled>Custom scenario</option>
          {HISTORICAL_PRESETS.map(preset => <option key={preset.id} value={preset.id}>{preset.name}</option>)}
        </select>
      </div>

      }
      {/* 2. Custom flood zone (Drawing & Circle) */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 border-b border-slate-200/50 pb-1.5">
          <PenTool className="w-4 h-4 text-cyan-700" />
          <h3 className="text-sm font-semibold text-slate-700">
            Custom flood zone
          </h3>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {/* Circle Mode Button */}
          <button
            onClick={() =>
              setActiveDrawingMode(
                activeDrawingMode === 'circle' ? 'none' : 'circle',
              )
            }
            className={`flex items-center justify-center gap-2 py-2 px-3 rounded-lg border text-sm font-medium transition-all  ${
              activeDrawingMode === 'circle'
                ? 'bg-cyan-500 text-slate-600 font-bold border-cyan-400 '
                : 'bg-slate-50/80 hover:bg-slate-100 text-slate-700 border-slate-200'
            }`}
          >
            <CircleDot className="w-4 h-4" />
            {activeDrawingMode === 'circle'
              ? 'Click Map for Epicenter'
              : 'Circle Radius'}
          </button>

          {/* Polygon Mode Button */}
          <button
            onClick={() =>
              setActiveDrawingMode(
                activeDrawingMode === 'polygon' ? 'none' : 'polygon',
              )
            }
            className={`flex items-center justify-center gap-2 py-2 px-3 rounded-lg border text-sm font-medium transition-all  ${
              activeDrawingMode === 'polygon'
                ? 'bg-cyan-500 text-slate-600 font-bold border-cyan-400 '
                : 'bg-slate-50/80 hover:bg-slate-100 text-slate-700 border-slate-200'
            }`}
          >
            <PenTool className="w-4 h-4" />
            {activeDrawingMode === 'polygon'
              ? `Points (${draftPolygonPoints.length})`
              : 'Draw Polygon'}
          </button>
        </div>

        {/* Dynamic Controls depending on drawing mode */}
        {activeDrawingMode === 'circle' && (
          <div className="bg-slate-50/50 p-3 rounded-lg border border-cyan-200/30 space-y-2 animate-slide-down ">
            <div className="flex justify-between text-sm">
              <span className="text-slate-700">Epicenter Radius:</span>
              <span className="font-mono font-bold text-cyan-700">
                {(circleRadiusMeters / 1000).toFixed(1)} km (
                {circleRadiusMeters} m)
              </span>
            </div>
            <input
              type="range"
              aria-label="Circle radius"
              min={500}
              max={5000}
              step={100}
              value={circleRadiusMeters}
              onChange={(e) => setCircleRadiusMeters(Number(e.target.value))}
              className="w-full slider-cyan cursor-pointer"
            />
            <p className="text-sm text-cyan-700/80 italic">
              * Click anywhere on the Chennai map to place the flood circle
              epicenter.
            </p>
          </div>
        )}

        {activeDrawingMode === 'polygon' && (
          <div className="bg-slate-50/50 p-3 rounded-lg border border-cyan-200/30 space-y-3 animate-slide-down ">
            <p className="text-sm text-slate-700">
              Click consecutive points on the map to define the polygon boundary
              perimeter.
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={onFinishPolygon}
                disabled={draftPolygonPoints.length < 3}
                className="flex-1 py-1.5 px-3 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed text-slate-900 text-sm font-semibold rounded-lg flex items-center justify-center gap-1.5 transition-colors"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                Finish ({draftPolygonPoints.length} pts)
              </button>
              <button
                onClick={onUndoLastPoint}
                disabled={draftPolygonPoints.length === 0}
                className="py-1.5 px-3 bg-amber-700 hover:bg-amber-600 disabled:opacity-40 disabled:cursor-not-allowed text-slate-900 text-sm rounded-lg flex items-center justify-center gap-1.5 transition-colors"
                title="Undo last placed point"
              >
                <Undo2 className="w-3.5 h-3.5" />
                Undo
              </button>
              <button
                onClick={onClearDrawing}
                className="py-1.5 px-3 bg-slate-100 hover:bg-slate-100 text-slate-700 text-sm rounded-lg flex items-center justify-center gap-1.5 transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Clear
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 3. Disaster Parameter Controls */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 border-b border-slate-200/50 pb-1.5">
          <CloudRain className="w-4 h-4 text-blue-700" />
          <h3 className="text-sm font-semibold text-slate-700">
            Disaster Parameters
          </h3>
        </div>

        {!advancedOnly && <>
        {/* Rainfall Intensity Slider (1 - 5) */}
        <div className="space-y-2">
          <div className="flex justify-between items-center text-sm">
            <span className="text-slate-700">Rainfall Intensity</span>
            <span className="font-mono font-bold text-blue-700">
              {intensityLabels[parameters.rainfall_intensity_mm_hr] ||
                `Level ${parameters.rainfall_intensity_mm_hr}`}
            </span>
          </div>
          <input
            type="range"
            aria-label="Rainfall intensity"
            min={1}
            max={5}
            step={1}
            value={parameters.rainfall_intensity_mm_hr}
            onChange={(e) =>
              onParametersChange({
                ...parameters,
                rainfall_intensity_mm_hr: Number(e.target.value),
                rainfall_input_unit: 'legacy_level',
              })
            }
            className="w-full slider-blue cursor-pointer"
          />
          <div className="flex justify-between px-1">
            {[1, 2, 3, 4, 5].map((val) => (
              <div
                key={val}
                className={`w-1.5 h-1.5 rounded-full ${
                  parameters.rainfall_intensity_mm_hr >= val
                    ? 'bg-blue-400 '
                    : 'bg-slate-100'
                }`}
              />
            ))}
          </div>
          <div className="flex justify-between text-[9px] text-slate-600 font-mono">
            <span>25 mm/h</span>
            <span>90 mm/h</span>
            <span>220 mm/h</span>
          </div>
        </div>

        </>}
        {/* Flood Depth Slider (0.1m - 3.0m) */}
        <div className="space-y-2">
          <div className="flex justify-between items-center text-sm">
            <span className="text-slate-700 flex items-center gap-1.5">
              <Waves className="w-3.5 h-3.5 text-cyan-700" />
              Peak water depth
            </span>
            <span className="font-mono font-bold text-cyan-700">
              {parameters.flood_depth_meters.toFixed(1)} m
            </span>
          </div>
          <input
            type="range"
            aria-label="Peak flood depth"
            min={0.1}
            max={3.0}
            step={0.1}
            value={parameters.flood_depth_meters}
            onChange={(e) =>
              onParametersChange({
                ...parameters,
                flood_depth_meters: Number(e.target.value),
              })
            }
            className="w-full slider-cyan cursor-pointer"
          />
        </div>

        {/* Spread Rate Slider (50m/hr - 500m/hr) */}
        <div className="space-y-2">
          <div className="flex justify-between items-center text-sm">
            <span className="text-slate-700 flex items-center gap-1.5">
              <Wind className="w-3.5 h-3.5 text-amber-800" />
              Spread rate
            </span>
            <span className="font-mono font-bold text-amber-800">
              {parameters.spread_rate_meters_hr} m/h
            </span>
          </div>
          <input
            type="range"
            aria-label="Flood spread rate"
            min={50}
            max={500}
            step={10}
            value={parameters.spread_rate_meters_hr}
            onChange={(e) =>
              onParametersChange({
                ...parameters,
                spread_rate_meters_hr: Number(e.target.value),
              })
            }
            className="w-full slider-amber cursor-pointer"
          />
        </div>
      </div>

      {!advancedOnly && <div className="space-y-2">
        <label
          htmlFor="duration"
          className="text-sm text-slate-700 flex justify-between"
        >
          Simulation duration{' '}
          <span className="text-cyan-700">
            {parameters.duration_hours} hours
          </span>
        </label>
        <input
          id="duration"
          aria-label="Simulation duration"
          type="range"
          min={1}
          max={12}
          step={1}
          value={parameters.duration_hours}
          onChange={(e) =>
            onParametersChange({
              ...parameters,
              duration_hours: Number(e.target.value),
            })
          }
          className="slider-cyan"
        />
      </div>}
    </div>
  );
}
