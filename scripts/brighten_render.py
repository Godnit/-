import bpy
import math
import os
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) if '__file__' in globals() else os.getcwd()
OUT = os.path.join(ROOT, 'output')
scene = bpy.context.scene

# High-key color management: brighter, softer, closer to the reference image.
try:
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'Medium Low Contrast'
except Exception:
    pass
scene.view_settings.exposure = 0.85
scene.view_settings.gamma = 1.0

# Brighter warm-white environment so shadowed walls/porch are not muddy.
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get('Background')
if bg:
    bg.inputs['Color'].default_value = (0.98, 0.965, 0.92, 1.0)
    bg.inputs['Strength'].default_value = 0.62

# Make the studio floor/backdrop closer to the cream-white reference background.
backdrop = bpy.data.objects.get('Backdrop')
if backdrop and backdrop.type == 'MESH' and backdrop.data.materials:
    mat = backdrop.data.materials[0]
    mat.diffuse_color = (0.96, 0.945, 0.90, 1.0)
    if mat.use_nodes:
        bsdf = mat.node_tree.nodes.get('Principled BSDF')
        if bsdf:
            bsdf.inputs['Base Color'].default_value = (0.96, 0.945, 0.90, 1.0)
            bsdf.inputs['Roughness'].default_value = 0.95

# Replace the old darker lighting with a soft high-key 3-point setup.
for obj in list(scene.objects):
    if obj.type == 'LIGHT':
        bpy.data.objects.remove(obj, do_unlink=True)

def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()

def add_area(name, location, energy, size, target=(0, 0, 2.0), color=(1.0, 0.97, 0.90)):
    bpy.ops.object.light_add(type='AREA', location=location)
    light = bpy.context.object
    light.name = name
    light.data.energy = energy
    light.data.shape = 'DISK'
    light.data.size = size
    light.data.color = color
    look_at(light, target)
    return light

# Large soft key from upper-left/front, strong fill from the other side,
# plus a gentle top/front lift. This keeps shadows visible but not dark.
add_area('Key_Softbox', (-5.8, -7.8, 11.5), 1550, 5.5, (-0.2, -0.2, 2.0), (1.0, 0.94, 0.84))
add_area('Fill_Softbox', (6.5, -1.5, 8.5), 900, 6.5, (0.2, 0.0, 2.1), (0.93, 0.97, 1.0))
add_area('Front_Lift', (0.0, -8.5, 6.0), 500, 7.0, (0.0, -0.3, 1.8), (1.0, 0.98, 0.94))

bpy.ops.object.light_add(type='SUN', location=(0, 0, 9))
sun = bpy.context.object
sun.name = 'Sun_Soft'
sun.data.energy = 1.25
sun.data.angle = math.radians(18)
sun.rotation_euler = (math.radians(28), math.radians(-18), math.radians(-38))

# Preserve the same approved camera framing and rerender every preview.
cam = scene.camera
if cam is None:
    bpy.ops.object.camera_add(location=(9.5, -11.5, 8.5))
    cam = bpy.context.object
    scene.camera = cam
cam.data.type = 'ORTHO'

def render_view(filename, pos, target, scale):
    cam.location = pos
    cam.data.ortho_scale = scale
    look_at(cam, target)
    scene.render.filepath = os.path.join(OUT, filename)
    bpy.ops.render.render(write_still=True)

views = {
    'preview_perspective.png': ((9.5, -11.5, 8.5), (0, -0.1, 2.0), 10.4),
    'preview_front.png': ((0, -14, 4.6), (-0.3, 0, 2.1), 9.6),
    'preview_back.png': ((0, 14, 4.6), (-0.3, 0, 2.1), 9.6),
    'preview_left.png': ((-14, 0, 4.6), (0, 0, 2.1), 9.6),
    'preview_right.png': ((14, 0, 4.6), (0, 0, 2.1), 9.6),
    'preview_top.png': ((0, 0, 16), (0, 0, 0), 9.8),
}
for filename, (pos, target, scale) in views.items():
    render_view(filename, pos, target, scale)

# Return to the perspective view and save the brighter Blender file too.
cam.location = (9.5, -11.5, 8.5)
cam.data.ortho_scale = 10.4
look_at(cam, (0, -0.1, 2.0))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'model.blend'))
print('BRIGHT_HIGH_KEY_RENDER_COMPLETE')
