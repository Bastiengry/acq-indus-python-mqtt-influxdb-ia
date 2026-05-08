import bpy
import bmesh
import math
import os

# 1. Nettoyage
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# 2. Construction du socle et moteur (Objets Statiques)
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=0.1, location=(0,0,0.05))
socle = bpy.context.active_object
socle.name = "Socle"

bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=1.5, location=(0,0,0.8))
pied = bpy.context.active_object
pied.name = "Pied"

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(0, 0, 1.5))
moteur = bpy.context.active_object
moteur.name = "Moteur"
moteur.scale[1] = 1.4

# 3. Création de l'Hélice (Objet SÉPARÉ)
mesh_helice = bpy.data.meshes.new("HeliceMesh")
obj_helice = bpy.data.objects.new("Helice", mesh_helice)
bpy.context.collection.objects.link(obj_helice)

bm = bmesh.new()
for i in range(3):
    angle = (math.pi * 2 / 3) * i
    # Note : on centre les pales sur Y=0 pour que le pivot soit bon
    v1 = bm.verts.new((0, 0, 1.5))
    v2 = bm.verts.new((math.sin(angle-0.2)*0.6, 0.05, 1.5 + math.cos(angle-0.2)*0.6))
    v3 = bm.verts.new((math.sin(angle)*0.7, 0.1, 1.5 + math.cos(angle)*0.7))
    v4 = bm.verts.new((math.sin(angle+0.2)*0.6, 0.05, 1.5 + math.cos(angle+0.2)*0.6))
    bm.faces.new((v1, v2, v3, v4))

bm.to_mesh(mesh_helice)
bm.free()

# On sélectionne l'hélice
bpy.context.view_layer.objects.active = obj_helice
obj_helice.select_set(True)

# On place l'origine (le pivot) au centre de la géométrie
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

# Maintenant que le pivot est au centre des pales, on la place précisément
obj_helice.location = (0, 0.4, 1.5)

# 4. Matériau
mat = bpy.data.materials.new(name="MetalNoir")
mat.use_nodes = True
principled = mat.node_tree.nodes.get("Principled BSDF")
if principled:
    principled.inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1)
    principled.inputs['Metallic'].default_value = 1.0
    principled.inputs['Roughness'].default_value = 0.2

# Appliquer le matériau à TOUS les objets
for obj in [socle, pied, moteur, obj_helice]:
    obj.data.materials.append(mat)

# 5. Exportation (SANS JOIN)
path = os.path.join(os.path.expanduser("~"), "Desktop", "fan_industrial.glb")
bpy.ops.export_scene.gltf(filepath=path, export_format='GLB')