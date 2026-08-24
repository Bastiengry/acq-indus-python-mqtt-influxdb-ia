export default function GrafanaMLEstimationsIFramePanel() {
  console.log('Rendering GrafanaMLEstimationsIFramePanel');
  return (
    <iframe 
        src="http://localhost:3001/d/industrial-ml-db/industrial-ml-diagnostics-dashboard?orgId=1&kiosk" 
        style={{ width: '100%', height: '80vh', border: 'none', borderRadius: '8px' }}
    />
  )
};