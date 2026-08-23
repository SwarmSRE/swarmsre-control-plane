import React from 'react';
import type { Incident } from '../hooks/useIncidents';
import { ConfidenceGauge } from './ConfidenceGauge';
import { YAMLViewer } from './YAMLViewer';
import { ApprovalControls } from './ApprovalControls';

interface RCAPanelProps {
  incident: Incident | null;
  onRefreshNeeded: () => void;
}

export const RCAPanel: React.FC<RCAPanelProps> = ({ incident, onRefreshNeeded }) => {
  if (!incident) {
    return (
      <div className="bg-[#111827]/50 backdrop-blur-md border border-[#1E293B] rounded-xl p-6 flex items-center justify-center min-h-[400px]">
        <div className="text-center text-[#94A3B8]">
          <p>Select an incident to view RCA</p>
        </div>
      </div>
    );
  }

  const isProposed = incident.status === 'PROPOSED';
  const isFailed = incident.status === 'FAILED';
  const confidence = incident.confidence_score ?? 0;

  return (
    <div className="bg-[#111827]/50 backdrop-blur-md border border-[#1E293B] rounded-xl flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex justify-between items-start p-6 pb-4 border-b border-[#1E293B]">
        <div>
          <h2 className="text-[#F8FAFC] font-semibold text-lg m-0 mb-1">{incident.title}</h2>
          <p className="text-xs text-[#94A3B8] m-0">ID: <span className="font-mono">{incident.id}</span></p>
        </div>
        {confidence > 0 && <ConfidenceGauge score={confidence} />}
      </div>

      {/* Content */}
      <div className="p-8 overflow-y-auto flex-1 custom-scrollbar">

        {/* FAILED — loud error banner */}
        {isFailed && (
          <div className="p-6 rounded-lg mb-8 border-2 border-[#EF4444]/60 bg-[#EF4444]/15 text-[#EF4444]">
            <div className="font-bold text-base flex items-center gap-2">
              💥 AI Workflow FAILED
            </div>
            <div className="text-sm opacity-90 mt-2 font-mono whitespace-pre-wrap">
              {incident.description}
            </div>
            <div className="text-xs opacity-70 mt-1">
              Check backend logs for the full traceback.
            </div>
          </div>
        )}

        {/* Status Alert for non-proposed terminal states */}
        {!isProposed && !isFailed && incident.status !== 'OPEN' && incident.status !== 'INVESTIGATING' && (
           <div className={`p-4 rounded-lg mb-8 border ${
             incident.status === 'RESOLVED' ? 'border-[#10B981]/30 bg-[#10B981]/10 text-[#10B981]' : 
             incident.status === 'REJECTED' ? 'border-[#EF4444]/30 bg-[#EF4444]/10 text-[#EF4444]' : 
             'border-[#00F0FF]/30 bg-[#00F0FF]/10 text-[#00F0FF]'
           }`}>
             <div className="font-semibold">{incident.status}</div>
             <div className="text-sm opacity-80 mt-1">This incident has been {incident.status.toLowerCase()}.</div>
           </div>
        )}

        {/* Agent Trace */}
        {incident.evidence_chain && incident.evidence_chain.some(e => e.message) && (
          <div className="mb-8">
            <h3 className="text-base font-semibold text-[#F8FAFC] mb-2 flex items-center gap-1">
              <span className="text-[#F59E0B]">🤖</span> Agent Trace
            </h3>
            <div className="bg-black/20 p-4 rounded-lg border border-[#1E293B] flex flex-col gap-2">
              {incident.evidence_chain
                .filter(e => typeof e.message === 'string')
                .map((e, idx) => (
                  <div key={idx} className="text-sm flex items-start gap-2">
                    <span className="text-[#94A3B8] shrink-0 mt-0.5">❯</span>
                    <span className="text-[#E2E8F0] font-mono leading-relaxed break-words">{e.message as string}</span>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Synthesis Details */}
        {incident.rca_summary && (
          <div className="mb-8">
            <h3 className="text-base font-semibold text-[#F8FAFC] mb-2 flex items-center gap-1">
              <span className="text-[#00F0FF]">🧠</span> Root Cause Analysis
            </h3>
            <div className="bg-black/20 p-4 rounded-lg border border-[#1E293B] text-sm text-[#94A3B8] leading-relaxed whitespace-pre-wrap">
              {incident.rca_summary}
            </div>
          </div>
        )}

        {incident.proposed_patch && (
          <div className="mb-8">
            <h3 className="text-base font-semibold text-[#F8FAFC] mb-2 flex items-center gap-1">
              <span className="text-[#10B981]">🛠️</span> Proposed Patch
            </h3>
            <YAMLViewer code={incident.proposed_patch} />
          </div>
        )}

        {/* Action Controls */}
        {isProposed && (
          <ApprovalControls incidentId={incident.id} onActionComplete={onRefreshNeeded} />
        )}
      </div>
    </div>
  );
};
