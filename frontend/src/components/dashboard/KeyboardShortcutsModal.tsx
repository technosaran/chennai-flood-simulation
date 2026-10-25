'use client';

import React, { useEffect } from 'react';
import { Keyboard, X, Play, FastForward, Brain, Sliders, Map, Package, HelpCircle } from 'lucide-react';

interface KeyboardShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function KeyboardShortcutsModal({
  isOpen,
  onClose,
}: KeyboardShortcutsModalProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const shortcuts = [
    {
      category: 'Timeline & Playback',
      items: [
        {
          keys: ['Space'],
          label: 'Play / Pause simulation',
          description: 'Play or pause the current analysis timeline',
          icon: Play,
        },
        {
          keys: ['←', '→'],
          label: 'Step backward / forward',
          description: 'Jump 1 hour back or ahead in the flood scenario',
          icon: FastForward,
        },
      ],
    },
    {
      category: 'Analysis tools',
      items: [
        {
          keys: ['A'],
          label: 'Open scenario advice',
          description: 'Read advice for the current simulated scenario',
          icon: Brain,
        },
        {
          keys: ['R'],
          label: 'Review scenario',
          description: 'Open the review step before running',
          icon: Sliders,
        },
      ],
    },
    {
      category: 'Workspace Navigation',
      items: [
        {
          keys: ['1', '2', '3'],
          label: 'Navigate the planner',
          description: '1: New analysis, 2: Saved analyses, 3: Models & datasets',
          icon: Map,
        },
        {
          keys: ['Esc'],
          label: 'Close active modal / Drawing',
          description: 'Dismiss any open inspector, advisor, or drawing tool',
          icon: X,
        },
        {
          keys: ['?'],
          label: 'Toggle shortcuts cheat sheet',
          description: 'Display this keyboard reference overlay',
          icon: HelpCircle,
        },
      ],
    },
  ];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-50/80 backdrop-blur-md animate-fade-in select-none"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="shortcuts-title"
        className="relative w-full max-w-xl glass-panel-strong border border-slate-200/80 rounded-2xl shadow-2xl overflow-hidden animate-scale-in"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-slate-50/90 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl border border-cyan-200/40 bg-cyan-50/40 text-cyan-700  flex items-center justify-center">
              <Keyboard className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-mono font-bold text-slate-700 uppercase tracking-widest">
                  Quick Controls
                </span>
                <span className="text-sm font-mono px-2 py-0.5 rounded-full bg-cyan-50/60 text-cyan-700 border border-cyan-200/80">
                  HUD KEYBOARD
                </span>
              </div>
              <h3 id="shortcuts-title" className="text-base font-bold text-slate-900 mt-0.5 font-sans">
                Keyboard Shortcuts
              </h3>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 text-slate-700 hover:text-slate-900 hover:bg-slate-50 rounded-lg transition-colors"
            title="Close shortcuts modal"
            aria-label="Close shortcuts"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content list */}
        <div className="p-6 space-y-6 max-h-[75vh] overflow-y-auto custom-scrollbar">
          {shortcuts.map((section) => (
            <div key={section.category} className="space-y-3">
              <h4 className="text-sm font-mono uppercase tracking-wider text-cyan-700/90 font-semibold border-b border-slate-200/80 pb-1.5">
                {section.category}
              </h4>
              <div className="grid gap-2.5">
                {section.items.map((item) => (
                  <div
                    key={item.label}
                    className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50/50 hover:bg-slate-50/80 border border-slate-200/60 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-1.5 rounded-lg bg-slate-50 text-slate-700">
                        <item.icon className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-sm font-medium text-slate-900">
                          {item.label}
                        </div>
                        <div className="text-sm text-slate-700">
                          {item.description}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5 flex-shrink-0 ml-3">
                      {item.keys.map((k) => (
                        <kbd
                          key={k}
                          className="px-2 py-1 text-sm font-mono font-bold text-cyan-700 bg-slate-50/90 border border-slate-200 rounded shadow-sm"
                        >
                          {k}
                        </kbd>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* Pro tip banner */}
          <div className="p-3.5 rounded-xl bg-cyan-50/40 border border-cyan-200/40 flex items-start gap-2.5 text-sm text-cyan-700">
            <span className="font-bold font-mono text-cyan-700">TIP:</span>
            <span>
              Press <kbd className="px-1.5 py-0.5 text-sm font-mono bg-cyan-50/80 border border-cyan-200/60 rounded text-cyan-700">A</kbd> at any point during playback to inspect evacuation bottlenecks and trigger bilingual broadcast advisories.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
