import { useState, useEffect } from 'react';
import './index.css';
import { useIncidents } from './hooks/useIncidents';
import { StatusBanner } from './components/StatusBanner';
import { IncidentTimeline } from './components/IncidentTimeline';
import { RCAPanel } from './components/RCAPanel';
import { AuditTrail } from './visualizations/AuditTrail';
import { TopologyGraph } from './visualizations/TopologyGraph';
import type { TopologyData } from './visualizations/topology-data';
import type { Incident } from './hooks/useIncidents';

type Tab = 'dashboard' | 'topology' | 'audit';

function App() {
  const { incidents, loading, isConnected, getStatusCounts } = useIncidents();
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [topologyData, setTopologyData] = useState<TopologyData | null>(null);
  const counts = getStatusCounts();

  // Fetch topology data when tab is selected
  useEffect(() => {
    fetch('/api/topology')
      .then(res => res.json())
      .then(data => setTopologyData(data))
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
            <h1 className="text-xl font-bold text-[#00F0FF]">SwarmSRE</h1>
            <span className="text-xs text-[#94A3B8]">AI Control Plane</span>
          </div>
        </div>
        <nav className="flex flex-col gap-2 flex-1">
          <button
            className={`flex items-center gap-4 px-4 py-3 rounded-lg text-sm font-medium transition-colors w-full text-left ${activeTab === 'dashboard' ? 'bg-[#00F0FF]/10 text-[#00F0FF]' : 'text-[#94A3B8] hover:bg-[#111827] hover:text-[#F8FAFC]'}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <span className="text-lg w-6 text-center">📊</span>
            Dashboard
          </button>
          <button
            className={`flex items-center gap-4 px-4 py-3 rounded-lg text-sm font-medium transition-colors w-full text-left ${activeTab === 'topology' ? 'bg-[#00F0FF]/10 text-[#00F0FF]' : 'text-[#94A3B8] hover:bg-[#111827] hover:text-[#F8FAFC]'}`}
            onClick={() => setActiveTab('topology')}
          >
            <span className="text-lg w-6 text-center">🗺️</span>
            Topology
          </button>
          <button
            className={`flex items-center gap-4 px-4 py-3 rounded-lg text-sm font-medium transition-colors w-full text-left ${activeTab === 'audit' ? 'bg-[#00F0FF]/10 text-[#00F0FF]' : 'text-[#94A3B8] hover:bg-[#111827] hover:text-[#F8FAFC]'}`}
            onClick={() => setActiveTab('audit')}
          >
            <span className="text-lg w-6 text-center">📋</span>
            Audit Trail
          </button>
        </nav>
        <div className="mt-auto pt-6 border-t border-[#1E293B]">
          <div className="flex items-center gap-4 px-4 py-3 rounded-lg text-[#94A3B8] text-sm">
            <span className="text-lg w-6 text-center">{isConnected ? '🟢' : '🔴'}</span>
            <span className="text-xs">{isConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-[260px] p-8 overflow-y-auto">
        <StatusBanner
          totalIncidents={counts.total}
          openIncidents={counts.open}
          investigatingIncidents={counts.investigating}
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
              {topologyData ? (
                <TopologyGraph data={topologyData} />
              ) : (
                <div className="flex justify-center items-center h-full text-[#94A3B8]">
                  Loading topology...
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'audit' && (
          <div className="bg-[#111827]/50 backdrop-blur-md border border-[#1E293B] rounded-xl p-6 h-[calc(100vh-180px)] flex flex-col">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-base font-semibold text-[#F8FAFC]">Audit Trail</h2>
            </div>
            <div className="flex-1 overflow-y-auto custom-scrollbar">
              <AuditTrail />
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
