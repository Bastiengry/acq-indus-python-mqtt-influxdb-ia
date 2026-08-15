import Fan from './Fan';

type Sensor = { id: string; label?: string };

export default function Fans({ sensors = [{ id: 'FAN_01', label: 'FAN 01' }], activeIndex = 0 }: { sensors?: Sensor[], activeIndex?: number }) {
  const idx = activeIndex ?? 0;
  const active = sensors[idx] ?? sensors[0];
  return (
    <div >
      <div id="fan">
        <Fan sensorId={active.id} label={active.label ?? active.id ?? 'UNKNOWN'} />
      </div>
    </div>
  );
}
