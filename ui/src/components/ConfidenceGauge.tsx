import React from 'react';

interface ConfidenceGaugeProps {
  score: number;
}

export const ConfidenceGauge: React.FC<ConfidenceGaugeProps> = ({ score }) => {
  const radius = 28;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  let colorVar = 'var(--status-green)';
  if (score < 0.5) colorVar = 'var(--status-red)';
  else if (score < 0.8) colorVar = 'var(--status-yellow)';

  // We assume score is 0-1 (e.g., 0.85) from the API, so we multiply by 100.
  const displayScore = Math.round(score * 100);

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
      <div style={{ position: 'relative', width: '64px', height: '64px' }}>
        <svg style={{ width: '100%', height: '100%', transform: 'rotate(-90deg)' }} viewBox="0 0 80 80">
          <circle
            cx="40"
            cy="40"
            r={radius}
            stroke="var(--border-subtle)"
            strokeWidth="8"
            fill="transparent"
          />
          <circle
            cx="40"
            cy="40"
            r={radius}
            stroke={colorVar}
            strokeWidth="8"
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            style={{ transition: 'stroke-dashoffset 1s ease-out' }}
          />
        </svg>
        <div style={{
          position: 'absolute', top: 0, left: 0, width: '100%', height: '100%',
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
          <span style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {displayScore}%
          </span>
        </div>
      </div>
      <div>
        <h4 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>AI Confidence</h4>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: 0 }}>Supervisor Model</p>
      </div>
    </div>
  );
};
