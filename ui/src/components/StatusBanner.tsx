import React from 'react';
import { Activity } from './Icons';

interface StatusBannerProps {
  totalIncidents: number;
  openIncidents: number;
  investigatingIncidents: number;
  resolvedIncidents?: number;
  isConnected: boolean;
}

export const StatusBanner: React.FC<StatusBannerProps> = ({
  totalIncidents,
  openIncidents,
  investigatingIncidents,
  resolvedIncidents = 0,
  isConnected,
}) => {
  const getStatus = () => {
    if (openIncidents > 0 || investigatingIncidents > 0) return 'critical';
    if (totalIncidents > 0 && totalIncidents > resolvedIncidents) return 'degraded';
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
    <div className={`flex items-center justify-between p-5 px-6 rounded-xl mb-8 backdrop-blur-md border transition-all duration-200 ${config.bg} ${config.border} ${config.glow}`}>
      <div className="flex items-center gap-4">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center bg-black/20 text-white ${status === 'healthy' ? 'text-[#10B981]' : status === 'degraded' ? 'text-[#F59E0B]' : 'text-[#EF4444] animate-pulse'}`}>
          <Activity size={20} />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-[#F8FAFC] m-0 mb-1">{labels[status]}</h3>
          <p className="text-xs text-[#94A3B8] m-0 flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-[#10B981]' : 'bg-[#EF4444]'}`} />
            {isConnected ? 'Live WebSocket Connected' : 'Disconnected'} · Last updated{' '}
            {new Date().toLocaleTimeString()}
          </p>
        </div>
      </div>
      <div className="flex gap-10">
        <div className="text-right flex flex-col justify-center">
          <div className="text-[0.625rem] uppercase font-semibold tracking-widest text-[#94A3B8] mb-1">Active</div>
          <div className={`text-2xl font-bold tabular-nums leading-none ${openIncidents > 0 || investigatingIncidents > 0 ? 'text-[#EF4444]' : 'text-[#10B981]'}`}>
            {openIncidents + investigatingIncidents}
          </div>
        </div>
        <div className="text-right flex flex-col justify-center border-l border-[#1E293B] pl-10">
          <div className="text-[0.625rem] uppercase font-semibold tracking-widest text-[#94A3B8] mb-1">Resolved</div>
          <div className="text-2xl font-bold tabular-nums leading-none text-[#10B981]">{resolvedIncidents}</div>
        </div>
        <div className="text-right flex flex-col justify-center border-l border-[#1E293B] pl-10">
          <div className="text-[0.625rem] uppercase font-semibold tracking-widest text-[#94A3B8] mb-1">Total</div>
          <div className="text-2xl font-bold tabular-nums leading-none text-[#F8FAFC]">{totalIncidents}</div>
        </div>
      </div>
    </div>
  );
};
