import bpy, math, os
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..')) if '__file__' in globals() else os.getcwd()
OUT=os.path.join(ROOT,'output')
REF=os.path.join(ROOT,'references','house_reference.jpg')
scene=bpy.context.scene

# ---------- helpers ----------
def look(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
def remove_prefixes(prefixes):
    for o in list(scene.objects):
        if any(o.name.startswith(p) for p in prefixes):bpy.data.objects.remove(o,do_unlink=True)
def mat(name):return bpy.data.materials.get(name)
def assign_all(o,m):
    o.data.materials.clear();o.data.materials.append(m)
def box(name,loc,dims,m,bev=.01,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc,rotation=rot);o=bpy.context.object;o.name=name;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
    if bev:
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
def sphere(name,loc,r,m,scale=(1,1,1),sub=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=r,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
    for p in o.data.polygons:p.use_smooth=True
    return o

def crop_image(src, name, x0f,y0f,x1f,y1f):
    w,h=src.size
    x0=max(0,min(w-1,int(x0f*w)));x1=max(x0+1,min(w,int(x1f*w)))
    y0=max(0,min(h-1,int(y0f*h)));y1=max(y0+1,min(h,int(y1f*h)))
    cw,ch=x1-x0,y1-y0
    pix=list(src.pixels);out=[]
    for y in range(y0,y1):
        start=(y*w+x0)*4;end=(y*w+x1)*4;out.extend(pix[start:end])
    im=bpy.data.images.get(name) or bpy.data.images.new(name,width=cw,height=ch,alpha=True)
    if im.size[0]!=cw or im.size[1]!=ch:
        bpy.data.images.remove(im);im=bpy.data.images.new(name,width=cw,height=ch,alpha=True)
    im.pixels=out;im.update()
    try:im.pack()
    except Exception:pass
    return im

remove_prefixes(['Shingle_Main','Shingle_Gable','DormerTile_','PorchFTile_','PorchRTile_','HipTileV11_','RightHip_Course_','EntryV11_'])

if not os.path.exists(REF):raise RuntimeError('reference missing')
src=bpy.data.images.load(REF,check_existing=True)
roof_crop=crop_image(src,'Roof_Reference_Crop',.46,.68,.58,.79)

roofmat=bpy.data.materials.get('Roof_Photo_Shingles') or bpy.data.materials.new('Roof_Photo_Shingles')
roofmat.use_nodes=True
n=roofmat.node_tree.nodes;l=roofmat.node_tree.links;n.clear()
out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');tex=n.new('ShaderNodeTexImage');tex.image=roof_crop;tex.extension='REPEAT';tex.interpolation='Linear'
tc=n.new('ShaderNodeTexCoord');mp=n.new('ShaderNodeMapping');mp.inputs['Scale'].default_value=(1.55,1.55,1.55)
l.new(tc.outputs['Generated'],mp.inputs['Vector']);l.new(mp.outputs['Vector'],tex.inputs['Vector']);l.new(tex.outputs['Color'],bs.inputs['Base Color'])
if 'Roughness' in bs.inputs:bs.inputs['Roughness'].default_value=.62
rgb=n.new('ShaderNodeRGBToBW');bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.11;bump.inputs['Distance'].default_value=.035
l.new(tex.outputs['Color'],rgb.inputs['Color']);l.new(rgb.outputs['Val'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal']);l.new(bs.outputs['BSDF'],out.inputs['Surface'])
for o in scene.objects:
    if o.type=='MESH' and (o.name.startswith('Roof_Main_') or o.name.startswith('Roof_FrontGable_') or o.name.startswith('Dormer_Roof_') or o.name.startswith('PorchRoof_')):
        assign_all(o,roofmat)

wallmat=bpy.data.materials.get('Wall_Reference_Siding') or bpy.data.materials.new('Wall_Reference_Siding');wallmat.use_nodes=True
n=wallmat.node_tree.nodes;l=wallmat.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');tc=n.new('ShaderNodeTexCoord');wave=n.new('ShaderNodeTexWave');wave.wave_type='BANDS';wave.bands_direction='Z';wave.inputs['Scale'].default_value=17.0;wave.inputs['Distortion'].default_value=.35;wave.inputs['Detail'].default_value=2.0
ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.38;ramp.color_ramp.elements[0].color=(.73,.69,.60,1);ramp.color_ramp.elements[1].position=.62;ramp.color_ramp.elements[1].color=(.94,.91,.82,1)
bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.13;bump.inputs['Distance'].default_value=.035
l.new(tc.outputs['Generated'],wave.inputs['Vector']);l.new(wave.outputs['Color'],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],bs.inputs['Base Color']);l.new(wave.outputs['Color'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal']);l.new(bs.outputs['BSDF'],out.inputs['Surface'])
if 'Roughness' in bs.inputs:bs.inputs['Roughness'].default_value=.78
remove_prefixes(['Siding_','GableSiding_'])
for o in scene.objects:
    if o.type=='MESH' and (o.name in ('House_Main','House_RightWing','Front_Gable_Wall') or o.name.startswith('Dormer_Body') or o.name.startswith('Dormer_Gable')):
        assign_all(o,wallmat)

for o in scene.objects:
    if o.name.startswith('Door_'):o.location.x+=.43
    if o.name.startswith('Dormer_'):o.location.x+=.30;o.location.y+=.04
    if o.name.startswith('Window_Front_Upper') or o.name.startswith('UpperTrim'):
        o.location.x+=.09;o.location.z-=.04;o.location.y=-2.225

TR=mat('Trim_OffWhite');RB=roofmat;RD=mat('Roof_Blue_Dark')
ex0,ex1=.72,1.62;er=1.17;ey0,ey1=-2.88,-1.80;ezE,ezR=2.60,2.98
solid_poly('EntryV13_RoofL',[(ex0,ey0,ezE),(er,ey0,ezR),(er,ey1,ezR),(ex0,ey1,ezE)],RB)
solid_poly('EntryV13_RoofR',[(er,ey0,ezR),(ex1,ey0,ezE),(ex1,ey1,ezE),(er,ey1,ezR)],RB)
box('EntryV13_Ridge',(er,(ey0+ey1)/2,ezR+.045),(.13,ey1-ey0+.08,.13),RD,.035)
tri_prism_y('EntryV13_Pediment',ex0+.08,ex1-.08,ey0+.01,ey0+.08,2.56,2.92,TR)

leaf=mat('Leaf_Mid') or mat('Shrub_Dark');leafhi=mat('Leaf_Light') or leaf
for i,(x,y,r) in enumerate([(-2.15,-1.25,.20),(-1.78,-1.17,.18),(-1.38,-1.16,.18),(-.88,-1.17,.18),(-.40,-1.22,.18),(.10,-1.30,.18),(1.00,-3.10,.18),(1.38,-3.16,.18),(1.78,-3.10,.19),(2.18,-3.03,.18),(2.60,-2.92,.18),(3.00,-2.72,.19),(3.30,-2.32,.20),(3.42,-1.88,.18),(3.42,-1.38,.18),(3.38,-.88,.18),(3.30,-.35,.18),(3.18,.18,.18)]):
    sphere(f'V13DenseBush_{i}',(x,y,.56),r,leafhi if i%3==0 else leaf,(1,.9,.88),2)

scene.world.use_nodes=True;bg=scene.world.node_tree.nodes.get('Background')
if bg:bg.inputs['Color'].default_value=(.975,.962,.925,1);bg.inputs['Strength'].default_value=.48
for o in list(scene.objects):
    if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
def area(n,loc,e,size,t,color):
    bpy.ops.object.light_add(type='AREA',location=loc);L=bpy.context.object;L.name=n;L.data.energy=e;L.data.shape='DISK';L.data.size=size;L.data.color=color;look(L,t)
area('V13_Key',(-6,-7,11),760,6.5,(0,-.2,2.1),(1,.95,.88));area('V13_Fill',(6,-4,8),270,8,(0,0,2.1),(.95,.98,1));area('V13_Rim',(-4,4,7),110,6,(0,.2,2),(1,.98,.92))
bpy.ops.object.light_add(type='SUN',location=(0,0,8));sun=bpy.context.object;sun.data.energy=.55;sun.data.angle=math.radians(20);sun.rotation_euler=(math.radians(28),math.radians(-18),math.radians(-36))
try:scene.view_settings.exposure=.02
except Exception:pass
cam=scene.camera
views={'preview_perspective.png':((9.3,-12.0,10.1),(-.12,-.06,2.25),9.05),'preview_front.png':((0,-14.5,4.8),(-.2,0,2.15),9.3),'preview_back.png':((0,14.5,4.8),(-.2,0,2.15),9.3),'preview_left.png':((-14.5,0,4.8),(0,0,2.15),9.3),'preview_right.png':((14.5,0,4.8),(0,0,2.15),9.3),'preview_top.png':((0,0,16),(0,0,0),9.6)}
for fn,(pos,t,scale) in views.items():cam.location=pos;cam.data.ortho_scale=scale;look(cam,t);scene.render.filepath=os.path.join(OUT,fn);bpy.ops.render.render(write_still=True)
cam.location=(9.3,-12.0,10.1);cam.data.ortho_scale=9.05;look(cam,(-.12,-.06,2.25))
for o in scene.objects:o.select_set(False)
for o in scene.objects:
    if o.type=='MESH' and o.name!='Backdrop':o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'model.glb'),export_format='GLB',use_selection=True,export_apply=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'model.blend'))
print('REFERENCE_TEXTURE_V14_COMPLETE')
