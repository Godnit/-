import bpy, os, math, random
from mathutils import Vector

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'output_classic_reference_v39')
os.makedirs(OUT,exist_ok=True)
scene=bpy.context.scene
scene.render.resolution_x=1024
scene.render.resolution_y=576
scene.render.resolution_percentage=100
SEED=390826
rng=random.Random(SEED)

# -----------------------------------------------------------------------------
# Keep the accepted V38 trees/colors/rocks exactly. Replace only the flat ground
# and pull the background mountain set inward so everything belongs to one island.
# -----------------------------------------------------------------------------
for name in ('ValleyGround','BackgroundGround','Reference_BackgroundGround'):
    o=bpy.data.objects.get(name)
    if o:
        bpy.data.objects.remove(o,do_unlink=True)

# Current mountains were built far away only to fake a horizon. Move/scale the
# complete mountain group to the rear edge of the floating island while keeping
# their low-poly shape and materials.
for o in list(scene.objects):
    if not o.name.startswith('Mountain'):
        continue
    ox,oy,oz=o.location
    o.location.x=ox*0.52
    o.location.y=150.0+(oy-290.0)*0.30
    o.location.z=-10.0+(oz+16.0)*0.30
    o.scale.x*=0.60
    o.scale.y*=0.60
    o.scale.z*=0.78

# -----------------------------------------------------------------------------
# Floating island materials.
# Farmer-2-like construction: green top, earthy upper cliff, dark stone underside.
# -----------------------------------------------------------------------------
def make_mat(name,rgb):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    if p:
        p.inputs['Base Color'].default_value=(*rgb,1.0)
        p.inputs['Roughness'].default_value=.98
    m.diffuse_color=(*rgb,1.0)
    return m

grass=bpy.data.materials.get('Grass')
if grass is None:
    raise RuntimeError('Grass material missing')
earth1=make_mat('IslandEarth',(0.47,0.43,0.21))
earth2=make_mat('IslandEarthDark',(0.39,0.35,0.18))
stone1=make_mat('IslandStone',(0.31,0.36,0.38))
stone2=make_mat('IslandStoneDark',(0.25,0.30,0.32))
rockmat=bpy.data.materials.get('Rock') or stone1
rockmat2=bpy.data.materials.get('Rock2') or stone2

# -----------------------------------------------------------------------------
# Closed rounded island mesh.
# Top radius contains all accepted trees and the compressed rear mountains.
# The lower rings taper inward, making it look torn out of the ground rather
# than a flat sheet.
# -----------------------------------------------------------------------------
N=56
CX,CY=0.0,48.0
RX,RY=182.0,188.0

# deterministic irregular edge: still circular/rounded, not a perfect cylinder
edge=[]
for i in range(N):
    a=2*math.pi*i/N
    wob=1.0+rng.uniform(-0.018,0.018)
    edge.append((CX+RX*wob*math.cos(a),CY+RY*wob*math.sin(a)))

verts=[]
faces=[]
face_mats=[]

# top: center + two radial rings for broad low-poly triangulation
center_idx=len(verts);verts.append((CX,CY,0.02))
ring_mid=[]
ring_top=[]
for i,(ex,ey) in enumerate(edge):
    mx=CX+(ex-CX)*0.58;my=CY+(ey-CY)*0.58
    ring_mid.append(len(verts));verts.append((mx,my,0.02+rng.uniform(-0.015,0.015)))
for i,(ex,ey) in enumerate(edge):
    ring_top.append(len(verts));verts.append((ex,ey,-0.04+rng.uniform(-0.03,0.015)))
for i in range(N):
    j=(i+1)%N
    faces.append((center_idx,ring_mid[i],ring_mid[j]));face_mats.append(0)
    # alternate diagonal direction to avoid a fan-like appearance
    if i%2:
        faces.extend([(ring_mid[i],ring_top[i],ring_mid[j]),(ring_top[i],ring_top[j],ring_mid[j])])
    else:
        faces.extend([(ring_mid[i],ring_top[i],ring_top[j]),(ring_mid[i],ring_top[j],ring_mid[j])])
    face_mats.extend([0,0])

# cliff rings: near-vertical earth band, then tapered rock body
rings=[]
for scale,z in ((0.985,-2.7),(0.91,-8.4),(0.76,-15.2)):
    rr=[]
    for i,(ex,ey) in enumerate(edge):
        # extra small lower wob gives faceted broken-rock silhouette
        ang=2*math.pi*i/N
        k=scale*(1.0+rng.uniform(-0.025,0.025))
        x=CX+(ex-CX)*k
        y=CY+(ey-CY)*k
        rr.append(len(verts));verts.append((x,y,z+rng.uniform(-0.35,0.35)))
    rings.append(rr)

# top edge to earth ring
prev=ring_top
for band,rr in enumerate(rings):
    for i in range(N):
        j=(i+1)%N
        if (i+band)%2:
            faces.extend([(prev[i],prev[j],rr[i]),(prev[j],rr[j],rr[i])])
        else:
            faces.extend([(prev[i],prev[j],rr[j]),(prev[i],rr[j],rr[i])])
        if band==0:
            face_mats.extend([1 if i%3 else 2,1 if (i+1)%3 else 2])
        elif band==1:
            face_mats.extend([3 if i%2 else 4,3 if i%2 else 4])
        else:
            face_mats.extend([4 if i%2 else 3,4 if i%2 else 3])
    prev=rr

# pointed/rocky underside closure
bottom=len(verts);verts.append((CX,CY,-20.0))
last=rings[-1]
for i in range(N):
    j=(i+1)%N
    faces.append((last[i],last[j],bottom));face_mats.append(4 if i%2 else 3)

mesh=bpy.data.meshes.new('FloatingIsland_Mesh')
mesh.from_pydata(verts,[],faces);mesh.validate();mesh.update()
island=bpy.data.objects.new('FloatingIsland',mesh);bpy.context.collection.objects.link(island)
for m in (grass,earth1,earth2,stone1,stone2):
    mesh.materials.append(m)
for p,mi in zip(mesh.polygons,face_mats):
    p.material_index=mi
    p.use_smooth=False

# scattered embedded side stones like the exposed rock chunks on TABS floating maps
for k in range(34):
    a=2*math.pi*(k/34.0+rng.uniform(-.012,.012))
    rx=RX*(.955+rng.uniform(-.01,.01));ry=RY*(.955+rng.uniform(-.01,.01))
    x=CX+rx*math.cos(a);y=CY+ry*math.sin(a)
    z=rng.uniform(-7.8,-2.8)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(x,y,z))
    o=bpy.context.object;o.name='CliffRock_%02d'%k
    s=rng.uniform(1.2,2.2)
    o.scale=(s*1.15,s*.55,s*.75)
    # orient broad face approximately along the island wall
    o.rotation_euler[2]=a+math.pi/2
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(rockmat if k%2 else rockmat2)
    for p in o.data.polygons:p.use_smooth=False

# -----------------------------------------------------------------------------
# Rendering: main preview deliberately shows the rounded edge and rocky underside.
# Additional views keep a useful map-level perspective.
# -----------------------------------------------------------------------------
def look_at(o,target):
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
cam=scene.camera
if cam is None:
    raise RuntimeError('Scene camera missing')

def render(name,loc,target,lens):
    cam.location=loc;cam.data.lens=lens;look_at(cam,target)
    scene.render.filepath=os.path.join(OUT,name)
    bpy.ops.render.render(write_still=True)

render('preview_main.png',(0,-255,112),(0,55,-2.5),55)
render('preview_closer.png',(0,-155,70),(0,52,3.0),52)
render('preview_left.png',(-205,-115,92),(0,55,-1.5),55)
render('preview_right.png',(205,-115,92),(0,55,-1.5),55)
render('preview_high.png',(0,-105,180),(0,52,-2.0),56)
cam.location=(0,-255,112);cam.data.lens=55;look_at(cam,(0,55,-2.5))

blend=os.path.join(OUT,'classic_reference_v39.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'classic_reference_v39.glb'),export_format='GLB',export_apply=True)

with open(os.path.join(OUT,'report.txt'),'w',encoding='utf-8') as f:
    f.write('Classic reference v39 floating island\n')
    f.write('Pine count: 993, V38 tree geometry/colors preserved\n')
    f.write('Ground: rounded closed floating island, no rectangular plane\n')
    f.write('Island top radii: %.1f x %.1f\n'%(RX,RY))
    f.write('Underside depth: 20 Blender units\n')
    f.write('Cliff rocks: 34\n')
print('V39_OK',blend)
