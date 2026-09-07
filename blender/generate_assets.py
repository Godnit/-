import bpy, os, math

out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets'))
os.makedirs(out_dir, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)

bpy.ops.mesh.primitive_torus_add(major_radius=0.59, minor_radius=0.08, major_segments=24, minor_segments=8, location=(0,0,0), rotation=(math.radians(90),0,0))
ring = bpy.context.object
ring.name = 'PortalRing'
mat = bpy.data.materials.new('PortalGlow')
mat.diffuse_color = (0.04, 0.72, 1.0, 1.0)
mat.metallic = 0.15
mat.roughness = 0.3
ring.data.materials.append(mat)

bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.42, depth=0.025, location=(0,0,0), rotation=(math.radians(90),0,0))
core = bpy.context.object
core.name = 'PortalSurface'
mat2 = bpy.data.materials.new('PortalSurface')
mat2.diffuse_color = (0.02, 0.16, 0.25, 0.8)
mat2.metallic = 0.0
mat2.roughness = 0.25
core.data.materials.append(mat2)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
path = os.path.join(out_dir, 'portal_ring.glb')
bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True)
print('Generated', path)
