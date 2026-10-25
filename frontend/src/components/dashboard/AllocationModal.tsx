import React, { useState, useEffect } from 'react';
import {
  WarehouseEntity,
  InventoryStatus,
  ResourceAllocateRequest,
} from '@/lib/types';
import {
  X,
  Droplets,
  Package,
  HeartPulse,
  Send,
  Warehouse,
  CheckCircle2,
} from 'lucide-react';

interface AllocationModalProps {
  isOpen: boolean;
  onClose: () => void;
  targetId: string;
  targetName: string;
  targetType: 'shelter' | 'point';
  warehouses: WarehouseEntity[];
  inventory: InventoryStatus;
  onConfirmAllocate: (request: ResourceAllocateRequest) => Promise<void>;
}

export default function AllocationModal({
  isOpen,
  onClose,
  targetId,
  targetName,
  targetType,
  warehouses,
  inventory,
  onConfirmAllocate,
}: AllocationModalProps) {
  const [selectedWarehouseId, setSelectedWarehouseId] = useState<string>(
    warehouses.length > 0 ? warehouses[0].id : '',
  );
  const [waterLitres, setWaterLitres] = useState<number>(5000);
  const [foodRations, setFoodRations] = useState<number>(2500);
  const [medicalKits, setMedicalKits] = useState<number>(50);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState('');
  useEffect(() => {
    setErrorMessage('');
    setSuccessMessage('');
  }, [isOpen, targetId]);

  // Fix #14: Close modal on Escape key press
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isSubmitting) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isSubmitting, onClose]);

  const depotStock = warehouses.find((w) => w.id === selectedWarehouseId)
    ?.supplies || { water_litres: 0, food_rations: 0, medical_kits: 0 };
  const maxWater = Math.min(
    inventory.available_water_litres,
    depotStock.water_litres,
  );
  const maxFood = Math.min(
    inventory.available_food_rations,
    depotStock.food_rations,
  );
  const maxMedical = Math.min(
    inventory.available_medical_kits,
    depotStock.medical_kits,
  );
  useEffect(() => {
    setWaterLitres((v) => Math.min(v, maxWater));
    setFoodRations((v) => Math.min(v, maxFood));
    setMedicalKits((v) => Math.min(v, maxMedical));
  }, [maxWater, maxFood, maxMedical]);
  if (!isOpen) return null;

  const handleSubmit = async () => {
    setErrorMessage('');
    setIsSubmitting(true);
    try {
      await onConfirmAllocate({
        shelter_or_point_id: targetId,
        warehouse_id: selectedWarehouseId,
        supplies: {
          water_litres: waterLitres,
          food_rations: foodRations,
          medical_kits: medicalKits,
        },
      });
      setSuccessMessage('Resources allocated successfully');
      setIsSubmitting(false);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : 'Allocation failed.',
      );
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-slate-50/80 backdrop-blur-sm animate-fade-in"
        onClick={!isSubmitting ? onClose : undefined}
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-label="Allocate simulation supplies"
        className="relative w-full max-w-lg glass-panel-strong rounded-2xl shadow-2xl animate-scale-in flex flex-col overflow-hidden border border-slate-200"
      >
        {successMessage ? (
          <div className="p-12 flex flex-col items-center justify-center animate-fade-in">
            <div className="relative">
              <div className="absolute inset-0 bg-emerald-500/20 rounded-full blur-xl animate-pulse" />
              <CheckCircle2 className="w-20 h-20 text-emerald-700 relative z-10 animate-scale-in" />
            </div>
            <h3 className="mt-6 text-xl font-medium text-slate-900">
              {successMessage}
            </h3>
            <p className="mt-2 text-sm text-slate-700">
              Recorded in the simulation inventory
            </p>
            <button
              onClick={onClose}
              className="mt-6 px-5 py-2 rounded-lg bg-cyan-700 text-slate-900"
              autoFocus
            >
              Done
            </button>
          </div>
        ) : (
          <>
            <div className="p-5 flex items-center justify-between border-b border-slate-200/50 bg-slate-50/30">
              <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                <Send className="w-5 h-5 text-cyan-700" />
                Allocate to {targetName}
              </h2>
              <button
                onClick={onClose}
                aria-label="Close allocation"
                autoFocus
                className="p-1.5 text-slate-700 hover:text-slate-900 hover:bg-slate-50 rounded-lg transition-colors"
                disabled={isSubmitting}
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-6 overflow-y-auto max-h-[70vh] custom-scrollbar">
              {errorMessage && (
                <p role="alert" className="text-sm text-red-700">
                  {errorMessage}
                </p>
              )}
              <div className="space-y-3">
                <h3 className="text-sm font-medium text-slate-700 uppercase tracking-wider flex items-center gap-2">
                  <Warehouse className="w-4 h-4" /> Source Depot
                </h3>
                <select
                  aria-label="Source depot"
                  value={selectedWarehouseId}
                  onChange={(e) => setSelectedWarehouseId(e.target.value)}
                  className="w-full bg-slate-50/80 border border-slate-200 text-slate-900 text-sm rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all"
                >
                  {warehouses.map((w) => (
                    <option key={w.id} value={w.id}>
                      {w.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-5">
                <h3 className="text-sm font-medium text-slate-700 uppercase tracking-wider">
                  Supply Quantities
                </h3>

                {/* Water Slider */}
                <div className="space-y-2 p-4 bg-slate-50/40 rounded-xl border border-slate-200/50">
                  <div className="flex justify-between items-end">
                    <label className="text-sm text-slate-700 flex items-center gap-2">
                      <Droplets className="w-4 h-4 text-cyan-700" /> Water (L)
                    </label>
                    <span className="text-lg font-mono font-medium text-cyan-700">
                      {waterLitres.toLocaleString()}
                    </span>
                  </div>
                  <input
                    type="range"
                    aria-label="Water litres"
                    min="0"
                    max={maxWater}
                    step="1"
                    value={waterLitres}
                    onChange={(e) => setWaterLitres(Number(e.target.value))}
                    className="w-full slider-cyan"
                  />
                  <div className="flex justify-between text-sm text-slate-600">
                    <span>0</span>
                    <span>Available: {maxWater.toLocaleString()} L</span>
                  </div>
                </div>

                {/* Food Slider */}
                <div className="space-y-2 p-4 bg-slate-50/40 rounded-xl border border-slate-200/50">
                  <div className="flex justify-between items-end">
                    <label className="text-sm text-slate-700 flex items-center gap-2">
                      <Package className="w-4 h-4 text-amber-800" /> Food (pkg)
                    </label>
                    <span className="text-lg font-mono font-medium text-amber-800">
                      {foodRations.toLocaleString()}
                    </span>
                  </div>
                  <input
                    type="range"
                    aria-label="Food rations"
                    min="0"
                    max={maxFood}
                    step="1"
                    value={foodRations}
                    onChange={(e) => setFoodRations(Number(e.target.value))}
                    className="w-full slider-amber"
                  />
                  <div className="flex justify-between text-sm text-slate-600">
                    <span>0</span>
                    <span>Available: {maxFood.toLocaleString()} pkg</span>
                  </div>
                </div>

                {/* Medical Slider */}
                <div className="space-y-2 p-4 bg-slate-50/40 rounded-xl border border-slate-200/50">
                  <div className="flex justify-between items-end">
                    <label className="text-sm text-slate-700 flex items-center gap-2">
                      <HeartPulse className="w-4 h-4 text-red-700" /> Medical
                      (kits)
                    </label>
                    <span className="text-lg font-mono font-medium text-red-700">
                      {medicalKits.toLocaleString()}
                    </span>
                  </div>
                  <input
                    type="range"
                    aria-label="Medical kits"
                    min="0"
                    max={maxMedical}
                    step="1"
                    value={medicalKits}
                    onChange={(e) => setMedicalKits(Number(e.target.value))}
                    className="w-full slider-red"
                  />
                  <div className="flex justify-between text-sm text-slate-600">
                    <span>0</span>
                    <span>Available: {maxMedical.toLocaleString()} kits</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="p-5 border-t border-slate-200/50 bg-slate-50/30 flex justify-end gap-3">
              <button
                onClick={onClose}
                disabled={isSubmitting}
                className="px-5 py-2.5 rounded-lg text-sm font-medium text-slate-700 border border-slate-200 hover:bg-slate-50 hover:text-slate-900 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={
                  isSubmitting ||
                  (waterLitres === 0 && foodRations === 0 && medicalKits === 0)
                }
                className="px-5 py-2.5 rounded-lg text-sm font-medium bg-cyan-600 text-slate-900  hover:bg-cyan-500 active:scale-95 transition-all disabled:opacity-50 disabled:active:scale-100 disabled:shadow-none flex items-center gap-2"
              >
                {isSubmitting ? 'Recording...' : 'Confirm Allocation'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
