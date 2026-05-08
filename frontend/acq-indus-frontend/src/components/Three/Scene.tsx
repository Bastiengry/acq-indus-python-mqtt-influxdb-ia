import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Environment, ContactShadows } from '@react-three/drei';
import FanModel from './FanModel'; 
import { Suspense } from 'react';

interface SceneProps {
  healthStatus: string;
  vibration: number;
}

export default function Scene({ healthStatus, vibration }: SceneProps) {
  return (
    <div className="w-full h-full bg-gradient-to-b from-slate-900 to-black">
      <Canvas shadows>
        {/* 1. Caméra interactive */}
        <PerspectiveCamera makeDefault position={[5, 2, 5]} fov={50} />
        <OrbitControls enablePan={false} minDistance={3} maxDistance={10} />

        {/* 2. Éclairage industriel */}
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1.5} castShadow />
        <spotLight position={[-10, 10, 10]} angle={0.15} penumbra={1} intensity={1} />
        
        {/* Optionnel : Ajoute un environnement réaliste (reflets métalliques) */}
        <Environment preset="city" />

        {/* 3. Le Modèle avec gestion du chargement */}
        <Suspense fallback={null}>
          <group position={[0, -2, 0]} rotation={[0, -2, 0]}>
            <FanModel healthStatus={healthStatus} vibration={vibration} />
          </group>
          
          {/* Ombres au sol pour ancrer l'objet */}
          <ContactShadows 
            position={[0, -2, 0]} 
            opacity={0.4} 
            scale={10} 
            blur={2} 
            far={1} 
          />
        </Suspense>
      </Canvas>
    </div>
  );
}