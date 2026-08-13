import bpy, os, math
from mathutils import Vector

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'output_classic_reference_v30')
os.makedirs(OUT,exist_ok=True)
scene=bpy.context.scene

# Keep the verified V27 tree/map scene. Replace mountains only.
for obj in list(scene.objects):
    if obj.name.startswith('Mountain'):
        bpy.data.objects.remove(obj,do_unlink=True)


def mat(name):
    m=bpy.data.materials.get(name)
    if not m: raise RuntimeError('Missing material: '+name)
    return m

def assign(o,m):
    o.data.materials.clear();o.data.materials.append(m)

def box(name,loc,dims,m):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object;o.name=name;o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    assign(o,m);return o

def ico(name,loc,scale,m,sub=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=1,location=loc)
    o=bpy.context.object;o.name=name;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    assign(o,m);return o

MGRASS=mat('Grass'); MM=mat('Mountain'); MS=mat('MountainShadow')

# Continue the same green plain behind the playable field so mountain bases disappear naturally.
box('BackgroundGround',(0,270,-0.70),(218,192,1.40),MGRASS)

# Broad, rounded/faceted mountain masses like the reference. Their centers are deeply buried.
front=[
(-185,215,54,36,13,0),(-145,219,58,39,16,1),(-102,223,59,40,14,0),
(-60,227,64,42,17,1),(-16,231,69,44,20,0),(31,230,67,44,17,1),
(78,226,64,42,18,0),(123,222,60,40,15,1),(166,218,56,38,13,0),(202,216,48,35,11,1)]
for i,(x,y,sx,sy,sz,v) in enumerate(front):
    mm=MM if v==0 else MS
    ico('Mountain_%02d'%i,(x,y,-7.0),(sx,sy,sz),mm,2)
    # low shoulder makes the silhouette asymmetric and wide, not spherical
    off=-1 if i%2==0 else 1
    ico('Mountain_Shoulder_%02d'%i,(x+off*sx*.27,y-4,-7.4),(sx*.60,sy*.72,sz*.62),MM,2)

# Softer rear layer; kept low so a clear sky band stays visible.
back=[(-190,270,68,40,9),(-125,274,72,42,10),(-58,277,75,43,11),(15,278,76,43,10),(88,276,73,42,10),(158,272,69,40,9)]
for i,(x,y,sx,sy,sz) in enumerate(back):
    ico('Mountain_Back_%02d'%i,(x,y,-7.2),(sx,sy,sz),MS,2)

# Ensure flat low-poly appearance.
for obj in scene.objects:
    if obj.name.startswith('Mountain') and obj.type=='MESH':
        for p in obj.data.polygons:p.use_smooth=False


def look_at(o,target):
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
cam=scene.camera
if not cam: raise RuntimeError('Scene camera missing')

def render(name,loc,target,lens):
    cam.location=loc;cam.data.lens=lens;look_at(cam,target)
    scene.render.filepath=os.path.join(OUT,name)
    bpy.ops.render.render(write_still=True)

render('preview_main.png',(0,-108,47),(0,44,3.8),47)
render('preview_closer.png',(-3,-98,44),(-4,47,3.7),49)
render('preview_left.png',(-50,-88,44),(0,44,3.8),50)
render('preview_right.png',(50,-88,44),(0,44,3.8),50)
render('preview_high.png',(0,-80,76),(0,45,.5),50)
cam.location=(0,-108,47);cam.data.lens=47;look_at(cam,(0,44,3.8))

blend=os.path.join(OUT,'classic_reference_v30.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'classic_reference_v30.glb'),export_format='GLB',export_apply=True)

mesh_objs=[o for o in scene.objects if o.type=='MESH']
with open(os.path.join(OUT,'report.txt'),'w',encoding='utf-8') as f:
    f.write('TABS Classic reference v30\n')
    f.write('Pine count: 993 (preserved from verified V27 layout)\n')
    f.write('Map only: church/graves/tents/path removed\n')
    f.write('Mountains: broad embedded low-poly masses; bases hidden by extended meadow\n')
    f.write('Playable field: 218 x 252 Blender units\n')
    f.write('Mesh objects: %d\n'%len(mesh_objs))
print('V30_OK',blend)
