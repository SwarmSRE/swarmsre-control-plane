import { useState, useEffect } from 'react';
import './index.css';
import { useIncidents } from './hooks/useIncidents';
import { StatusBanner } from './components/StatusBanner';
import { IncidentTimeline } from './components/IncidentTimeline';
import { RCAPanel } from './components/RCAPanel';
import { AuditTrail } from './visualizations/AuditTrail';
import { TopologyGraph } from './visualizations/TopologyGraph';
import { LayoutDashboard, Map, List, Activity, Cpu } from './components/Icons';
import type { TopologyData } from './visualizations/topology-data';
import type { Incident } from './hooks/useIncidents';
import { ErrorBoundary } from './components/ErrorBoundary';

type Tab = 'dashboard' | 'topology' | 'audit';

function App() {
  const { incidents, loading, isConnected, getStatusCounts } = useIncidents();
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [topologyData, setTopologyData] = useState<TopologyData | null>(null);
  const [healthData, setHealthData] = useState<any>(null);
  const counts = getStatusCounts();

  // Fetch topology data when tab is selected
  useEffect(() => {
    fetch('/api/topology')
      .then(res => res.json())
      .then(data => setTopologyData(data))
      .catch(console.error);
  }, []);

  // Fetch health data for the footer
  useEffect(() => {
    fetch('/health')
      .then(res => res.json())
      .then(data => setHealthData(data))
      .catch(console.error);
  }, []);

  // Sync selectedIncident when incidents array updates from websocket
  useEffect(() => {
    if (selectedIncident) {
      const updated = incidents.find(i => i.id === selectedIncident.id);
      if (updated && updated.status !== selectedIncident.status) {
        setSelectedIncident(updated);
      }
    }
  }, [incidents]);

  return (
    <div className="flex w-full min-h-screen bg-[#0B1120] text-[#F8FAFC]">
      {/* Sidebar */}
      <aside className="w-[260px] bg-[#111827]/50 backdrop-blur-md border-r border-[#1E293B] p-6 flex flex-col fixed h-screen z-50">
        <div className="flex items-center gap-3 mb-10 pb-6 border-b border-[#1E293B]">
          <img src="/logo.png" alt="SwarmSRE Logo" className="w-8 h-8" />
          <div>
            <h1 className="text-xl font-bold text-[#00F0FF] tracking-wide">SwarmSRE</h1>
            <span className="text-[0.65rem] uppercase tracking-widest text-[#94A3B8] font-semibold">AI Control Plane</span>
          </div>
        </div>
        <nav className="flex flex-col gap-2 flex-1">
          <button
            className={`flex items-center gap-4 px-4 py-3 rounded-lg text-sm font-medium transition-colors w-full text-left ${activeTab === 'dashboard' ? 'bg-[#00F0FF]/10 text-[#00F0FF]' : 'text-[#94A3B8] hover:bg-[#111827] hover:text-[#F8FAFC]'}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <LayoutDashboard size={18} />
            Dashboard
          </button>
          <button
            className={`flex items-center gap-4 px-4 py-3 rounded-lg text-sm font-medium transition-colors w-full text-left ${activeTab === 'topology' ? 'bg-[#00F0FF]/10 text-[#00F0FF]' : 'text-[#94A3B8] hover:bg-[#111827] hover:text-[#F8FAFC]'}`}
            onClick={() => setActiveTab('topology')}
          >
            <Map size={18} />
            Topology
          </button>
          <button
            className={`flex items-center gap-4 px-4 py-3 rounded-lg text-sm font-medium transition-colors w-full text-left ${activeTab === 'audit' ? 'bg-[#00F0FF]/10 text-[#00F0FF]' : 'text-[#94A3B8] hover:bg-[#111827] hover:text-[#F8FAFC]'}`}
            onClick={() => setActiveTab('audit')}
          >
            <List size={18} />
            Audit Trail
          </button>
        </nav>
        
        <div className="mt-auto flex flex-col gap-4">
          {healthData?.llm && (
            <div className="flex flex-col gap-2 p-3 bg-black/20 rounded-lg border border-[#1E293B]">
              <div className="flex items-center gap-2 text-[0.65rem] uppercase tracking-widest text-[#94A3B8] font-semibold">
                <Cpu size={12} /> Active AI Models
              </div>
              <div className="text-xs text-[#E2E8F0] truncate">
                <span className="text-[#00F0FF] font-medium">{healthData.llm.orchestrator_provider}</span>
                <span className="text-[#64748B] mx-1">/</span>
                {healthData.llm.orchestrator_model.split('/').pop()}
              </div>
            </div>
          )}
          
          <div className="flex items-center gap-3 px-4 py-3 rounded-lg text-[#94A3B8] text-sm bg-black/20 border border-[#1E293B]">
            <Activity size={16} className={isConnected ? "text-[#10B981]" : "text-[#EF4444]"} />
            <span className="text-xs font-medium">{isConnected ? 'System Connected' : 'Disconnected'}</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-[260px] p-8 overflow-y-auto">
        <StatusBanner
          totalIncidents={counts.total}
          openIncidents={counts.open}
          investigatingIncidents={counts.investigating}
          resolvedIncidents={counts.resolved}
          isConnected={isConnected}
        />

        {activeTab === 'dashboard' && (
          <div className="grid grid-cols-2 gap-8 mb-8">
            <IncidentTimeline
              incidents={incidents}
              onSelect={setSelectedIncident}
              selectedId={selectedIncident?.id}
            />
            <RCAPanel 
              incident={selectedIncident} 
              onRefreshNeeded={(newStatus) => {
                if (selectedIncident && newStatus) {
                  setSelectedIncident({ ...selectedIncident, status: newStatus });
                }
              }} 
            />
          </div>
        )}

        {activeTab === 'topology' && (
          <div className="bg-[#111827]/50 backdrop-blur-md border border-[#1E293B] rounded-xl p-6 h-[calc(100vh-180px)] flex flex-col">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-base font-semibold text-[#F8FAFC]">Service Topology</h2>
            </div>
            <div className="flex-1 relative">
              <ErrorBoundary>
                {topologyData ? (
                  <TopologyGraph data={topologyData} />
                ) : (
                  <div className="flex justify-center items-center h-full text-[#94A3B8]">
                    Loading topology...
                  </div>
                )}
              </ErrorBoundary>
            </div>
          </div>
        )}

        {activeTab === 'audit' && (
          <div className="bg-[#111827]/50 backdrop-blur-md border border-[#1E293B] rounded-xl p-6 h-[calc(100vh-180px)] flex flex-col">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-base font-semibold text-[#F8FAFC]">Audit Trail</h2>
            </div>
            <div className="flex-1 overflow-y-auto custom-scrollbar">
              <ErrorBoundary>
                <AuditTrail />
              </ErrorBoundary>
            </div>
          </div>
        )}

        {loading && (
          <div className="text-center p-12 text-[#94A3B8]">
            Loading incidents...
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
