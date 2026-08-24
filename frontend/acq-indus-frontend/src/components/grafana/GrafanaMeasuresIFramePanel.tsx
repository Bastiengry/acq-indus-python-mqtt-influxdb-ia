export default function GrafanaMeasuresIFramePanel() {
  return (
    <iframe 
        src="http://localhost:3001/d/acq-indus-tunnel-dashboard/supervision-ventilateurs?orgId=1&kiosk" 
        style={{ width: '100%', height: '80vh', border: 'none', borderRadius: '8px' }}
    />
  )
};