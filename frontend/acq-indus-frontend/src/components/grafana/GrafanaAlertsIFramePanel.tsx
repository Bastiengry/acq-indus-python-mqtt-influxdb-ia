export default function GrafanaHistoryIFramePanel() {
  return (
    <iframe 
        src="http://localhost:3001/d/industrial-alarms-db/industrial-alarms-dashboard?orgId=1&kiosk" 
        style={{ width: '100%', height: '80vh', border: 'none', borderRadius: '8px' }}
    />
  )
};