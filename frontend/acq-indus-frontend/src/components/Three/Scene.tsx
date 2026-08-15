import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Environment, ContactShadows, Center } from '@react-three/drei';
import FanModel from './FanModel'; 
import { Suspense, useEffect, useMemo, useRef, useState } from 'react';

interface SceneInstance {
  healthStatus: string;
  vibration: number;
  position?: [number, number, number];
  rotation?: [number, number, number];
}

interface SceneProps {
  healthStatus?: string;
  vibration?: number;
  instances?: SceneInstance[];
}

export default function Scene({ healthStatus = 'OK', vibration = 0, instances }: SceneProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  const list = useMemo(() => {
    return instances && instances.length > 0 
      ? instances 
      : [{ healthStatus, vibration }];
  }, [instances, healthStatus, vibration]);

  const count = list.length;

  const positioned = useMemo(() => {
    const spacing = 3.5;
    const startX = -((count - 1) * spacing) / 2;

    return list.map((it, i) => ({
      ...it,
      position: it.position ?? [startX + i * spacing, 0, 0] as [number, number, number],
      rotation: (it.rotation ?? [0, -0.5, 0]) as [number, number, number]
    }));
  }, [list, count]);

  const [responsiveZ, setResponsiveZ] = useState<number>(6);

  // ÉCOUTE LA LARGEUR EXACTE DU CONTENEUR DIV
  useEffect(() => {
    if (!containerRef.current) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const width = entry.contentRect.width;
        
        // Ajuste la caméra selon la largeur réelle de la div 3D
        if (width < 350) {
          setResponsiveZ(13); // Très étroit (comme sur votre image) -> Recul fort
        } else if (width < 500) {
          setResponsiveZ(10); // Étroit -> Recul moyen
        } else if (width < 750) {
          setResponsiveZ(8);
        } else {
          setResponsiveZ(6);  // Largeur normale
        }
      }
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={containerRef} className="relative w-full h-full min-h-[300px] overflow-hidden bg-gradient-to-b from-slate-900 to-black">
      <Canvas shadows camera={{ position: [0, 0, responsiveZ], fov: 50 }}>
        <PerspectiveCamera makeDefault position={[0, 0, responsiveZ]} fov={50} />
        
        <OrbitControls enablePan={false} minDistance={2} maxDistance={30} target={[0, 0, 0]} />

        <ambientLight intensity={0.7} />
        <pointLight position={[10, 10, 10]} intensity={1.5} castShadow />
        <spotLight position={[-10, 10, 10]} angle={0.15} penumbra={1} intensity={1} />
        
        <Environment preset="city" />

        <Suspense fallback={null}>
          {positioned.map((it, idx) => (
            <group key={idx} position={it.position} rotation={it.rotation}>
              <Center top={false}>
                <FanModel healthStatus={it.healthStatus} vibration={it.vibration} />
              </Center>
            </group>
          ))}

          <ContactShadows 
            position={[0, -1.8, 0]} 
            opacity={0.5} 
            scale={Math.max(8, count * 4)} 
            blur={2} 
            far={1} 
          />
        </Suspense>
      </Canvas>
    </div>
  );
}