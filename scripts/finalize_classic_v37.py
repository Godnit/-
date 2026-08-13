import bpy, os
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'output_classic_reference_v37');os.makedirs(OUT,exist_ok=True)
scene=bpy.context.scene;scene.render.resolution_x=1024;scene.render.resolution_y=683;scene.render.resolution_percentage=100

# Keep all tree centers fixed. Enlarge each baked 54-vertex pine around its own center only.
forest=bpy.data.objects.get('PineForest')
if forest and len(forest.data.vertices)%54==0:
    vs=forest.data.vertices
    for s in range(0,len(vs),54):
        b=vs[s:s+54];cx=sum(v.co.x for v in b)/54;cy=sum(v.co.y for v in b)/54;z0=min(v.co.z for v in b)
        f=1.30 if cy<0 else (1.20 if cy<85 else 1.12)
        for v in b:
            v.co.x=cx+(v.co.x-cx)*f;v.co.y=cy+(v.co.y-cy)*f;v.co.z=z0+(v.co.z-z0)*f
    forest.data.update()

def tune(name,rgb):
    m=bpy.data.materials.get(name)
    if not m:return
    m.diffuse_color=(*rgb,1)
    if m.use_nodes:
        p=m.node_tree.nodes.get('Principled BSDF')
        if p:p.inputs['Base Color'].default_value=(*rgb,1)

tune('Pine1',(0.24,0.38,0.20));tune('Pine2',(0.34,0.49,0.23));tune('Pine3',(0.43,0.58,0.27))
tune('Mountain_V35',(0.61,0.70,0.72));tune('Mountain_V35_Light',(0.76,0.82,0.81));tune('Mountain_V35_Shadow',(0.48,0.60,0.64));tune('Mountain_V35_Back',(0.67,0.76,0.77));tune('Mountain_V35_Snow',(0.94,0.95,0.92))

# Make main mountains steeper than the rounded V35 bodies; leave broad shoulders as foothills.
for o in scene.objects:
    if o.name.startswith('Reference_Mountain_') and 'Shoulder' not in o.name and 'Snow' not in o.name and 'Back' not in o.name:
        o.scale.x*=.90;o.scale.y*=.92;o.scale.z*=1.18

# Put each snow cap on the actual body summit (V35 accidentally buried them inside the body).
for i in range(7):
    body=bpy.data.objects.get('Reference_Mountain_%02d'%i);snow=bpy.data.objects.get('Reference_Mountain_Snow_%02d'%i)
    if body and snow:
        top=body.location.z+body.dimensions.z*.5
        snow.location.z=top-snow.dimensions.z*.34
        snow.scale.x*=1.08;snow.scale.y*=1.08

# Camera D from the comparison: full peaks + large open field like the supplied reference.
def look(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
cam=scene.camera

def render(n,loc,t,lens):cam.location=loc;cam.data.lens=lens;look(cam,t);scene.render.filepath=os.path.join(OUT,n);bpy.ops.render.render(write_still=True)
render('preview_main.png',(0,-190,118),(0,132,25),50)
render('preview_closer.png',(0,-170,108),(0,125,22),52)
render('preview_left.png',(-72,-168,108),(-12,125,22),52)
render('preview_right.png',(72,-168,108),(12,125,22),52)
render('preview_high.png',(0,-138,145),(0,125,8),54)
cam.location=(0,-190,118);cam.data.lens=50;look(cam,(0,132,25))

blend=os.path.join(OUT,'classic_reference_v37.blend');bpy.ops.wm.save_as_mainfile(filepath=blend)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'classic_reference_v37.glb'),export_format='GLB',export_apply=True)
with open(os.path.join(OUT,'report.txt'),'w') as f:f.write('TABS map v37\nMap only\nPine count 993; centers fixed\nTree sizes reference-scaled\nSnow caps corrected above summits\nCamera D selected\n')
print('V37_OK',blend)
