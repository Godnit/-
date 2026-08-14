import bpy, math, os, random
from mathutils import Vector
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] if len(Path(__file__).resolve().parents) >= 3 else Path.cwd()
OUT = ROOT / 'output_cottage_multiview'
OUT.mkdir(parents=True, exist_ok=True)
random.seed(240813)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 900
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
scene.world.color = (0.82, 0.80, 0.74)
try:
    scene.view_settings.look = 'Medium High Contrast'
except Exception:
    pass
try:
    scene.view_settings.exposure = -0.15
except Exception:
    pass

def make_mat(name, color, rough=0.75, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Roughness'].default_value = rough
    bs.inputs['Metallic'].default_value = metallic
    m.diffuse_color = (*color, 1)
    return m

WOOD = make_mat('Wood_Main', (0.37,0.29,0.20), .90)
WOOD_LIGHT = make_mat('Wood_Trim_Light', (0.58,0.43,0.27), .88)
WOOD_DARK = make_mat('Wood_Dark', (0.24,0.19,0.15), .94)
WOOD_MID = make_mat('Wood_Mid', (0.45,0.34,0.24), .91)
ROOF = make_mat('Roof_BlueGrey', (0.20,0.27,0.34), .96)
ROOF_LIGHT = make_mat('Roof_BlueGrey_Light', (0.25,0.33,0.41), .96)
ROOF_DARK = make_mat('Roof_BlueGrey_Dark', (0.15,0.21,0.29), .97)
STONE = make_mat('Stone_Grey', (0.40,0.40,0.39), .98)
STONE_L = make_mat('Stone_Light', (0.53,0.52,0.49), .98)
STONE_D = make_mat('Stone_Dark', (0.31,0.32,0.33), .99)
GLASS = make_mat('Glass_BlueDark', (0.045,0.08,0.10), .45)
METAL = make_mat('Metal_Dark', (0.08,0.085,0.09), .40, .55)
GROUND = make_mat('Studio_Ground', (0.82,0.80,0.75), 1.0)

def set_mat(o, m):
    if o.type == 'MESH':
        o.data.materials.append(m)

def box(name, loc, scale, mat, rot=(0,0,0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    set_mat(o, mat)
    if bevel > 0:
        mod = o.modifiers.new('Soft_Edges','BEVEL'); mod.width=bevel; mod.segments=1
    return o

def mesh_obj(name, verts, faces, mat):
    me=bpy.data.meshes.new(name+'_Mesh'); me.from_pydata(verts,[],faces); me.validate(); me.update()
    o=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o); set_mat(o,mat); return o

def gable_panel(name, y, zbase, width, zpeak, thickness, mat):
    y0=y-thickness/2; y1=y+thickness/2; x=width/2
    v=[(-x,y0,zbase),(x,y0,zbase),(0,y0,zpeak),(-x,y1,zbase),(x,y1,zbase),(0,y1,zpeak)]
    f=[(0,1,2),(5,4,3),(0,3,4,1),(1,4,5,2),(2,5,3,0)]
    return mesh_obj(name,v,f,mat)

def beam_between(name, p1, p2, width, depth, mat):
    p1,p2=Vector(p1),Vector(p2); mid=(p1+p2)/2; vec=p2-p1; L=vec.length
    o=box(name, mid, (width, depth, L), mat)
    o.rotation_euler = vec.to_track_quat('Z','Y').to_euler()
    return o

def roof_z(absx):
    pts=[(0.0,5.25),(0.72,5.08),(1.46,4.73),(2.20,4.20),(2.90,3.62),(3.48,3.22)]
    x=min(abs(absx),pts[-1][0])
    for i in range(len(pts)-1):
        x0,z0=pts[i]; x1,z1=pts[i+1]
        if x<=x1:
            t=(x-x0)/(x1-x0); return z0+(z1-z0)*t
    return pts[-1][1]

def roof_angle(xa, xb, side):
    za,zb=roof_z(xa),roof_z(xb); ang=math.atan2(zb-za, xb-xa)
    return -ang if side<0 else ang

W=6.0; D=5.0; wall0=0.62; wall_top=3.18; roof_len=D+0.65
box('Foundation_Core',(0,0,0.28),(W, D, .56),STONE_D, bevel=.04)
stone_specs=[]
for side in (-1,1):
    x=-W/2+.35
    while x<W/2-.2:
        ww=random.uniform(.55,.88); hh=random.uniform(.35,.55)
        stone_specs.append((x+ww/2,side*(D/2+.03),.28,ww,.34,hh)); x+=ww+.04
for side in (-1,1):
    y=-D/2+.35
    while y<D/2-.2:
        dd=random.uniform(.55,.86); hh=random.uniform(.34,.54)
        stone_specs.append((side*(W/2+.03),y+dd/2,.28,.34,dd,hh)); y+=dd+.04
for i,(x,y,z,sx,sy,sz) in enumerate(stone_specs):
    m=[STONE,STONE_L,STONE_D][i%3]; box(f'Stone_{i:03d}',(x,y,z),(sx,sy,sz),m, rot=(0,0,random.uniform(-.04,.04)), bevel=.055)

box('Wall_Core',(0,0,(wall0+wall_top)/2),(W-0.18,D-0.18,wall_top-wall0),WOOD_DARK)
plank_w=.52
for side_y in (-1,1):
    x=-W/2+.20; idx=0
    while x<W/2-.18:
        ww=min(plank_w+random.uniform(-.05,.05), W/2-.18-x); col=[WOOD,WOOD_MID,WOOD_DARK][idx%3]
        box(f'FrontBack_Plank_{side_y}_{idx}',(x+ww/2,side_y*(D/2+.01),(wall0+wall_top)/2),(ww-.025,.10,wall_top-wall0-.05),col)
        x+=ww; idx+=1
for side_x in (-1,1):
    y=-D/2+.18; idx=0
    while y<D/2-.18:
        dd=min(.52+random.uniform(-.05,.05), D/2-.18-y); col=[WOOD,WOOD_MID,WOOD_DARK][(idx+1)%3]
        box(f'Side_Plank_{side_x}_{idx}',(side_x*(W/2+.01),y+dd/2,(wall0+wall_top)/2),(.10,dd-.025,wall_top-wall0-.05),col)
        y+=dd; idx+=1

gable_panel('Front_Gable',-D/2-.02,wall_top,W-.28,5.02,.12,WOOD)
gable_panel('Back_Gable', D/2+.02,wall_top,W-.28,5.02,.12,WOOD)
for y in (-D/2-.10,D/2+.10):
    box(f'WallBand_{y}',(0,y,wall0+.28),(W+.14,.20,.22),WOOD_LIGHT, bevel=.03)
    box(f'WallTopBand_{y}',(0,y,wall_top-.10),(W+.12,.20,.22),WOOD_LIGHT, bevel=.03)
for x in (-W/2-.10,W/2+.10):
    box(f'SideBandBottom_{x}',(x,0,wall0+.28),(.20,D+.15,.22),WOOD_LIGHT, bevel=.03)
    box(f'SideBandTop_{x}',(x,0,wall_top-.10),(.20,D+.15,.22),WOOD_LIGHT, bevel=.03)
    for y in (-D/2-.06,D/2+.06):
        box(f'CornerPost_{x}_{y}',(x,y,(wall0+wall_top)/2),(.25,.25,wall_top-wall0+.10),WOOD_LIGHT, bevel=.03)
for y,tag in [(-D/2-.12,'Front'),(D/2+.12,'Back')]:
    beam_between(tag+'_GableTrimL',(-W/2+.05,y,wall_top),(0,y,5.08),.18,.18,WOOD_LIGHT)
    beam_between(tag+'_GableTrimR',(0,y,5.08),(W/2-.05,y,wall_top),.18,.18,WOOD_LIGHT)
    box(tag+'_GableBase',(0,y,wall_top+.05),(W+.15,.18,.19),WOOD_LIGHT,bevel=.025)
    beam_between(tag+'_GableCenter',(0,y,wall_top+.05),(0,y,5.02),.15,.16,WOOD_LIGHT)
    beam_between(tag+'_GableCross',(-1.25,y,3.82),(1.25,y,3.82),.14,.16,WOOD_LIGHT)

band_edges=[0,.72,1.46,2.20,2.90,3.48]
for side in (-1,1):
    for bi in range(len(band_edges)-1):
        xa,xb=band_edges[bi],band_edges[bi+1]; ca=(xa+xb)/2*side; za,zb=roof_z(xa),roof_z(xb); z=(za+zb)/2
        length=math.sqrt((xb-xa)**2+(zb-za)**2)+.09; ang=roof_angle(xa,xb,side)
        box(f'RoofUnder_{side}_{bi}',(ca,0,z),(length,roof_len,.12),ROOF_DARK,rot=(0,ang,0))
cols=7
for side in (-1,1):
    for bi in range(len(band_edges)-1):
        xa,xb=band_edges[bi],band_edges[bi+1]; z=(roof_z(xa)+roof_z(xb))/2 + .07; xmid=(xa+xb)/2*side
        angle=roof_angle(xa,xb,side); seg_len=math.sqrt((xb-xa)**2+(roof_z(xb)-roof_z(xa))**2); tile_y=(roof_len+.20)/cols; stagger=(bi%2)*tile_y*.45
        for j in range(cols+1):
            y=-roof_len/2 - .08 + j*tile_y - stagger
            if y>roof_len/2+.08: continue
            m=[ROOF,ROOF_LIGHT,ROOF_DARK][(j+bi+(0 if side<0 else 1))%3]
            box(f'Shingle_{side}_{bi}_{j}',(xmid,y,z),(seg_len+.09,tile_y+.12,.075),m,rot=(0,angle,random.uniform(-.012,.012)),bevel=.018)
box('Roof_Ridge',(0,0,5.30),(.30,roof_len+.25,.25),WOOD_LIGHT,bevel=.05)
for side in (-1,1): box(f'EaveTrim_{side}',(side*3.48,0,3.19),(.22,roof_len+.25,.20),WOOD_LIGHT,bevel=.035)
for y,tag in [(-roof_len/2-.10,'Front'),(roof_len/2+.10,'Back')]:
    for side in (-1,1):
        for bi in range(len(band_edges)-1):
            xa,xb=band_edges[bi],band_edges[bi+1]
            beam_between(f'{tag}_Rake_{side}_{bi}',(side*xa,y,roof_z(xa)+.10),(side*xb,y,roof_z(xb)+.10),.16,.16,WOOD_LIGHT)

frontY=-D/2-.16
box('Front_Door',(-.66,frontY-.02,1.72),(1.05,.16,2.05),WOOD_MID,bevel=.03)
for x in (-1.20,-.12): box('DoorFrameV_'+str(x),(x,frontY-.14,1.72),(.16,.16,2.24),WOOD_LIGHT,bevel=.02)
box('DoorFrameTop',(-.66,frontY-.14,2.80),(1.24,.16,.17),WOOD_LIGHT,bevel=.02)
for i in range(4): box(f'DoorPlank_{i}',(-1.03+i*.25,frontY-.13,1.72),(.06,.05,1.90),WOOD_DARK)
bpy.ops.mesh.primitive_torus_add(major_radius=.11,minor_radius=.022,major_segments=12,minor_segments=6,location=(-.38,frontY-.26,1.72),rotation=(math.pi/2,0,0)); ring=bpy.context.object; ring.name='Door_Ring'; set_mat(ring,METAL)
wx=1.28; wz=2.03
box('Front_Window_Glass',(wx,frontY-.07,wz),(1.10,.11,1.18),GLASS)
for dx in (-.63,.63): box('Front_Window_FrameV_'+str(dx),(wx+dx,frontY-.17,wz),(.13,.14,1.43),WOOD_LIGHT)
for dz in (-.72,.72): box('Front_Window_FrameH_'+str(dz),(wx,frontY-.17,wz+dz),(1.38,.14,.13),WOOD_LIGHT)
box('Front_Window_MullionV',(wx,frontY-.19,wz),(.10,.15,1.25),WOOD_LIGHT)
box('Front_Window_MullionH',(wx,frontY-.19,wz),(1.18,.15,.10),WOOD_LIGHT)
box('Front_Window_Sill',(wx,frontY-.20,1.31),(1.45,.26,.18),WOOD_LIGHT,bevel=.025)
box('Porch_Deck',(-.55,-3.03,.83),(2.75,1.0,.24),WOOD_LIGHT,bevel=.03)
for i in range(3): box(f'Porch_Step_{i}',(-.55,-3.52-i*.32,.62-i*.17),(2.35+i*.20,.58,.20),WOOD_LIGHT,bevel=.025)
for x in (-1.82,.72):
    box('PorchPost_'+str(x),(x,-3.00,1.47),(.20,.20,1.55),WOOD_LIGHT,bevel=.025)
    beam_between('PorchBrace_'+str(x),(x,-3.00,2.07),(x+(.34 if x<0 else -.34),-2.62,2.48),.12,.12,WOOD_LIGHT)
for x0,x1 in [(-1.82,-1.28),(.18,.72)]:
    box('PorchRail_'+str(x0),((x0+x1)/2,-3.18,1.18),(x1-x0,.12,.12),WOOD_LIGHT)
    for x in [x0+.15,(x0+x1)/2,x1-.15]: box('PorchBaluster_'+str(x),(x,-3.18,.99),(.08,.08,.42),WOOD_LIGHT)
for side in (-1,1):
    box(f'PorchRoof_{side}',(-.55,-2.98+side*.36,2.68),(2.80,.84,.10),ROOF,rot=(side*math.radians(24),0,0),bevel=.018)
box('PorchRoofRidge',(-.55,-2.98,2.83),(2.95,.16,.16),WOOD_LIGHT,bevel=.03)

DX=-1.85; DY=-.55; DZ=4.35
box('Dormer_Body',(DX,DY,DZ),(1.05,1.28,1.12),WOOD_DARK)
box('Dormer_Window_Glass',(DX-.56,DY,DZ+.02),(.10,.78,.68),GLASS)
for yy in (DY-.47,DY+.47): box('Dormer_Frame_HSide_'+str(yy),(DX-.63,yy,DZ+.02),(.13,.13,.86),WOOD_LIGHT)
for zz in (DZ-.42,DZ+.42): box('Dormer_Frame_VSide_'+str(zz),(DX-.63,DY,zz),(.13,.98,.13),WOOD_LIGHT)
box('Dormer_MullionV',(DX-.65,DY,DZ+.02),(.12,.08,.72),WOOD_LIGHT)
box('Dormer_MullionH',(DX-.65,DY,DZ+.02),(.12,.82,.10),WOOD_LIGHT)
for side in (-1,1): box(f'DormerRoof_{side}',(DX-.02,DY+side*.40,DZ+.72),(1.58,.92,.10),ROOF,rot=(side*math.radians(32),0,0),bevel=.018)
box('Dormer_Ridge',(DX-.04,DY,DZ+.98),(1.67,.14,.14),WOOD_LIGHT,bevel=.03)
beam_between('DormerGableL',(DX-.67,DY-.62,DZ+.50),(DX-.67,DY,DZ+1.00),.10,.10,WOOD_LIGHT)
beam_between('DormerGableR',(DX-.67,DY,DZ+1.00),(DX-.67,DY+.62,DZ+.50),.10,.10,WOOD_LIGHT)

CX=-2.08; CY=1.25
box('Chimney_Core',(CX,CY,4.70),(.92,.92,2.42),STONE_D)
for row,z in enumerate([3.70,4.12,4.54,4.96,5.38,5.80]):
    h=.38
    for face in range(4):
        if face<2:
            y=CY+(-.47 if face==0 else .47)
            for k,x in enumerate([CX-.24,CX+.24]): box(f'ChStone_{row}_{face}_{k}',(x,y,z),(.44,.12,h),[STONE,STONE_L,STONE_D][(row+k)%3],bevel=.045)
        else:
            x=CX+(-.47 if face==2 else .47)
            for k,y in enumerate([CY-.24,CY+.24]): box(f'ChStone_{row}_{face}_{k}',(x,y,z),(.12,.44,h),[STONE_L,STONE,STONE_D][(row+k)%3],bevel=.045)
box('ChimneyCapL',(CX-.47,CY,6.06),(.22,1.13,.24),STONE_L,bevel=.04)
box('ChimneyCapR',(CX+.47,CY,6.06),(.22,1.13,.24),STONE_L,bevel=.04)
box('ChimneyCapF',(CX,CY-.47,6.06),(.72,.22,.24),STONE_L,bevel=.04)
box('ChimneyCapB',(CX,CY+.47,6.06),(.72,.22,.24),STONE_L,bevel=.04)
box('ChimneyHole',(CX,CY,6.04),(.70,.70,.06),WOOD_DARK)

sx=W/2+.10; sy=.55; sz=1.90
box('Side_Window_Glass',(sx,sy,sz),(.10,1.03,1.04),GLASS)
for y in (sy-.58,sy+.58): box('SideWinFrameY_'+str(y),(sx+.05,y,sz),(.14,.13,1.27),WOOD_LIGHT)
for z in (sz-.61,sz+.61): box('SideWinFrameZ_'+str(z),(sx+.05,sy,z),(.14,1.28,.13),WOOD_LIGHT)
box('SideWinMullionY',(sx+.08,sy,sz),(.14,.09,1.08),WOOD_LIGHT)
box('SideWinMullionZ',(sx+.08,sy,sz),(.14,1.10,.09),WOOD_LIGHT)

ground=box('Preview_Ground',(0,0,-.18),(16,16,.20),GROUND); ground['preview_only']=True
bpy.ops.object.light_add(type='SUN', location=(4,-6,10)); sun=bpy.context.object; sun.name='Sun'; sun.data.energy=2.0; sun.rotation_euler=(math.radians(32),0,math.radians(-28))
bpy.ops.object.light_add(type='AREA', location=(-4,-5,8)); area=bpy.context.object; area.name='Softbox'; area.data.energy=520; area.data.size=6.5; area.rotation_euler=(math.radians(25),0,math.radians(-35))
bpy.ops.object.light_add(type='AREA', location=(5,3,5)); fill=bpy.context.object; fill.name='Fill'; fill.data.energy=220; fill.data.size=5.0

def look_at(obj, target): obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(9,-11,8)); cam=bpy.context.object; cam.name='Camera'; scene.camera=cam; cam.data.lens=58

def render(name, loc, target=(0,0,2.7), lens=58):
    cam.location=loc; cam.data.lens=lens; look_at(cam,target); scene.render.filepath=str(OUT/name); bpy.ops.render.render(write_still=True)
render('preview_perspective.png',(9,-11,8.0),(0,-.25,2.75),58)
render('preview_front.png',(0,-12.5,3.4),(0,-.5,2.7),62)
render('preview_back.png',(0,12.5,3.6),(0,.5,2.7),62)
render('preview_left.png',(-12.5,0,3.8),(-.3,0,2.8),62)
render('preview_right.png',(12.5,0,3.8),(.3,0,2.8),62)
render('preview_top.png',(0,-.2,15),(0,0,1.2),58)
render('preview_rear_perspective.png',(-9,11,7.2),(0,.25,2.7),58)

bpy.data.objects.remove(ground, do_unlink=True)
cam.location=(9,-11,8); cam.data.lens=58; look_at(cam,(0,-.25,2.75))
for o in scene.objects:
    if o.type=='MESH':
        for p in o.data.polygons: p.use_smooth=False
blend_path=OUT/'cottage_multiview.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
for o in scene.objects: o.select_set(False)
for o in scene.objects:
    if o.type=='MESH': o.select_set(True)
bpy.context.view_layer.objects.active=next((o for o in scene.objects if o.type=='MESH'),None)
bpy.ops.export_scene.gltf(filepath=str(OUT/'cottage_multiview.glb'), export_format='GLB', use_selection=True, export_apply=True)
verts=sum(len(o.data.vertices) for o in scene.objects if o.type=='MESH')
faces=sum(len(o.data.polygons) for o in scene.objects if o.type=='MESH')
tris=sum(len(p.vertices)-2 for o in scene.objects if o.type=='MESH' for p in o.data.polygons)
with open(OUT/'model_report.txt','w',encoding='utf-8') as f:
    f.write('Cottage multiview reference build\n')
    f.write('Approx dimensions: 7.2m W x 7.0m D including porch x 6.2m H\n')
    f.write(f'Mesh objects: {sum(1 for o in scene.objects if o.type=="MESH")}\n')
    f.write(f'Vertices: {verts}\nFaces: {faces}\nTriangles approx: {tris}\n')
    f.write('Materials: Wood variants, Roof blue-grey variants, Stone variants, Glass, Metal\n')
    f.write('Reference features: curved-profile blue roof, dormer, stone chimney, timber walls, porch/steps, front window/door, stone foundation\n')
    f.write('GLB export: OK\nBLEND save: OK\n')
print('COTTAGE_MULTIVIEW_BUILD_OK', blend_path)
