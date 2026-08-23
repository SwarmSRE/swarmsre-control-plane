import React, { useState } from 'react';
import { ChevronRight, ChevronDown } from './Icons';

interface AgentCardProps {
  icon: React.ReactNode;
  title: string;
  accentColor: string;
  status?: 'pending' | 'running' | 'complete' | 'error';
  summary?: string;
  timestamp?: string;
  rawData?: any;
  children: React.ReactNode;
  defaultExpanded?: boolean;
}

export const AgentCard: React.FC<AgentCardProps> = ({
  icon,
  title,
  accentColor,
  status = 'complete',
  summary,
  timestamp,
  rawData,
  children,
  defaultExpanded = false,
}) => {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const [showRaw, setShowRaw] = useState(false);

  // Format timestamp nicely
  const timeStr = timestamp ? new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '';

  return (
    <div 
      className="bg-black/30 border border-[#1E293B] rounded-lg overflow-hidden animate-fade-in transition-all duration-200 hover:border-[#334155]"
      style={{ borderLeft: `3px solid var(--${accentColor})` }}
    >
      <div 
        className="flex items-center justify-between p-3 cursor-pointer bg-black/20 hover:bg-black/40 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3 overflow-hidden">
          <div style={{ color: `var(--${accentColor})`, flexShrink: 0 }}>
            {icon}
          </div>
          <div className="flex flex-col overflow-hidden">
            <h4 className="font-semibold text-[#E2E8F0] m-0 text-sm tracking-wide">
              {title}
            </h4>
            {summary && !expanded && (
              <span className="text-xs text-[#94A3B8] truncate mt-0.5">{summary}</span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3 text-[#94A3B8] ml-2 flex-shrink-0">
          {timeStr && <span className="text-xs opacity-60 font-mono hidden sm:inline-block">{timeStr}</span>}
          {status === 'running' && (
            <div className="flex items-center gap-2 text-xs text-[#00F0FF] animate-pulse">
              <div className="w-1.5 h-1.5 bg-[#00F0FF] rounded-full" />
              Running...
            </div>
          )}
          {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </div>
      </div>
      
      {expanded && (
        <div className="p-4 border-t border-[#1E293B]/50 bg-black/10">
          {children}
          
          {rawData && (
            <div className="mt-4 pt-3 border-t border-[#1E293B]/50">
              <button 
                onClick={(e) => { e.stopPropagation(); setShowRaw(!showRaw); }}
                className="text-xs text-[#94A3B8] hover:text-[#E2E8F0] transition-colors flex items-center gap-1"
              >
                {showRaw ? 'Hide Raw Evidence' : 'Show Raw Evidence'}
              </button>
              
              {showRaw && (
                <pre className="mt-2 p-3 text-xs font-mono text-[#CBD5E1] bg-black/60 rounded overflow-x-auto border border-[#1E293B] max-h-60 overflow-y-auto custom-scrollbar">
                  {typeof rawData === 'string' ? rawData : JSON.stringify(rawData, null, 2)}
                </pre>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
