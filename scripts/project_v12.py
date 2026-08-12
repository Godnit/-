import bpy, math, os
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..')) if '__file__' in globals() else os.getcwd()
OUT=os.path.join(ROOT,'output')
REF=os.path.join(ROOT,'references','house_reference.jpg')
scene=bpy.context.scene
cam=scene.camera

def remove_prefixes(prefixes):
    for o in list(scene.objects):
        if any(o.name.startswith(p) for p in prefixes):
            bpy.data.objects.remove(o,do_unlink=True)

def assign(o,m):
    if m.name not in [x.name for x in o.data.materials]: o.data.materials.append(m)
    return list(o.data.materials).index(m)

def look(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
def mat(name):return bpy.data.materials.get(name)
def box(name,loc,dims,m,bev=.01,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc,rotation=rot);o=bpy.context.object;o.name=name;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
    if bev>0:
        md=o.modifiers.new('Bevel','BEVEL');md.width=bev;md.segments=2;md.limit_method='ANGLE';bpy.context.view_layer.objects.active=o
        try:bpy.ops.object.modifier_apply(modifier=md.name)
        except Exception:pass
    return o
def mesh_obj(name,verts,faces,m):
    me=bpy.data.meshes.new(name+'_Mesh');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.data.materials.append(m);return o
def solid_poly(name,pts,m,th=.06):
    me=bpy.data.meshes.new(name+'_Mesh');me.from_pydata(pts,[],[tuple(range(len(pts)))]);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.data.materials.append(m);bpy.context.view_layer.objects.active=o;o.select_set(True);md=o.modifiers.new('Solidify','SOLIDIFY');md.thickness=th;md.offset=0;bpy.ops.object.modifier_apply(modifier=md.name);o.select_set(False);return o
def tri_prism_y(name,x0,x1,y0,y1,z0,zp,m):
    xm=(x0+x1)/2;v=[(x0,y0,z0),(x1,y0,z0),(xm,y0,zp),(x0,y1,z0),(x1,y1,z0),(xm,y1,zp)];f=[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)];return mesh_obj(name,v,f,m)

remove_prefixes(['Shingle_Main','Shingle_Gable','DormerTile_','PorchFTile_','PorchRTile_','HipTileV11_','RightHip_Course_','Siding_','GableSiding_',
                 'Window_Front_','UpperTrim','Window_Awning','Door_Recess','Door_Main','Door_Glass_','DormerWin_','Window_Right_Porch','SideDoorV11','EntryV11_'])

for o in scene.objects:
    if o.name.startswith('Dormer_'):
        o.location.x += .32
        o.location.y += .06
for o in scene.objects:
    if o.name.startswith('Chimney'):
        o.location.x += .04; o.location.y += .10

TR=mat('Trim_OffWhite');RB=mat('Roof_Blue');RD=mat('Roof_Blue_Dark')
ex0,ex1=.50,1.46;er=.98;ey0,ey1=-2.92,-1.78;ezE,ezR=2.58,3.00
solid_poly('EntryV12_RoofL',[(ex0,ey0,ezE),(er,ey0,ezR),(er,ey1,ezR),(ex0,ey1,ezE)],RB)
solid_poly('EntryV12_RoofR',[(er,ey0,ezR),(ex1,ey0,ezE),(ex1,ey1,ezE),(er,ey1,ezR)],RB)
box('EntryV12_Ridge',(er,(ey0+ey1)/2,ezR+.045),(.13,ey1-ey0+.08,.13),RD,.035)
tri_prism_y('EntryV12_Pediment',ex0+.08,ex1-.08,ey0+.01,ey0+.08,2.54,2.94,TR)

cam.location=(9.0,-12.2,10.0)
cam.data.type='ORTHO';cam.data.ortho_scale=9.05
look(cam,(-.10,-.08,2.25))
scene.camera=cam

if not os.path.exists(REF):
    raise RuntimeError('Missing reference image: '+REF)
img=bpy.data.images.load(REF,check_existing=True)
proj=bpy.data.materials.get('Reference_Camera_Projection') or bpy.data.materials.new('Reference_Camera_Projection')
proj.use_nodes=True
nodes=proj.node_tree.nodes;links=proj.node_tree.links
nodes.clear()
out=nodes.new('ShaderNodeOutputMaterial')
tex=nodes.new('ShaderNodeTexImage');tex.image=img;tex.interpolation='Linear';tex.extension='CLIP'
em=nodes.new('ShaderNodeEmission');em.inputs['Strength'].default_value=1.0
links.new(tex.outputs['Color'],em.inputs['Color']);links.new(em.outputs['Emission'],out.inputs['Surface'])

target_prefixes=('House_','Front_Gable_Wall','Roof_Main_','Roof_FrontGable_','Dormer_','Chimney','PorchRoof_','EntryV12_')

def project_object(o):
    if o.type!='MESH' or not o.data.polygons:return
    idx=assign(o,proj)
    uv=o.data.uv_layers.get('ReferenceUV') or o.data.uv_layers.new(name='ReferenceUV')
    o.data.uv_layers.active=uv
    try:uv.active_render=True
    except Exception:pass
    for poly in o.data.polygons:
        world_center=o.matrix_world @ poly.center
        n=(o.matrix_world.to_3x3() @ poly.normal).normalized()
        view=(cam.location-world_center).normalized()
        if n.dot(view)>0.08: poly.material_index=idx
        for li in poly.loop_indices:
            vi=o.data.loops[li].vertex_index
            co=o.matrix_world @ o.data.vertices[vi].co
            ndc=world_to_camera_view(scene,cam,co)
            uv.data[li].uv=(ndc.x,ndc.y)

for o in scene.objects:
    if any(o.name.startswith(p) for p in target_prefixes):
        project_object(o)

scene.world.use_nodes=True
bg=scene.world.node_tree.nodes.get('Background')
if bg:
    bg.inputs['Color'].default_value=(0.985,0.975,0.945,1);bg.inputs['Strength'].default_value=.75
back=bpy.data.objects.get('Backdrop')
if back and back.data.materials:
    m=back.data.materials[0];m.diffuse_color=(.97,.955,.91,1)
    if m.use_nodes:
        bs=m.node_tree.nodes.get('Principled BSDF')
        if bs:bs.inputs['Base Color'].default_value=(.97,.955,.91,1)

for o in list(scene.objects):
    if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
def area(n,loc,e,size,t,color):
    bpy.ops.object.light_add(type='AREA',location=loc);L=bpy.context.object;L.name=n;L.data.energy=e;L.data.shape='DISK';L.data.size=size;L.data.color=color;look(L,t)
area('V12_Key',(-6.5,-7.5,11),520,7,(0,-.2,2),(1,.96,.9))
area('V12_Fill',(6,-4,8),190,8,(0,0,2),(.95,.98,1))
bpy.ops.object.light_add(type='SUN',location=(0,0,8));sun=bpy.context.object;sun.data.energy=.38;sun.data.angle=math.radians(22);sun.rotation_euler=(math.radians(28),math.radians(-18),math.radians(-36))
try:
    scene.view_settings.exposure=0.0
    scene.view_settings.look='Medium High Contrast'
except Exception:pass

views={
'preview_perspective.png':((9.0,-12.2,10.0),(-.10,-.08,2.25),9.05),
'preview_front.png':((0,-14.5,4.8),(-.2,0,2.15),9.3),
'preview_back.png':((0,14.5,4.8),(-.2,0,2.15),9.3),
'preview_left.png':((-14.5,0,4.8),(0,0,2.15),9.3),
'preview_right.png':((14.5,0,4.8),(0,0,2.15),9.3),
'preview_top.png':((0,0,16),(0,0,0),9.6)}
pos,t,scale=views['preview_perspective.png'];cam.location=pos;cam.data.ortho_scale=scale;look(cam,t);scene.render.filepath=os.path.join(OUT,'preview_perspective.png');bpy.ops.render.render(write_still=True)
for fn in ['preview_front.png','preview_back.png','preview_left.png','preview_right.png','preview_top.png']:
    pos,t,scale=views[fn];cam.location=pos;cam.data.ortho_scale=scale;look(cam,t);scene.render.filepath=os.path.join(OUT,fn);bpy.ops.render.render(write_still=True)
cam.location=(9.0,-12.2,10.0);cam.data.ortho_scale=9.05;look(cam,(-.10,-.08,2.25))

for o in scene.objects:o.select_set(False)
for o in scene.objects:
    if o.type=='MESH' and o.name!='Backdrop':o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'model.glb'),export_format='GLB',use_selection=True,export_apply=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'model.blend'))
print('REFERENCE_PROJECTION_V12_COMPLETE')
