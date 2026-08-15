import { useState } from 'react';
import Fans from './Fans';
import Chat from './Chat';
import './App.css';

const App = () => {
  const [isOpen, setIsOpen] = useState(true);
  const [activeView, setActiveView] = useState('monitor');
  // Exemple : plusieurs capteurs disponibles
  const sensors = [
    { id: 'FAN_01', label: 'FAN 01' },
    { id: 'FAN_02', label: 'FAN 02' },
    { id: 'FAN_03', label: 'FAN 03' },
    { id: 'FAN_04', label: 'FAN 04' },
  ];
  const [selectedSensorIndex, setSelectedSensorIndex] = useState(0);

  return (
    <div className="w-full h-full flex bg-white margin-0">
      
      {/* SIDEBAR (Le Drawer) */}
      <div className={`
        ${isOpen ? 'w-64' : 'w-0'} 
        flex flex-col bg-[#2c3e50] overflow-hidden transition-all duration-300 flex-shrink-0
      `}>
        <div className="p-5 font-bold text-[1.2rem] border-b border-[#34495e] text-center text-white">
          FAN CONTROL 01
        </div>
        <nav style={{ padding: '10px' }}>
          <button 
            onClick={() => setActiveView('monitor')}
            style={navButtonStyle(activeView === 'monitor')}>
            📊 Dashboard Live
          </button>
          <button 
            onClick={() => setActiveView('grafana')}
            style={navButtonStyle(activeView === 'grafana')}>
            📈 Analyses Grafana
          </button>
          <button 
            onClick={() => setActiveView('chat')}
            style={navButtonStyle(activeView === 'chat')}>
            💬 Chat IA
          </button>
        </nav>
      </div>

      {/* CONTENU PRINCIPAL */}
      <div className="flex-1 flex flex-col">
        <header className="p-4 flex items-center bg-[#34495e] text-white">
          <button onClick={() => setIsOpen(!isOpen)} style={{ marginRight: '15px', cursor: 'pointer' }}>☰</button>
          <h2 className="flex-1" style={{ margin: 0 }}>{activeView === 'monitor' ? 'Live Monitoring' : 'Grafana Analytics'}</h2>
          {activeView === 'monitor' && (
            <select
              value={selectedSensorIndex}
              onChange={(e) => setSelectedSensorIndex(Number(e.target.value))}
              className="bg-[#2c3e50] text-white px-3 py-2 rounded"
              style={{ marginLeft: '12px' }}
            >
              {sensors.map((s, idx) => (
                <option key={s.id} value={idx}>{s.label ?? s.id ?? 'UNKNOWN'}</option>
              ))}
            </select>
          )}
        </header>

        <main className="flex-1 p-4 overflow-auto">
          {activeView === 'monitor' && (
             <div id="fan">
               <Fans sensors={sensors} activeIndex={selectedSensorIndex} />
             </div>
          )}
          {activeView === 'grafana' && (
             // Ecrire "d-solo" avoir uniquement le panel sans les menus, "d" pour le dashboard complet
             <iframe 
               src="http://localhost:3001/d/acq-indus-tunnel-dashboard/supervision-ventilateurs?orgId=1&kiosk" 
               style={{ width: '100%', height: '80vh', border: 'none', borderRadius: '8px' }}
             />
          )}
          {activeView === 'chat' && (
             <Chat />
          )}
        </main>
      </div>
    </div>
  );
};

// Petit helper pour le style des boutons
const navButtonStyle = (isActive: boolean): React.CSSProperties => ({
  width: '100%',
  padding: '12px',
  marginBottom: '10px',
  backgroundColor: isActive ? '#3498db' : 'transparent',
  color: 'white',
  border: 'none',
  borderRadius: '4px',
  textAlign: 'left' as const, 
  cursor: 'pointer',
  transition: '0.2s'
});

export default App;