import bpy, bmesh, math, os, random
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) if '__file__' in globals() else os.getcwd()
OUT = os.path.join(ROOT, 'output_farmer2')
os.makedirs(OUT, exist_ok=True)
SEED = 2208
random.seed(SEED)

# -----------------------------------------------------------------------------
# Reset / scene
# -----------------------------------------------------------------------------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
    pass

scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'METERS'
scene.unit_settings.scale_length = 1.0
scene.render.resolution_x = 900
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.render.engine = 'BLENDER_EEVEE' if bpy.app.version < (4, 2, 0) else 'BLENDER_EEVEE_NEXT'
try:
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'Medium High Contrast'
except Exception:
    pass
scene.world.color = (0.91, 0.89, 0.83)
try:
    if hasattr(scene, 'eevee'):
        scene.eevee.use_gtao = True
        scene.eevee.gtao_distance = 5
        scene.eevee.gtao_factor = 1.35
        scene.eevee.use_soft_shadows = True
except Exception:
    pass

# -----------------------------------------------------------------------------
# Materials
# -----------------------------------------------------------------------------
def make_mat(name, rgb, rough=0.82, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    if p:
        p.inputs['Base Color'].default_value = (*rgb, 1.0)
        p.inputs['Roughness'].default_value = rough
        p.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*rgb, 1.0)
    return m

M = {
    'grass': make_mat('Grass_Mustard_Olive', (0.53, 0.52, 0.18), .95),
    'grass2': make_mat('Grass_Light', (0.61, 0.59, 0.21), .95),
    'grass3': make_mat('Grass_Shadow', (0.37, 0.41, 0.13), .95),
    'dirt': make_mat('Packed_Dirt', (0.47, 0.35, 0.18), .98),
    'dirt2': make_mat('Dry_Dirt', (0.57, 0.43, 0.23), .98),
    'earth1': make_mat('Cliff_Earth_1', (0.35, 0.30, 0.18), 1.0),
    'earth2': make_mat('Cliff_Earth_2', (0.44, 0.37, 0.21), 1.0),
    'earth3': make_mat('Cliff_Earth_3', (0.26, 0.25, 0.18), 1.0),
    'stone1': make_mat('Cobble_Grey_1', (0.38, 0.39, 0.34), .95),
    'stone2': make_mat('Cobble_Grey_2', (0.48, 0.48, 0.39), .95),
    'stone3': make_mat('Cobble_Grey_3', (0.29, 0.31, 0.29), .95),
    'wheat1': make_mat('Wheat_Gold', (0.88, 0.55, 0.18), .92),
    'wheat2': make_mat('Wheat_Light', (0.95, 0.67, 0.25), .92),
    'hay': make_mat('Hay_Bales', (0.84, 0.62, 0.25), .92),
    'wood': make_mat('Wood_Dark', (0.28, 0.18, 0.10), .88),
    'wood2': make_mat('Wood_Warm', (0.42, 0.25, 0.12), .88),
    'roof': make_mat('Roof_Weathered', (0.25, 0.24, 0.21), .92),
    'window': make_mat('Window_Warm', (0.93, 0.70, 0.22), .58),
    'pumpkin': make_mat('Pumpkin', (0.82, 0.30, 0.06), .9),
    'trough': make_mat('Trough', (0.30, 0.32, 0.28), .92),
    'water': make_mat('Water_Dark', (0.12, 0.20, 0.20), .48),
    'leaf1': make_mat('Leaves_Olive', (0.37, 0.40, 0.16), .95),
    'leaf2': make_mat('Leaves_Green', (0.30, 0.36, 0.14), .95),
    'leaf3': make_mat('Leaves_Light', (0.49, 0.49, 0.19), .95),
    'dark': make_mat('Dark', (0.06, 0.06, 0.05), .9),
}


def assign(obj, material):
    obj.data.materials.clear()
    obj.data.materials.append(material)


def bevel(obj, width=0.08, segments=1):
    if width <= 0:
        return obj
    mod = obj.modifiers.new('SoftBevel', 'BEVEL')
    mod.width = width
    mod.segments = segments
    mod.limit_method = 'ANGLE'
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.modifier_apply(modifier=mod.name)
    except Exception:
        pass
    return obj


def box(name, loc, dims, material, rot=(0, 0, 0), bev=.04):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(o, material)
    bevel(o, bev, 1)
    return o


def cyl(name, loc, radius, depth, material, vertices=10, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    assign(o, material)
    return o


def ico(name, loc, radius, material, scale=(1, 1, 1), sub=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=radius, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(o, material)
    return o


def mesh_obj(name, verts, faces, materials, face_mats=None):
    me = bpy.data.meshes.new(name + '_Mesh')
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    for mat in materials:
        me.materials.append(mat)
    if face_mats:
        for poly, mi in zip(me.polygons, face_mats):
            poly.material_index = mi
    return o

# -----------------------------------------------------------------------------
# Floating circular island
# -----------------------------------------------------------------------------
def make_island():
    rng = random.Random(SEED + 1)
    n = 56
    top = []
    mid = []
    bot = []
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = 28.5 + rng.uniform(-0.7, 0.65)
        top.append((rr * math.cos(a), rr * math.sin(a), 0.0))
        rm = rr - rng.uniform(0.5, 1.6)
        mid.append((rm * math.cos(a), rm * math.sin(a), -1.8 + rng.uniform(-0.25, .18)))
        rb = rr - rng.uniform(3.2, 5.1)
        bot.append((rb * math.cos(a), rb * math.sin(a), -5.8 + rng.uniform(-0.35, .25)))
    verts = [(0, 0, 0.0)] + top + mid + bot + [(0, 0, -6.0)]
    top0 = 1
    mid0 = 1 + n
    bot0 = 1 + 2 * n
    bottom_center = len(verts) - 1
    faces = []
    fm = []
    for i in range(n):
        j = (i + 1) % n
        faces.append((0, top0+i, top0+j)); fm.append(0)
    for i in range(n):
        j = (i + 1) % n
        faces.append((top0+i, mid0+i, mid0+j, top0+j)); fm.append(1 + (i % 3))
        faces.append((mid0+i, bot0+i, bot0+j, mid0+j)); fm.append(1 + ((i+1) % 3))
        faces.append((bottom_center, bot0+j, bot0+i)); fm.append(2)
    return mesh_obj('Farmer2_Floating_Island', verts, faces,
                    [M['grass'], M['earth1'], M['earth2'], M['earth3']], fm)

make_island()

rng = random.Random(SEED + 2)
for i in range(42):
    a = 2 * math.pi * i / 42 + rng.uniform(-.04, .04)
    r = rng.uniform(27.1, 28.6)
    z = rng.uniform(-2.5, -.2)
    rr = rng.uniform(.35, .75)
    ico(f'CliffRock_{i:02d}', (r*math.cos(a), r*math.sin(a), z), rr,
        [M['stone1'], M['stone2'], M['stone3']][i % 3],
        scale=(rng.uniform(.8,1.4), rng.uniform(.7,1.2), rng.uniform(.6,1.2)), sub=1)

# -----------------------------------------------------------------------------
# Terrain overlays: paths, tracks, hill
# -----------------------------------------------------------------------------
def ribbon(name, points, width, z, material):
    verts = []
    faces = []
    for i, p in enumerate(points):
        p = Vector((p[0], p[1], z))
        if i == 0:
            tang = Vector((points[1][0]-points[0][0], points[1][1]-points[0][1], 0)).normalized()
        elif i == len(points)-1:
            tang = Vector((points[-1][0]-points[-2][0], points[-1][1]-points[-2][1], 0)).normalized()
        else:
            tang = Vector((points[i+1][0]-points[i-1][0], points[i+1][1]-points[i-1][1], 0)).normalized()
        perp = Vector((-tang.y, tang.x, 0)) * (width/2)
        verts.extend([tuple(p+perp), tuple(p-perp)])
    for i in range(len(points)-1):
        a = i*2
        b = a+2
        faces.append((a, a+1, b+1, b))
    return mesh_obj(name, verts, faces, [material])

ribbon('Main_Open_Path', [(-27, 0.4), (-19, .8), (-10, .6), (-2, .5), (6, .4), (10.5, 2.0)], 2.5, .08, M['dirt2'])
ribbon('Main_Wheel_Rut_A', [(-27, 1.15), (-19, 1.45), (-10, 1.25), (-2, 1.15), (6, 1.0)], .34, .105, M['dirt'])
ribbon('Main_Wheel_Rut_B', [(-27, -.25), (-19, .05), (-10, -.15), (-2, -.25), (6, -.35)], .34, .105, M['dirt'])
ribbon('Lower_Left_Alley', [(-19.1, -24), (-18.8,-18), (-18.6,-12), (-16.8,-7.4)], 1.7, .09, M['dirt2'])
ribbon('Upper_Center_Alley', [(-1.4, 11.8), (-1.2, 18.0), (-1.1, 27.0)], 1.9, .09, M['dirt2'])
ribbon('Wheat_Cut_Path', [(10.0, 1.4), (10.4, 5.0), (9.0, 9.8), (7.8, 14.0)], 2.2, .10, M['dirt2'])

ico('Right_Grassy_Hill', (19.0, 5.2, 1.1), 1.0, M['grass2'], scale=(8.4, 7.2, 2.1), sub=2)

# -----------------------------------------------------------------------------
# Combined low-poly cobblestone walls
# -----------------------------------------------------------------------------
def append_cuboid(verts, faces, center, dims, yaw=0.0):
    cx, cy, cz = center
    dx, dy, dz = [d/2 for d in dims]
    local = [(-dx,-dy,-dz),(dx,-dy,-dz),(dx,dy,-dz),(-dx,dy,-dz),
             (-dx,-dy,dz),(dx,-dy,dz),(dx,dy,dz),(-dx,dy,dz)]
    c = math.cos(yaw); s = math.sin(yaw)
    base = len(verts)
    for x,y,z in local:
        verts.append((cx + x*c - y*s, cy + x*s + y*c, cz + z))
    faces.extend([(base+0,base+1,base+2,base+3), (base+4,base+7,base+6,base+5),
                  (base+0,base+4,base+5,base+1), (base+1,base+5,base+6,base+2),
                  (base+2,base+6,base+7,base+3), (base+3,base+7,base+4,base+0)])


def wall_mesh(name, points, spacing=.72, seed=0):
    rng = random.Random(SEED + seed)
    verts=[]; faces=[]; mats=[]
    stone_index = 0
    for si in range(len(points)-1):
        p0 = Vector((points[si][0], points[si][1], 0))
        p1 = Vector((points[si+1][0], points[si+1][1], 0))
        d = p1-p0
        L = d.length
        if L < 0.01:
            continue
        t = d.normalized(); yaw = math.atan2(t.y, t.x)
        count = max(1, int(L/spacing))
        for k in range(count+1):
            u = min(1.0, k/count)
            p = p0.lerp(p1,u)
            w = rng.uniform(.55,.86); dep=rng.uniform(.52,.74); h=rng.uniform(.42,.66)
            off = rng.uniform(-.08,.08)
            perp = Vector((-t.y,t.x,0))*off
            append_cuboid(verts,faces,(p.x+perp.x,p.y+perp.y,.23+h/2),(w,dep,h),yaw+rng.uniform(-.16,.16))
            mats.extend([stone_index%3]*6); stone_index += 1
            if (k + si) % 2 == 0:
                w2=w*rng.uniform(.70,.92); d2=dep*rng.uniform(.70,.92); h2=rng.uniform(.34,.50)
                append_cuboid(verts,faces,(p.x-perp.x*.4,p.y-perp.y*.4,.23+h+.05+h2/2),(w2,d2,h2),yaw+rng.uniform(-.2,.2))
                mats.extend([stone_index%3]*6); stone_index += 1
    return mesh_obj(name,verts,faces,[M['stone1'],M['stone2'],M['stone3']],mats)

wall_mesh('Wall_UpperLeft_Bottom', [(-26, 12.2),(-17,11.8),(-8,11.5),(-3.0,11.4)], seed=11)
wall_mesh('Wall_House_Back', [(-24,22.0),(-18,22.8),(-10,22.7),(-5.0,22.0)], seed=12)
wall_mesh('Wall_Center_Left', [(-2.6,12.0),(-2.8,18.5),(-2.6,27.2)], seed=13)
wall_mesh('Wall_Center_Right', [(0.3,12.0),(0.6,18.4),(0.8,27.0)], seed=14)
wall_mesh('Wall_Pasture_Top', [(-10.5,-7.2),(-2.0,-7.0),(6.0,-7.1),(12.5,-8.1)], seed=15)
wall_mesh('Wall_LowerLeft_West', [(-22.0,-23.5),(-21.8,-16.0),(-21.2,-8.6)], seed=16)
wall_mesh('Wall_LowerLeft_East', [(-16.4,-23.0),(-16.0,-15.8),(-15.0,-8.5)], seed=17)
wall_mesh('Wall_LowerLeft_Top', [(-21.3,-8.5),(-18.5,-7.9),(-15.0,-8.5),(-10.8,-7.3)], seed=18)
wall_mesh('Wall_Right_Diagonal', [(12.4,-8.0),(15.0,-10.0),(18.0,-12.0)], seed=19)
wall_mesh('Wall_Wheat_Upper', [(2.0,12.3),(7.0,13.0),(11.4,14.4)], seed=20)

# -----------------------------------------------------------------------------
# Wheat fields as one low-poly mesh
# -----------------------------------------------------------------------------
def wheat_mesh(name, points, seed=0):
    rng = random.Random(SEED + 100 + seed)
    verts=[]; faces=[]; fm=[]
    for idx,(x,y) in enumerate(points):
        for q in range(2):
            ox = rng.uniform(-.18,.18) + (q*.16-.08)
            oy = rng.uniform(-.18,.18)
            z0 = .10
            r = rng.uniform(.13,.22)
            h = rng.uniform(.72,1.05) * (1.0 if q==0 else .82)
            base=len(verts)
            verts.extend([(x+ox-r,y+oy-r,z0),(x+ox+r,y+oy-r,z0),(x+ox+r,y+oy+r,z0),(x+ox-r,y+oy+r,z0),(x+ox,y+oy,z0+h)])
            faces.extend([(base,base+1,base+2,base+3),(base,base+4,base+1),(base+1,base+4,base+2),(base+2,base+4,base+3),(base+3,base+4,base)])
            mi = 0 if rng.random()<.62 else 1
            fm.extend([mi]*5)
    return mesh_obj(name,verts,faces,[M['wheat1'],M['wheat2']],fm)

wheat_pts=[]
rng = random.Random(SEED+101)
cx,cy=19.0,5.2
for ri,r in enumerate([10.1,11.0,12.4,13.3,14.8,15.7,17.1,18.0,19.4,20.3,21.7,22.6]):
    for deg in range(28, 151, 5):
        a=math.radians(deg)
        x=cx+r*math.cos(a)+rng.uniform(-.12,.12)
        y=cy+r*math.sin(a)+rng.uniform(-.12,.12)
        if x*x+y*y < 27.2*27.2:
            wheat_pts.append((x,y))
    for deg in range(-102, 10, 5):
        a=math.radians(deg)
        x=cx+r*math.cos(a)+rng.uniform(-.12,.12)
        y=cy+r*math.sin(a)+rng.uniform(-.12,.12)
        if x*x+y*y < 27.0*27.0:
            wheat_pts.append((x,y))
for x in [2.2,3.0,3.8,4.6,5.4,6.2,7.0,7.8]:
    for y in [17.0,18.0,19.0,20.0,21.0,22.0,23.0,24.0,25.0,26.0]:
        if x*x+y*y < 27.0*27.0:
            wheat_pts.append((x+rng.uniform(-.12,.12),y+rng.uniform(-.12,.12)))
wheat_mesh('Wheat_Fields', wheat_pts, seed=1)

# -----------------------------------------------------------------------------
# Farm house (back-left)
# -----------------------------------------------------------------------------
HX, HY = -13.8, 20.5
box('FarmHouse_Body',(HX,HY,1.55),(5.3,3.9,3.0),M['wood2'],bev=.07)
box('FarmHouse_Porch',(HX,HY-2.25,.45),(5.0,1.2,.35),M['wood'],bev=.05)
for i in range(3):
    box(f'FarmHouse_Step_{i}',(HX,HY-2.9-i*.35,.22+i*.10),(2.3,.45,.20),M['wood2'],bev=.03)
verts=[(HX-3.1,HY-2.2,3.0),(HX+3.1,HY-2.2,3.0),(HX,HY-2.2,4.8),
       (HX-3.1,HY+2.2,3.0),(HX+3.1,HY+2.2,3.0),(HX,HY+2.2,4.8)]
faces=[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)]
mesh_obj('FarmHouse_GableRoof',verts,faces,[M['roof']])
for j in range(-3,4):
    box(f'Roof_Rib_{j}',(HX+j*.75,HY,3.62),(0.10,4.65,0.12),M['dark'],rot=(0,math.radians(29 if j<0 else -29),0),bev=.01)
box('FarmHouse_Door',(HX,HY-1.98,1.45),(1.0,.18,1.9),M['wood'],bev=.04)
for xx in (HX-1.65,HX+1.65):
    box('FarmWindow_Frame_'+str(xx),(xx,HY-2.02,1.8),(1.05,.15,1.0),M['dark'],bev=.03)
    box('FarmWindow_Glow_'+str(xx),(xx,HY-2.11,1.8),(.78,.04,.72),M['window'],bev=.01)
    box('FarmWindow_V_'+str(xx),(xx,HY-2.13,1.8),(.07,.04,.75),M['wood'],bev=.01)
    box('FarmWindow_H_'+str(xx),(xx,HY-2.13,1.8),(.80,.04,.07),M['wood'],bev=.01)

# -----------------------------------------------------------------------------
# Trees and bushes
# -----------------------------------------------------------------------------
def tree(name,x,y,s=1.0,seed=0):
    rng=random.Random(SEED+300+seed)
    cyl(name+'_Trunk',(x,y,.75*s),.22*s,1.45*s,M['wood'],vertices=8)
    clusters=[(0,0,2.1,.82),(-.55,.10,1.65,.68),(.52,.08,1.65,.72),(-.20,-.48,1.63,.64),(.26,.45,1.72,.62)]
    for i,(ox,oy,zz,rr) in enumerate(clusters):
        mat=[M['leaf1'],M['leaf2'],M['leaf3']][(i+seed)%3]
        ico(f'{name}_Leaf_{i}',(x+ox*s,y+oy*s,zz*s),rr*s,mat,
            scale=(rng.uniform(.75,1.15),rng.uniform(.75,1.15),rng.uniform(1.0,1.45)),sub=1)


def bush(name,x,y,s=.7,seed=0):
    rng=random.Random(SEED+500+seed)
    for i,(ox,oy) in enumerate([(0,0),(.45,.10),(-.38,.08),(.10,-.35)]):
        ico(f'{name}_{i}',(x+ox*s,y+oy*s,.52*s),.58*s,[M['leaf1'],M['leaf2'],M['leaf3']][(i+seed)%3],
            scale=(rng.uniform(.8,1.15),rng.uniform(.8,1.15),rng.uniform(.75,1.1)),sub=1)

TREE_POS=[(-24,20,1.4),(-20,23,1.15),(-18,19,1.0),(-8,23,1.2),(-5,20,1.0),
          (-25,-4,1.25),(-23,-9,1.0),(-22,-15,1.2),(-18,-12,1.05),(-14,-10,1.0),
          (15,-9,1.0),(18,-12,1.25),(22,-14,1.15),(25,-9,1.25),(26,18,1.2),(23,23,1.3),
          (7,15,1.0),(3,15,1.1)]
for i,(x,y,s) in enumerate(TREE_POS):
    tree(f'Tree_{i:02d}',x,y,s,i)

BUSH_POS=[(-17,22),(-11,22),(-9,18),(-6,17),(-21,18),(-24,-11),(-20,-9),(-17,-9),(-15,-13),
          (13,-8),(17,-10),(21,-12),(24,-6),(24,18),(20,22),(9,13),(4,13)]
for i,(x,y) in enumerate(BUSH_POS):
    bush(f'Bush_{i:02d}',x,y,.78,i)

# -----------------------------------------------------------------------------
# Hay bales in the lower pasture
# -----------------------------------------------------------------------------
def hay_bale(name,x,y,rot=0.0,scale=1.0):
    cyl(name,(x,y,.55*scale),.52*scale,.85*scale,M['hay'],vertices=10,rot=(math.pi/2,0,rot))
    cyl(name+'_EndA',(x,y-.45*scale,.55*scale),.53*scale,.05*scale,M['wheat1'],vertices=10,rot=(math.pi/2,0,rot))
    cyl(name+'_EndB',(x,y+.45*scale,.55*scale),.53*scale,.05*scale,M['wheat1'],vertices=10,rot=(math.pi/2,0,rot))

rng=random.Random(SEED+700)
HAY=[(-10,-14),(-6,-12),(-2,-13),(3,-12),(8,-14),(-12,-19),(-7,-21),(-2,-18),(4,-20),(10,-18),
     (-5,-25),(2,-24),(8,-23),(13,-19),(-13,-9),(-8,-9)]
for i,(x,y) in enumerate(HAY):
    hay_bale(f'Hay_{i:02d}',x+rng.uniform(-.4,.4),y+rng.uniform(-.4,.4),rng.uniform(-.4,.4),rng.uniform(.75,1.1))

# -----------------------------------------------------------------------------
# Carts, pumpkins, trough, barrels, scarecrow
# -----------------------------------------------------------------------------
def cart(name,x,y,yaw=0.0,pumpkins=False,scale=1.0):
    box(name+'_Bed',(x,y,.72*scale),(2.2*scale,1.25*scale,.35*scale),M['wood2'],rot=(0,0,yaw),bev=.05)
    for sx in (-1,1):
        ox = math.cos(yaw)*(sx*1.0*scale)
        oy = math.sin(yaw)*(sx*1.0*scale)
        box(name+f'_Side{sx}',(x+ox,y+oy,1.0*scale),(.14*scale,1.25*scale,.65*scale),M['wood'],rot=(0,0,yaw),bev=.025)
    for sy in (-.48,.48):
        ox = -math.sin(yaw)*(sy*scale); oy=math.cos(yaw)*(sy*scale)
        cyl(name+f'_Wheel{sy}',(x+ox,y+oy,.48*scale),.55*scale,.18*scale,M['dark'],vertices=10,rot=(0,math.pi/2,yaw))
    for sx in (-.55,.55):
        ox = math.cos(yaw)*(sx*scale) - math.sin(yaw)*(1.45*scale)
        oy = math.sin(yaw)*(sx*scale) + math.cos(yaw)*(1.45*scale)
        box(name+f'_Handle{sx}',(x+ox,y+oy,.63*scale),(.09*scale,2.1*scale,.09*scale),M['wood'],rot=(0,0,yaw),bev=.015)
    if pumpkins:
        rng=random.Random(int((x+40)*100+(y+40)*10))
        for i in range(8):
            lx=rng.uniform(-.75,.75)*scale; ly=rng.uniform(-.35,.35)*scale
            ox=math.cos(yaw)*lx-math.sin(yaw)*ly; oy=math.sin(yaw)*lx+math.cos(yaw)*ly
            ico(name+f'_Pumpkin{i}',(x+ox,y+oy,1.20*scale),.26*scale,M['pumpkin'],scale=(1,1,.8),sub=1)

cart('PumpkinCart_A',(3.0,14.0),yaw=.10,pumpkins=True,scale=.95)
cart('PumpkinCart_B',(5.6,14.9),yaw=-.22,pumpkins=True,scale=.80)
cart('PastureCart',(0.5,-24.0),yaw=.18,pumpkins=False,scale=.88)

box('WaterTrough_Base',(-4.6,17.0,.55),(2.2,1.0,.75),M['trough'],rot=(0,0,.05),bev=.12)
box('WaterTrough_Water',(-4.6,17.0,.96),(1.65,.60,.07),M['water'],rot=(0,0,.05),bev=.02)
for i,(x,y) in enumerate([(-3.4,15.2),(-4.3,14.8),(-2.8,16.3)]):
    cyl(f'Barrel_{i}',(x,y,.62),.43,1.0,M['wood2'],vertices=10)
    cyl(f'BarrelRingA_{i}',(x,y,.32),.45,.08,M['dark'],vertices=10)
    cyl(f'BarrelRingB_{i}',(x,y,.92),.45,.08,M['dark'],vertices=10)

sx,sy=5.0,23.4
cyl('Scarecrow_Post',(sx,sy,1.25),.10,2.5,M['wood'],vertices=8)
box('Scarecrow_Arms',(sx,sy,1.95),(2.4,.12,.12),M['wood'],bev=.02)
ico('Scarecrow_Head',(sx,sy,2.62),.42,M['hay'],scale=(.9,.9,1.0),sub=1)
box('Scarecrow_Body',(sx,sy,1.55),(1.0,.22,1.2),M['wood2'],bev=.03)
box('Scarecrow_HatBrim',(sx,sy,3.0),(1.25,.7,.12),M['dark'],bev=.03)
cyl('Scarecrow_HatTop',(sx,sy,3.22),.38,.45,M['dark'],vertices=8)

for i in range(4):
    x=-20.3+i*1.2
    box(f'BrokenFence_Post_{i}',(x,-10.4,.65),(.16,.16,1.3),M['wood'],rot=(0,0,random.uniform(-.15,.15)),bev=.02)
box('BrokenFence_Rail_A',(-18.8,-10.4,.85),(4.0,.14,.14),M['wood'],rot=(0,0,.04),bev=.02)
box('BrokenFence_Rail_B',(-18.4,-10.4,.45),(2.0,.14,.14),M['wood'],rot=(0,0,-.18),bev=.02)

rng=random.Random(SEED+900)
for i in range(34):
    a=rng.uniform(0,2*math.pi); r=rng.uniform(22.5,27.0)
    x=r*math.cos(a); y=r*math.sin(a)
    if (x-19)**2+(y-5)**2 < 45:
        continue
    ico(f'TopRock_{i:02d}',(x,y,.35),rng.uniform(.25,.55),[M['stone1'],M['stone2'],M['stone3']][i%3],
        scale=(rng.uniform(.8,1.4),rng.uniform(.7,1.3),rng.uniform(.6,1.0)),sub=1)

# -----------------------------------------------------------------------------
# Mesh cleanup: merge doubles and recalc normals
# -----------------------------------------------------------------------------
for obj in list(bpy.context.scene.objects):
    if obj.type != 'MESH':
        continue
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    try:
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
        if bm.faces:
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    except Exception:
        pass
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()

# -----------------------------------------------------------------------------
# Lighting and render cameras
# -----------------------------------------------------------------------------
def look_at(obj, target=(0,0,0)):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z','Y').to_euler()

bpy.ops.object.light_add(type='AREA', location=(-25,-30,48))
key=bpy.context.object; key.name='Key_Area'; key.data.energy=1500; key.data.shape='DISK'; key.data.size=28
look_at(key,(0,0,0))
bpy.ops.object.light_add(type='AREA', location=(30,18,30))
fill=bpy.context.object; fill.name='Fill_Area'; fill.data.energy=800; fill.data.size=24
look_at(fill,(0,0,0))
bpy.ops.object.light_add(type='SUN', location=(0,0,35))
sun=bpy.context.object; sun.name='Sun'; sun.data.energy=1.8; sun.rotation_euler=(math.radians(30),math.radians(-25),math.radians(-35))

bpy.ops.object.camera_add(location=(44,-54,49))
cam=bpy.context.object; cam.name='Camera'; scene.camera=cam; cam.data.lens=55
look_at(cam,(0,1,-1.2))

scene.render.resolution_x=900; scene.render.resolution_y=900

def render_view(filename, loc, target=(0,0,-1), lens=55, ortho=None):
    cam.location=loc
    look_at(cam,target)
    if ortho:
        cam.data.type='ORTHO'; cam.data.ortho_scale=ortho
    else:
        cam.data.type='PERSP'; cam.data.lens=lens
    scene.render.filepath=os.path.join(OUT,filename)
    bpy.ops.render.render(write_still=True)

render_view('preview_perspective.png',(44,-54,49),(0,1,-1.2),55)
render_view('preview_top.png',(0,0,72),(0,0,0),55,64)
render_view('preview_front.png',(0,-67,24),(0,0,-1.5),60)
render_view('preview_back.png',(0,67,24),(0,0,-1.5),60)
render_view('preview_left.png',(-67,0,24),(0,0,-1.5),60)
render_view('preview_right.png',(67,0,24),(0,0,-1.5),60)

cam.data.type='PERSP'; cam.data.lens=55; cam.location=(44,-54,49); look_at(cam,(0,1,-1.2))

# -----------------------------------------------------------------------------
# Save / export / report
# -----------------------------------------------------------------------------
blend_path=os.path.join(OUT,'farmer2.blend')
glb_path=os.path.join(OUT,'farmer2.glb')
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
try:
    bpy.ops.export_scene.gltf(filepath=glb_path, export_format='GLB', export_apply=True)
except TypeError:
    bpy.ops.export_scene.gltf(filepath=glb_path, export_format='GLB')

objs=[o for o in scene.objects if o.type=='MESH']
verts=sum(len(o.data.vertices) for o in objs)
polys=sum(len(o.data.polygons) for o in objs)
with open(os.path.join(OUT,'farmer2_report.txt'),'w',encoding='utf-8') as f:
    f.write('Farmer 2 map recreation\n')
    f.write('Built procedurally in Blender headless / GitHub Actions\n')
    f.write('Reference layout: circular floating island, cobble-separated fields, upper-left farmhouse, right wheat hill, pasture, alleys, carts, hay, trees.\n')
    f.write(f'Seed: {SEED}\n')
    f.write(f'Mesh objects: {len(objs)}\n')
    f.write(f'Vertices: {verts}\n')
    f.write(f'Polygons: {polys}\n')
    f.write('Approx map diameter: 57 m; cliff depth: 6 m\n')
    f.write('Team split line and battle units intentionally omitted because they are gameplay overlays/units, not terrain.\n')

print('FARMER2_BUILD_OK')
print(blend_path)
print(glb_path)
