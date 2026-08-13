import bpy, os
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'output_classic_reference_v35');os.makedirs(OUT,exist_ok=True)
scene=bpy.context.scene

# Reversible pass: hide old mountain helpers, preserve all source geometry.
for o in scene.objects:
    if o.name.startswith('Mountain') or o.name=='BackgroundGround':
        o.hide_render=True;o.hide_viewport=True

scene.render.resolution_x=1024;scene.render.resolution_y=683;scene.render.resolution_percentage=100

def tune(name,rgb):
    m=bpy.data.materials.get(name)
    if not m:return
    m.diffuse_color=(*rgb,1)
    if m.use_nodes:
        p=m.node_tree.nodes.get('Principled BSDF')
        if p:p.inputs['Base Color'].default_value=(*rgb,1)

def mk(name,rgb):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    if p:p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=.98
    m.diffuse_color=(*rgb,1);return m

# Keep the exact 993-tree mesh, only calibrate its material palette to the reference.
tune('Grass',(0.55,0.63,0.20));tune('GrassHill',(0.47,0.55,0.20))
tune('Pine1',(0.20,0.35,0.23));tune('Pine2',(0.30,0.47,0.29));tune('Pine3',(0.40,0.56,0.32))
MAIN=mk('Mountain_V35',(0.53,0.64,0.67));LIGHT=mk('Mountain_V35_Light',(0.67,0.75,0.75))
SHADOW=mk('Mountain_V35_Shadow',(0.39,0.51,0.57));BACK=mk('Mountain_V35_Back',(0.60,0.70,0.72));SNOW=mk('Mountain_V35_Snow',(0.90,0.92,0.89))
GRASS=bpy.data.materials.get('Grass')

def assign(o,m):o.data.materials.clear();o.data.materials.append(m)
def ico(name,loc,scale,m,sub=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);assign(o,m)
    for p in o.data.polygons:p.use_smooth=False
    return o

def cap(name,x,y,rx,ry,h,z):
    bpy.ops.mesh.primitive_cone_add(vertices=7,radius1=rx,radius2=rx*.08,depth=h,location=(x,y,z));o=bpy.context.object;o.name=name;o.scale.y=ry/rx
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);assign(o,SNOW)

# Seamless visual ground beyond gameplay field.
bpy.ops.mesh.primitive_plane_add(size=2,location=(0,360,-.07));g=bpy.context.object;g.name='Reference_BackgroundGround';g.scale=(180,520,1)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);assign(g,GRASS)

# Reference-like snow mountain enclosure. Bodies are buried to avoid visible bases.
specs=[(-205,270,105,76,62),(-145,315,92,67,54),(-78,340,88,65,58),(-5,352,102,72,70),(72,345,94,69,62),(145,315,100,72,67),(210,270,112,78,72)]
for i,(x,y,rx,ry,h) in enumerate(specs):
    m=MAIN if i%2==0 else SHADOW;ico('Reference_Mountain_%02d'%i,(x,y,h*.22-7),(rx,ry,h),m,2)
    off=-1 if i%2==0 else 1;ico('Reference_Mountain_Shoulder_%02d'%i,(x+off*rx*.28,y-8,h*.12-8),(rx*.62,ry*.72,h*.58),LIGHT,2)
    cap('Reference_Mountain_Snow_%02d'%i,x+off*rx*.05,y-2,rx*.28,ry*.24,h*.28,h*.78)
for i,(x,y,rx,ry,h) in enumerate([(-180,420,125,82,42),(-75,438,130,84,48),(45,440,132,85,50),(160,420,125,82,43)]):
    ico('Reference_MountainBack_%02d'%i,(x,y,h*.18-8),(rx,ry,h),BACK,2)

world=scene.world
if world and world.use_nodes:
    bg=world.node_tree.nodes.get('Background')
    if bg:bg.inputs['Color'].default_value=(0.64,0.84,0.86,1);bg.inputs['Strength'].default_value=.72
try:scene.view_settings.exposure=-.12
except Exception:pass
for o in scene.objects:
    if o.type=='LIGHT' and o.data.type=='SUN':o.data.energy=1.45

def look(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
cam=scene.camera
def render(n,loc,t,lens):cam.location=loc;cam.data.lens=lens;look(cam,t);scene.render.filepath=os.path.join(OUT,n);bpy.ops.render.render(write_still=True)
render('preview_main.png',(0,-138,88),(0,64,3),50);render('preview_closer.png',(-3,-120,78),(-5,66,3),52)
render('preview_left.png',(-68,-116,76),(-8,68,3),52);render('preview_right.png',(68,-116,76),(8,68,3),52);render('preview_high.png',(0,-98,116),(0,68,.5),54)
cam.location=(0,-138,88);cam.data.lens=50;look(cam,(0,64,3))
blend=os.path.join(OUT,'classic_reference_v35.blend');bpy.ops.wm.save_as_mainfile(filepath=blend)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'classic_reference_v35.glb'),export_format='GLB',export_apply=True)
with open(os.path.join(OUT,'report.txt'),'w') as f:f.write('TABS map v35\nPine count: 993 preserved\nMap only\nReference elevated camera\nSnow mountains\n')
print('V35_OK',blend)
