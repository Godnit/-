import bpy, bmesh, math, os, random
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) if '__file__' in globals() else os.getcwd()
OUT = os.path.join(ROOT, 'output')
os.makedirs(OUT, exist_ok=True)
random.seed(7)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'METERS'
scene.unit_settings.scale_length = 1.0
scene.render.resolution_x = 768
scene.render.resolution_y = 768
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.render.engine = 'BLENDER_EEVEE' if bpy.app.version < (4,2,0) else 'BLENDER_EEVEE_NEXT'
try:
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'Medium High Contrast'
    scene.view_settings.exposure = 0.12
except Exception:
    pass

def mat(name, color, rough=0.65, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    if bs:
        bs.inputs['Base Color'].default_value = (*color, 1)
        if 'Roughness' in bs.inputs: bs.inputs['Roughness'].default_value = rough
        if 'Metallic' in bs.inputs: bs.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*color, 1)
    return m

M = {}
M['wall']      = mat('Wall_Warm_Cream', (0.88,0.84,0.74), 0.82)
M['wall_hi']   = mat('Wall_Siding_Highlight', (0.96,0.93,0.85), 0.86)
M['trim']      = mat('Trim_OffWhite', (0.965,0.955,0.91), 0.72)
M['roof']      = mat('Roof_Blue', (0.055,0.245,0.48), 0.58)
M['roof_mid']  = mat('Roof_Blue_Mid', (0.075,0.31,0.58), 0.56)
M['roof_dark'] = mat('Roof_Blue_Dark', (0.035,0.17,0.36), 0.60)
M['wood']      = mat('Wood_Warm_Brown', (0.48,0.245,0.095), 0.68)
M['wood2']     = mat('Wood_Awning', (0.65,0.34,0.13), 0.66)
M['brick']     = mat('Chimney_Brick', (0.72,0.43,0.19), 0.78)
M['brick_hi']  = mat('Chimney_Mortar', (0.90,0.72,0.48), 0.82)
M['glass']     = mat('Glass_BlueGray', (0.095,0.19,0.20), 0.24)
M['stone']     = mat('Foundation_Stone', (0.53,0.40,0.30), 0.87)
M['step']      = mat('Path_Stone', (0.78,0.72,0.63), 0.90)
M['grass']     = mat('Grass', (0.34,0.64,0.085), 0.92)
M['earth']     = mat('Base_Edge', (0.52,0.36,0.23), 0.92)
M['hedge']     = mat('Hedge_Dark', (0.18,0.44,0.045), 0.92)
M['leaf']      = mat('Leaf_Mid', (0.30,0.60,0.055), 0.90)
M['leaf_hi']   = mat('Leaf_Light', (0.48,0.73,0.09), 0.90)
M['leaf_dark'] = mat('Leaf_Dark', (0.13,0.34,0.035), 0.92)
M['flower_p']  = mat('Flower_Pink', (0.93,0.46,0.62), 0.70)
M['flower_y']  = mat('Flower_Yellow', (0.97,0.72,0.10), 0.72)
M['flower_w']  = mat('Flower_White', (0.98,0.95,0.86), 0.74)
M['dark']      = mat('Dark', (0.018,0.018,0.018), 0.9)
M['bg']        = mat('Backdrop_Cream', (0.94,0.92,0.86), 0.98)

def assign(o,m):
    if hasattr(o.data, 'materials'):
        o.data.materials.clear(); o.data.materials.append(m)

def bevel(o, width=0.02, seg=2):
    if width <= 0: return
    md = o.modifiers.new('Bevel','BEVEL')
    md.width = width; md.segments = seg; md.limit_method='ANGLE'
    bpy.context.view_layer.objects.active = o
    try: bpy.ops.object.modifier_apply(modifier=md.name)
    except Exception: pass

def box(name, loc, dims, material, bev=0.012, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o=bpy.context.object; o.name=name; o.dimensions=dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(o,material); bevel(o,bev)
    return o

def cyl(name, loc, r, depth, material, verts=20):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc)
    o=bpy.context.object; o.name=name; assign(o,material); return o

def sphere(name, loc, r, material, scale=(1,1,1), sub=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    assign(o,material)
    for p in o.data.polygons: p.use_smooth=True
    return o

def mesh_obj(name, verts, faces, material):
    me=bpy.data.meshes.new(name+'_Mesh'); me.from_pydata(verts,[],faces); me.validate(); me.update()
    o=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o); assign(o,material); return o

def solid_poly(name, pts, material, th=0.075):
    me=bpy.data.meshes.new(name+'_Mesh'); me.from_pydata(pts,[],[tuple(range(len(pts)))]); me.validate(); me.update()
    o=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o); assign(o,material)
    bpy.context.view_layer.objects.active=o; o.select_set(True)
    md=o.modifiers.new('Solidify','SOLIDIFY'); md.thickness=th; md.offset=0
    bpy.ops.object.modifier_apply(modifier=md.name); o.select_set(False)
    return o

def tri_prism_y(name,x0,x1,y0,y1,z0,zp,material):
    xm=(x0+x1)/2
    v=[(x0,y0,z0),(x1,y0,z0),(xm,y0,zp),(x0,y1,z0),(x1,y1,z0),(xm,y1,zp)]
    f=[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)]
    return mesh_obj(name,v,f,material)

def look_at(o,target):
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()

def roof_tile(name, loc, dims, rot, idx):
    material=[M['roof'],M['roof_mid'],M['roof'],M['roof_dark']][idx%4]
    return box(name,loc,dims,material,0.008,rot)

box('Base_Earth',(0,0,0.11),(9.4,8.8,0.38),M['earth'],0.16)
box('Base_Grass',(0,0,0.31),(9.08,8.48,0.20),M['grass'],0.14)
box('Foundation_Main',(-0.18,0.12,0.61),(4.45,4.20,0.40),M['stone'],0.035)
box('House_Main',(-0.18,0.12,1.95),(4.35,4.10,2.64),M['wall'],0.022)
box('House_RightWing',(1.58,0.25,1.56),(1.35,3.45,1.98),M['wall'],0.022)
for i,z in enumerate([0.92,1.13,1.34,1.55,1.76,1.97,2.18,2.39,2.60,2.81,3.02]):
    box(f'Siding_F_{i}',(-0.52,-1.95,z),(3.55,0.024,0.030),M['wall_hi'],0.002)
for i,z in enumerate([0.92,1.13,1.34,1.55,1.76,1.97,2.18,2.39,2.60,2.81]):
    box(f'Siding_R_{i}',(2.01,0.10,z),(0.024,3.65,0.030),M['wall_hi'],0.002)

xMin,xMax=-2.58,2.20
yF,yB=-2.05,2.42
yR=0.35
zE,zR=3.22,5.38
ridgeMin,ridgeMax=-1.15,1.15
solid_poly('Roof_Main_Front',[(xMin,yF,zE),(xMax,yF,zE),(ridgeMax,yR,zR),(ridgeMin,yR,zR)],M['roof'])
solid_poly('Roof_Main_Back',[(xMin,yB,zE),(ridgeMin,yR,zR),(ridgeMax,yR,zR),(xMax,yB,zE)],M['roof'])
solid_poly('Roof_Main_LeftHip',[(xMin,yB,zE),(xMin,yF,zE),(ridgeMin,yR,zR)],M['roof'])
solid_poly('Roof_Main_RightHip',[(xMax,yF,zE),(xMax,yB,zE),(ridgeMax,yR,zR)],M['roof'])
box('Roof_Main_Ridge',((ridgeMin+ridgeMax)/2,yR,zR+0.06),(ridgeMax-ridgeMin+0.18,0.16,0.16),M['roof_dark'],0.05)

def shingle_trapezoid(prefix, front=True, rows=8, cols=13):
    y0=yF if front else yB
    d=Vector((0,yR-y0,zR-zE)); L=d.length; u=d.normalized(); ang=math.atan2(d.z,d.y)
    for r in range(rows):
        t=(r+0.48)/rows
        p=Vector((0,y0,zE))+u*(t*L)
        xl=xMin+(ridgeMin-xMin)*t; xr=xMax+(ridgeMax-xMax)*t
        span=xr-xl; cw=span/cols*0.92; rl=L/rows*0.91
        stagger=(0.44*span/cols if r%2 else 0)
        for c in range(cols):
            x=xl+(c+0.5)*span/cols+stagger
            if x>xr-cw*0.20: continue
            roof_tile(f'{prefix}_{r}_{c}',(x,p.y,p.z+0.045),(cw,rl,0.038),(ang,0,0),r+c)
shingle_trapezoid('Shingle_MainF',True)
shingle_trapezoid('Shingle_MainB',False)
for i,t in enumerate([.14,.27,.40,.53,.66,.79,.90]):
    x=xMax+(ridgeMax-xMax)*t; z=zE+(zR-zE)*t
    ya=yF+(yR-yF)*t; yb=yB+(yR-yB)*t
    box(f'RightHip_Course_{i}',(x,(ya+yb)/2,z+0.045),(0.035,abs(yb-ya)*0.96,0.035),M['roof_mid'],0.004)

gx0,gx1=-2.62,0.30
gy0,gy1=-2.18,0.72
gridge=-1.15
gzE,gzR=3.18,5.18
solid_poly('Roof_FrontGable_Left',[(gx0,gy0,gzE),(gridge,gy0,gzR),(gridge,gy1,gzR),(gx0,gy1,gzE)],M['roof'])
solid_poly('Roof_FrontGable_Right',[(gridge,gy0,gzR),(gx1,gy0,gzE),(gx1,gy1,gzE),(gridge,gy1,gzR)],M['roof'])
box('Roof_FrontGable_Ridge',(gridge,(gy0+gy1)/2,gzR+0.055),(0.16,gy1-gy0+0.12,0.16),M['roof_dark'],0.05)
tri_prism_y('Front_Gable_Wall',gx0+0.18,gx1-0.18,gy0+0.09,gy0+0.20,3.08,4.96,M['wall'])
for i,z in enumerate([3.28,3.48,3.68,3.88,4.08,4.28,4.48]):
    half=max(0.15,(4.96-z)/(4.96-3.08)*(gx1-gx0-0.5)/2)
    box(f'GableSiding_{i}',(gridge,gy0+0.07,z),(half*2,0.025,0.028),M['wall_hi'],0.002)

def shingles_gable(prefix,eave_x,rows=7,cols=8):
    p0=Vector((eave_x,0,gzE)); p1=Vector((gridge,0,gzR)); d=p1-p0; L=d.length; u=d.normalized(); ang=-math.atan2(d.z,d.x)
    for r in range(rows):
        s=(r+0.48)*L/rows; p=p0+u*s; tl=L/rows*0.91; yw=(gy1-gy0)/cols*0.92
        for c in range(cols):
            y=gy0+(c+0.5)*(gy1-gy0)/cols
            roof_tile(f'{prefix}_{r}_{c}',(p.x,y,p.z+0.046),(tl,yw,0.038),(0,ang,0),r+c)
shingles_gable('Shingle_GableL',gx0)
shingles_gable('Shingle_GableR',gx1)

dx=0.78; dy=-0.82
box('Dormer_Body',(dx,dy,4.12),(1.22,0.95,1.04),M['wall'],0.014)
tri_prism_y('Dormer_Gable',dx-0.61,dx+0.61,dy-0.50,dy-0.38,4.50,5.04,M['wall'])
solid_poly('Dormer_Roof_L',[(dx-0.76,dy-0.58,4.54),(dx,dy-0.58,5.12),(dx,dy+0.42,5.12),(dx-0.76,dy+0.42,4.54)],M['roof'])
solid_poly('Dormer_Roof_R',[(dx,dy-0.58,5.12),(dx+0.76,dy-0.58,4.54),(dx+0.76,dy+0.42,4.54),(dx,dy+0.42,5.12)],M['roof'])
box('Dormer_Ridge',(dx,dy-0.08,5.17),(0.15,1.12,0.15),M['roof_dark'],0.045)
for side,eave in [('L',dx-0.76),('R',dx+0.76)]:
    p0=Vector((eave,0,4.54));p1=Vector((dx,0,5.12));d=p1-p0;L=d.length;u=d.normalized();ang=-math.atan2(d.z,d.x)
    for r in range(4):
        p=p0+u*((r+0.5)*L/4)
        for c in range(5):
            y=dy-0.52+(c+0.5)*0.19
            roof_tile(f'DormerTile_{side}_{r}_{c}',(p.x,y,p.z+0.04),(L/4*.90,.17,.035),(0,ang,0),r+c)

box('Chimney',(1.28,0.78,5.55),(0.54,0.54,2.15),M['brick'],0.012)
for i,z in enumerate([4.73,4.98,5.23,5.48,5.73,5.98,6.23]):
    box(f'Chimney_Mortar_{i}',(1.28,0.78,z),(0.56,0.56,0.025),M['brick_hi'],0.001)
box('Chimney_Cap',(1.28,0.78,6.68),(0.75,0.75,0.19),M['trim'],0.025)
box('Chimney_Hole',(1.28,0.78,6.77),(0.38,0.38,0.12),M['dark'],0.01)

def front_window(pre,x,z,w,h,brown_trim=False):
    y=-2.025
    box(pre+'_Top',(x,y,z+h/2),(w+0.16,0.09,0.10),M['trim'],0.008)
    box(pre+'_Bot',(x,y,z-h/2),(w+0.20,0.13,0.10),M['trim'],0.008)
    box(pre+'_L',(x-w/2,y,z),(0.10,0.09,h),M['trim'],0.008)
    box(pre+'_R',(x+w/2,y,z),(0.10,0.09,h),M['trim'],0.008)
    box(pre+'_Glass',(x,y-0.045,z),(w-0.12,0.035,h-0.12),M['glass'],0.003)
    box(pre+'_V',(x,y-0.07,z),(0.055,0.04,h-0.14),M['trim'],0.003)
    box(pre+'_H',(x,y-0.07,z),(w-0.14,0.04,0.055),M['trim'],0.003)
    if brown_trim:
        box(pre+'_BrownL',(x-w/2-0.13,y-0.015,z),(0.13,0.08,h*0.94),M['wood'],0.01)
        box(pre+'_BrownR',(x+w/2+0.13,y-0.015,z),(0.13,0.08,h*0.94),M['wood'],0.01)

def side_window(pre,y,z,w,h):
    x=2.015
    box(pre+'_Top',(x,y,z+h/2),(0.09,w+0.16,0.10),M['trim'],0.008)
    box(pre+'_Bot',(x,y,z-h/2),(0.13,w+0.20,0.10),M['trim'],0.008)
    box(pre+'_L',(x,y-w/2,z),(0.09,0.10,h),M['trim'],0.008)
    box(pre+'_R',(x,y+w/2,z),(0.09,0.10,h),M['trim'],0.008)
    box(pre+'_Glass',(x+0.045,y,z),(0.035,w-0.12,h-0.12),M['glass'],0.003)
    box(pre+'_V',(x+0.07,y,z),(0.04,0.055,h-0.14),M['trim'],0.003)
    box(pre+'_H',(x+0.07,y,z),(0.04,w-0.14,0.055),M['trim'],0.003)

front_window('Window_Front_Lower',-1.18,1.63,1.12,1.18,True)
box('Window_Awning',(-1.18,-2.14,2.33),(1.48,0.30,0.12),M['wood2'],0.018,(math.radians(-10),0,0))
front_window('Window_Front_Upper',-1.18,3.58,0.82,0.90,False)
box('UpperTrimL',(-1.72,-2.03,3.58),(0.10,0.08,0.84),M['wood'],0.008)
box('UpperTrimR',(-0.64,-2.03,3.58),(0.10,0.08,0.84),M['wood'],0.008)

def dormer_window():
    x=dx; y=dy-0.505; z=4.20; w=.68; h=.78
    box('DormerWin_T',(x,y,z+h/2),(w+.14,.08,.09),M['trim'],.006)
    box('DormerWin_B',(x,y,z-h/2),(w+.16,.11,.09),M['trim'],.006)
    box('DormerWin_L',(x-w/2,y,z),(.09,.08,h),M['trim'],.006)
    box('DormerWin_R',(x+w/2,y,z),(.09,.08,h),M['trim'],.006)
    box('DormerWin_Glass',(x,y-.04,z),(w-.12,.03,h-.12),M['glass'],.002)
    box('DormerWin_V',(x,y-.06,z),(.05,.03,h-.14),M['trim'],.002)
    box('DormerWin_H',(x,y-.06,z),(w-.14,.03,.05),M['trim'],.002)
dormer_window()
side_window('Window_Right_Porch',-0.20,1.47,0.88,0.98)

box('Door_Recess',(0.55,-2.035,1.39),(0.92,0.12,1.82),M['trim'],0.012)
box('Door_Main',(0.55,-2.11,1.38),(0.70,0.09,1.58),M['wood'],0.012)
for j,x in enumerate([0.39,0.55,0.71]):
    box(f'Door_Glass_{j}',(x,-2.17,1.80),(0.10,0.025,0.28),M['glass'],0.002)

box('Porch_Deck_F',(1.25,-2.42,0.76),(2.60,0.93,0.18),M['step'],0.025)
box('Porch_Deck_R',(2.23,-0.40,0.76),(0.93,3.20,0.18),M['step'],0.025)
for i,(y,z,w) in enumerate([(-3.04,.49,1.18),(-2.78,.61,1.02),(-2.56,.70,.88)]):
    box(f'FrontStep_{i}',(0.62,y,z),(w,0.42,0.14),M['step'],0.024)
for i,(x,z,w) in enumerate([(3.02,.49,1.06),(2.78,.61,.90),(2.57,.70,.76)]):
    box(f'SideStep_{i}',(x,0.60,z),(0.42,w,0.14),M['step'],0.024)

pA=(-0.05,-2.98,2.55); pB=(-0.05,-1.70,3.10)
d=Vector(pB)-Vector(pA); L=d.length; mid=(Vector(pA)+Vector(pB))/2; ang=math.atan2(d.z,d.y)
box('PorchRoof_Front',(1.22,mid.y,mid.z),(2.72,L,0.10),M['roof'],0.012,(ang,0,0))
for r in range(4):
    p=Vector(pA)+d.normalized()*((r+.5)*L/4)
    for c in range(8):
        x=-0.05+(c+.5)*2.72/8
        roof_tile(f'PorchFTile_{r}_{c}',(x,p.y,p.z+.05),(2.72/8*.9,L/4*.9,.034),(ang,0,0),r+c)
pA=Vector((2.98,-0.25,2.54)); pB=Vector((1.70,-0.25,3.08)); d=pB-pA; L=d.length; mid=(pA+pB)/2; ang=-math.atan2(d.z,d.x)
box('PorchRoof_Right',(mid.x,-0.25,mid.z),(L,3.25,0.10),M['roof'],0.012,(0,ang,0))
for r in range(4):
    p=pA+d.normalized()*((r+.5)*L/4)
    for c in range(9):
        y=-1.78+(c+.5)*3.25/9
        roof_tile(f'PorchRTile_{r}_{c}',(p.x,y,p.z+.05),(L/4*.9,3.25/9*.9,.034),(0,ang,0),r+c)

posts=[(-0.02,-2.78),(0.95,-2.78),(1.90,-2.78),(2.66,-2.78),(2.72,-1.70),(2.72,-0.68),(2.72,0.35),(2.72,1.25)]
for i,(x,y) in enumerate(posts):
    box(f'PorchPost_{i}',(x,y,1.65),(0.15,0.15,1.86),M['trim'],0.014)
    box(f'PorchPostBase_{i}',(x,y,0.86),(0.23,0.23,0.28),M['trim'],0.014)
    box(f'PorchPostCap_{i}',(x,y,2.55),(0.23,0.23,0.14),M['trim'],0.014)
box('PorchBeam_F',(1.32,-2.78,2.59),(2.78,0.15,0.18),M['trim'],0.012)
box('PorchBeam_R',(2.72,-0.18,2.59),(0.15,3.06,0.18),M['trim'],0.012)

def rail_x(pre,x0,x1,y,z=.98):
    L=x1-x0
    box(pre+'_Top',((x0+x1)/2,y,z+0.18),(L,.07,.09),M['trim'],.006)
    box(pre+'_Bot',((x0+x1)/2,y,z-0.21),(L,.06,.07),M['trim'],.006)
    n=max(2,int(L/.18))
    for i in range(n+1): box(f'{pre}_B{i}',(x0+i*L/n,y,z),(.05,.05,.49),M['trim'],.004)
def rail_y(pre,y0,y1,x,z=.98):
    L=y1-y0
    box(pre+'_Top',(x,(y0+y1)/2,z+0.18),(.07,L,.09),M['trim'],.006)
    box(pre+'_Bot',(x,(y0+y1)/2,z-0.21),(.06,L,.07),M['trim'],.006)
    n=max(2,int(L/.18))
    for i in range(n+1): box(f'{pre}_B{i}',(x,y0+i*L/n,z),(.05,.05,.49),M['trim'],.004)
rail_x('RailFrontA',-0.02,0.12,-2.78)
rail_x('RailFrontB',1.12,2.60,-2.78)
rail_y('RailSideA',-2.45,-1.22,2.72)
rail_y('RailSideB',-0.98,1.16,2.72)

for i in range(5): box(f'PathStraight_{i}',(-1.85,-3.55+i*.46,0.45),(0.92,0.40,0.075),M['step'],0.025)
for i in range(5): box(f'PathTurn_{i}',(-1.55+i*.48,-1.72,0.45),(0.42,0.72,0.075),M['step'],0.025)

def hedge_box(name,x,y,sx=.48,sy=.48,h=.52,light=False):
    return box(name,(x,y,0.55),(sx,sy,h),M['leaf'] if light else M['hedge'],0.17)
def bush(name,x,y,r=.24,light=False):
    mm=M['leaf_hi'] if light else M['hedge']
    sphere(name+'A',(x,y,0.58),r,mm,(1.0,.90,.90),2)
    sphere(name+'B',(x+r*.36,y+r*.10,0.62),r*.70,mm,(1,.9,.9),2)
    sphere(name+'C',(x-r*.34,y-r*.10,0.61),r*.66,mm,(1,.9,.9),2)
def tree(name,x,y,s=1.0):
    cyl(name+'_Trunk',(x,y,0.92*s),0.11*s,1.30*s,M['wood'],18)
    cl=[(0,0,.49),(.25,.10,.31),(-.24,.10,.30),(.09,-.22,.29),(-.13,-.18,.28),(.04,.22,.28)]
    for i,(ox,oy,r) in enumerate(cl):
        mm=[M['leaf_hi'],M['leaf'],M['leaf_dark']][i%3]
        sphere(f'{name}_Leaf{i}',(x+ox*s,y+oy*s,1.62*s+(0.08*s if i==0 else 0)),r*s,mm,(1,.92,1.0),2)
def flower(name,x,y,kind='p'):
    bush(name+'_Bush',x,y,.17,True)
    mm={'p':M['flower_p'],'y':M['flower_y'],'w':M['flower_w']}[kind]
    for i,(ox,oy) in enumerate([(-.08,-.03),(.06,-.03),(-.01,.07),(.09,.08)]): sphere(f'{name}_F{i}',(x+ox,y+oy,.72),.042,mm,sub=1)

for i,x in enumerate([-4.00,-3.52,-3.04,-2.56]): hedge_box(f'HedgeFrontL_{i}',x,-3.08,.45,.48,.52,i%2==0)
for i,y in enumerate([-2.58,-2.08,-1.58,-1.08,-.58]): hedge_box(f'HedgeLeft_{i}',-4.00,y,.48,.44,.53,i%2==1)
tree_specs=[('Tree_Left',-3.72,0.15,1.02),('Tree_BackLeft',-3.10,2.60,.83),('Tree_Right',3.72,1.90,.93)]
for spec in tree_specs: tree(*spec)
pts=[(-2.42,-1.52,.23),(-1.92,-1.45,.22),(-1.48,-1.44,.20),(-.62,-1.46,.20),(.05,-1.50,.21),(1.45,-3.04,.23),(2.02,-3.02,.22),(2.55,-2.90,.23),(3.20,-2.48,.25),(3.38,-1.88,.24),(3.38,-1.18,.23),(3.35,-.48,.24),(3.28,.25,.23),(3.08,.88,.23),(-2.50,2.62,.22)]
for i,(x,y,r) in enumerate(pts): bush(f'Bush_{i}',x,y,r,i%2==0)
for i,(x,y,k) in enumerate([(-2.28,-1.22,'p'),(-1.60,-1.20,'w'),(-.85,-1.20,'y'),(.05,-1.28,'p'),(1.10,-3.12,'p'),(2.45,-3.06,'y'),(3.42,-1.52,'p'),(3.32,-.10,'w'),(3.10,.72,'y')]): flower(f'Flower_{i}',x,y,k)

def picket(name,x,y,axis='x'):
    dims=(.075,.06,.63) if axis=='x' else (.06,.075,.63)
    box(name,(x,y,.72),dims,M['trim'],.012)
    if axis=='x':
        v=[(x-.038,y-.03,1.035),(x+.038,y-.03,1.035),(x,y-.03,1.16),(x-.038,y+.03,1.035),(x+.038,y+.03,1.035),(x,y+.03,1.16)]
    else:
        v=[(x-.03,y-.038,1.035),(x+.03,y-.038,1.035),(x,y,1.16),(x-.03,y+.038,1.035),(x+.03,y+.038,1.035),(x,y,1.16)]
    mesh_obj(name+'_Tip',v,[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)],M['trim'])

fy=-3.95
xs=[-4.18+i*.30 for i in range(29)]
for i,x in enumerate(xs):
    if -2.36 < x < -1.34: continue
    picket(f'FenceFront_{i}',x,fy,'x')
box('FenceFrontRailL',(-3.32,fy,.75),(1.68,.055,.065),M['trim'],.005)
box('FenceFrontRailL2',(-3.32,fy,.94),(1.68,.055,.065),M['trim'],.005)
box('FenceFrontRailR',(1.50,fy,.75),(5.26,.055,.065),M['trim'],.005)
box('FenceFrontRailR2',(1.50,fy,.94),(5.26,.055,.065),M['trim'],.005)
rx=4.18
ys=[-3.67+i*.31 for i in range(24)]
for i,y in enumerate(ys): picket(f'FenceRight_{i}',rx,y,'y')
box('FenceRightRail',(rx,-.10,.75),(.055,7.20,.065),M['trim'],.005)
box('FenceRightRail2',(rx,-.10,.94),(.055,7.20,.065),M['trim'],.005)
for i,(x,y) in enumerate([(-4.24,fy),(-2.48,fy),(-1.24,fy),(4.18,fy),(4.18,3.52)]):
    box(f'FencePost_{i}',(x,y,.74),(.15,.15,.86),M['trim'],.014); box(f'FencePostCap_{i}',(x,y,1.20),(.21,.21,.10),M['trim'],.012)

for o in [o for o in scene.objects if o.type=='MESH']:
    bpy.context.view_layer.objects.active=o; o.select_set(True)
    try: bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    except Exception: pass
    bm=bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-6)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    bm.to_mesh(o.data); bm.free(); o.data.update(); o.select_set(False)

scene.world.use_nodes=True
bg=scene.world.node_tree.nodes.get('Background')
if bg:
    bg.inputs['Color'].default_value=(0.965,0.948,0.90,1)
    bg.inputs['Strength'].default_value=0.55
box('Backdrop',(0,0,-0.20),(18,18,.14),M['bg'],0.02)

def area(name,loc,energy,size,target,color=(1,1,1)):
    bpy.ops.object.light_add(type='AREA',location=loc)
    L=bpy.context.object;L.name=name;L.data.energy=energy;L.data.shape='DISK';L.data.size=size;L.data.color=color;look_at(L,target)
    return L
area('Key_Soft',(-6.5,-7.5,11.5),980,6.5,(0,-.2,2.2),(1.0,.95,.87))
area('Fill_Camera',(7.0,-7.0,8.5),360,8.0,(0,-.1,2.2),(.94,.97,1.0))
area('Fill_Left',(-5.5,3.0,7.0),230,7.0,(-.2,.2,2.0),(1.0,.98,.93))
bpy.ops.object.light_add(type='SUN',location=(0,0,8));sun=bpy.context.object;sun.data.energy=.70;sun.data.angle=math.radians(18);sun.rotation_euler=(math.radians(28),math.radians(-18),math.radians(-36))

bpy.ops.object.camera_add(location=(10.4,-11.6,10.1))
cam=bpy.context.object;cam.name='Camera';cam.data.type='ORTHO';cam.data.ortho_scale=9.70;scene.camera=cam;look_at(cam,(0,-.05,2.15))
views={
'preview_perspective.png':((10.4,-11.6,10.1),(0,-.05,2.15),9.70),
'preview_front.png':((0,-14.5,4.8),(-.2,0,2.15),9.3),
'preview_back.png':((0,14.5,4.8),(-.2,0,2.15),9.3),
'preview_left.png':((-14.5,0,4.8),(0,0,2.15),9.3),
'preview_right.png':((14.5,0,4.8),(0,0,2.15),9.3),
'preview_top.png':((0,0,16),(0,0,0),9.6),
}
for fn,(pos,target,scale) in views.items():
    cam.location=pos; cam.data.ortho_scale=scale; look_at(cam,target)
    scene.render.filepath=os.path.join(OUT,fn)
    bpy.ops.render.render(write_still=True)
cam.location=(10.4,-11.6,10.1);cam.data.ortho_scale=9.70;look_at(cam,(0,-.05,2.15))
blend=os.path.join(OUT,'model.blend');bpy.ops.wm.save_as_mainfile(filepath=blend)
for o in scene.objects:o.select_set(False)
for o in scene.objects:
    if o.type=='MESH' and o.name!='Backdrop':o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'model.glb'),export_format='GLB',use_selection=True,export_apply=True)
bpy.ops.wm.save_as_mainfile(filepath=blend)
print('REFERENCE_REBUILD_V10_COMPLETE')
