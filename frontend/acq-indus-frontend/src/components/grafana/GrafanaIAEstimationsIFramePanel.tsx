export default function GrafanaIAEstimationsIFramePanel() {
  return (
    <iframe 
        src="http://localhost:3001/d/industrial-ai-db/industrial-ai-diagnostics-dashboard?orgId=1&kiosk" 
        style={{ width: '100%', height: '80vh', border: 'none', borderRadius: '8px' }}
    />
  )
};