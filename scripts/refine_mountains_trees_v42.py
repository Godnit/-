import bpy, os, math, random
from mathutils import Vector

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'output_classic_reference_v42')
os.makedirs(OUT,exist_ok=True)
scene=bpy.context.scene
scene.render.resolution_x=1024
scene.render.resolution_y=576
scene.render.resolution_percentage=100
rng=random.Random(420826)
CX,CY=0.0,48.0

# -----------------------------------------------------------------------------
# V42 goals:
# 1) Remove the busy tiny-triangle mountain surface from V41.
# 2) Build broad, readable mountain masses arranged on a curved rear arc.
# 3) Enlarge the rear/mountain-side pines so they are varied but never tiny.
# 4) Preserve the accepted floating island and the rest of the map.
# -----------------------------------------------------------------------------
for o in list(scene.objects):
    if o.name.startswith('Mountain'):
        bpy.data.objects.remove(o,do_unlink=True)


def make_mat(name,rgb,rough=.94):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    if p:
        p.inputs['Base Color'].default_value=(*rgb,1.0)
        if 'Roughness' in p.inputs:
            p.inputs['Roughness'].default_value=rough
    m.diffuse_color=(*rgb,1.0)
    return m

# broad pastel stone palette: few colors, no checkerboard/triangle mosaic
mat_grassrock=make_mat('MountainBaseGreenV42',(0.39,0.47,0.30))
mat_low=make_mat('MountainStoneLowV42',(0.48,0.54,0.53))
mat_mid=make_mat('MountainStoneMidV42',(0.58,0.64,0.63))
mat_high=make_mat('MountainStoneHighV42',(0.69,0.74,0.72))
mat_snow=make_mat('MountainSnowV42',(0.84,0.87,0.84))
mat_shadow=make_mat('MountainShadowV42',(0.40,0.46,0.47))
MATS=[mat_grassrock,mat_low,mat_mid,mat_high,mat_snow,mat_shadow]


def build_mountain(name,cx,cy,rx,ry,h,seed,rot=0.0,snow=False):
    """Broad low-poly mountain with large faces instead of many tiny triangles."""
    rr=random.Random(seed)
    n=10
    # 4 rings: broad foot, lower shoulder, upper shoulder, ridge ring
    ring_scales=(1.00,0.73,0.43,0.18)
    ring_heights=(0.00,0.23,0.58,0.88)
    verts=[]
    for r,(sc,zf) in enumerate(zip(ring_scales,ring_heights)):
        for k in range(n):
            a=2*math.pi*k/n+rot
            # keep silhouette organic, but broad
            wob=1.0+rr.uniform(-0.08,0.08)
            tang=rr.uniform(-0.55,0.55) if r in (1,2) else rr.uniform(-0.25,0.25)
            x=cx+rx*sc*wob*math.cos(a)-tang*math.sin(a)
            y=cy+ry*sc*wob*math.sin(a)+tang*math.cos(a)
            z=max(0.02,h*zf+rr.uniform(-0.35,0.35) if r else 0.02)
            verts.append((x,y,z))

    # summit is a small irregular ridge, not one sharp pyramid tip
    top0=len(verts)
    verts.append((cx-rx*0.10*math.cos(rot),cy-ry*0.05*math.sin(rot),h*0.98))
    top1=len(verts)
    verts.append((cx+rx*0.13*math.cos(rot+0.6),cy+ry*0.08*math.sin(rot+0.6),h))
    top2=len(verts)
    verts.append((cx+rx*0.03*math.cos(rot+2.0),cy+ry*0.12*math.sin(rot+2.0),h*0.94))

    faces=[];fm=[]
    # Use mostly QUADS for the broad slopes. GLB may triangulate internally,
    # but Blender shading/materials keep them reading as large continuous faces.
    for r in range(3):
        a0=r*n;b0=(r+1)*n
        for k in range(n):
            j=(k+1)%n
            faces.append((a0+k,a0+j,b0+j,b0+k))
            if r==0:
                mi=0 if k%4 else 1
            elif r==1:
                mi=1 if k%3 else 2
            else:
                mi=2 if k%4 else 3
            fm.append(mi)

    # summit uses only ten broad triangles total
    r0=3*n
    tops=(top0,top1,top2)
    for k in range(n):
        j=(k+1)%n
        t=tops[(k//4)%3]
        faces.append((r0+k,r0+j,t))
        if snow and k in (0,1,4,5,8):
            fm.append(4)
        else:
            fm.append(3 if k%3 else 5)

    mesh=bpy.data.meshes.new(name+'_Mesh')
    mesh.from_pydata(verts,[],faces)
    mesh.validate();mesh.update()
    ob=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(ob)
    for m in MATS: mesh.materials.append(m)
    for p,mi in zip(mesh.polygons,fm):
        p.material_index=mi
        p.use_smooth=False
    return ob

# -----------------------------------------------------------------------------
# Curved mountain chain. Each mountain is a real volumetric terrain mass.
# Positions follow a rear semi-ellipse, so from above there is no straight wall.
# -----------------------------------------------------------------------------
mount_specs=[
    (23,15.5,19.0,14.0,16.0,0.10,False),
    (39,20.5,24.0,18.0,22.5,-0.08,True),
    (58,24.0,27.0,20.0,28.0,0.12,True),
    (78,19.5,23.0,17.5,23.0,-0.05,False),
    (98,27.0,30.0,21.0,31.0,0.08,True),
    (119,22.5,26.0,19.0,26.0,-0.12,True),
    (139,19.0,22.0,16.5,21.0,0.05,False),
    (156,14.0,18.0,13.0,15.5,-0.08,False),
]
for idx,(deg,rad_off,rx,ry,h,rot,snow) in enumerate(mount_specs):
    a=math.radians(deg)
    # ellipse follows rounded island back edge
    radx=106.0+rad_off
    rady=116.0+rad_off*0.72
    x=CX+radx*math.cos(a)
    y=CY+rady*math.sin(a)
    build_mountain('MountainV42_%02d'%idx,x,y,rx,ry,h,42000+idx,rot,snow)

# secondary rear silhouettes, fewer/larger faces, slightly pale for atmospheric depth
for idx,(deg,h) in enumerate(((48,16.0),(88,19.0),(130,15.5))):
    a=math.radians(deg)
    x=CX+142.0*math.cos(a)
    y=CY+148.0*math.sin(a)
    ob=build_mountain('MountainBackV42_%02d'%idx,x,y,21.0,16.0,h,42500+idx,0.0,idx==1)
    # keep them a touch muted
    ob.scale.z=0.92

# -----------------------------------------------------------------------------
# Rear tree correction. PineForest contains 54 verts per tree in this pipeline.
# Increase only trees near the mountain arc; preserve every tree center/location.
# -----------------------------------------------------------------------------
forest=bpy.data.objects.get('PineForest')
if forest is None or forest.type!='MESH':
    raise RuntimeError('PineForest missing')
if len(forest.data.vertices)%54!=0:
    raise RuntimeError('Unexpected PineForest topology')
vs=forest.data.vertices
pine_count=len(vs)//54
if pine_count!=993:
    raise RuntimeError('Expected 993 pines, got %d'%pine_count)

rr=random.Random(421993)
rear_scaled=0
for start in range(0,len(vs),54):
    block=vs[start:start+54]
    cx=sum(v.co.x for v in block)/54.0
    cy=sum(v.co.y for v in block)/54.0
    z0=min(v.co.z for v in block)
    # the previous rear trees were visually too small. This range ensures
    # variation without any tiny trees beside the mountains.
    if cy>82:
        factor=rr.uniform(1.18,1.34)
    elif cy>62:
        factor=rr.uniform(1.07,1.18)
    else:
        continue
    rear_scaled+=1
    for v in block:
        v.co.x=cx+(v.co.x-cx)*factor
        v.co.y=cy+(v.co.y-cy)*factor
        v.co.z=z0+(v.co.z-z0)*factor
forest.data.update()

# Keep accepted warm tree palette; slightly improve sky/grass harmony.
def tune(name,rgb):
    m=bpy.data.materials.get(name)
    if not m: return
    m.diffuse_color=(*rgb,1.0)
    if m.use_nodes:
        p=m.node_tree.nodes.get('Principled BSDF')
        if p:p.inputs['Base Color'].default_value=(*rgb,1.0)

tune('Grass',(0.57,0.64,0.29))
tune('Pine1',(0.25,0.39,0.21))
tune('Pine2',(0.35,0.50,0.24))
tune('Pine3',(0.44,0.59,0.28))

world=scene.world
if world:
    world.use_nodes=True
    bg=world.node_tree.nodes.get('Background')
    if bg:
        bg.inputs['Color'].default_value=(0.66,0.82,0.86,1.0)
        bg.inputs['Strength'].default_value=0.78
for o in scene.objects:
    if o.type=='LIGHT' and o.data.type=='SUN':
        o.data.energy=1.75
        o.data.angle=math.radians(18.0)
try:
    scene.view_settings.view_transform='Standard'
    scene.view_settings.look='Medium High Contrast'
except Exception:
    pass
scene.view_settings.exposure=0.10

# -----------------------------------------------------------------------------
# Render/export
# -----------------------------------------------------------------------------
def look_at(o,target):
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
cam=scene.camera
if cam is None: raise RuntimeError('Camera missing')
def render(name,loc,target,lens):
    cam.location=loc;cam.data.lens=lens;look_at(cam,target)
    scene.render.filepath=os.path.join(OUT,name)
    bpy.ops.render.render(write_still=True)

render('preview_main.png',(0,-520,235),(0,57,-1.5),40)
render('preview_mountains.png',(0,-150,78),(0,132,14),50)
render('preview_high.png',(0,-285,305),(0,60,-1.0),44)
render('preview_left.png',(-330,-285,150),(0,60,1.0),43)
render('preview_right.png',(330,-285,150),(0,60,1.0),43)
render('preview_closer.png',(0,-315,128),(0,60,3.5),42)
cam.location=(0,-520,235);cam.data.lens=40;look_at(cam,(0,57,-1.5))

blend=os.path.join(OUT,'classic_reference_v42.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'classic_reference_v42.glb'),export_format='GLB',export_apply=True)
with open(os.path.join(OUT,'report.txt'),'w',encoding='utf-8') as f:
    f.write('Classic Reference V42\n')
    f.write('Mountains: 8 broad front massifs + 3 rear masses on curved arc\n')
    f.write('Mountain surface: broad quads, minimal summit triangles, no dense triangle mosaic\n')
    f.write('Pine count: %d unchanged\n'%pine_count)
    f.write('Rear trees enlarged with varied size; centers unchanged; adjusted trees: %d\n'%rear_scaled)
    f.write('Floating island preserved from V40\n')
print('V42_OK',blend)
