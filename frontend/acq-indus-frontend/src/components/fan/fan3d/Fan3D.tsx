import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import * as THREE from 'three';

interface Fan3DProps {
  healthStatus: string;
  vibration: number;
  position?: [number, number, number];
  rotation?: [number, number, number];
}

export default function Fan3D({ healthStatus, vibration, position, rotation }: Fan3DProps) {
  const group = useRef<THREE.Group>(null);
  const { scene } = useGLTF('/fan.glb');
  const clonedScene = useMemo(() => scene.clone(), [scene]);
  
  // recentrer le modèle à l'origine en se basant sur sa bounding box
  useMemo(() => {
    try {
      const box = new THREE.Box3().setFromObject(clonedScene as THREE.Object3D);
      const center = new THREE.Vector3();
      box.getCenter(center);
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    } catch (error) {
      // ignore if bounding box fails
    }
  }, [clonedScene]);

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
        // On cherche l'objet nommé "Helice" dans le modèle cloné
        const blades = group.current.getObjectByName("Helice");
        
        if (blades) {
          blades.rotation.z += delta * 6; 
        }

        // Le "Shake" s'applique au groupe (vibration)
        if (healthStatus === 'CRITICAL') {
          const shake = Math.sin(state.clock.getElapsedTime() * 50) * (vibration / 200);
          group.current.position.x = shake;
        } else {
          // reset small offset when not critical
          group.current.position.x = 0;
        }
    }
  });

  return (
    <group ref={group} position={position} rotation={rotation}>
      <primitive object={clonedScene} scale={2} />
    </group>
  );
}
