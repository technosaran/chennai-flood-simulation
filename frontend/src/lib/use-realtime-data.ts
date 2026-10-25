'use client';
import { useEffect, useRef, useState } from 'react';
import type { RealtimeSnapshot } from './realtime';

const API = process.env.NEXT_PUBLIC_API_URL || '';
export function useRealtimeData() {
  const [enabled, setEnabled] = useState(false);
  const [snapshot, setSnapshot] = useState<RealtimeSnapshot | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const latest = useRef({ enabled: false, generation: 0, controller: null as AbortController | null });
  const toggle = () => {
    latest.current.controller?.abort();
    latest.current.generation += 1;
    latest.current.enabled = !latest.current.enabled;
    setEnabled(latest.current.enabled);
    setLoading(false);
    setError('');
  };
  useEffect(() => {
    const generation = ++latest.current.generation;
    let active = true;
    const controller = new AbortController();
    latest.current.controller = controller;
    let inFlight = false;
    const load = async () => {
      if (inFlight) return;
      inFlight = true;
      if (active) { setLoading(true); setError(''); }
      const timeout = window.setTimeout(() => controller.abort(), 30000);
      try {
        const response = await fetch(`${API}/api/realtime/${enabled ? 'refresh' : 'cache'}`, { method: enabled ? 'POST' : 'GET', cache: 'no-store', signal: controller.signal });
        if (!response.ok) throw new Error('Recent data unavailable. Your local simulation is still usable.');
        const body: RealtimeSnapshot = await response.json();
        if (active && generation === latest.current.generation) setSnapshot(body);
      } catch {
        if (active && generation === latest.current.generation) setError('Connection unavailable. Showing the last downloaded snapshot if available. Local simulation is still usable.');
      } finally {
        window.clearTimeout(timeout);
        inFlight = false;
        if (active && generation === latest.current.generation) setLoading(false);
      }
    };
    void load();
    const timer = enabled ? window.setInterval(() => { if (!controller.signal.aborted) void load(); else setAttempt(n => n+1); }, 300000) : null;
    return () => { active = false; controller.abort(); if (timer !== null) window.clearInterval(timer); };
  }, [enabled, attempt]);
  return { enabled, toggle, snapshot, loading, error, refresh: () => setAttempt(n => n+1) };
}
