import bpy, math, os
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..')) if '__file__' in globals() else os.getcwd()
OUT=os.path.join(ROOT,'output')
scene=bpy.context.scene

def mat(name): return bpy.data.materials.get(name)
def set_base(name,c,rough=.62):
    m=mat(name)
    if not m:return
    m.diffuse_color=(*c,1)
    if m.use_nodes:
        bs=m.node_tree.nodes.get('Principled BSDF')
        if bs:
            bs.inputs['Base Color'].default_value=(*c,1)
            if 'Roughness' in bs.inputs: bs.inputs['Roughness'].default_value=rough

def assign(o,m):
    if o and o.type=='MESH': o.data.materials.clear();o.data.materials.append(m)
def box(name,loc,dims,m,bev=.005,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc,rotation=rot);o=bpy.context.object;o.name=name;o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);assign(o,m)
    if bev>0:
        md=o.modifiers.new('Bevel','BEVEL');md.width=bev;md.segments=2;md.limit_method='ANGLE';bpy.context.view_layer.objects.active=o
        try:bpy.ops.object.modifier_apply(modifier=md.name)
        except Exception:pass
    return o
def mesh_obj(name,verts,faces,m):
    me=bpy.data.meshes.new(name+'_Mesh');me.from_pydata(verts,[],faces);me.validate();me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);assign(o,m);return o
def solid_poly(name,pts,m,th=.075):
    me=bpy.data.meshes.new(name+'_Mesh');me.from_pydata(pts,[],[tuple(range(len(pts)))]);me.validate();me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);assign(o,m)
    bpy.context.view_layer.objects.active=o;o.select_set(True);md=o.modifiers.new('Solidify','SOLIDIFY');md.thickness=th;md.offset=0;bpy.ops.object.modifier_apply(modifier=md.name);o.select_set(False);return o
def tri_prism_y(name,x0,x1,y0,y1,z0,zp,m):
    xm=(x0+x1)/2;v=[(x0,y0,z0),(x1,y0,z0),(xm,y0,zp),(x0,y1,z0),(x1,y1,z0),(xm,y1,zp)];f=[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)];return mesh_obj(name,v,f,m)
def sphere(name,loc,r,m,scale=(1,1,1),sub=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=r,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);assign(o,m)
    for p in o.data.polygons:p.use_smooth=True
    return o
def look(o,t): o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
def remove_prefixes(prefixes):
    for o in list(scene.objects):
        if any(o.name.startswith(p) for p in prefixes): bpy.data.objects.remove(o,do_unlink=True)

remove_prefixes(['Roof_Main_','Shingle_Main','RightHip_Course_','HipTileV11_','Shingle_Gable','DormerTile_','PorchFTile_','PorchRTile_','EntryV11_','EntryV13_','EntryV12_','Roof_FrontGable_'])
set_base('Wall_Warm_Cream',(0.86,0.82,0.73),.84)
set_base('Wall_Siding_Highlight',(0.94,0.91,0.83),.86)
set_base('Roof_Blue',(0.032,0.155,0.335),.61)
set_base('Roof_Blue_Mid',(0.045,0.205,0.430),.60)
set_base('Roof_Blue_Dark',(0.020,0.095,0.225),.63)
RB=mat('Roof_Blue'); RM=mat('Roof_Blue_Mid'); RD=mat('Roof_Blue_Dark'); TR=mat('Trim_OffWhite')
seam=bpy.data.materials.get('Roof_Seam') or bpy.data.materials.new('Roof_Seam');seam.use_nodes=True
bs=seam.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.012,.055,.13,1);bs.inputs['Roughness'].default_value=.68

xMin,xMax=-2.56,1.90; ridgeMin,ridgeMax=-1.20,.92; yF,yB,yR=-2.08,2.40,.38; zE,zR=3.22,5.35
solid_poly('Roof_Main_Front',[(xMin,yF,zE),(xMax,yF,zE),(ridgeMax,yR,zR),(ridgeMin,yR,zR)],RB)
solid_poly('Roof_Main_Back',[(xMin,yB,zE),(ridgeMin,yR,zR),(ridgeMax,yR,zR),(xMax,yB,zE)],RB)
solid_poly('Roof_Main_LeftHip',[(xMin,yB,zE),(xMin,yF,zE),(ridgeMin,yR,zR)],RB)
solid_poly('Roof_Main_RightHip',[(xMax,yF,zE),(xMax,yB,zE),(ridgeMax,yR,zR)],RB)
box('Roof_Main_Ridge',((ridgeMin+ridgeMax)/2,yR,zR+.06),(ridgeMax-ridgeMin+.16,.15,.15),RD,.045)
GX0,GX1=-2.62,.24; GR=-1.18; GY0,GY1=-2.18,.72; GE,GRZ=3.18,5.12
solid_poly('Roof_FrontGable_Left',[(GX0,GY0,GE),(GR,GY0,GRZ),(GR,GY1,GRZ),(GX0,GY1,GE)],RB)
solid_poly('Roof_FrontGable_Right',[(GR,GY0,GRZ),(GX1,GY0,GE),(GX1,GY1,GE),(GR,GY1,GRZ)],RB)
box('Roof_FrontGable_Ridge',(GR,(GY0+GY1)/2,GRZ+.06),(.15,GY1-GY0+.12,.15),RD,.045)

def grid_y(prefix,x0,x1,y0,yr,z0,zr,rows=9,cols=12):
    d=Vector((0,yr-y0,zr-z0));L=d.length;u=d.normalized();ang=math.atan2(d.z,d.y)
    for r in range(1,rows):
        t=r/rows;p=Vector((0,y0,z0))+u*(t*L);xl=x0+(ridgeMin-x0)*t;xr=x1+(ridgeMax-x1)*t
        box(f'{prefix}_Course_{r}',((xl+xr)/2,p.y,p.z+.055),(max(.08,xr-xl),.032,.024),seam,.003,(ang,0,0))
        prevt=(r-.55)/rows;p0=Vector((0,y0,z0))+u*(prevt*L);segL=(t-prevt)*L*.88;n=max(3,int((xr-xl)/.36));offset=.5 if r%2 else 0
        for c in range(n):
            x=xl+(c+offset)*(xr-xl)/n
            if x<xl+.08 or x>xr-.08:continue
            pm=(p+p0)/2;box(f'{prefix}_Joint_{r}_{c}',(x,pm.y,pm.z+.058),(.022,segL,.022),seam,.002,(ang,0,0))
grid_y('MainF',xMin,xMax,yF,yR,zE,zR,9,13)
for r in range(1,8):
    t=r/8;x=xMax+(ridgeMax-xMax)*t;z=zE+(zR-zE)*t;ya=yF+(yR-yF)*t;yb=yB+(yR-yB)*t
    box(f'HipCourse_{r}',(x,(ya+yb)/2,z+.05),(.025,abs(yb-ya),.022),seam,.002)

def grid_x(prefix,eave,rr,y0,y1,z0,zr,rows=8,cols=8):
    p0=Vector((eave,0,z0));p1=Vector((rr,0,zr));d=p1-p0;L=d.length;u=d.normalized();ang=-math.atan2(d.z,d.x)
    for r in range(1,rows):
        t=r/rows;p=p0+u*(t*L);box(f'{prefix}_Course_{r}',(p.x,(y0+y1)/2,p.z+.055),(.032,y1-y0,.024),seam,.003,(0,ang,0))
        prevt=(r-.55)/rows;pp=p0+u*(prevt*L);seg=(t-prevt)*L*.88;off=.5 if r%2 else 0
        for c in range(cols):
            y=y0+(c+off)*(y1-y0)/cols
            if y<y0+.05 or y>y1-.05:continue
            pm=(p+pp)/2;box(f'{prefix}_Joint_{r}_{c}',(pm.x,y,pm.z+.058),(seg,.022,.022),seam,.002,(0,ang,0))
grid_x('GableL',GX0,GR,GY0,GY1,GE,GRZ,8,8);grid_x('GableR',GX1,GR,GY0,GY1,GE,GRZ,8,8)

for o in scene.objects:
    if o.name.startswith('Door_'): o.location.x += .42
    if o.name.startswith('Window_Front_Upper') or o.name.startswith('UpperTrim'):
        o.location.x += .04;o.location.y=-2.225;o.location.z-=.04
    if o.name.startswith('Dormer_') or o.name.startswith('DormerWin_'):
        o.location.x += .28;o.location.y += .05
for o in scene.objects:
    if o.type=='MESH' and o.name.startswith('Dormer_Roof_'): assign(o,RB)
DX=1.06;DY=-.77
for side,eave in [('L',DX-.76),('R',DX+.76)]:
    p0=Vector((eave,0,4.54));p1=Vector((DX,0,5.12));d=p1-p0;L=d.length;u=d.normalized();ang=-math.atan2(d.z,d.x)
    for r in range(1,4):
        p=p0+u*(r/4*L);box(f'DormerCourse_{side}_{r}',(p.x,DY-.08,p.z+.05),(.028,1.02,.022),seam,.002,(0,ang,0))
for o in scene.objects:
    if o.type=='MESH' and o.name.startswith('PorchRoof_'):assign(o,RB)
pA=Vector((0,-2.98,2.52));pB=Vector((0,-1.72,3.05));d=pB-pA;L=d.length;u=d.normalized();ang=math.atan2(d.z,d.y)
for r in range(1,5):
    p=pA+u*(r/5*L);box(f'PorchFrontCourse_{r}',(1.45,p.y,p.z+.05),(3.05,.028,.022),seam,.002,(ang,0,0))
pA=Vector((3.18,0,2.57));pB=Vector((1.72,0,3.07));d=pB-pA;L=d.length;u=d.normalized();ang=-math.atan2(d.z,d.x)
for r in range(1,5):
    p=pA+u*(r/5*L);box(f'PorchSideCourse_{r}',(p.x,-.25,p.z+.05),(.028,3.35,.022),seam,.002,(0,ang,0))

ex0,ex1=.55,1.50;er=1.02;ey0,ey1=-2.89,-1.85;ezE,ezR=2.60,2.99
solid_poly('EntryV15_L',[(ex0,ey0,ezE),(er,ey0,ezR),(er,ey1,ezR),(ex0,ey1,ezE)],RB)
solid_poly('EntryV15_R',[(er,ey0,ezR),(ex1,ey0,ezE),(ex1,ey1,ezE),(er,ey1,ezR)],RB)
box('EntryV15_Ridge',(er,(ey0+ey1)/2,ezR+.045),(.13,ey1-ey0+.08,.13),RD,.035)
tri_prism_y('EntryV15_Pediment',ex0+.08,ex1-.08,ey0+.01,ey0+.08,2.56,2.93,TR)

leaf=mat('Leaf_Mid');leafhi=mat('Leaf_Light')
for o in scene.objects:
    if o.name.startswith('TreeLeft'):o.location.x-=.25;o.location.y-=.85
for i,(x,y,r) in enumerate([(-2.30,-1.25,.22),(-1.85,-1.18,.20),(-1.42,-1.18,.19),(-.92,-1.20,.18),(-.43,-1.23,.18),(.08,-1.30,.19),(.65,-3.12,.18),(1.15,-3.16,.20),(1.62,-3.15,.19),(2.05,-3.07,.19),(2.48,-2.98,.20),(2.90,-2.78,.21),(3.22,-2.42,.22),(3.36,-1.95,.21),(3.38,-1.45,.20),(3.34,-.92,.19),(3.25,-.38,.19),(3.10,.20,.18)]):
    sphere(f'V15Bush_{i}',(x,y,.58),r,leafhi if i%4==0 else leaf,(1,.88,.9),2)

scene.world.use_nodes=True;bg=scene.world.node_tree.nodes.get('Background')
if bg:bg.inputs['Color'].default_value=(.98,.97,.94,1);bg.inputs['Strength'].default_value=.44
for o in list(scene.objects):
    if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
def area(n,loc,e,size,t,color):
    bpy.ops.object.light_add(type='AREA',location=loc);L=bpy.context.object;L.name=n;L.data.energy=e;L.data.shape='DISK';L.data.size=size;L.data.color=color;look(L,t)
area('V15_Key',(-6.5,-7.3,11.2),760,6.8,(0,-.2,2.1),(1,.95,.88));area('V15_Fill',(6,-4.5,8.2),280,8.2,(0,0,2.1),(.95,.98,1));area('V15_Front',(0,-8.5,6.4),125,8.5,(0,-.3,1.8),(1,.98,.93))
bpy.ops.object.light_add(type='SUN',location=(0,0,8));sun=bpy.context.object;sun.data.energy=.54;sun.data.angle=math.radians(20);sun.rotation_euler=(math.radians(28),math.radians(-18),math.radians(-36))
try:scene.view_settings.exposure=.02;scene.view_settings.look='Medium High Contrast'
except Exception:pass
cam=scene.camera
views={'preview_perspective.png':((9.6,-12.2,10.5),(-.15,-.05,2.30),9.10),'preview_front.png':((0,-14.5,4.8),(-.2,0,2.15),9.3),'preview_back.png':((0,14.5,4.8),(-.2,0,2.15),9.3),'preview_left.png':((-14.5,0,4.8),(0,0,2.15),9.3),'preview_right.png':((14.5,0,4.8),(0,0,2.15),9.3),'preview_top.png':((0,0,16),(0,0,0),9.6)}
for fn,(pos,t,scale) in views.items():cam.location=pos;cam.data.ortho_scale=scale;look(cam,t);scene.render.filepath=os.path.join(OUT,fn);bpy.ops.render.render(write_still=True)
cam.location=(9.6,-12.2,10.5);cam.data.ortho_scale=9.10;look(cam,(-.15,-.05,2.30))
for o in scene.objects:o.select_set(False)
for o in scene.objects:
    if o.type=='MESH' and o.name!='Backdrop':o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'model.glb'),export_format='GLB',use_selection=True,export_apply=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'model.blend'))
print('REFERENCE_REFINE_V15_COMPLETE')
