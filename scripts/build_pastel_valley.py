import bpy, math, random, os, bmesh
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'output_pastel_valley')
os.makedirs(OUT, exist_ok=True)
SEED = 8122026
random.seed(SEED)

# -----------------------------------------------------------------------------
# Clean scene
# -----------------------------------------------------------------------------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
try:
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'Medium High Contrast'
    scene.view_settings.exposure = 0.15
    scene.view_settings.gamma = 1.0
except Exception:
    pass
scene.world.color = (0.68, 0.87, 0.90)
try:
    scene.eevee.use_gtao = True
    scene.eevee.gtao_distance = 6
    scene.eevee.gtao_factor = 1.2
    scene.eevee.use_soft_shadows = True
    scene.eevee.shadow_cube_size = '2048'
    scene.eevee.shadow_cascade_size = '2048'
except Exception:
    pass

# -----------------------------------------------------------------------------
# Materials
# -----------------------------------------------------------------------------
def mat(name, rgb, rough=.9, metal=0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    if p:
        p.inputs['Base Color'].default_value = (*rgb, 1)
        p.inputs['Roughness'].default_value = rough
        p.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*rgb, 1)
    return m

M = {
    'grass': mat('Grass_Pastel_YellowGreen', (0.56,0.67,0.25), .97),
    'grass_dark': mat('Grass_Shadow_Green', (0.30,0.43,0.22), .97),
    'grass_hill': mat('Grass_Hill', (0.50,0.62,0.31), .97),
    'tree1': mat('Pine_Muted_1', (0.34,0.48,0.30), .98),
    'tree2': mat('Pine_Muted_2', (0.42,0.55,0.34), .98),
    'tree3': mat('Pine_Muted_3', (0.28,0.40,0.29), .98),
    'trunk': mat('Trunk', (0.31,0.20,0.13), .95),
    'rock': mat('Rock_Light', (0.56,0.60,0.62), .95),
    'rock2': mat('Rock_BlueGray', (0.43,0.50,0.55), .95),
    'mountain': mat('Mountain_BlueGray', (0.60,0.70,0.71), .98),
    'mountain2': mat('Mountain_Cool', (0.51,0.63,0.67), .98),
    'snow': mat('Snow', (0.88,0.91,0.89), .98),
    'path': mat('Path_Sand', (0.78,0.72,0.48), .98),
    'church': mat('Church_Stone', (0.46,0.51,0.52), .96),
    'church2': mat('Church_Stone_Light', (0.57,0.60,0.59), .96),
    'roof': mat('Church_Roof', (0.22,0.28,0.30), .96),
    'roof2': mat('Roof_Highlight', (0.31,0.37,0.39), .96),
    'window': mat('Window_Dark', (0.11,0.16,0.17), .82),
    'door': mat('Door_Wood', (0.28,0.20,0.14), .92),
    'tent_blue': mat('Tent_Blue', (0.05,0.38,0.72), .9),
    'tent_pink': mat('Tent_Pink', (0.91,0.37,0.48), .9),
    'water': mat('Water_Cyan', (0.20,0.69,0.78), .55),
}

def assign(o, m):
    if hasattr(o.data, 'materials'):
        o.data.materials.clear(); o.data.materials.append(m)

def box(name, loc, dims, m, rot=(0,0,0), bevel=.04):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o=bpy.context.object; o.name=name; o.dimensions=dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(o,m)
    if bevel>0:
        mod=o.modifiers.new('Bevel','BEVEL'); mod.width=bevel; mod.segments=1
        mod.limit_method='ANGLE'
        bpy.context.view_layer.objects.active=o
        try: bpy.ops.object.modifier_apply(modifier=mod.name)
        except: pass
    return o

def cyl(name, loc, radius, depth, m, vertices=8, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    o=bpy.context.object; o.name=name; assign(o,m); return o

def cone(name, loc, r1, r2, depth, m, vertices=8, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=r1, radius2=r2, depth=depth, location=loc, rotation=rot)
    o=bpy.context.object; o.name=name; assign(o,m); return o

def ico(name, loc, radius, m, scale=(1,1,1), sub=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=radius, location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(o,m); return o

def mesh_obj(name, verts, faces, materials, face_mats=None):
    me=bpy.data.meshes.new(name+'_Mesh')
    me.from_pydata(verts,[],faces); me.update(); me.validate()
    o=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o)
    for mm in materials: me.materials.append(mm)
    if face_mats:
        for p,mi in zip(me.polygons,face_mats): p.material_index=mi
    return o

def ribbon(name, pts, width, z, m):
    verts=[]; faces=[]
    for i,p in enumerate(pts):
        v=Vector((p[0],p[1],z))
        if i==0: t=Vector((pts[1][0]-pts[0][0],pts[1][1]-pts[0][1],0)).normalized()
        elif i==len(pts)-1: t=Vector((pts[-1][0]-pts[-2][0],pts[-1][1]-pts[-2][1],0)).normalized()
        else: t=Vector((pts[i+1][0]-pts[i-1][0],pts[i+1][1]-pts[i-1][1],0)).normalized()
        p2=Vector((-t.y,t.x,0))*width*.5
        verts.extend([tuple(v+p2),tuple(v-p2)])
    for i in range(len(pts)-1):
        a=i*2; faces.append((a,a+1,a+3,a+2))
    return mesh_obj(name,verts,faces,[m])

# -----------------------------------------------------------------------------
# Ground valley
# -----------------------------------------------------------------------------
box('Main_Valley_Ground',(0,0,-0.6),(120,90,1.2),M['grass'],bevel=.6)
# raised edge slopes to avoid dead-flat perimeter
for i,(x,y,sx,sy) in enumerate([
    (-52,15,18,54),(52,14,18,56),(-30,38,38,18),(28,39,42,17),(-32,-40,44,12),(30,-41,48,12)
]):
    ico(f'Valley_Rim_{i}',(x,y,0.8),1.0,M['grass_hill'],scale=(sx,sy,2.0),sub=2)

# subtle center lift/roll
ico('Center_Ground_Roll',(8,7,-0.15),1,M['grass'],scale=(35,28,0.7),sub=2)

# -----------------------------------------------------------------------------
# Mountain ring – faceted low poly + snow caps
# -----------------------------------------------------------------------------
def mountain(name,x,y,z,sx,sy,sz,mat_base, snow=True, seed=0):
    rng=random.Random(SEED+seed)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1, location=(x,y,z))
    o=bpy.context.object; o.name=name; o.scale=(sx,sy,sz)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True); assign(o,mat_base)
    o.rotation_euler[2]=rng.uniform(-.3,.3)
    if snow:
        cone(name+'_SnowCap',(x,y,z+sz*.76),sx*.45,0,sz*.60,M['snow'],vertices=7,rot=(0,0,rng.uniform(-.3,.3)))
    return o

mounts=[
('Mtn_L1',-55,50,16,25,16,25,M['mountain2'],1),('Mtn_L2',-28,55,21,26,17,31,M['mountain'],2),
('Mtn_C',0,59,28,27,19,36,M['mountain'],3),('Mtn_R1',33,57,20,27,18,31,M['mountain'],4),
('Mtn_R2',58,50,18,26,17,27,M['mountain2'],5),('Mtn_farL',-77,47,18,32,20,26,M['mountain2'],6),
('Mtn_farR',79,44,19,32,20,28,M['mountain2'],7)
]
for n,x,y,z,sx,sy,sz,mm,seed in mounts: mountain(n,x,y,z,sx,sy,sz,mm,True,seed)

# distant cyan waterfall streak
ribbon('Distant_Waterfall',[(-13,52),(-11,47),(-9,43),(-8,39)],2.4,12.0,M['water'])

# -----------------------------------------------------------------------------
# Tree prototypes and forests
# -----------------------------------------------------------------------------
def pine(name,x,y,s=1.0,seed=0):
    rng=random.Random(SEED+2000+seed)
    cyl(name+'_Trunk',(x,y,0.75*s),.18*s,1.5*s,M['trunk'],vertices=6)
    mats=[M['tree1'],M['tree2'],M['tree3']]
    cone(name+'_Low',(x,y,1.55*s),1.18*s,0.15*s,1.70*s,mats[seed%3],vertices=7)
    cone(name+'_Mid',(x,y,2.45*s),.95*s,0.10*s,1.55*s,mats[(seed+1)%3],vertices=7)
    cone(name+'_Top',(x,y,3.25*s),.68*s,0.0,1.35*s,mats[(seed+2)%3],vertices=7)
    return name

# tree placement ring, leaving central field open
rng=random.Random(SEED+3000)
tree_count=0
for side in range(4):
    pass
# left/right forest bands
for x0,x1,y0,y1,n in [(-58,-35,-38,38,95),(35,58,-38,38,95),(-35,35,27,43,110)]:
    for i in range(n):
        x=rng.uniform(x0,x1); y=rng.uniform(y0,y1)
        # preserve central church clearing and right small camp
        if (x+3)**2+(y-19)**2 < 95: continue
        s=rng.uniform(.70,1.42)
        pine(f'Pine_{tree_count:03d}',x,y,s,tree_count); tree_count+=1
# foreground edge framing
for i in range(38):
    x=rng.uniform(-58,58); y=rng.uniform(-43,-34)
    if -24<x<24 and rng.random()<.60: continue
    s=rng.uniform(.80,1.45); pine(f'Pine_{tree_count:03d}',x,y,s,tree_count); tree_count+=1
# sparse mid trees
for i in range(42):
    x=rng.uniform(-42,42); y=rng.uniform(-5,30)
    if abs(x)<25 and y<20: continue
    s=rng.uniform(.65,1.1); pine(f'Pine_{tree_count:03d}',x,y,s,tree_count); tree_count+=1

# one round deciduous tree left as in reference
cyl('RoundTree_Trunk',(-33,-3,1.2),.36,2.4,M['trunk'],vertices=7)
ico('RoundTree_Crown',(-33,-3,3.2),1.9,M['tree2'],scale=(1.4,1.2,1.1),sub=1)
ico('RoundTree_Crown2',(-34.2,-2.7,3.1),1.2,M['tree1'],scale=(1.1,1.0,.9),sub=1)

# -----------------------------------------------------------------------------
# Church and circular path
# -----------------------------------------------------------------------------
CX,CY=-2,19
# looping path approaching church
pts=[]
for i in range(42):
    a=2*math.pi*i/41
    pts.append((CX+8.6*math.cos(a),CY+5.4*math.sin(a)))
ribbon('Church_Loop_Path',pts,1.15,.05,M['path'])
ribbon('Approach_Path',[(CX-1,CY-5),(CX-4,CY-9),(CX-9,CY-12),(CX-16,CY-14)],1.0,.06,M['path'])

# nave
box('Church_Nave',(CX,CY,2.05),(7.6,5.4,4.1),M['church'],bevel=.10)
# transept-ish side volume
box('Church_SideWing',(CX+3.3,CY+.2,1.72),(3.2,4.2,3.4),M['church2'],bevel=.08)
# gable roofs
roof_verts=[(-4,-3,0),(4,-3,0),(0,-3,2.1),(-4,3,0),(4,3,0),(0,3,2.1)]
roof_faces=[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)]
o=mesh_obj('Church_Main_Roof',[(x+CX,y+CY,z+4.05) for x,y,z in roof_verts],roof_faces,[M['roof']])
# tower
box('Church_Tower',(CX-2.9,CY-.2,4.1),(2.5,2.6,7.0),M['church2'],bevel=.08)
cone('Church_Spire',(CX-2.9,CY-.2,8.7),2.05,.05,3.5,M['roof'],vertices=6)
# tower cap / small finial
cyl('Church_Finial',(CX-2.9,CY-.2,10.55),.10,.7,M['roof'],vertices=6)
box('Church_Cross_H',(CX-2.9,CY-.2,10.75),(.85,.10,.11),M['roof'],bevel=.01)
box('Church_Cross_V',(CX-2.9,CY-.2,10.75),(.10,.10,.95),M['roof'],bevel=.01)
# front door and windows
box('Church_Door',(CX,CY-2.74,1.45),(1.4,.16,2.45),M['door'],bevel=.08)
for xx in [CX-2.2,CX+2.2]:
    box(f'Church_Window_{xx}',(xx,CY-2.76,2.55),(1.0,.12,1.75),M['window'],bevel=.15)
for zz in [3.8,5.7]:
    box(f'Tower_Window_{zz}',(CX-2.9,CY-1.52,zz),(.70,.10,1.25),M['window'],bevel=.12)
# gravestones/markers
for i in range(24):
    a=rng.uniform(0,2*math.pi); rr=rng.uniform(7.5,13.0)
    x=CX+math.cos(a)*rr; y=CY+math.sin(a)*rr*.65
    if y<CY-4: continue
    box(f'Grave_{i:02d}',(x,y,.45),(.42,.30,.9),M['rock2'],rot=(0,0,rng.uniform(-.15,.15)),bevel=.06)

# -----------------------------------------------------------------------------
# Camps: blue left foreground / pink right midground
# -----------------------------------------------------------------------------
def tent(name,x,y,m,scale=1.0,yaw=0):
    verts=[(-1,-.8,0),(1,-.8,0),(1,.8,0),(-1,.8,0),(0,-.8,1.25),(0,.8,1.25)]
    faces=[(0,1,4),(3,5,2),(0,3,2,1),(0,4,5,3),(1,2,5,4)]
    c=math.cos(yaw); s=math.sin(yaw)
    vv=[]
    for px,py,pz in verts:
        px*=scale;py*=scale;pz*=scale
        vv.append((x+px*c-py*s,y+px*s+py*c,.08+pz))
    return mesh_obj(name,vv,faces,[m])

blue_pos=[(-31,-19),(-26,-18),(-21,-17),(-34,-24),(-28,-24),(-22,-23),(-17,-21),(-30,-29)]
for i,(x,y) in enumerate(blue_pos): tent(f'BlueTent_{i:02d}',x,y,M['tent_blue'],.9,rng.uniform(-.25,.25))
pink_pos=[(31,21),(35,22),(39,20),(34,17),(40,16)]
for i,(x,y) in enumerate(pink_pos): tent(f'PinkTent_{i:02d}',x,y,M['tent_pink'],.75,rng.uniform(-.25,.25))

# -----------------------------------------------------------------------------
# Rocks scattered in meadow
# -----------------------------------------------------------------------------
for i in range(58):
    x=rng.uniform(-48,48); y=rng.uniform(-32,30)
    if (x-CX)**2+(y-CY)**2<120: continue
    if abs(x)>38 and rng.random()<.45: continue
    rr=rng.uniform(.28,1.0)
    ico(f'Rock_{i:02d}',(x,y,.15+rr*.35),rr,[M['rock'],M['rock2']][i%2],scale=(rng.uniform(.8,1.5),rng.uniform(.7,1.25),rng.uniform(.55,.95)),sub=1)

# -----------------------------------------------------------------------------
# Cleanup normals
# -----------------------------------------------------------------------------
for obj in scene.objects:
    if obj.type!='MESH': continue
    bm=bmesh.new(); bm.from_mesh(obj.data)
    try:
        bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-6)
        if bm.faces: bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    except: pass
    bm.to_mesh(obj.data); bm.free(); obj.data.update()

# -----------------------------------------------------------------------------
# Lighting
# -----------------------------------------------------------------------------
def look_at(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

bpy.ops.object.light_add(type='SUN', location=(-20,-20,50))
sun=bpy.context.object; sun.name='Sun'; sun.data.energy=2.0
sun.rotation_euler=(math.radians(28),math.radians(-18),math.radians(-35))
try: sun.data.angle=math.radians(8)
except: pass
bpy.ops.object.light_add(type='AREA', location=(-25,-25,42))
key=bpy.context.object; key.name='Soft_Key'; key.data.energy=1150; key.data.size=38; look_at(key,(0,5,0))
bpy.ops.object.light_add(type='AREA', location=(35,12,28))
fill=bpy.context.object; fill.name='Soft_Fill'; fill.data.energy=650; fill.data.size=32; look_at(fill,(0,5,0))

# -----------------------------------------------------------------------------
# Cameras / renders
# -----------------------------------------------------------------------------
bpy.ops.object.camera_add(location=(0,-75,42))
cam=bpy.context.object; cam.name='Camera'; scene.camera=cam; cam.data.lens=52

def render(name,loc,target=(0,11,2),lens=52):
    cam.data.type='PERSP'; cam.data.lens=lens; cam.location=loc; look_at(cam,target)
    scene.render.filepath=os.path.join(OUT,name); bpy.ops.render.render(write_still=True)

render('preview_main.png',(0,-76,43),(0,11,3),52)
render('preview_left.png',(-34,-66,36),(-2,13,3),55)
render('preview_right.png',(34,-66,36),(0,13,3),55)
render('preview_high.png',(0,-54,60),(0,10,0),58)

# -----------------------------------------------------------------------------
# Save + GLB
# -----------------------------------------------------------------------------
cam.location=(0,-76,43); look_at(cam,(0,11,3))
blend=os.path.join(OUT,'pastel_valley.blend')
glb=os.path.join(OUT,'pastel_valley.glb')
bpy.ops.wm.save_as_mainfile(filepath=blend)
try:
    bpy.ops.export_scene.gltf(filepath=glb,export_format='GLB',export_apply=True)
except TypeError:
    bpy.ops.export_scene.gltf(filepath=glb,export_format='GLB')

objs=[o for o in scene.objects if o.type=='MESH']
with open(os.path.join(OUT,'report.txt'),'w',encoding='utf-8') as f:
    f.write('Pastel low-poly valley map\n')
    f.write('Reference target: pale yellow-green battlefield, dense muted pines, cool mountain ring, central church, scattered rocks, blue/pink camps.\n')
    f.write(f'Mesh objects: {len(objs)}\n')
    f.write(f'Trees: {tree_count}\n')
    f.write(f'Vertices: {sum(len(o.data.vertices) for o in objs)}\n')
    f.write(f'Polygons: {sum(len(o.data.polygons) for o in objs)}\n')
print('PASTEL_VALLEY_BUILD_OK')
