import bpy, os
from mathutils import Vector

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'output_classic_reference_v38')
os.makedirs(OUT,exist_ok=True)
scene=bpy.context.scene
scene.render.resolution_x=1024
scene.render.resolution_y=576
scene.render.resolution_percentage=100

# Restore only the tree appearance from the previously accepted larger/warmer pass.
# Mountain geometry, meadow, tree centers, tree count, and map layout stay untouched.
forest=bpy.data.objects.get('PineForest')
if forest is None or forest.type!='MESH':
    raise RuntimeError('PineForest mesh missing')
if len(forest.data.vertices)%54!=0:
    raise RuntimeError('Unexpected PineForest topology: %d vertices'%len(forest.data.vertices))

vs=forest.data.vertices
pine_count=len(vs)//54
if pine_count!=993:
    raise RuntimeError('Expected 993 pines, got %d'%pine_count)

# Same visual sizes as the earlier accepted tree pass; scale around each tree's own center,
# so locations and spacing do not move at all.
for start in range(0,len(vs),54):
    block=vs[start:start+54]
    cx=sum(v.co.x for v in block)/54.0
    cy=sum(v.co.y for v in block)/54.0
    z0=min(v.co.z for v in block)
    factor=1.30 if cy<0 else (1.20 if cy<85 else 1.12)
    for v in block:
        v.co.x=cx+(v.co.x-cx)*factor
        v.co.y=cy+(v.co.y-cy)*factor
        v.co.z=z0+(v.co.z-z0)*factor
forest.data.update()


def tune(name,rgb):
    m=bpy.data.materials.get(name)
    if m is None:
        raise RuntimeError('Missing tree material: '+name)
    m.diffuse_color=(*rgb,1.0)
    if m.use_nodes:
        p=m.node_tree.nodes.get('Principled BSDF')
        if p:
            p.inputs['Base Color'].default_value=(*rgb,1.0)

# Exact warmer green palette used in the previous tree pass.
tune('Pine1',(0.24,0.38,0.20))
tune('Pine2',(0.34,0.49,0.23))
tune('Pine3',(0.43,0.58,0.27))


def look_at(o,target):
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
cam=scene.camera
if cam is None:
    raise RuntimeError('Scene camera missing')

def render(name,loc,target,lens):
    cam.location=loc
    cam.data.lens=lens
    look_at(cam,target)
    scene.render.filepath=os.path.join(OUT,name)
    bpy.ops.render.render(write_still=True)

# Keep the V32 refined camera exactly, so the only visible change is the trees.
render('preview_main.png',(0,-108,47),(0,44,3.8),47)
render('preview_closer.png',(-3,-98,44),(-4,47,3.7),49)
render('preview_left.png',(-50,-88,44),(0,44,3.8),50)
render('preview_right.png',(50,-88,44),(0,44,3.8),50)
render('preview_high.png',(0,-80,76),(0,45,.5),50)
cam.location=(0,-108,47)
cam.data.lens=47
look_at(cam,(0,44,3.8))

blend=os.path.join(OUT,'classic_reference_v38.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'classic_reference_v38.glb'),export_format='GLB',export_apply=True)

with open(os.path.join(OUT,'report.txt'),'w',encoding='utf-8') as f:
    f.write('Classic reference v38\n')
    f.write('Mountains: unchanged from V32 refined\n')
    f.write('Pine count: 993 unchanged\n')
    f.write('Pine centers/locations: unchanged\n')
    f.write('Tree size/color: restored to previous larger warmer pass\n')
print('V38_OK',blend)
