import bpy, os
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'output_camera_v36');os.makedirs(OUT,exist_ok=True)
scene=bpy.context.scene;scene.render.resolution_x=720;scene.render.resolution_y=480;scene.render.resolution_percentage=100

# Keep tree centers/positions exactly fixed; enlarge geometry around each center to match reference visual scale.
forest=bpy.data.objects.get('PineForest')
if forest and forest.type=='MESH' and len(forest.data.vertices)%54==0:
    vs=forest.data.vertices
    for start in range(0,len(vs),54):
        block=vs[start:start+54]
        cx=sum(v.co.x for v in block)/54;cy=sum(v.co.y for v in block)/54;z0=min(v.co.z for v in block)
        factor=1.30 if cy<0 else (1.20 if cy<85 else 1.12)
        for v in block:
            v.co.x=cx+(v.co.x-cx)*factor;v.co.y=cy+(v.co.y-cy)*factor;v.co.z=z0+(v.co.z-z0)*factor
    forest.data.update()

# Warmer greens from the supplied reference image.
def tune(name,rgb):
    m=bpy.data.materials.get(name)
    if not m:return
    m.diffuse_color=(*rgb,1)
    if m.use_nodes:
        p=m.node_tree.nodes.get('Principled BSDF')
        if p:p.inputs['Base Color'].default_value=(*rgb,1)
tune('Pine1',(0.24,0.38,0.20));tune('Pine2',(0.34,0.49,0.23));tune('Pine3',(0.43,0.58,0.27))

def look(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
cam=scene.camera
candidates=[
('A',(0,-165,100),(0,100,18),47),
('B',(0,-180,110),(0,112,20),49),
('C',(0,-170,105),(0,125,24),46),
('D',(0,-190,118),(0,132,25),50),
]
for name,loc,t,lens in candidates:
    cam.location=loc;cam.data.lens=lens;look(cam,t);scene.render.filepath=os.path.join(OUT,'candidate_'+name+'.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'camera_test_v36.blend'))
with open(os.path.join(OUT,'report.txt'),'w') as f:f.write('4 camera candidates A-D; tree centers unchanged; tree geometry scaled per depth\n')
print('CAMERA_V36_OK')
