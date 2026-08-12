import bpy, bmesh, math, os
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..')) if '__file__' in globals() else os.getcwd()
OUT=os.path.join(ROOT,'output')
scene=bpy.context.scene

def mat(name): return bpy.data.materials.get(name)
def set_base(name, rgba, rough=None):
    m=mat(name)
    if not m: return
    m.diffuse_color=(*rgba,1)
    if m.use_nodes:
        bs=m.node_tree.nodes.get('Principled BSDF')
        if bs:
            bs.inputs['Base Color'].default_value=(*rgba,1)
            if rough is not None and 'Roughness' in bs.inputs: bs.inputs['Roughness'].default_value=rough

def assign(o,m):
    o.data.materials.clear(); o.data.materials.append(m)
def bevel(o,w=.01):
    md=o.modifiers.new('Bevel','BEVEL'); md.width=w; md.segments=2; md.limit_method='ANGLE'; bpy.context.view_layer.objects.active=o
    try:bpy.ops.object.modifier_apply(modifier=md.name)
    except Exception:pass
def box(name,loc,dims,m,bev_w=.01,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc,rotation=rot);o=bpy.context.object;o.name=name;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);assign(o,m);bevel(o,bev_w);return o
def mesh_obj(name,verts,faces,m):
    me=bpy.data.meshes.new(name+'_Mesh');me.from_pydata(verts,[],faces);me.validate();me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);assign(o,m);return o
def solid_poly(name,pts,m,th=.065):
    me=bpy.data.meshes.new(name+'_Mesh');me.from_pydata(pts,[],[tuple(range(len(pts)))]);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);assign(o,m);bpy.context.view_layer.objects.active=o;o.select_set(True);md=o.modifiers.new('Solidify','SOLIDIFY');md.thickness=th;md.offset=0;bpy.ops.object.modifier_apply(modifier=md.name);o.select_set(False);return o
def tri_prism_y(name,x0,x1,y0,y1,z0,zp,m):
    xm=(x0+x1)/2;v=[(x0,y0,z0),(x1,y0,z0),(xm,y0,zp),(x0,y1,z0),(x1,y1,z0),(xm,y1,zp)];f=[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)];return mesh_obj(name,v,f,m)
def look(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()

set_base('Roof_Blue',(0.030,0.145,0.315),0.61)
set_base('Roof_Blue_Mid',(0.040,0.185,0.390),0.59)
set_base('Roof_Blue_Dark',(0.022,0.105,0.245),0.62)
set_base('Wall_Warm_Cream',(0.845,0.815,0.735),0.84)
set_base('Wall_Siding_Highlight',(0.925,0.900,0.835),0.86)
set_base('Wood_Warm_Brown',(0.46,0.22,0.075),0.70)
set_base('Wood_Awning',(0.62,0.31,0.105),0.68)

TR=mat('Trim_OffWhite'); RB=mat('Roof_Blue'); RM=mat('Roof_Blue_Mid'); RD=mat('Roof_Blue_Dark'); WD=mat('Wood_Warm_Brown'); GL=mat('Glass_BlueGray')

for o in scene.objects:
    if o.name.startswith('Window_Front_Upper') or o.name.startswith('UpperTrim'):
        o.location.y=-2.225
        o.location.z-=0.05

for o in scene.objects:
    if o.name=='Door_Recess' or o.name=='Door_Main' or o.name.startswith('Door_Glass_'):
        o.location.x += 0.16

for o in list(scene.objects):
    if o.name.startswith('EntryV11_'):
        bpy.data.objects.remove(o,do_unlink=True)
ex0,ex1=0.08,1.46; er=.77; ey0,ey1=-3.04,-1.72; ezE,ezR=2.52,3.10
solid_poly('EntryV11_RoofL',[(ex0,ey0,ezE),(er,ey0,ezR),(er,ey1,ezR),(ex0,ey1,ezE)],RB)
solid_poly('EntryV11_RoofR',[(er,ey0,ezR),(ex1,ey0,ezE),(ex1,ey1,ezE),(er,ey1,ezR)],RB)
box('EntryV11_Ridge',(er,(ey0+ey1)/2,ezR+.05),(.14,ey1-ey0+.10,.14),RD,.04)
tri_prism_y('EntryV11_Pediment',ex0+.10,ex1-.10,ey0+.02,ey0+.10,2.48,3.00,TR)
for side,eave in [('L',ex0),('R',ex1)]:
    p0=Vector((eave,0,ezE));p1=Vector((er,0,ezR));d=p1-p0;L=d.length;u=d.normalized();ang=-math.atan2(d.z,d.x)
    for r in range(3):
        p=p0+u*((r+.5)*L/3)
        for c in range(5):
            y=ey0+(c+.5)*(ey1-ey0)/5
            box(f'EntryV11_Tile_{side}_{r}_{c}',(p.x,y,p.z+.04),(L/3*.90,(ey1-ey0)/5*.90,.034),RM,.006,(0,ang,0))

for nm in ('SideDoorV11','SideDoorV11_Glass'):
    o=bpy.data.objects.get(nm)
    if o:bpy.data.objects.remove(o,do_unlink=True)
box('SideDoorV11',(2.035,0.72,1.43),(.07,.72,1.58),WD,.012)
box('SideDoorV11_Glass',(2.075,0.72,1.75),(.025,.50,.30),GL,.003)

for o in list(scene.objects):
    if o.name.startswith('HipTileV11_'):bpy.data.objects.remove(o,do_unlink=True)
xMax=2.20; ridgeMax=1.15; yF=-2.05; yB=2.42; yR=.35; zE=3.22; zR=5.38
p0=Vector((xMax,yR,zE));p1=Vector((ridgeMax,yR,zR));d=p1-p0;L=d.length;u=d.normalized();ang=-math.atan2(d.z,d.x)
rows=7
for r in range(rows):
    t=(r+.48)/rows;p=p0+u*(t*L);ya=yF+(yR-yF)*t;yb=yB+(yR-yB)*t;span=yb-ya;cols=max(2,int(span/.36));tw=span/cols*.91;tl=L/rows*.90
    for c in range(cols):
        y=ya+(c+.5)*span/cols
        box(f'HipTileV11_{r}_{c}',(p.x,y,p.z+.045),(tl,tw,.035),RM if (r+c)%5==0 else RB,.006,(0,ang,0))

cap=bpy.data.objects.get('Chimney_Cap')
if cap:
    cap.dimensions=(.68,.68,.16);bpy.context.view_layer.objects.active=cap;cap.select_set(True);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);cap.select_set(False)

try:
    scene.view_settings.exposure=0.04
    scene.view_settings.look='Medium High Contrast'
except Exception:pass
scene.world.use_nodes=True;bg=scene.world.node_tree.nodes.get('Background')
if bg:
    bg.inputs['Color'].default_value=(0.98,0.965,0.925,1);bg.inputs['Strength'].default_value=.42
for o in list(scene.objects):
    if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
def area(n,loc,e,size,t,color):
    bpy.ops.object.light_add(type='AREA',location=loc);L=bpy.context.object;L.name=n;L.data.energy=e;L.data.shape='DISK';L.data.size=size;L.data.color=color;look(L,t)
area('V11_Key',(-6.5,-7.2,11.0),850,6.5,(0,-.2,2.1),(1,.95,.87))
area('V11_Fill',(6.5,-4.5,8.5),300,8.0,(0,0,2.1),(.94,.97,1))
area('V11_SoftFront',(0,-8,6.5),130,8.5,(0,-.3,1.8),(1,.98,.93))
bpy.ops.object.light_add(type='SUN',location=(0,0,8));sun=bpy.context.object;sun.data.energy=.62;sun.data.angle=math.radians(20);sun.rotation_euler=(math.radians(28),math.radians(-18),math.radians(-36))

cam=scene.camera
views={
'preview_perspective.png':((10.4,-11.6,10.1),(0,-.05,2.15),9.70),
'preview_front.png':((0,-14.5,4.8),(-.2,0,2.15),9.3),
'preview_back.png':((0,14.5,4.8),(-.2,0,2.15),9.3),
'preview_left.png':((-14.5,0,4.8),(0,0,2.15),9.3),
'preview_right.png':((14.5,0,4.8),(0,0,2.15),9.3),
'preview_top.png':((0,0,16),(0,0,0),9.6)}
for fn,(pos,t,scale) in views.items():
    cam.location=pos;cam.data.ortho_scale=scale;look(cam,t);scene.render.filepath=os.path.join(OUT,fn);bpy.ops.render.render(write_still=True)
cam.location=(10.4,-11.6,10.1);cam.data.ortho_scale=9.70;look(cam,(0,-.05,2.15))
for o in scene.objects:o.select_set(False)
for o in scene.objects:
    if o.type=='MESH' and o.name!='Backdrop':o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'model.glb'),export_format='GLB',use_selection=True,export_apply=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'model.blend'))
print('REFERENCE_REFINE_V11_COMPLETE')
