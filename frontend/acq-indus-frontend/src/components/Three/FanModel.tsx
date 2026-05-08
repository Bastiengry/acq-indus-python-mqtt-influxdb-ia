import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import * as THREE from 'three';

interface FanModelProps {
  healthStatus: string;
  vibration: number;
}

export default function FanModel({ healthStatus, vibration }: FanModelProps) {
  const group = useRef<THREE.Group>(null);
  const { scene } = useGLTF('/fan.glb');
  const clonedScene = useMemo(() => scene.clone(), [scene]);

  
  // Appliquer la couleur aux maillages du modèle
  const fanColor = healthStatus === "CRITICAL" ? "#ff0000" : "#444444";
  useMemo(() => {
    clonedScene.traverse((child) => {
      if ((child as THREE.Mesh).isMesh) {
        const mesh = child as THREE.Mesh;
        // On vérifie si on veut peindre tout le ventilateur ou juste une partie
        // Ici, on applique fanColor à tous les matériaux du GLTF
        if (mesh.material instanceof THREE.MeshStandardMaterial) {
          mesh.material.color.set(fanColor);
        }
      }
    });
  }, [clonedScene, fanColor]);

  useFrame((state, delta) => {
    if (group.current) {
        // On cherche l'objet nommé "Helice" dans le script Blender
        const blades = group.current.getObjectByName("Helice");
        
        if (blades) {
        // Selon l'export, c'est peut-être .rotation.y ou .rotation.x
        blades.rotation.z += delta * 6; 
        }

        // Le "Shake" s'applique à 'group.current' (tout le monde vibre)
        if (healthStatus === 'CRITICAL') {
        group.current.position.x = Math.sin(state.clock.getElapsedTime() * 50) * (vibration / 200);
        }
    }
  });

  return <primitive object={clonedScene} ref={group} scale={2} />;
}
