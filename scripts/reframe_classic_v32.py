import bpy, os
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'output_classic_reference_v32')
scene=bpy.context.scene
cam=scene.camera

def look_at(o,target):
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()

def render(name,loc,target,lens):
    cam.location=loc;cam.data.lens=lens;look_at(cam,target)
    scene.render.filepath=os.path.join(OUT,name)
    bpy.ops.render.render(write_still=True)

render('preview_main.png',(0,-108,47),(0,48,14.0),47)
render('preview_closer.png',(-3,-98,44),(-4,51,13.0),49)
render('preview_left.png',(-50,-88,44),(0,49,13.0),50)
render('preview_right.png',(50,-88,44),(0,49,13.0),50)
render('preview_high.png',(0,-80,76),(0,50,7.0),50)
cam.location=(0,-108,47);cam.data.lens=47;look_at(cam,(0,48,14.0))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'classic_reference_v32.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'classic_reference_v32.glb'),export_format='GLB',export_apply=True)
print('V32_REFRAME_OK')
