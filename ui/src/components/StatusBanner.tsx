import React from 'react';

interface StatusBannerProps {
  totalIncidents: number;
  openIncidents: number;
  investigatingIncidents: number;
  isConnected: boolean;
}

export const StatusBanner: React.FC<StatusBannerProps> = ({
  totalIncidents,
  openIncidents,
  investigatingIncidents,
  isConnected,
}) => {
  const getStatus = () => {
    if (openIncidents > 0 || investigatingIncidents > 0) return 'critical';
    if (totalIncidents > 0) return 'degraded';
    return 'healthy';
  };

  const status = getStatus();
  const labels: Record<string, string> = {
    healthy: 'All Systems Operational',
    degraded: 'Minor Issues Detected',
    critical: 'Active Incidents Detected',
  };

  return (
    <div className={`status-banner ${status} animate-fade-in`} id="status-banner">
      <div className="status-info">
        <div className="status-dot" />
        <div>
          <h3>{labels[status]}</h3>
          <p>
            {isConnected ? '🟢 Live' : '🔴 Disconnected'} · Last updated{' '}
            {new Date().toLocaleTimeString()}
          </p>
        </div>
      </div>
      <div className="status-metrics">
        <div className="status-metric">
          <div className="label">Active</div>
          <div className="value" style={{ color: openIncidents > 0 ? 'var(--status-red)' : 'var(--status-green)' }}>
            {openIncidents + investigatingIncidents}
          </div>
        </div>
        <div className="status-metric">
          <div className="label">Total</div>
          <div className="value">{totalIncidents}</div>
        </div>
      </div>
    </div>
  );
};
