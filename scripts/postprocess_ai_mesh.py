import bpy
import bmesh
import math
import os
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) if '__file__' in globals() else os.getcwd()
RAW = os.path.join(ROOT, 'ai_raw', '0', 'mesh.glb')
OUT = os.path.join(ROOT, 'ai_output')
os.makedirs(OUT, exist_ok=True)

if not os.path.exists(RAW):
    raise SystemExit(f'AI mesh not found: {RAW}')

# Clean scene and import the TripoSR result.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=RAW)

mesh_objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
if not mesh_objects:
    raise SystemExit('No mesh objects imported from TripoSR GLB')

# Apply transforms and repair basic mesh issues while preserving materials / vertex color setup.
for obj in mesh_objects:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    if bm.faces:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    obj.select_set(False)

# Compute world-space bounds.
def world_bounds(objects):
    mins = Vector((1e20, 1e20, 1e20))
    maxs = Vector((-1e20, -1e20, -1e20))
    for obj in objects:
        for c in obj.bound_box:
            p = obj.matrix_world @ Vector(c)
            mins.x = min(mins.x, p.x); mins.y = min(mins.y, p.y); mins.z = min(mins.z, p.z)
            maxs.x = max(maxs.x, p.x); maxs.y = max(maxs.y, p.y); maxs.z = max(maxs.z, p.z)
    return mins, maxs

mins, maxs = world_bounds(mesh_objects)
center = (mins + maxs) * 0.5
span = max(maxs.x - mins.x, maxs.y - mins.y, maxs.z - mins.z)
if span <= 1e-8:
    raise SystemExit('Degenerate AI mesh bounds')

# Normalize to a convenient architectural preview size, centered on XY with ground at Z=0.
scale = 5.6 / span
for obj in mesh_objects:
    obj.scale *= scale
    obj.location = (obj.location.x - center.x) * scale, (obj.location.y - center.y) * scale, (obj.location.z - mins.z) * scale

# Re-evaluate after normalization.
mins, maxs = world_bounds(mesh_objects)
dims = maxs - mins

scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'METERS'
scene.render.resolution_x = 768
scene.render.resolution_y = 768
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.render.engine = 'BLENDER_EEVEE' if bpy.app.version < (4, 2, 0) else 'BLENDER_EEVEE_NEXT'
try:
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'Medium Low Contrast'
    scene.view_settings.exposure = 0.10
except Exception:
    pass

# Neutral cream studio world, deliberately not overexposed.
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get('Background')
if bg:
    bg.inputs['Color'].default_value = (0.965, 0.95, 0.91, 1.0)
    bg.inputs['Strength'].default_value = 0.34

# Floor material.
mat = bpy.data.materials.new('AI_Studio_Floor')
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get('Principled BSDF')
bsdf.inputs['Base Color'].default_value = (0.94, 0.92, 0.87, 1.0)
bsdf.inputs['Roughness'].default_value = 0.92
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.08))
floor = bpy.context.object
floor.name = 'AI_Backdrop_Floor'
floor.dimensions = (12, 12, 0.12)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
floor.data.materials.append(mat)

# Soft balanced lighting.
def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()

def area(name, loc, energy, size, target=(0, 0, 2.0), color=(1.0, 0.97, 0.91)):
    bpy.ops.object.light_add(type='AREA', location=loc)
    l = bpy.context.object
    l.name = name
    l.data.energy = energy
    l.data.size = size
    l.data.color = color
    look_at(l, target)
    return l

area('AI_Key', (-5.5, -7.0, 9.5), 900, 5.5, (0, 0, 2.0))
area('AI_Fill', (5.5, -1.0, 6.5), 430, 6.5, (0, 0, 2.0), (0.95, 0.98, 1.0))
area('AI_Front', (0, -7.0, 4.5), 180, 6.5, (0, 0, 1.7))
bpy.ops.object.light_add(type='SUN', location=(0, 0, 8))
sun = bpy.context.object
sun.name = 'AI_Sun'
sun.data.energy = 0.55
sun.data.angle = math.radians(22)
sun.rotation_euler = (math.radians(30), math.radians(-18), math.radians(-35))

# Camera / previews.
bpy.ops.object.camera_add(location=(8.0, -9.2, 6.7))
cam = bpy.context.object
cam.name = 'AI_Camera'
cam.data.type = 'ORTHO'
scene.camera = cam

def render(name, pos, target, ortho):
    cam.location = pos
    cam.data.ortho_scale = ortho
    look_at(cam, target)
    scene.render.filepath = os.path.join(OUT, name)
    bpy.ops.render.render(write_still=True)

ortho = max(6.7, max(dims.x, dims.y, dims.z) * 1.35)
target_z = max(1.5, dims.z * 0.42)
views = {
    'ai_preview_perspective.png': ((8.0, -9.2, 6.7), (0, 0, target_z), ortho),
    'ai_preview_front.png': ((0, -12, 3.8), (0, 0, target_z), ortho),
    'ai_preview_back.png': ((0, 12, 3.8), (0, 0, target_z), ortho),
    'ai_preview_left.png': ((-12, 0, 3.8), (0, 0, target_z), ortho),
    'ai_preview_right.png': ((12, 0, 3.8), (0, 0, target_z), ortho),
    'ai_preview_top.png': ((0, 0, 14), (0, 0, 0), ortho),
}
for filename, (pos, target, s) in views.items():
    render(filename, pos, target, s)

# Save blend and re-export normalized GLB without studio helpers.
blend_path = os.path.join(OUT, 'ai_model.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
for o in scene.objects:
    o.select_set(False)
for o in mesh_objects:
    o.select_set(True)
bpy.context.view_layer.objects.active = mesh_objects[0]
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'ai_model.glb'), export_format='GLB', use_selection=True, export_apply=True)

# Validation/report.
verts = edges = faces = tris = nonman = loose = degenerate = 0
for obj in mesh_objects:
    me = obj.data
    verts += len(me.vertices); edges += len(me.edges); faces += len(me.polygons)
    tris += sum(max(1, len(p.vertices) - 2) for p in me.polygons)
    bm = bmesh.new(); bm.from_mesh(me)
    nonman += sum(1 for e in bm.edges if not e.is_manifold)
    loose += sum(1 for v in bm.verts if len(v.link_edges) == 0)
    degenerate += sum(1 for f in bm.faces if f.calc_area() < 1e-10)
    bm.free()

report = [
    'Experiment: TripoSR single-image cottage reconstruction',
    f'Blender: {bpy.app.version_string}',
    f'Mesh objects: {len(mesh_objects)}',
    f'Vertices: {verts}',
    f'Edges: {edges}',
    f'Faces: {faces}',
    f'Triangles approx: {tris}',
    f'Dimensions XYZ after normalization (m): {[round(dims.x,4), round(dims.y,4), round(dims.z,4)]}',
    f'Non-manifold edges: {nonman}',
    f'Loose vertices: {loose}',
    f'Degenerate faces: {degenerate}',
    'Normals: recalculated outside during Blender post-process',
]
with open(os.path.join(OUT, 'ai_model_report.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(report))
print('\n'.join(report))
print('AI_POSTPROCESS_COMPLETE')
