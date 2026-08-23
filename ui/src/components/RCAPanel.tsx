import React from 'react';
import type { Incident } from '../hooks/useIncidents';
import { ConfidenceGauge } from './ConfidenceGauge';
import { YAMLViewer } from './YAMLViewer';
import { ApprovalControls } from './ApprovalControls';
import { AgentCard } from './AgentCard';
import { Shield, FileSearch, Terminal, BarChart, Cpu, Zap, CheckCircle, XCircle } from './Icons';

interface RCAPanelProps {
  incident: Incident | null;
  onRefreshNeeded: (newStatus?: 'RESOLVED' | 'REJECTED') => void;
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

  // Extract structured findings if available (from JSON strings in state)
  let logHunterData = null;
  let telemetryData = null;
  let gitopsData = null;
  try {
    if (incident.log_hunter_output) logHunterData = JSON.parse(incident.log_hunter_output as string);
    if (incident.telemetry_output) telemetryData = JSON.parse(incident.telemetry_output as string);
    if (incident.gitops_output) gitopsData = JSON.parse(incident.gitops_output as string);
  } catch (e) {
    console.error("Failed to parse structured agent outputs", e);
  }

  return (
    <div className="bg-[#111827]/50 backdrop-blur-md border border-[#1E293B] rounded-xl flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex justify-between items-start p-6 pb-4 border-b border-[#1E293B]">
        <div>
          <h2 className="text-[#F8FAFC] font-semibold text-lg m-0 mb-1">{incident.title}</h2>
          <p className="text-xs text-[#94A3B8] m-0 font-mono">ID: {incident.id}</p>
        </div>
        {confidence > 0 && <ConfidenceGauge score={confidence} />}
      </div>

      {/* Content */}
      <div className="p-8 overflow-y-auto flex-1 custom-scrollbar">

        {/* FAILED — loud error banner */}
        {isFailed && (
          <div className="p-6 rounded-lg mb-8 border-2 border-[#EF4444]/60 bg-[#EF4444]/15 text-[#EF4444] animate-fade-in shadow-[0_0_20px_rgba(239,68,68,0.15)]">
            <div className="font-bold text-base flex items-center gap-2">
              <Zap size={20} /> AI Workflow FAILED
            </div>
            <div className="text-sm opacity-90 mt-3 font-mono whitespace-pre-wrap bg-black/30 p-3 rounded-md border border-[#EF4444]/20">
              {incident.description}
            </div>
            <div className="text-xs opacity-70 mt-3 flex items-center gap-1">
              Check backend logs for the full traceback.
            </div>
          </div>
        )}

        {/* Status Alert for non-proposed terminal states */}
        {!isProposed && !isFailed && incident.status !== 'OPEN' && incident.status !== 'INVESTIGATING' && (
           <div className={`p-4 rounded-lg mb-8 border animate-fade-in flex items-center gap-4 ${
             incident.status === 'RESOLVED' ? 'border-[#10B981]/30 bg-[#10B981]/10 text-[#10B981]' : 
             incident.status === 'REJECTED' ? 'border-[#EF4444]/30 bg-[#EF4444]/10 text-[#EF4444]' : 
             'border-[#00F0FF]/30 bg-[#00F0FF]/10 text-[#00F0FF]'
           }`}>
             {incident.status === 'RESOLVED' ? <CheckCircle size={24} /> : <XCircle size={24} />}
             <div>
               <div className="font-bold tracking-wide">{incident.status}</div>
               <div className="text-sm opacity-80 mt-0.5">This incident has been {incident.status.toLowerCase()}.</div>
             </div>
           </div>
        )}

        {/* AI Agent Reasoning Pipeline */}
        {(incident.evidence_chain || incident.rca_summary || incident.agent_trace?.length) && (
          <div className="mb-8 flex flex-col gap-4 relative p-6 rounded-xl bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-[#1E293B]/20 via-transparent to-transparent border border-[#1E293B]/30 shadow-inner">
            {/* Connecting line behind cards */}
            <div className="absolute left-[3.25rem] top-8 bottom-8 w-0.5 bg-gradient-to-b from-[#334155] via-[#1E293B] to-transparent -z-10" />

            {/* Helper to find trace info for an agent */}
            {(() => {
              const getTrace = (agentName: string) => incident.agent_trace?.find(t => t.agent === agentName);
              const triageTrace = getTrace('Triage');
              const quarantineTrace = getTrace('Quarantine');
              const investigatorTrace = getTrace('Investigator');
              const logHunterTrace = getTrace('Log Hunter');
              const telemetryTrace = getTrace('Telemetry Analyst');
              const gitopsTrace = getTrace('GitOps Auditor');
              const orchestratorTrace = getTrace('Orchestrator');
              
              return (
                <>
                  {/* Triage Agent */}
                  <div className="animate-fade-in delay-100 hover:-translate-y-0.5 transition-transform duration-300">
                    <AgentCard 
                      icon={<Shield />} 
                      title="Triage Agent" 
                      accentColor="agent-triage"
                      summary={triageTrace?.summary || "Passed severity filter. Incident assigned for investigation."}
                      timestamp={triageTrace?.timestamp}
                      rawData={triageTrace?.details}
                    >
                      <div className="text-sm text-[#CBD5E1]">
                        {triageTrace?.details || "Severity critical. Triggering deep investigation."}
                      </div>
                    </AgentCard>
                  </div>

                  {/* Quarantine Agent */}
                  {quarantineTrace && (
                    <div className="animate-fade-in delay-150 hover:-translate-y-0.5 transition-transform duration-300">
                      <AgentCard 
                        icon={<Shield />} 
                        title="Pod Quarantine" 
                        accentColor="agent-quarantine"
                        summary={quarantineTrace.summary}
                        timestamp={quarantineTrace.timestamp}
                        rawData={incident.quarantine_result || quarantineTrace.details}
                      >
                        <div className="text-sm text-[#CBD5E1]">
                          {quarantineTrace.details}
                        </div>
                      </AgentCard>
                    </div>
                  )}

                  {/* Investigator Agent */}
                  {incident.evidence_chain && incident.evidence_chain.length > 0 && (
                    <div className="animate-fade-in delay-200 hover:-translate-y-0.5 transition-transform duration-300">
                      <AgentCard 
                        icon={<FileSearch />} 
                        title="Investigator" 
                        accentColor="agent-investigator"
                        summary={investigatorTrace?.summary || "Extracted logs and events for the affected resources."}
                        timestamp={investigatorTrace?.timestamp}
                        rawData={incident.evidence_chain}
                      >
                        <div className="text-sm text-[#CBD5E1]">
                          {investigatorTrace?.details || "Successfully fetched pod logs and Kubernetes events using MCP."}
                        </div>
                      </AgentCard>
                    </div>
                  )}

                  {/* Log Hunter */}
                  {logHunterData && (
                    <div className="animate-fade-in delay-300 hover:-translate-y-0.5 transition-transform duration-300">
                      <AgentCard 
                        icon={<Terminal />} 
                        title="Log Hunter" 
                        accentColor="agent-log-hunter"
                        summary={logHunterTrace?.summary || `Extracted ${logHunterData.error_class} error`}
                        timestamp={logHunterTrace?.timestamp}
                        rawData={logHunterData}
                      >
                        <div className="flex flex-col gap-3">
                          <div className="flex gap-6">
                            <div>
                              <div className="text-xs text-[#94A3B8] uppercase tracking-wider mb-1">Error Class</div>
                              <div className="text-sm font-semibold text-[#F8FAFC]">{logHunterData.error_class}</div>
                            </div>
                            <div>
                              <div className="text-xs text-[#94A3B8] uppercase tracking-wider mb-1">Frequency</div>
                              <div className="text-sm text-[#F8FAFC] capitalize">{logHunterData.frequency}</div>
                            </div>
                          </div>
                          {logHunterData.stack_trace && (
                            <div>
                              <div className="text-xs text-[#94A3B8] uppercase tracking-wider mb-1">Stack Trace Context</div>
                              <pre className="text-xs font-mono text-[#CBD5E1] bg-black/40 p-3 rounded border border-[#1E293B] overflow-x-auto shadow-inner">
                                {logHunterData.stack_trace}
                              </pre>
                            </div>
                          )}
                        </div>
                      </AgentCard>
                    </div>
                  )}

                  {/* Telemetry Analyst */}
                  {telemetryData && (
                    <div className="animate-fade-in delay-400 hover:-translate-y-0.5 transition-transform duration-300">
                      <AgentCard 
                        icon={<BarChart />} 
                        title="Telemetry Analyst" 
                        accentColor="agent-telemetry"
                        summary={telemetryTrace?.summary || `Resource status: ${telemetryData.resource_status}`}
                        timestamp={telemetryTrace?.timestamp}
                        rawData={telemetryData}
                      >
                        <div className="flex flex-col gap-3">
                          <div>
                            <div className="text-xs text-[#94A3B8] uppercase tracking-wider mb-1">Resource Status</div>
                            <div className="text-sm font-semibold text-[#F8FAFC] capitalize">
                              {telemetryData.resource_status?.replace('_', ' ')}
                            </div>
                          </div>
                          {telemetryData.anomalies && telemetryData.anomalies.length > 0 && (
                            <div>
                              <div className="text-xs text-[#94A3B8] uppercase tracking-wider mb-1">Detected Anomalies</div>
                              <ul className="list-disc list-inside text-sm text-[#CBD5E1] m-0 space-y-1">
                                {telemetryData.anomalies.map((a: string, i: number) => (
                                  <li key={i}>{a}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </AgentCard>
                    </div>
                  )}

                  {/* GitOps Auditor */}
                  {gitopsData && (
                    <div className="animate-fade-in delay-450 hover:-translate-y-0.5 transition-transform duration-300">
                      <AgentCard 
                        icon={<FileSearch />} 
                        title="GitOps Auditor" 
                        accentColor="agent-gitops"
                        summary={gitopsTrace?.summary || `Configuration drift: ${gitopsData.drift_detected}`}
                        timestamp={gitopsTrace?.timestamp}
                        rawData={gitopsData}
                      >
                        <div className="flex flex-col gap-3">
                          <div>
                            <div className="text-xs text-[#94A3B8] uppercase tracking-wider mb-1">Configuration Drift</div>
                            <div className="text-sm font-semibold text-[#F8FAFC] capitalize">
                              {gitopsData.drift_detected}
                            </div>
                          </div>
                          {gitopsData.drift_details && (
                            <div>
                              <div className="text-xs text-[#94A3B8] uppercase tracking-wider mb-1">Details</div>
                              <div className="text-sm text-[#CBD5E1] whitespace-pre-wrap bg-black/40 p-3 rounded border border-[#1E293B]">
                                {gitopsData.drift_details}
                              </div>
                            </div>
                          )}
                          {gitopsData.suspect_commits && gitopsData.suspect_commits.length > 0 && (
                            <div>
                              <div className="text-xs text-[#94A3B8] uppercase tracking-wider mb-1">Suspect Commits</div>
                              <ul className="list-disc list-inside text-sm text-[#CBD5E1] m-0 space-y-1">
                                {gitopsData.suspect_commits.map((c: string, i: number) => (
                                  <li key={i}>{c}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </AgentCard>
                    </div>
                  )}

                  {/* Supervisor (Synthesis & Patch) */}
                  {incident.rca_summary && (
                    <div className="animate-fade-in delay-500 hover:-translate-y-0.5 transition-transform duration-300">
                      <AgentCard 
                        icon={<Cpu />} 
                        title="Orchestrator Synthesis" 
                        accentColor="agent-supervisor"
                        summary={orchestratorTrace?.summary || "Synthesized findings into root cause analysis."}
                        timestamp={orchestratorTrace?.timestamp}
                        rawData={orchestratorTrace?.details}
                        defaultExpanded={true}
                      >
                        <div className="flex flex-col gap-4">
                          <div>
                            <div className="text-xs text-[#94A3B8] uppercase tracking-wider mb-2">Root Cause Analysis</div>
                            <div className="text-sm text-[#E2E8F0] leading-relaxed whitespace-pre-wrap p-5 bg-[#00F0FF]/5 rounded-xl border border-[#00F0FF]/20 shadow-[inset_0_0_20px_rgba(0,240,255,0.03)] backdrop-blur-sm">
                              {incident.rca_summary}
                            </div>
                          </div>
                          
                          {incident.proposed_patch && (
                            <div>
                              <div className="text-xs text-[#94A3B8] uppercase tracking-wider mb-2">Proposed Resolution (Kubernetes Patch)</div>
                              <YAMLViewer code={incident.proposed_patch} />
                            </div>
                          )}
                        </div>
                      </AgentCard>
                    </div>
                  )}
                </>
              );
            })()}
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

