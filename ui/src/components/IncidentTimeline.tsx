import React from 'react';
import type { Incident } from '../hooks/useIncidents';
import { AlertCircle, Search, Brain, CheckCircle, XCircle, Zap } from './Icons';

interface IncidentTimelineProps {
  incidents: Incident[];
  onSelect: (incident: Incident) => void;
  selectedId?: string;
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'OPEN': return <AlertCircle />;
    case 'INVESTIGATING': return <Search />;
    case 'PROPOSED': return <Brain />;
    case 'RESOLVED': return <CheckCircle />;
    case 'REJECTED': return <XCircle />;
    case 'FAILED': return <Zap />;
    default: return <AlertCircle />;
  }
};

const getStatusColorClass = (status: string) => {
  switch(status) {
    case 'OPEN': return 'border-[#60A5FA]/30 bg-[#60A5FA]/10 text-[#60A5FA]';
    case 'INVESTIGATING': return 'border-[#F59E0B]/30 bg-[#F59E0B]/10 text-[#F59E0B]';
    case 'PROPOSED': return 'border-[#00F0FF]/30 bg-[#00F0FF]/10 text-[#00F0FF]';
    case 'RESOLVED': return 'border-[#10B981]/30 bg-[#10B981]/10 text-[#10B981]';
    case 'REJECTED': 
    case 'FAILED': return 'border-[#EF4444]/30 bg-[#EF4444]/10 text-[#EF4444]';
    default: return 'border-[#94A3B8]/30 bg-[#94A3B8]/10 text-[#94A3B8]';
  }
};

function timeAgo(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = Math.floor((now - then) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export const IncidentTimeline: React.FC<IncidentTimelineProps> = ({
  incidents,
  onSelect,
  selectedId,
}) => {
  const sorted = [...incidents].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  if (sorted.length === 0) {
    return (
      <div className="bg-[#111827]/50 backdrop-blur-md border border-[#1E293B] rounded-xl flex flex-col h-full">
        <div className="p-6 pb-4 border-b border-[#1E293B]">
          <h2 className="text-[#F8FAFC] font-semibold text-lg m-0">Incident Timeline</h2>
        </div>
        <div className="flex flex-col items-center justify-center p-12 m-0 flex-1 opacity-50">
          <CheckCircle size={48} className="text-[#10B981] mb-4" />
          <p className="text-[#94A3B8] text-center m-0">
            No incidents detected. The cluster is healthy.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#111827]/50 backdrop-blur-md border border-[#1E293B] rounded-xl flex flex-col h-full overflow-hidden">
      <div className="p-6 pb-4 border-b border-[#1E293B] flex justify-between items-center bg-[#111827]/80">
        <h2 className="text-[#F8FAFC] font-semibold text-lg m-0">Incident Timeline</h2>
        <span className="text-[#94A3B8] text-xs font-medium px-2.5 py-1 rounded-full bg-[#1E293B]">
          {sorted.length} total
        </span>
      </div>
      <div className="flex flex-col gap-2 p-4 overflow-y-auto flex-1 custom-scrollbar">
        {sorted.map((incident, index) => {
          const isActive = incident.status === 'OPEN' || incident.status === 'INVESTIGATING';
          
          return (
            <div
              key={incident.id}
              className={`flex items-start gap-4 p-4 rounded-lg bg-black/20 border transition-all duration-200 cursor-pointer hover:bg-[#111827] hover:border-[#00F0FF]/40 hover:translate-x-1 animate-fade-in relative overflow-hidden ${
                selectedId === incident.id ? 'border-[#00F0FF] bg-[#00F0FF]/5' : 'border-[#1E293B]'
              }`}
              onClick={() => onSelect(incident)}
              style={{ animationDelay: `${index * 50}ms` }}
            >
              {isActive && (
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#EF4444] animate-pulse" />
              )}
              <div className={`w-10 h-10 flex items-center justify-center rounded-lg shrink-0 ${getStatusColorClass(incident.status).split(' ').slice(0, 2).join(' ')} ${getStatusColorClass(incident.status).split(' ')[2]}`}>
                {getStatusIcon(incident.status)}
              </div>
              <div className="flex-1 min-w-0 pt-0.5">
                <div className="text-sm font-semibold text-[#F8FAFC] truncate mb-1.5 leading-none">{incident.title}</div>
                <div className="text-xs text-[#94A3B8] flex items-center gap-2 mt-2">
                  <span className={`px-2 py-0.5 rounded-full text-[0.65rem] font-bold uppercase tracking-wider border ${getStatusColorClass(incident.status)}`}>
                    {incident.status}
                  </span>
                  <span>·</span>
                  <span className="truncate">{incident.source}</span>
                </div>
              </div>
              <div className="text-[0.7rem] font-medium text-[#64748B] tabular-nums whitespace-nowrap shrink-0 pt-1">
                {timeAgo(incident.created_at)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
