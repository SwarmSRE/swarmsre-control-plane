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

  const statusConfig = {
    healthy: {
      bg: 'bg-[#10B981]/10',
      border: 'border-[#10B981]/30',
      text: 'text-[#10B981]',
      glow: 'shadow-[0_0_15px_rgba(16,185,129,0.2)]'
    },
    degraded: {
      bg: 'bg-[#F59E0B]/10',
      border: 'border-[#F59E0B]/30',
      text: 'text-[#F59E0B]',
      glow: ''
    },
    critical: {
      bg: 'bg-[#EF4444]/10',
      border: 'border-[#EF4444]/30',
      text: 'text-[#EF4444]',
      glow: 'shadow-[0_0_15px_rgba(239,68,68,0.2)] animate-pulse'
    }
  };

  const config = statusConfig[status];

  return (
    <div className={`flex items-center justify-between p-4 px-6 rounded-xl mb-8 backdrop-blur-md border transition-all duration-200 ${config.bg} ${config.border} ${config.glow}`}>
      <div className="flex items-center gap-4">
        <div className={`w-2.5 h-2.5 rounded-full animate-pulse ${status === 'healthy' ? 'bg-[#10B981]' : status === 'degraded' ? 'bg-[#F59E0B]' : 'bg-[#EF4444]'}`} />
        <div>
          <h3 className="text-sm font-semibold text-[#F8FAFC] m-0">{labels[status]}</h3>
          <p className="text-xs text-[#94A3B8] m-0 mt-0.5">
            {isConnected ? '🟢 Live' : '🔴 Disconnected'} · Last updated{' '}
            {new Date().toLocaleTimeString()}
          </p>
        </div>
      </div>
      <div className="flex gap-8">
        <div className="text-right">
          <div className="text-[0.625rem] uppercase tracking-wider text-[#94A3B8]">Active</div>
          <div className={`text-xl font-bold tabular-nums ${openIncidents > 0 || investigatingIncidents > 0 ? 'text-[#EF4444]' : 'text-[#10B981]'}`}>
            {openIncidents + investigatingIncidents}
          </div>
        </div>
        <div className="text-right">
          <div className="text-[0.625rem] uppercase tracking-wider text-[#94A3B8]">Total</div>
          <div className="text-xl font-bold tabular-nums text-[#F8FAFC]">{totalIncidents}</div>
        </div>
      </div>
    </div>
  );
};
