import bpy, os
from mathutils import Vector

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'output_classic_reference_v40')
os.makedirs(OUT,exist_ok=True)
scene=bpy.context.scene
scene.render.resolution_x=1024
scene.render.resolution_y=576
scene.render.resolution_percentage=100

CX,CY=0.0,48.0

# -----------------------------------------------------------------------------
# V40: keep V39's actual closed floating-island geometry, but bring the rounded
# edge much closer to the accepted V38 forest footprint. This replaces the old
# oversized sheet feeling with a real compact TABS/Farmer-style ripped land disc.
# Trees, their colors, and all original meadow props remain untouched.
# -----------------------------------------------------------------------------
island=bpy.data.objects.get('FloatingIsland')
if island is None:
    raise RuntimeError('FloatingIsland missing')

# V39 radii 182 x 188 -> about 131 x 147. This still contains the original
# 218 x 252 map footprint while making the curved edge visible around the forest.
island.scale.x*=0.72
island.scale.y*=0.78
bpy.context.view_layer.objects.active=island
island.select_set(True)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
island.select_set(False)

# Bring exposed cliff rocks with the new edge, preserving their individual shape.
for o in scene.objects:
    if o.name.startswith('CliffRock_'):
        o.location.x=CX+(o.location.x-CX)*0.72
        o.location.y=CY+(o.location.y-CY)*0.78

# Mountains should sit at/just inside the rear rounded rim instead of beyond a
# distant rectangular ground extension. Keep their current materials and shape.
for o in scene.objects:
    if o.name.startswith('Mountain'):
        o.location.x=CX+(o.location.x-CX)*0.76
        o.location.y=CY+(o.location.y-CY)*0.74
        o.scale.x*=0.78
        o.scale.y*=0.78
        o.scale.z*=0.96

# Slightly deepen the bottom point so the island reads as torn from the ground.
# The final vertex of the island mesh is the underside closure point in V39.
if island.type=='MESH' and len(island.data.vertices)>0:
    bottom=min(island.data.vertices,key=lambda v:v.co.z)
    bottom.co.z-=2.5
    island.data.update()

# -----------------------------------------------------------------------------
# Cameras. Main view deliberately shows the whole rounded disc and underside.
# -----------------------------------------------------------------------------
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

render('preview_main.png',(0,-520,235),(0,50,-5.0),40)
render('preview_closer.png',(0,-315,128),(0,45,-6.0),42)
render('preview_left.png',(-330,-285,150),(0,48,-5.0),43)
render('preview_right.png',(330,-285,150),(0,48,-5.0),43)
render('preview_high.png',(0,-285,305),(0,50,-4.0),44)
cam.location=(0,-520,235);cam.data.lens=40;look_at(cam,(0,50,-5.0))

blend=os.path.join(OUT,'classic_reference_v40.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'classic_reference_v40.glb'),export_format='GLB',export_apply=True)

with open(os.path.join(OUT,'report.txt'),'w',encoding='utf-8') as f:
    f.write('Classic reference v40 compact floating island\n')
    f.write('Pine count: 993, inherited unchanged from V38/V39\n')
    f.write('Trees/colors: unchanged from accepted V38\n')
    f.write('Ground: rounded closed floating disc; no rectangular plane\n')
    f.write('Approx top radii: 131 x 147 Blender units\n')
    f.write('Underside: tapered earth/stone body with cliff rocks\n')
print('V40_OK',blend)
