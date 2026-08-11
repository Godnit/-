import bpy, bmesh, math, os
from mathutils import Vector

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..')) if '__file__' in globals() else os.getcwd()
OUT=os.path.join(ROOT,'output'); os.makedirs(OUT,exist_ok=True)

# ---------- reset ----------
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'; scene.unit_settings.length_unit='METERS'; scene.unit_settings.scale_length=1.0
scene.render.resolution_x=768; scene.render.resolution_y=768; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=False
scene.render.engine='BLENDER_EEVEE' if bpy.app.version<(4,2,0) else 'BLENDER_EEVEE_NEXT'
try:
    scene.view_settings.view_transform='Standard'
    scene.view_settings.look='Medium High Contrast'
except Exception: pass

# ---------- materials ----------
def mat(name,c,rough=.65,metal=0):
    m=bpy.data.materials.new(name); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*c,1); p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
    m.diffuse_color=(*c,1); return m
M={
'wall':mat('Wall_Main',(0.92,0.89,0.80),.82), 'trim':mat('Trim_White',(0.98,0.97,0.93),.72),
'roof':mat('Roof_Blue',(0.008,0.035,0.12),.62), 'roof2':mat('Roof_Tile',(0.012,0.060,0.20),.60),
'wood':mat('Wood',(0.42,0.20,0.07),.7), 'wood2':mat('Wood_Light',(0.62,0.31,0.10),.7),
'glass':mat('Glass',(0.08,0.20,0.26),.22), 'brick':mat('Brick',(0.70,0.39,0.15),.8), 'brick2':mat('Brick_Light',(0.83,0.58,0.30),.8),
'stone':mat('Stone',(0.52,0.42,0.34),.86), 'path':mat('Path',(0.73,0.65,0.55),.9),
'grass':mat('Grass',(0.30,0.58,0.07),.9), 'green':mat('Shrub',(0.20,0.46,0.03),.9), 'green2':mat('Shrub_Light',(0.36,0.66,0.08),.9),
'green3':mat('Tree_Dark',(0.13,0.34,0.02),.9), 'pink':mat('Flower_Pink',(0.92,0.35,0.54),.7), 'yellow':mat('Flower_Yellow',(1.0,0.70,0.07),.7),
'whiteflower':mat('Flower_White',(0.98,0.94,0.85),.7), 'dark':mat('Dark',(0.02,0.02,0.02),.85), 'bg':mat('Backdrop',(0.88,0.84,0.76),.95)
}

def assign(o,m): o.data.materials.clear(); o.data.materials.append(m)
def bevel(o,w=.02,seg=2):
    if w<=0:return
    md=o.modifiers.new('Bevel','BEVEL'); md.width=w; md.segments=seg; md.limit_method='ANGLE'; bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=md.name)
def box(n,loc,dims,m,bev=.015,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc,rotation=rot); o=bpy.context.object; o.name=n; o.dimensions=dims; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); assign(o,m); bevel(o,bev); return o
def cyl(n,loc,r,d,m,v=18):
    bpy.ops.mesh.primitive_cylinder_add(vertices=v,radius=r,depth=d,location=loc); o=bpy.context.object; o.name=n; assign(o,m); return o
def ico(n,loc,r,m,sub=2,scale=(1,1,1)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=r,location=loc); o=bpy.context.object; o.name=n; o.scale=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); assign(o,m); return o
def mesh(n,verts,faces,m):
    me=bpy.data.meshes.new(n+'_Mesh'); me.from_pydata(verts,[],faces); me.validate(); me.update(); o=bpy.data.objects.new(n,me); bpy.context.collection.objects.link(o); assign(o,m); return o

def tri_prism(n,x0,x1,z0,z1,y0,y1,m):
    xc=(x0+x1)/2; v=[(x0,y0,z0),(x1,y0,z0),(xc,y0,z1),(x0,y1,z0),(x1,y1,z0),(xc,y1,z1)]; f=[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)]; return mesh(n,v,f,m)

def slope_x(n,xe,xr,yc,yd,ze,zr,m,th=.11):
    p0=Vector((xe,yc,ze)); p1=Vector((xr,yc,zr)); d=p1-p0; L=d.length; mid=(p0+p1)/2; a=math.atan2(d.z,d.x); return box(n,mid,(L,yd,th),m,.012,(0,-a,0))
def slope_y(n,ye,yr,xc,xd,ze,zr,m,th=.11):
    p0=Vector((xc,ye,ze)); p1=Vector((xc,yr,zr)); d=p1-p0; L=d.length; mid=(p0+p1)/2; a=math.atan2(d.z,d.y); return box(n,mid,(xd,L,th),m,.012,(a,0,0))

def tiles_x(pre,xe,xr,yc,yd,ze,zr,rows,cols):
    p0=Vector((xe,yc,ze)); p1=Vector((xr,yc,zr)); d=p1-p0; L=d.length; u=d.normalized(); a=math.atan2(d.z,d.x); tl=L/rows*.90; tw=yd/cols*.88
    for r in range(rows):
        s=(r+.46)*L/rows
        for c in range(cols):
            y=yc-yd/2+(c+.5)*yd/cols; p=p0+u*s; box(f'{pre}_{r:02d}_{c:02d}',(p.x,y,p.z+.07),(tl,tw,.052),M['roof2'],.012,(0,-a,0))
def tiles_y(pre,ye,yr,xc,xd,ze,zr,rows,cols):
    p0=Vector((xc,ye,ze)); p1=Vector((xc,yr,zr)); d=p1-p0; L=d.length; u=d.normalized(); a=math.atan2(d.z,d.y); tl=L/rows*.90; tw=xd/cols*.88
    for r in range(rows):
        s=(r+.46)*L/rows
        for c in range(cols):
            x=xc-xd/2+(c+.5)*xd/cols; p=p0+u*s; box(f'{pre}_{r:02d}_{c:02d}',(x,p.y,p.z+.07),(tw,tl,.052),M['roof2'],.012,(a,0,0))

def win_front(pre,x,y,z,w,h,shutters=None):
    box(pre+'_Frame',(x,y,z),(w,.11,h),M['trim'],.012); box(pre+'_Glass',(x,y-.065,z),(w*.76,.035,h*.76),M['glass'],.004)
    box(pre+'_V',(x,y-.085,z),(.05,.05,h*.76),M['trim'],.004); box(pre+'_H',(x,y-.085,z),(w*.76,.05,.05),M['trim'],.004); box(pre+'_Sill',(x,y-.11,z-h*.52),(w*1.08,.18,.09),M['trim'],.01)
    if shutters:
        mm=M[shutters]; box(pre+'_SL',(x-w*.63,y-.07,z),(w*.19,.08,h*.92),mm,.012); box(pre+'_SR',(x+w*.63,y-.07,z),(w*.19,.08,h*.92),mm,.012)
def win_side(pre,x,y,z,w,h):
    box(pre+'_Frame',(x,y,z),(.11,w,h),M['trim'],.012); box(pre+'_Glass',(x+.065,y,z),(.035,w*.76,h*.76),M['glass'],.004)
    box(pre+'_V',(x+.085,y,z),(.05,.05,h*.76),M['trim'],.004); box(pre+'_H',(x+.085,y,z),(.05,w*.76,.05),M['trim'],.004); box(pre+'_Sill',(x+.11,y,z-h*.52),(.18,w*1.08,.09),M['trim'],.01)

def railing_x(pre,x0,x1,y,z=.85):
    L=x1-x0; box(pre+'_Top',((x0+x1)/2,y,z+.27),(L,.07,.09),M['trim'],.008); box(pre+'_Bot',((x0+x1)/2,y,z-.15),(L,.06,.07),M['trim'],.008)
    n=max(2,int(L/.20))
    for i in range(n+1): box(f'{pre}_{i:02d}',(x0+i*L/n,y,z+.04),(.05,.05,.48),M['trim'],.006)
def railing_y(pre,y0,y1,x,z=.85):
    L=y1-y0; box(pre+'_Top',(x,(y0+y1)/2,z+.27),(.07,L,.09),M['trim'],.008); box(pre+'_Bot',(x,(y0+y1)/2,z-.15),(.06,L,.07),M['trim'],.008)
    n=max(2,int(L/.20))
    for i in range(n+1): box(f'{pre}_{i:02d}',(x,y0+i*L/n,z+.04),(.05,.05,.48),M['trim'],.006)
def bush(pre,x,y,r=.27,light=False):
    mm=M['green2'] if light else M['green']; ico(pre+'a',(x,y,.50),r,mm,2,(1,.85,.9)); ico(pre+'b',(x+r*.4,y+r*.12,.58),r*.7,mm,2); ico(pre+'c',(x-r*.38,y-r*.08,.56),r*.66,mm,2)
def tree(pre,x,y,s=1):
    cyl(pre+'_tr',(x,y,.85*s),.11*s,1.18*s,M['wood'],16)
    cl=[(0,0,.52),(.28,.12,.36),(-.27,.10,.34),(.10,-.26,.34),(-.16,-.21,.31),(.04,.22,.33)]
    for i,(ox,oy,r) in enumerate(cl): ico(f'{pre}_{i}',(x+ox*s,y+oy*s,1.60*s+(0.10*s if i==0 else 0)),r*s,M['green3'] if i%3==0 else M['green2'],2)
def flower(pre,x,y,which='pink'):
    bush(pre+'_b',x,y,.20,True)
    for i,(ox,oy) in enumerate([(-.08,-.04),(.07,-.03),(-.02,.08),(.09,.08)]): ico(f'{pre}_{i}',(x+ox,y+oy,.67),.045,M[which],1)

# ---------- diorama base ----------
box('Base_Earth',(0,0,.10),(9.1,8.55,.34),M['stone'],.16); box('Base_Grass',(0,0,.31),(8.80,8.25,.21),M['grass'],.13)
# front walkway with gap in fence
for i in range(5): box(f'Path_{i}',(-2.15,-3.45+i*.50,.45),(1.05,.44,.09),M['path'],.03)
for i in range(3): box(f'PathTurn_{i}',(-1.60+i*.52,-1.48,.45),(.46,.55,.08),M['path'],.025)

# ---------- house body ----------
box('Foundation',(-.25,.15,.60),(4.25,4.15,.40),M['stone'],.035)
box('House_Main',(-.25,.15,1.95),(4.15,4.05,2.62),M['wall'],.022)
# front-left projecting gable wall triangle only
tri_prism('Front_Gable',-2.30,.20,3.26,4.86,-1.93,-1.82,M['wall'])
# subtle siding
for i,z in enumerate([.93,1.18,1.43,1.68,1.93,2.18,2.43,2.68,2.93,3.18]): box(f'SidingFront_{i}',(-.98,-1.935,z),(2.55,.026,.03),M['trim'],.003)

# facade windows
win_front('WinLower',-1.20,-2.00,1.75,1.10,1.13,'wood')
win_front('WinUpper',-1.20,-2.00,3.62,.82,.90,'roof')
# brown lower awning
box('WinLower_Awning',(-1.20,-2.12,2.40),(1.45,.20,.12),M['wood2'],.018,rot=(math.radians(-10),0,0))
# entry near porch
box('Door',(0.62,-2.00,1.38),(.76,.11,1.60),M['wood2'],.015)
box('DoorFrameTop',(0.62,-2.07,2.23),(.93,.10,.09),M['trim'],.01); box('DoorFrameL',(0.16,-2.07,1.39),(.09,.10,1.70),M['trim'],.01); box('DoorFrameR',(1.08,-2.07,1.39),(.09,.10,1.70),M['trim'],.01)
for j,x in enumerate([.45,.62,.79]): box(f'DoorPane{j}',(x,-2.07,1.80),(.11,.03,.30),M['glass'],.003)

# ---------- cross-gabled roof ----------
# main roof ridge left-right (X), front/back slopes in Y
xc=-.20; xd=4.65; yr=.40; zR=5.05; yF=-2.08; yB=2.38; zE=3.18
slope_y('RoofMainFront',yF,yr,xc,xd,zE,zR,M['roof']); slope_y('RoofMainBack',yB,yr,xc,xd,zE,zR,M['roof'])
tiles_y('TileMainFront',yF,yr,xc,xd,zE,zR,7,11); tiles_y('TileMainBack',yB,yr,xc,xd,zE,zR,7,11)
box('RoofMainRidge',(xc,yr,zR+.06),(xd+.15,.17,.17),M['roof2'],.055)
# front-left cross gable ridge front-back (Y)
xr=-1.18; ycg=-.70; yd=3.25; xL=-2.65; xR=.30; zEg=3.18; zRg=4.95
slope_x('RoofCrossLeft',xL,xr,ycg,yd,zEg,zRg,M['roof']); slope_x('RoofCrossRight',xR,xr,ycg,yd,zEg,zRg,M['roof'])
tiles_x('TileCrossLeft',xL,xr,ycg,yd,zEg,zRg,6,8); tiles_x('TileCrossRight',xR,xr,ycg,yd,zEg,zRg,6,8)
box('RoofCrossRidge',(xr,ycg,zRg+.06),(.17,yd+.15,.17),M['roof2'],.055)

# ---------- dormer on main front slope ----------
# body front faces -Y
box('DormerBody',(.85,-.68,4.02),(1.22,.98,1.03),M['wall'],.018)
tri_prism('DormerGable',.24,1.46,4.45,4.96,-1.18,-1.08,M['wall'])
slope_x('DormerRoofL',.12,.85,-.67,1.30,4.43,5.02,M['roof']); slope_x('DormerRoofR',1.58,.85,-.67,1.30,4.43,5.02,M['roof'])
tiles_x('DormerTileL',.12,.85,-.67,1.30,4.43,5.02,4,5); tiles_x('DormerTileR',1.58,.85,-.67,1.30,4.43,5.02,4,5)
box('DormerRidge',(.85,-.67,5.07),(.15,1.40,.15),M['roof2'],.05)
win_front('WinDormer',.85,-1.19,4.18,.72,.78,None)

# ---------- chimney ----------
box('Chimney',(1.35,.88,5.45),(.52,.52,2.25),M['brick'],.01)
for i,z in enumerate([4.62,4.87,5.12,5.37,5.62,5.87,6.12,6.37]): box(f'ChimneyBand{i}',(1.35,.88,z),(.55,.55,.026),M['brick2'],.002)
box('ChimneyCap',(1.35,.88,6.63),(.72,.72,.17),M['stone'],.02); box('ChimneyHole',(1.35,.88,6.73),(.34,.34,.12),M['dark'],.01)

# ---------- wraparound porch ----------
box('PorchFront',(1.62,-2.43,.73),(2.55,.92,.18),M['path'],.03); box('PorchSide',(2.33,-.40,.73),(1.06,3.15,.18),M['path'],.03)
box('Step1',(.70,-3.03,.49),(1.05,.42,.16),M['path'],.025); box('Step2',(.70,-2.76,.61),(.92,.34,.14),M['path'],.025)
# front lean roof and side lean roof
slope_y('PorchRoofFront',-2.98,-1.72,1.55,3.05,2.52,3.05,M['roof']); tiles_y('PorchTileFront',-2.98,-1.72,1.55,3.05,2.52,3.05,4,8)
slope_x('PorchRoofSide',3.22,1.73,-.25,3.45,2.58,3.10,M['roof']); tiles_x('PorchTileSide',3.22,1.73,-.25,3.45,2.58,3.10,4,9)
# small entry gable over door
slope_x('EntryRoofL',-.05,.62,-2.34,1.20,2.62,3.10,M['roof']); slope_x('EntryRoofR',1.30,.62,-2.34,1.20,2.62,3.10,M['roof']); tiles_x('EntryTileL',-.05,.62,-2.34,1.20,2.62,3.10,3,4); tiles_x('EntryTileR',1.30,.62,-2.34,1.20,2.62,3.10,3,4); box('EntryRidge',(.62,-2.34,3.15),(.15,1.30,.15),M['roof2'],.045)
# posts
posts=[(.00,-2.83),(.95,-2.83),(1.95,-2.83),(2.78,-2.83),(2.85,-1.75),(2.85,-.75),(2.85,.30),(2.85,1.05)]
for i,(x,y) in enumerate(posts):
    box(f'Post{i}',(x,y,1.65),(.15,.15,1.88),M['trim'],.016); box(f'PostBase{i}',(x,y,.82),(.23,.23,.23),M['trim'],.016); box(f'PostCap{i}',(x,y,2.56),(.22,.22,.14),M['trim'],.016)
box('BeamFront',(1.40,-2.83,2.59),(2.90,.15,.18),M['trim'],.014); box('BeamSide',(2.85,-.34,2.59),(.15,2.85,.18),M['trim'],.014)
railing_x('RailFrontA',-.02,.15,-2.83); railing_x('RailFrontB',1.28,2.70,-2.83); railing_y('RailSideA',-2.48,-1.28,2.85); railing_y('RailSideB',-.90,.90,2.85)
# right wall window under porch
win_side('WinSide',1.86,-.35,1.58,.86,.96)

# ---------- fence (lower than previous model) ----------
def picket(n,x,y,axis='x'):
    dims=(.08,.06,.58) if axis=='x' else (.06,.08,.58); box(n,(x,y,.72),dims,M['trim'],.014)
    if axis=='x': v=[(x-.04,y-.03,1.01),(x+.04,y-.03,1.01),(x,y-.03,1.13),(x-.04,y+.03,1.01),(x+.04,y+.03,1.01),(x,y+.03,1.13)]
    else: v=[(x-.03,y-.04,1.01),(x+.03,y-.04,1.01),(x,y,1.13),(x-.03,y+.04,1.01),(x+.03,y+.04,1.01),(x,y,1.13)]
    f=[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)]; mesh(n+'Tip',v,f,M['trim'])
fy=-3.92
for i,x in enumerate([-4.0+i*.31 for i in range(27)]):
    if not (-2.72<x<-1.55): picket(f'FenceF{i}',x,fy,'x')
box('FRailL',(-3.36,fy,.73),(1.24,.055,.065),M['trim'],.006); box('FRailL2',(-3.36,fy,.92),(1.24,.055,.065),M['trim'],.006); box('FRailR',(1.20,fy,.73),(5.00,.055,.065),M['trim'],.006); box('FRailR2',(1.20,fy,.92),(5.00,.055,.065),M['trim'],.006)
rx=4.06
for i,y in enumerate([-3.65+i*.33 for i in range(23)]): picket(f'FenceR{i}',rx,y,'y')
box('RRail',(rx,.0,.73),(.055,7.35,.065),M['trim'],.006); box('RRail2',(rx,.0,.92),(.055,7.35,.065),M['trim'],.006)
for i,(x,y) in enumerate([(-4.10,fy),(-2.82,fy),(-1.45,fy),(4.06,fy),(4.06,3.72)]): box(f'FencePost{i}',(x,y,.74),(.16,.16,.82),M['trim'],.018); box(f'FencePostCap{i}',(x,y,1.18),(.21,.21,.10),M['trim'],.014)

# ---------- landscaping ----------
for i,x in enumerate([-3.68,-3.20,-2.72]): box(f'HedgeF{i}',(x,-3.04,.70),(.46,.48,.50),M['green'],.15)
for i,y in enumerate([-2.52,-2.02,-1.52,-1.02,-.52]): box(f'HedgeL{i}',(-3.70,y,.70),(.49,.44,.50),M['green'],.15)
tree('TreeLeft',-3.60,.20,1.0); tree('TreeBack',-3.05,2.65,.88); tree('TreeRight',3.55,1.95,.92)
for i,(x,y,r) in enumerate([(-2.45,-1.55,.25),(-1.95,-1.47,.23),(-1.50,-1.48,.21),(-.45,-1.48,.22),(.05,-1.55,.22),(1.60,-3.05,.24),(2.15,-3.02,.23),(2.70,-2.90,.24),(3.20,-2.45,.26),(3.35,-1.85,.25),(3.34,-1.20,.23),(3.33,-.55,.25),(3.28,.18,.24),(3.06,.88,.24),(-2.40,2.65,.24)]): bush(f'Bush{i}',x,y,r,i%2==0)
for i,(x,y,c) in enumerate([(-2.30,-1.25,'pink'),(-1.65,-1.22,'whiteflower'),(-.85,-1.22,'yellow'),(.10,-1.30,'pink'),(1.20,-3.12,'pink'),(2.50,-3.05,'yellow'),(3.42,-1.48,'pink'),(3.30,-.10,'whiteflower'),(3.10,.70,'yellow')]): flower(f'Flower{i}',x,y,c)

# ---------- cleanup ----------
for o in [o for o in scene.objects if o.type=='MESH']:
    bpy.context.view_layer.objects.active=o; o.select_set(True); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bm=bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-6); bmesh.ops.recalc_face_normals(bm,faces=bm.faces); bm.to_mesh(o.data); bm.free(); o.data.update(); o.select_set(False)

# ---------- lighting / camera ----------
def look(o,t): o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
scene.world.use_nodes=True; bg=scene.world.node_tree.nodes.get('Background'); bg.inputs['Color'].default_value=(0.90,0.86,0.77,1); bg.inputs['Strength'].default_value=.30
bpy.ops.object.light_add(type='AREA',location=(5.5,-7.0,10.5)); key=bpy.context.object; key.data.energy=820; key.data.size=5; look(key,(0,0,2.0))
bpy.ops.object.light_add(type='AREA',location=(-5,2,7)); fill=bpy.context.object; fill.data.energy=220; fill.data.size=6; look(fill,(0,0,2))
bpy.ops.object.light_add(type='SUN',location=(0,0,8)); sun=bpy.context.object; sun.data.energy=.85; sun.rotation_euler=(math.radians(25),math.radians(-20),math.radians(-30))
box('Backdrop',(0,0,-.18),(18,18,.14),M['bg'],.03)
bpy.ops.object.camera_add(location=(9.5,-11.5,8.5)); cam=bpy.context.object; cam.name='Camera'; cam.data.type='ORTHO'; cam.data.ortho_scale=10.4; scene.camera=cam; look(cam,(0,-.1,2.0))

# ---------- save/export/render ----------
blend=os.path.join(OUT,'model.blend'); bpy.ops.wm.save_as_mainfile(filepath=blend)
for o in scene.objects:o.select_set(False)
for o in scene.objects:
    if o.type=='MESH' and o.name!='Backdrop': o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'model.glb'),export_format='GLB',use_selection=True,export_apply=True)
views={
'preview_perspective.png':((9.5,-11.5,8.5),(0,-.1,2.0),10.4),
'preview_front.png':((0,-14,4.6),(-.3,0,2.1),9.6),
'preview_back.png':((0,14,4.6),(-.3,0,2.1),9.6),
'preview_left.png':((-14,0,4.6),(0,0,2.1),9.6),
'preview_right.png':((14,0,4.6),(0,0,2.1),9.6),
'preview_top.png':((0,0,16),(0,0,0),9.8)}
for fn,(pos,target,scale) in views.items(): cam.location=pos; cam.data.ortho_scale=scale; look(cam,target); scene.render.filepath=os.path.join(OUT,fn); bpy.ops.render.render(write_still=True)
cam.location=(9.5,-11.5,8.5); cam.data.ortho_scale=10.4; look(cam,(0,-.1,2.0)); bpy.ops.wm.save_as_mainfile(filepath=blend)
print('BUILD_COMPLETE_V4')
