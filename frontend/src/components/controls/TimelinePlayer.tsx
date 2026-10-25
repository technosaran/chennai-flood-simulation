'use client';
import { Play, Pause, SkipBack, SkipForward, Clock } from 'lucide-react';
interface Props {
  totalSteps: number;
  currentStepIndex: number;
  onStepChange: (index: number) => void;
  isPlaying: boolean;
  onTogglePlay: () => void;
  playbackSpeed: number;
  onSpeedChange: (speed: number) => void;
  stepDescription?: string;
}
export default function TimelinePlayer({
  totalSteps,
  currentStepIndex,
  onStepChange,
  isPlaying,
  onTogglePlay,
  playbackSpeed,
  onSpeedChange,
  stepDescription,
}: Props) {
  return (
    <div className="glass-panel timeline-player">
      <div className="timeline-heading">
        <span>
          <Clock size={15} />
          Scenario timeline
        </span>
        <div>
          <button
            aria-pressed={playbackSpeed === 1}
            onClick={() => onSpeedChange(1)}
          >
            1×
          </button>
          <button
            aria-pressed={playbackSpeed === 2}
            onClick={() => onSpeedChange(2)}
          >
            2×
          </button>
          <strong>
            T+{currentStepIndex}h <small>/ {totalSteps - 1}h</small>
          </strong>
        </div>
      </div>
      <div className="timeline-controls">
        <button
          title="Previous step"
          aria-label="Previous step"
          onClick={() => onStepChange(Math.max(0, currentStepIndex - 1))}
          disabled={currentStepIndex === 0}
        >
          <SkipBack size={17} />
        </button>
        <button
          className="play-button"
          title={isPlaying ? 'Pause simulation' : 'Play simulation'}
          aria-label={isPlaying ? 'Pause simulation' : 'Play simulation'}
          onClick={onTogglePlay}
        >
          {isPlaying ? <Pause size={19} /> : <Play size={19} />}
        </button>
        <button
          title="Next step"
          aria-label="Next step"
          onClick={() =>
            onStepChange(Math.min(totalSteps - 1, currentStepIndex + 1))
          }
          disabled={currentStepIndex >= totalSteps - 1}
        >
          <SkipForward size={17} />
        </button>
        <div className="timeline-scrubber">
          <input
            aria-label="Simulation hour"
            type="range"
            min={0}
            max={totalSteps - 1}
            step={1}
            value={currentStepIndex}
            onChange={(e) => onStepChange(Number(e.target.value))}
            className="slider-cyan"
          />
          <div>
            {Array.from({ length: totalSteps }, (_, i) => (
              <button
                key={i}
                aria-label={`Go to hour ${i}`}
                aria-pressed={i === currentStepIndex}
                onClick={() => onStepChange(i)}
              >
                {i}
              </button>
            ))}
          </div>
        </div>
      </div>
      <p className="timeline-description">{stepDescription}</p>
    </div>
  );
}
