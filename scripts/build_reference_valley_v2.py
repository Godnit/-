import bpy, math, random, os
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'output_reference_valley_v2')
os.makedirs(OUT, exist_ok=True)
SEED = 130826
random.seed(SEED)

# -----------------------------------------------------------------------------
# Scene reset / render
# -----------------------------------------------------------------------------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1536
scene.render.resolution_y = 864
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
try:
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'Medium High Contrast'
    scene.view_settings.exposure = 0.35
    scene.view_settings.gamma = 1.0
except Exception:
    pass
try:
    scene.eevee.use_gtao = True
    scene.eevee.gtao_distance = 5
    scene.eevee.gtao_factor = 0.75
    scene.eevee.use_soft_shadows = True
except Exception:
    pass

world = scene.world
world.use_nodes = True
bg = world.node_tree.nodes.get('Background')
bg.inputs['Color'].default_value = (0.72, 0.88, 0.90, 1.0)
bg.inputs['Strength'].default_value = 0.75

# -----------------------------------------------------------------------------
# Materials sampled toward the reference palette
# -----------------------------------------------------------------------------
def mat(name, rgb, rough=.95):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    if p:
        p.inputs['Base Color'].default_value = (*rgb, 1.0)
        p.inputs['Roughness'].default_value = rough
    m.diffuse_color = (*rgb, 1.0)
    return m

M = {
    'grass': mat('Grass_Reference', (0.710, 0.753, 0.431), .98),
    'grass_hill': mat('Grass_Hill', (0.620, 0.700, 0.390), .98),
    'tree_a': mat('Pine_Mint_A', (0.455, 0.610, 0.520), .98),
    'tree_b': mat('Pine_Mint_B', (0.505, 0.655, 0.555), .98),
    'tree_c': mat('Pine_Muted_C', (0.385, 0.535, 0.455), .98),
    'trunk': mat('Trunk_Muted', (0.325, 0.265, 0.180), .98),
    'mountain': mat('Mountain_Pale_Blue', (0.700, 0.815, 0.810), .99),
    'mountain_shadow': mat('Mountain_Shadow', (0.580, 0.735, 0.740), .99),
    'snow': mat('Mountain_Snow', (0.900, 0.925, 0.910), .99),
    'rock': mat('Rock_Pale', (0.600, 0.640, 0.655), .98),
    'rock2': mat('Rock_Cool', (0.500, 0.570, 0.590), .98),
    'path': mat('Path_Pale_Sand', (0.780, 0.735, 0.535), .98),
    'church': mat('Church_Stone', (0.485, 0.535, 0.535), .97),
    'church_light': mat('Church_Light_Stone', (0.610, 0.650, 0.630), .97),
    'roof': mat('Church_Roof', (0.265, 0.325, 0.330), .97),
    'window': mat('Church_Window', (0.105, 0.160, 0.175), .90),
    'door': mat('Church_Door', (0.345, 0.245, 0.170), .95),
    'blue': mat('Blue_Camp', (0.060, 0.420, 0.765), .92),
    'pink': mat('Pink_Camp', (0.915, 0.430, 0.500), .92),
    'pole': mat('Tent_Pole', (0.780, 0.770, 0.655), .95),
}

def assign(obj, material):
    if hasattr(obj.data, 'materials'):
        obj.data.materials.clear()
        obj.data.materials.append(material)

def bevel(obj, width=.04):
    if width <= 0: return obj
    mod = obj.modifiers.new('TinyBevel','BEVEL')
    mod.width = width
    mod.segments = 1
    mod.limit_method = 'ANGLE'
    bpy.context.view_layer.objects.active = obj
    try: bpy.ops.object.modifier_apply(modifier=mod.name)
    except Exception: pass
    return obj

def box(name, loc, dims, material, rot=(0,0,0), bev=.04):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o=bpy.context.object; o.name=name; o.dimensions=dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(o,material); bevel(o,bev); return o

def cyl(name, loc, radius, depth, material, vertices=8, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    o=bpy.context.object; o.name=name; assign(o,material); return o

def cone(name, loc, r1, r2, depth, material, vertices=8):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=r1, radius2=r2, depth=depth, location=loc)
    o=bpy.context.object; o.name=name; assign(o,material); return o

def ico(name, loc, radius, material, scale=(1,1,1), sub=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=radius, location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(o,material); return o

def mesh_obj(name, verts, faces, materials, face_mats=None):
    me=bpy.data.meshes.new(name+'_Mesh')
    me.from_pydata(verts,[],faces); me.validate(); me.update()
    o=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o)
    for mm in materials: me.materials.append(mm)
    if face_mats:
        for poly, mi in zip(me.polygons, face_mats): poly.material_index=mi
    return o

def ribbon(name, pts, width, z, material):
    verts=[]; faces=[]
    for i,p in enumerate(pts):
        v=Vector((p[0],p[1],z))
        if i==0: t=Vector((pts[1][0]-pts[0][0],pts[1][1]-pts[0][1],0)).normalized()
        elif i==len(pts)-1: t=Vector((pts[-1][0]-pts[-2][0],pts[-1][1]-pts[-2][1],0)).normalized()
        else: t=Vector((pts[i+1][0]-pts[i-1][0],pts[i+1][1]-pts[i-1][1],0)).normalized()
        perp=Vector((-t.y,t.x,0))*width*.5
        verts.extend([tuple(v+perp),tuple(v-perp)])
    for i in range(len(pts)-1):
        a=i*2; faces.append((a,a+1,a+3,a+2))
    return mesh_obj(name,verts,faces,[material])

# -----------------------------------------------------------------------------
# Wide continuous valley ground — no floating island, no visible edge
# -----------------------------------------------------------------------------
box('Valley_Ground',(0,8,-0.75),(190,132,1.5),M['grass'],bev=.35)
# soft rear/side hills under forest, kept low so the open field dominates
for i,(x,y,sx,sy,sz) in enumerate([
    (-62,34,38,34,3.5),(62,34,38,34,3.5),(-35,51,44,26,4.5),(25,52,52,26,4.2),
    (-78,5,20,55,3.0),(78,8,20,55,3.0)
]):
    ico('Valley_Hill_%02d'%i,(x,y,0.0),1,M['grass_hill'],scale=(sx,sy,sz),sub=2)

# -----------------------------------------------------------------------------
# Faceted mountain wall across background
# -----------------------------------------------------------------------------
def mountain_mesh(name, cx, cy, base_z, radius_x, depth_y, height, seed):
    rng=random.Random(SEED+seed)
    n=11
    verts=[]
    # bottom ring, middle ring, peak cluster
    for i in range(n):
        a=2*math.pi*i/n
        rx=radius_x*(0.88+rng.uniform(-.10,.10))
        ry=depth_y*(0.88+rng.uniform(-.12,.10))
        verts.append((cx+rx*math.cos(a), cy+ry*math.sin(a), base_z+rng.uniform(-.7,.5)))
    for i in range(n):
        a=2*math.pi*i/n + 0.10
        rx=radius_x*.53*(0.9+rng.uniform(-.12,.12))
        ry=depth_y*.55*(0.9+rng.uniform(-.12,.12))
        verts.append((cx+rx*math.cos(a), cy+ry*math.sin(a), base_z+height*.58+rng.uniform(-1.1,1.1)))
    peak1=len(verts); verts.append((cx+rng.uniform(-2.0,2.0),cy+rng.uniform(-1.0,1.0),base_z+height))
    peak2=len(verts); verts.append((cx+radius_x*.12,cy-depth_y*.03,base_z+height*.91))
    faces=[]; fm=[]
    for i in range(n):
        j=(i+1)%n
        faces.append((i,j,n+j,n+i)); fm.append((i+seed)%2)
        if i%2==0:
            faces.append((n+i,n+j,peak1)); fm.append((i+1+seed)%2)
        else:
            faces.append((n+i,n+j,peak2)); fm.append((i+1+seed)%2)
    o=mesh_obj(name,verts,faces,[M['mountain'],M['mountain_shadow']],fm)
    # snow cap as irregular low polygon cone, intentionally pale and broad
    cone(name+'_Snow',(cx,cy,base_z+height*.86),radius_x*.34,0,height*.28,M['snow'],vertices=7)
    return o

mountain_specs=[
    (-86,76,30,17,28),(-61,78,32,18,33),(-34,80,31,17,31),(-7,82,29,18,37),
    (22,81,34,19,34),(51,79,36,19,39),(82,76,32,18,31)
]
for i,(x,y,rx,dy,h) in enumerate(mountain_specs):
    mountain_mesh('Mountain_%02d'%i,x,y,-0.2,rx,dy,h,100+i)

# -----------------------------------------------------------------------------
# Low-poly pines, mostly framing the huge empty field
# -----------------------------------------------------------------------------
def pine(name,x,y,s=1.0,variant=0):
    cyl(name+'_Trunk',(x,y,.62*s),.14*s,1.24*s,M['trunk'],vertices=6)
    mats=[M['tree_a'],M['tree_b'],M['tree_c']]
    cone(name+'_L',(x,y,1.35*s),.88*s,.12*s,1.45*s,mats[variant%3],vertices=7)
    cone(name+'_M',(x,y,2.05*s),.70*s,.09*s,1.28*s,mats[(variant+1)%3],vertices=7)
    cone(name+'_T',(x,y,2.68*s),.48*s,0.0,1.10*s,mats[(variant+2)%3],vertices=7)

def inside_open_field(x,y):
    # broad ellipse deliberately much larger than previous version
    return ((x-4)/47.0)**2 + ((y-4)/34.0)**2 < 1.0

rng=random.Random(SEED+2000)
tree_id=0
# dense left and right border forests
for x0,x1,y0,y1,n in [(-82,-43,-35,57,135),(44,82,-34,57,135)]:
    for _ in range(n):
        x=rng.uniform(x0,x1); y=rng.uniform(y0,y1)
        if inside_open_field(x,y): continue
        pine('Pine_%03d'%tree_id,x,y,rng.uniform(.75,1.35),tree_id); tree_id+=1
# back forest belt with a central break around church and meadow
for _ in range(235):
    x=rng.uniform(-78,78); y=rng.uniform(32,66)
    # keep church meadow and a few clean gaps
    if ((x+13)/19)**2+((y-33)/11)**2 < 1.0: continue
    if x>20 and x<45 and y<43 and rng.random()<.32: continue
    pine('Pine_%03d'%tree_id,x,y,rng.uniform(.65,1.25),tree_id); tree_id+=1
# foreground corner framing only; central bottom remains open
for _ in range(70):
    side=-1 if rng.random()<.5 else 1
    x=rng.uniform(47,82)*side; y=rng.uniform(-39,-15)
    pine('Pine_%03d'%tree_id,x,y,rng.uniform(.85,1.35),tree_id); tree_id+=1
# sparse trees near back edges of the meadow
for _ in range(38):
    x=rng.uniform(-50,52); y=rng.uniform(18,38)
    if inside_open_field(x,y) and rng.random()<.72: continue
    pine('Pine_%03d'%tree_id,x,y,rng.uniform(.62,.95),tree_id); tree_id+=1

# single broadleaf tree on left like reference
cyl('RoundTree_Trunk',(-43,-6,1.1),.28,2.2,M['trunk'],vertices=7)
ico('RoundTree_Crown',(-43,-6,2.9),1.5,M['tree_b'],scale=(1.35,1.12,1.05),sub=1)
ico('RoundTree_Crown_2',(-44.0,-5.8,2.8),.85,M['tree_a'],scale=(1.1,1.0,.9),sub=1)

# -----------------------------------------------------------------------------
# Small distant church — intentionally small relative to the map
# -----------------------------------------------------------------------------
CX,CY=-13.0,30.5
# winding pale path
ribbon('Church_Path',[(-1,5),(-2,11),(-6,16),(-7,22),(-11,26),(CX,CY-3.0)],1.15,.055,M['path'])
ribbon('Church_Side_Path',[(CX,CY-2.8),(CX-7,CY-4.0),(CX-12,CY-3.0)],.72,.058,M['path'])

# nave/body
box('Church_Nave',(CX,CY,1.55),(6.3,4.1,3.1),M['church'],bev=.06)
# front apse / small side section
box('Church_Wing',(CX+2.5,CY+.2,1.35),(2.2,3.1,2.7),M['church_light'],bev=.05)
# low gable roof mesh
rv=[(-3.45,-2.3,0),(3.45,-2.3,0),(0,-2.3,1.55),(-3.45,2.3,0),(3.45,2.3,0),(0,2.3,1.55)]
rf=[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)]
mesh_obj('Church_Roof',[(x+CX,y+CY,z+3.05) for x,y,z in rv],rf,[M['roof']])
# modest tower, not oversized
box('Church_Tower',(CX-2.35,CY-.15,3.3),(1.75,1.9,5.1),M['church_light'],bev=.05)
cone('Church_Spire',(CX-2.35,CY-.15,6.75),1.35,.05,2.35,M['roof'],vertices=6)
cyl('Church_Finial',(CX-2.35,CY-.15,8.05),.055,.55,M['roof'],vertices=6)
# door and tiny dark windows
box('Church_Door',(CX,CY-2.08,1.1),(1.0,.10,1.75),M['door'],bev=.03)
for x in (CX-1.75,CX+1.75):
    box('Church_Window_'+str(x),(x,CY-2.11,1.85),(.58,.08,.95),M['window'],bev=.02)
box('Tower_Window',(CX-2.35,CY-1.10,4.15),(.50,.08,.72),M['window'],bev=.02)
# few gravestones near church
for i in range(14):
    a=rng.uniform(0,2*math.pi); r=rng.uniform(4.5,9.0)
    x=CX+math.cos(a)*r; y=CY+math.sin(a)*r*.65
    box('Grave_%02d'%i,(x,y,.28),(.32,.18,.56),M['rock2'],rot=(0,0,rng.uniform(-.2,.2)),bev=.03)

# -----------------------------------------------------------------------------
# Camps: blue front-left and pink far-right
# -----------------------------------------------------------------------------
def tent(name,x,y,material,yaw=0.0,s=.75):
    # triangular prism tent
    L=1.45*s; W=1.12*s; H=.72*s
    local=[(-L/2,-W/2,0),(L/2,-W/2,0),(0,-W/2,H),(-L/2,W/2,0),(L/2,W/2,0),(0,W/2,H)]
    c=math.cos(yaw); ss=math.sin(yaw)
    verts=[]
    for px,py,pz in local:
        verts.append((x+px*c-py*ss,y+px*ss+py*c,.05+pz))
    faces=[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)]
    mesh_obj(name,verts,faces,[material])
    # small ridge caps/pegs
    cyl(name+'_PoleA',(x-math.sin(yaw)*W*.52,y+math.cos(yaw)*W*.52,.42*s),.035*s,.9*s,M['pole'],vertices=6)
    cyl(name+'_PoleB',(x+math.sin(yaw)*W*.52,y-math.cos(yaw)*W*.52,.42*s),.035*s,.9*s,M['pole'],vertices=6)

blue_positions=[(-39,-25),(-31,-27),(-23,-26),(-36,-18),(-27,-18),(-18,-19),(-34,-10),(-25,-11)]
for i,(x,y) in enumerate(blue_positions): tent('BlueTent_%02d'%i,x,y,M['blue'],yaw=rng.uniform(-.3,.3),s=rng.uniform(.70,.86))
pink_positions=[(36,28),(41,29),(46,27),(39,23),(45,22),(50,24)]
for i,(x,y) in enumerate(pink_positions): tent('PinkTent_%02d'%i,x,y,M['pink'],yaw=rng.uniform(-.3,.3),s=rng.uniform(.63,.78))

# -----------------------------------------------------------------------------
# Sparse scattered rocks — not cluttered
# -----------------------------------------------------------------------------
rock_positions=[(-52,-18),(-45,-13),(-37,-4),(-28,1),(-18,-1),(-5,-8),(8,-14),(18,-9),(31,-13),(44,-6),
                (-48,8),(-32,13),(-18,11),(2,16),(17,12),(31,9),(48,13),(-55,22),(-25,23),(7,24),(23,22),(55,18)]
for i,(x,y) in enumerate(rock_positions):
    ico('Rock_%02d'%i,(x,y,.34),rng.uniform(.32,.70),M['rock'] if i%2==0 else M['rock2'],
        scale=(rng.uniform(.9,1.5),rng.uniform(.7,1.2),rng.uniform(.55,.9)),sub=1)

# -----------------------------------------------------------------------------
# Lighting: bright, soft, slightly hazy reference tone
# -----------------------------------------------------------------------------
def look_at(obj,target):
    direction=Vector(target)-obj.location
    obj.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()

bpy.ops.object.light_add(type='SUN', location=(-30,-45,55))
sun=bpy.context.object; sun.name='Soft_Sun'; sun.data.energy=2.1
sun.data.angle=math.radians(12)
sun.rotation_euler=(math.radians(29),math.radians(-20),math.radians(-30))

bpy.ops.object.light_add(type='AREA', location=(-25,-38,48))
area=bpy.context.object; area.name='Sky_Fill'; area.data.energy=850; area.data.size=45
look_at(area,(0,15,0))

# -----------------------------------------------------------------------------
# Cameras: main matches reference proportions closely
# -----------------------------------------------------------------------------
bpy.ops.object.camera_add(location=(0,-92,48))
cam=bpy.context.object; cam.name='Camera_Main'; scene.camera=cam
cam.data.type='PERSP'; cam.data.lens=48
look_at(cam,(0,18,3.3))

def render(name,loc,target,lens=48):
    cam.data.type='PERSP'; cam.data.lens=lens; cam.location=loc; look_at(cam,target)
    scene.render.filepath=os.path.join(OUT,name)
    bpy.ops.render.render(write_still=True)

render('preview_main.png',(0,-92,48),(0,18,3.3),48)
render('preview_closer.png',(-5,-82,42),(-7,21,3.0),52)
render('preview_left.png',(-54,-74,41),(0,18,3.0),52)
render('preview_right.png',(54,-74,41),(0,18,3.0),52)
render('preview_high.png',(0,-78,67),(0,15,1.0),52)

# restore main camera
cam.location=(0,-92,48); cam.data.lens=48; look_at(cam,(0,18,3.3))

# save/export
blend_path=os.path.join(OUT,'reference_valley_v2.blend')
glb_path=os.path.join(OUT,'reference_valley_v2.glb')
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
try:
    bpy.ops.export_scene.gltf(filepath=glb_path,export_format='GLB',export_apply=True)
except TypeError:
    bpy.ops.export_scene.gltf(filepath=glb_path,export_format='GLB')

mesh_objs=[o for o in scene.objects if o.type=='MESH']
with open(os.path.join(OUT,'report.txt'),'w',encoding='utf-8') as f:
    f.write('Reference Valley v2\n')
    f.write('Priority: match open area scale and pastel palette of supplied reference.\n')
    f.write('Ground: continuous 190m x 132m valley; no floating edge.\n')
    f.write('Palette sampled toward reference: grass ~ #B5C070, sky ~ #BFDFDF, trees muted mint/teal.\n')
    f.write('Church intentionally small and distant. Forest concentrated at sides/back.\n')
    f.write('Mesh objects: %d\n' % len(mesh_objs))
    f.write('Seed: %d\n' % SEED)
print('REFERENCE_VALLEY_V2_OK')
print(blend_path)
print(glb_path)
