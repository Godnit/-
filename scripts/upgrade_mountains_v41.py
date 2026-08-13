import bpy, os, math, random
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'output_classic_reference_v41')
os.makedirs(OUT, exist_ok=True)
scene = bpy.context.scene
scene.render.resolution_x = 1024
scene.render.resolution_y = 576
scene.render.resolution_percentage = 100
rng = random.Random(410826)
CX, CY = 0.0, 48.0

# -----------------------------------------------------------------------------
# V41: replace the old straight mountain wall with a true curved mountain range.
# The accepted V40 floating island, trees and meadow props stay in place.
# -----------------------------------------------------------------------------
for o in list(scene.objects):
    if o.name.startswith('Mountain'):
        bpy.data.objects.remove(o, do_unlink=True)


def make_mat(name, rgb, roughness=0.96):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    if p:
        p.inputs['Base Color'].default_value = (*rgb, 1.0)
        if 'Roughness' in p.inputs:
            p.inputs['Roughness'].default_value = roughness
    m.diffuse_color = (*rgb, 1.0)
    return m


def tune_mat(name, rgb):
    m = bpy.data.materials.get(name)
    if not m:
        return
    m.diffuse_color = (*rgb, 1.0)
    if m.use_nodes:
        p = m.node_tree.nodes.get('Principled BSDF')
        if p:
            p.inputs['Base Color'].default_value = (*rgb, 1.0)

# Richer but still pastel/TABS-like palette.
tune_mat('Grass', (0.53, 0.61, 0.25))
tune_mat('IslandEarth', (0.43, 0.35, 0.19))
tune_mat('IslandEarthDark', (0.33, 0.27, 0.15))
tune_mat('IslandStone', (0.34, 0.39, 0.40))
tune_mat('IslandStoneDark', (0.25, 0.30, 0.31))

mount_moss = make_mat('MountainMossV41', (0.33, 0.40, 0.27))
mount_low = make_mat('MountainRockLowV41', (0.39, 0.44, 0.43))
mount_mid = make_mat('MountainRockMidV41', (0.47, 0.52, 0.51))
mount_cool = make_mat('MountainRockCoolV41', (0.51, 0.57, 0.58))
mount_light = make_mat('MountainRockLightV41', (0.63, 0.68, 0.66))
mount_shadow = make_mat('MountainRockShadowV41', (0.31, 0.36, 0.37))
materials = [mount_moss, mount_low, mount_mid, mount_cool, mount_light, mount_shadow]

# -----------------------------------------------------------------------------
# Curved terrain strip: 6 depth rows following an elliptical arc around the rear
# island edge. Peak heights rise and fall naturally instead of forming a line.
# -----------------------------------------------------------------------------
segments = 43
rows = 6
angles = [math.radians(18.0 + (162.0 - 18.0) * i / (segments - 1)) for i in range(segments)]
radial_scales = [0.83, 0.90, 0.965, 1.015, 1.075, 1.125]
RX, RY = 118.0, 126.0


def gauss(u, c, w):
    return math.exp(-((u - c) / w) ** 2)

heights = []
for i in range(segments):
    u = i / (segments - 1)
    # Three large massifs plus smaller irregular variation.
    h = (8.0
         + 9.0 * gauss(u, 0.22, 0.11)
         + 15.0 * gauss(u, 0.50, 0.12)
         + 11.0 * gauss(u, 0.78, 0.10)
         + 2.4 * math.sin(u * math.pi * 9.0 + 0.5)
         + rng.uniform(-1.4, 1.4))
    # Let the range sink naturally into the terrain at both ends.
    edge = min(1.0, u / 0.115, (1.0 - u) / 0.115)
    h = 3.8 + (h - 3.8) * max(0.0, edge)
    heights.append(max(3.5, h))

verts = []
for r in range(rows):
    sc = radial_scales[r]
    for i, a in enumerate(angles):
        h = heights[i]
        # six terrain bands: foot -> lower slope -> upper slope -> ridge -> rear shoulder -> rear foot
        if r == 0:
            frac = 0.02
        elif r == 1:
            frac = 0.22 + rng.uniform(-0.025, 0.025)
        elif r == 2:
            frac = 0.53 + rng.uniform(-0.035, 0.035)
        elif r == 3:
            frac = 1.00
        elif r == 4:
            frac = 0.48 + rng.uniform(-0.045, 0.045)
        else:
            frac = 0.015

        # Small radial/tangential perturbations create real low-poly terrain facets.
        jitter_r = rng.uniform(-1.2, 1.2) if 0 < r < rows - 1 else rng.uniform(-0.45, 0.45)
        jitter_t = rng.uniform(-0.8, 0.8) if 0 < i < segments - 1 else 0.0
        x = CX + (RX * sc + jitter_r) * math.cos(a) - jitter_t * math.sin(a)
        y = CY + (RY * sc + jitter_r) * math.sin(a) + jitter_t * math.cos(a)
        z = 0.05 + h * frac
        if r not in (0, 5):
            z += rng.uniform(-0.35, 0.35)
        verts.append((x, y, z))

faces = []
face_mats = []
for r in range(rows - 1):
    for i in range(segments - 1):
        a = r * segments + i
        b = a + 1
        c = (r + 1) * segments + i
        d = c + 1
        if (i + r) % 2:
            faces.extend([(a, b, c), (b, d, c)])
        else:
            faces.extend([(a, b, d), (a, d, c)])

        # Material by altitude band with deterministic variation across facets.
        if r == 0:
            pair = [0, 1]
        elif r == 1:
            pair = [1, 2]
        elif r == 2:
            pair = [2, 3]
            if heights[i] > 19 and (i % 5 == 0):
                pair[1] = 4
        elif r == 3:
            pair = [3, 4 if (i % 4 == 0) else 2]
        else:
            pair = [5, 1]
        face_mats.extend(pair)

# close the two curved-strip ends so the range is a real solid mesh
faces.append(tuple(r * segments for r in range(rows)))
face_mats.append(1)
faces.append(tuple((r + 1) * segments - 1 for r in reversed(range(rows))))
face_mats.append(1)

mesh = bpy.data.meshes.new('MountainRangeTerrainV41_Mesh')
mesh.from_pydata(verts, [], faces)
mesh.validate()
mesh.update()
mountain = bpy.data.objects.new('MountainRangeTerrainV41', mesh)
bpy.context.collection.objects.link(mountain)
for m in materials:
    mesh.materials.append(m)
for p, mi in zip(mesh.polygons, face_mats):
    p.material_index = mi
    p.use_smooth = False

# -----------------------------------------------------------------------------
# Secondary rocky shoulders. These are terrain masses, not cone props, and make
# the silhouette deeper and less uniform when viewed from either side.
# -----------------------------------------------------------------------------
def build_massif(name, center, rx, ry, height, seed):
    rr = random.Random(seed)
    ring_n = 11
    v = []
    # outer foot ring
    for k in range(ring_n):
        a = 2 * math.pi * k / ring_n
        wob = 1.0 + rr.uniform(-0.12, 0.12)
        v.append((center[0] + rx * wob * math.cos(a), center[1] + ry * wob * math.sin(a), 0.05))
    # middle shoulder ring
    for k in range(ring_n):
        a = 2 * math.pi * k / ring_n
        wob = 0.58 + rr.uniform(-0.07, 0.07)
        v.append((center[0] + rx * wob * math.cos(a), center[1] + ry * wob * math.sin(a), height * (0.36 + rr.uniform(-0.05, 0.05))))
    # irregular summit cluster: one top plus two near-top vertices
    summit = len(v)
    v.append((center[0] + rr.uniform(-rx * 0.08, rx * 0.08), center[1] + rr.uniform(-ry * 0.07, ry * 0.07), height))
    f = []
    fm = []
    for k in range(ring_n):
        j = (k + 1) % ring_n
        o0, o1 = k, j
        m0, m1 = ring_n + k, ring_n + j
        if k % 2:
            f.extend([(o0, o1, m0), (o1, m1, m0)])
        else:
            f.extend([(o0, o1, m1), (o0, m1, m0)])
        fm.extend([0 if k % 3 else 1, 1 if k % 2 else 2])
        f.append((m0, m1, summit))
        fm.append(4 if height > 20 and k % 4 == 0 else (3 if k % 2 else 2))
    me = bpy.data.meshes.new(name + '_Mesh')
    me.from_pydata(v, [], f)
    me.validate(); me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    for m in materials:
        me.materials.append(m)
    for p, mi in zip(me.polygons, fm):
        p.material_index = mi
        p.use_smooth = False
    return ob

# Place behind/within the curved range, following the same arc rather than a line.
for idx, (deg, h, rxm, rym) in enumerate([
    (34, 15.0, 15.0, 11.0),
    (54, 20.0, 17.5, 13.0),
    (76, 17.0, 15.5, 11.5),
    (103, 21.5, 18.5, 14.0),
    (128, 18.5, 16.0, 12.0),
    (147, 13.5, 13.0, 10.0),
]):
    a = math.radians(deg)
    rradius = 128.0
    cx = CX + rradius * math.cos(a)
    cy = CY + 136.0 * math.sin(a)
    build_massif('MountainMassifV41_%02d' % idx, (cx, cy), rxm, rym, h, 41100 + idx)

# A handful of large embedded rocks at mountain feet for transition into forest.
for idx, deg in enumerate((25, 43, 64, 89, 114, 137, 155)):
    a = math.radians(deg)
    x = CX + 104.0 * math.cos(a)
    y = CY + 111.0 * math.sin(a)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0, location=(x, y, 1.0))
    o = bpy.context.object
    o.name = 'MountainFootRockV41_%02d' % idx
    s = rng.uniform(2.2, 4.0)
    o.scale = (s * rng.uniform(1.0, 1.45), s * rng.uniform(0.7, 1.0), s * rng.uniform(0.55, 0.9))
    o.rotation_euler[2] = a + rng.uniform(-0.5, 0.5)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mount_low if idx % 2 else mount_mid)
    for p in o.data.polygons:
        p.use_smooth = False

# -----------------------------------------------------------------------------
# Softer natural daylight / sky. Keep the tree palette itself unchanged.
# -----------------------------------------------------------------------------
world = scene.world
if world:
    world.use_nodes = True
    bg = world.node_tree.nodes.get('Background')
    if bg:
        bg.inputs['Color'].default_value = (0.60, 0.78, 0.84, 1.0)
        bg.inputs['Strength'].default_value = 0.72

sun_found = False
for o in scene.objects:
    if o.type == 'LIGHT' and o.data.type == 'SUN':
        sun_found = True
        o.data.energy = 2.0
        o.data.angle = math.radians(16.0)
if not sun_found:
    bpy.ops.object.light_add(type='SUN', location=(-80, -120, 150))
    sun = bpy.context.object
    sun.name = 'SunV41'
    sun.data.energy = 2.0
    sun.data.angle = math.radians(16.0)
    sun.rotation_euler = (math.radians(28), math.radians(-18), math.radians(-28))

try:
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'Medium High Contrast'
except Exception:
    pass
scene.view_settings.exposure = 0.12
scene.view_settings.gamma = 1.0

# -----------------------------------------------------------------------------
# Render / export.
# -----------------------------------------------------------------------------
def look_at(o, target):
    o.rotation_euler = (Vector(target) - o.location).to_track_quat('-Z', 'Y').to_euler()

cam = scene.camera
if cam is None:
    raise RuntimeError('Scene camera missing')


def render(name, loc, target, lens):
    cam.location = loc
    cam.data.lens = lens
    look_at(cam, target)
    scene.render.filepath = os.path.join(OUT, name)
    bpy.ops.render.render(write_still=True)

render('preview_main.png', (0, -520, 235), (0, 55, -2.5), 40)
render('preview_closer.png', (0, -315, 128), (0, 58, 3.5), 42)
render('preview_left.png', (-330, -285, 150), (0, 58, 1.5), 43)
render('preview_right.png', (330, -285, 150), (0, 58, 1.5), 43)
render('preview_high.png', (0, -285, 305), (0, 58, -1.0), 44)
render('preview_mountains.png', (0, -155, 82), (0, 132, 12.0), 50)
cam.location = (0, -520, 235)
cam.data.lens = 40
look_at(cam, (0, 55, -2.5))

blend = os.path.join(OUT, 'classic_reference_v41.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'classic_reference_v41.glb'), export_format='GLB', export_apply=True)

forest = bpy.data.objects.get('PineForest')
pine_count = int(len(forest.data.vertices) / 54) if forest and forest.type == 'MESH' else -1
with open(os.path.join(OUT, 'report.txt'), 'w', encoding='utf-8') as f:
    f.write('Classic reference v41 natural curved mountain terrain\n')
    f.write('Pine count: %d (tree mesh inherited unchanged)\n' % pine_count)
    f.write('Old straight Mountain* objects removed\n')
    f.write('New mountain range: curved elliptical terrain strip, %d segments x %d depth rows\n' % (segments, rows))
    f.write('Secondary mountain massifs: 6\n')
    f.write('Mountain foot rocks: 7\n')
    f.write('Palette: moss/stone/cool-gray/light-stone with brighter natural sky\n')
    f.write('Floating island geometry: inherited unchanged from V40\n')
print('V41_OK', blend)
