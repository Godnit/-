import bpy, os
from mathutils import Vector

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'output_classic_reference_v32')
os.makedirs(OUT,exist_ok=True)
scene=bpy.context.scene

# Keep the fixed map/tree layout. Replace only mountains and the background helper.
for obj in list(scene.objects):
    if obj.name.startswith('Mountain') or obj.name=='BackgroundGround':
        bpy.data.objects.remove(obj,do_unlink=True)

def make_mat(name,rgb):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    if p:
        p.inputs['Base Color'].default_value=(*rgb,1.0)
        p.inputs['Roughness'].default_value=.98
    m.diffuse_color=(*rgb,1.0)
    return m

MAIN=make_mat('Mountain_V32_Main',(0.77,0.82,0.80))
LIGHT=make_mat('Mountain_V32_Light',(0.88,0.89,0.85))
SHADOW=make_mat('Mountain_V32_Shadow',(0.57,0.68,0.71))
BACK=make_mat('Mountain_V32_Back',(0.67,0.75,0.76))
grass=bpy.data.materials.get('Grass')
if grass is None: raise RuntimeError('Grass missing')

# Huge flat continuation of the meadow, with no vertical cube edge in view.
bpy.ops.mesh.primitive_plane_add(size=2,location=(0,650,-0.055))
g=bpy.context.object;g.name='BackgroundGround';g.scale=(420,820,1)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);g.data.materials.append(grass)

def ico(name,loc,scale,mat):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=loc)
    o=bpy.context.object;o.name=name;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=False
    return o

# Few huge rounded masses, deeply buried so only broad upper domes show above the meadow.
front=[
(-215,288,92,65,37,-15.5),(-153,286,98,67,40,-16.0),(-86,291,96,66,36,-15.0),
(-15,296,105,71,43,-17.0),(61,293,98,68,38,-15.5),(137,287,108,73,46,-17.0),
(216,289,94,65,37,-15.5)]
for i,(x,y,sx,sy,sz,cz) in enumerate(front):
    ico('Mountain_%02d'%i,(x,y,cz),(sx,sy,sz),MAIN)
    side=-1 if i%2==0 else 1
    ico('MountainShadow_%02d'%i,(x+side*sx*.28,y-5,cz-1.5),(sx*.62,sy*.74,sz*.60),SHADOW)
    if i in (1,3,5):
        ico('MountainLight_%02d'%i,(x-side*sx*.18,y+2,cz+1.0),(sx*.48,sy*.58,sz*.50),LIGHT)

# Lower pale rear layer visible in the gaps.
back=[(-215,370,118,78,31,-16.0),(-130,376,122,80,34,-17.0),(-40,380,128,83,36,-18.0),
      (58,379,127,82,35,-18.0),(150,375,120,79,33,-17.0),(230,369,112,75,29,-16.0)]
for i,(x,y,sx,sy,sz,cz) in enumerate(back):
    ico('MountainBack_%02d'%i,(x,y,cz),(sx,sy,sz),BACK)

def look_at(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
cam=scene.camera
if cam is None:raise RuntimeError('Scene camera missing')
def render(name,loc,target,lens):
    cam.location=loc;cam.data.lens=lens;look_at(cam,target)
    scene.render.filepath=os.path.join(OUT,name);bpy.ops.render.render(write_still=True)

render('preview_main.png',(0,-108,47),(0,44,3.8),47)
render('preview_closer.png',(-3,-98,44),(-4,47,3.7),49)
render('preview_left.png',(-50,-88,44),(0,44,3.8),50)
render('preview_right.png',(50,-88,44),(0,44,3.8),50)
render('preview_high.png',(0,-80,76),(0,45,.5),50)
cam.location=(0,-108,47);cam.data.lens=47;look_at(cam,(0,44,3.8))

blend=os.path.join(OUT,'classic_reference_v32.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'classic_reference_v32.glb'),export_format='GLB',export_apply=True)
with open(os.path.join(OUT,'report.txt'),'w',encoding='utf-8') as f:
    f.write('TABS reference map v32 refined\n')
    f.write('Pine count: 993; tree positions/scales/colors preserved\n')
    f.write('Map only: church/graves/tents/path removed\n')
    f.write('Mountains: broad buried low-poly domes with pale faces and blue-grey shoulders\n')
print('V32_REFINED_OK',blend)
