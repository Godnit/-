import bpy, math, random
from pathlib import Path
from mathutils import Vector

# Build the approved exterior first, but keep helpers in this namespace so we can
# convert the shell into a real furnished interior and overwrite the final outputs.
base = Path(__file__).with_name('build_model.py')
src = base.read_text(encoding='utf-8')
src = src.replace("scene.world.color = (0.82, 0.80, 0.74)","if scene.world is None:\n    scene.world = bpy.data.worlds.new('World')\nscene.world.color = (0.76, 0.74, 0.70)")
src = src.replace("scene.view_settings.exposure = -0.15","scene.view_settings.exposure = -0.38")
src = src.replace("WOOD = make_mat('Wood_Main', (0.37,0.29,0.20), .90)","WOOD = make_mat('Wood_Main', (0.28,0.22,0.17), .92)")
src = src.replace("WOOD_LIGHT = make_mat('Wood_Trim_Light', (0.58,0.43,0.27), .88)","WOOD_LIGHT = make_mat('Wood_Trim_Light', (0.46,0.34,0.23), .91)")
src = src.replace("WOOD_DARK = make_mat('Wood_Dark', (0.24,0.19,0.15), .94)","WOOD_DARK = make_mat('Wood_Dark', (0.16,0.13,0.11), .96)")
src = src.replace("WOOD_MID = make_mat('Wood_Mid', (0.45,0.34,0.24), .91)","WOOD_MID = make_mat('Wood_Mid', (0.34,0.26,0.19), .93)")
src = src.replace("ROOF = make_mat('Roof_BlueGrey', (0.20,0.27,0.34), .96)","ROOF = make_mat('Roof_BlueGrey', (0.16,0.22,0.29), .97)")
src = src.replace("ROOF_LIGHT = make_mat('Roof_BlueGrey_Light', (0.25,0.33,0.41), .96)","ROOF_LIGHT = make_mat('Roof_BlueGrey_Light', (0.21,0.29,0.37), .97)")
src = src.replace("ROOF_DARK = make_mat('Roof_BlueGrey_Dark', (0.15,0.21,0.29), .97)","ROOF_DARK = make_mat('Roof_BlueGrey_Dark', (0.11,0.16,0.22), .98)")
src = src.replace("STONE = make_mat('Stone_Grey', (0.40,0.40,0.39), .98)","STONE = make_mat('Stone_Grey', (0.32,0.32,0.32), .99)")
src = src.replace("STONE_L = make_mat('Stone_Light', (0.53,0.52,0.49), .98)","STONE_L = make_mat('Stone_Light', (0.43,0.42,0.40), .99)")
src = src.replace("STONE_D = make_mat('Stone_Dark', (0.31,0.32,0.33), .99)","STONE_D = make_mat('Stone_Dark', (0.23,0.24,0.25), .99)")
src = src.replace("return -ang if side<0 else ang","return abs(ang)*side")
src = src.replace("rot=(side*math.radians(24),0,0)","rot=(-side*math.radians(24),0,0)")
src = src.replace("rot=(side*math.radians(32),0,0)","rot=(-side*math.radians(32),0,0)")
src = src.replace("sun.data.energy=2.0","sun.data.energy=1.15")
src = src.replace("area.data.energy=520","area.data.energy=280")
src = src.replace("fill.data.energy=220","fill.data.energy=100")
src = src.replace("render('preview_perspective.png',(9,-11,8.0),(0,-.25,2.75),58)","render('preview_perspective.png',(-9,-11,8.0),(0,-.25,2.75),58)")
src = src.replace("render('preview_rear_perspective.png',(-9,11,7.2),(0,.25,2.7),58)","render('preview_rear_perspective.png',(9,11,7.2),(0,.25,2.7),58)")
src = src.replace("cam.location=(9,-11,8); cam.data.lens=58; look_at(cam,(0,-.25,2.75))","cam.location=(-9,-11,8); cam.data.lens=58; look_at(cam,(0,-.25,2.75))")
exec(compile(src, str(base), 'exec'), globals())

# -----------------------------------------------------------------------------
# Convert opaque shell into a hollow house with true window openings.
# -----------------------------------------------------------------------------
def remove_obj(name):
    o = bpy.data.objects.get(name)
    if o:
        bpy.data.objects.remove(o, do_unlink=True)

def remove_prefix(prefix):
    for o in list(bpy.data.objects):
        if o.name.startswith(prefix):
            bpy.data.objects.remove(o, do_unlink=True)

remove_obj('Wall_Core')
remove_obj('Dormer_Body')
remove_prefix('FrontBack_Plank_-1_')
remove_prefix('Side_Plank_1_')

# Transparent, slightly blue game-friendly glass.
glass = bpy.data.materials.get('Glass_BlueDark')
if glass and glass.use_nodes:
    bs = glass.node_tree.nodes.get('Principled BSDF')
    if bs:
        if 'Base Color' in bs.inputs:
            bs.inputs['Base Color'].default_value = (0.28, 0.48, 0.58, 1.0)
        if 'Roughness' in bs.inputs:
            bs.inputs['Roughness'].default_value = 0.10
        if 'Alpha' in bs.inputs:
            bs.inputs['Alpha'].default_value = 0.20
        if 'Transmission Weight' in bs.inputs:
            bs.inputs['Transmission Weight'].default_value = 0.22
        elif 'Transmission' in bs.inputs:
            bs.inputs['Transmission'].default_value = 0.22
        if 'IOR' in bs.inputs:
            bs.inputs['IOR'].default_value = 1.42
    glass.diffuse_color = (0.28,0.48,0.58,0.20)
    try:
        glass.surface_render_method = 'DITHERED'
    except Exception:
        try: glass.blend_method = 'BLEND'
        except Exception: pass
    try: glass.show_transparent_back = True
    except Exception: pass

# Interior materials.
FLOOR = make_mat('Interior_Floor', (0.30,0.19,0.11), .88)
WALL_IN = make_mat('Interior_Wall_Warm', (0.56,0.45,0.34), .94)
PINK = make_mat('Sofa_DustyPink', (0.68,0.31,0.40), .88)
PINK_D = make_mat('Sofa_DarkPink', (0.48,0.20,0.28), .90)
CREAM = make_mat('Fabric_Cream', (0.78,0.71,0.58), .93)
BLANKET = make_mat('Blanket_Sage', (0.34,0.43,0.32), .94)
BLACK = make_mat('TV_Black', (0.025,0.03,0.035), .38)
SCREEN = make_mat('TV_Screen', (0.04,0.10,0.13), .22)
CERAMIC = make_mat('Ceramic_Mint', (0.30,0.53,0.48), .70)
POT = make_mat('Plant_Pot', (0.48,0.27,0.17), .90)
LEAF = make_mat('Plant_Green', (0.18,0.36,0.18), .90)
LEAF_L = make_mat('Plant_Green_Light', (0.28,0.48,0.22), .88)
RUG = make_mat('Rug_MutedBlue', (0.22,0.34,0.42), .95)
BOOK_RED = make_mat('Book_Red', (0.48,0.16,0.12), .92)
BOOK_BLUE = make_mat('Book_Blue', (0.12,0.25,0.42), .92)
BOOK_GOLD = make_mat('Book_Gold', (0.60,0.42,0.13), .92)
CLOCK_FACE = make_mat('Clock_Face', (0.78,0.74,0.64), .90)
FLOWER = make_mat('Flower_Rose', (0.65,0.18,0.24), .88)
LAMP_SHADE = make_mat('Lamp_Shade', (0.72,0.58,0.34), .90)

# Rebuild front planks around door and window openings.
front_wall_y = -D/2 + 0.01
z0, z1 = wall0 + 0.03, wall_top - 0.03

def planks_x(tag, x0, x1, zz0, zz1, y=front_wall_y, width=.48):
    if x1 <= x0 or zz1 <= zz0: return
    x=x0; i=0
    mats=[WOOD,WOOD_MID,WOOD_DARK]
    while x < x1-0.015:
        ww=min(width, x1-x)
        box(f'{tag}_{i}', (x+ww/2,y,(zz0+zz1)/2),(max(.08,ww-.025),.10,zz1-zz0),mats[i%3])
        x += ww; i += 1

# full-height zones
planks_x('FrontShell_Left', -2.88, -1.30, z0, z1)
planks_x('FrontShell_Mid',  -0.02,  0.55, z0, z1)
planks_x('FrontShell_Right', 2.02,  2.88, z0, z1)
# above door
planks_x('FrontShell_DoorTop', -1.30, -0.02, 2.84, z1)
# below / above window
planks_x('FrontShell_WinLow', .55, 2.02, z0, 1.32)
planks_x('FrontShell_WinHigh', .55, 2.02, 2.74, z1)

# Rebuild right wall around side window.
right_x = W/2 - .01

def planks_y(tag, y0, y1, zz0, zz1, x=right_x, depth=.48):
    if y1 <= y0 or zz1 <= zz0: return
    y=y0; i=0; mats=[WOOD_MID,WOOD,WOOD_DARK]
    while y < y1-.015:
        dd=min(depth,y1-y)
        box(f'{tag}_{i}',(x,y+dd/2,(zz0+zz1)/2),(.10,max(.08,dd-.025),zz1-zz0),mats[i%3])
        y+=dd; i+=1

planks_y('RightShell_Front', -2.32, -0.13, z0, z1)
planks_y('RightShell_Back',   1.23,  2.32, z0, z1)
planks_y('RightShell_WinLow', -.13,  1.23, z0, 1.22)
planks_y('RightShell_WinHigh',-.13,  1.23, 2.60, z1)

# Interior floorboards.
for i in range(11):
    x=-2.48+i*.49
    box(f'Interior_FloorBoard_{i}',(x,0,.625),(.46,4.55,.075),FLOOR,bevel=.012)

# Interior warm wall liners on the back and left walls; thin enough to preserve shell.
box('Interior_BackWall',(0,2.39,1.86),(5.55,.07,2.42),WALL_IN)
box('Interior_LeftWall',(-2.79,0,1.86),(.07,4.55,2.42),WALL_IN)

# Window reveals make openings read as real wall thickness.
for x in (.58,1.98): box('FrontWindow_RevealV_'+str(x),(x,-2.44,2.03),(.10,.30,1.34),WOOD_LIGHT)
for z in (1.34,2.71): box('FrontWindow_RevealH_'+str(z),(1.28,-2.44,z),(1.50,.30,.10),WOOD_LIGHT)
for y in (-.10,1.20): box('SideWindow_RevealY_'+str(y),(2.86,y,1.90),(.30,.10,1.28),WOOD_LIGHT)
for z in (1.24,2.56): box('SideWindow_RevealZ_'+str(z),(2.86,.55,z),(.30,1.40,.10),WOOD_LIGHT)

# Hollow dormer cavity behind transparent dormer window.
box('Dormer_BackWall',(-1.35,-.55,4.35),(.10,1.15,1.02),WALL_IN)
box('Dormer_SideA',(-1.87,-1.12,4.35),(1.00,.10,1.02),WOOD_DARK)
box('Dormer_SideB',(-1.87,.02,4.35),(1.00,.10,1.02),WOOD_DARK)
box('Dormer_Floor',(-1.87,-.55,3.86),(1.00,1.14,.10),FLOOR)

# -----------------------------------------------------------------------------
# Furniture arrangement.
# Living room occupies front-right half; bedroom occupies rear-left half.
# -----------------------------------------------------------------------------
# Rug under living area.
box('Living_Rug',(.60,-.25,.69),(2.55,1.75,.035),RUG,bevel=.05)

# Dusty-pink sofa facing the TV on the back wall.
box('Sofa_Seat',(.55,.35,.91),(2.05,.82,.28),PINK,bevel=.10)
box('Sofa_Back',(.55,.73,1.25),(2.05,.18,.82),PINK_D,rot=(math.radians(-5),0,0),bevel=.08)
for sx in (-.48,1.58):
    box('Sofa_Arm_'+str(sx),(sx,.35,1.08),(.20,.84,.48),PINK_D,bevel=.08)
box('Sofa_CushionA',(.05,.20,1.08),(.72,.55,.18),PINK,bevel=.07)
box('Sofa_CushionB',(1.05,.20,1.08),(.72,.55,.18),PINK,bevel=.07)

# Coffee table with vase exactly visible from front window.
box('Coffee_TableTop',(.65,-.78,.91),(1.28,.68,.12),WOOD_LIGHT,bevel=.04)
for x in (.15,1.15):
    for y in (-1.02,-.54): box('Coffee_Leg_'+str(x)+'_'+str(y),(x,y,.77),(.11,.11,.36),WOOD_DARK,bevel=.02)
# Vase: low-poly ceramic body, neck and flowers.
bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, location=(.65,-.78,1.12), scale=(.16,.16,.22))
vase=bpy.context.object; vase.name='Vase_Body'; set_mat(vase,CERAMIC)
box('Vase_Neck',(.65,-.78,1.32),(.13,.13,.18),CERAMIC,bevel=.035)
for i,(dx,dy,h) in enumerate([(-.08,0,.33),(.06,.03,.37),(0,-.07,.31)]):
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=.018, depth=h, location=(.65+dx,-.78+dy,1.42+h/2))
    stem=bpy.context.object; stem.name=f'Flower_Stem_{i}'; set_mat(stem,LEAF)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=.09, location=(.65+dx,-.78+dy,1.42+h))
    fl=bpy.context.object; fl.name=f'Flower_{i}'; set_mat(fl,FLOWER)

# TV console and screen on back wall.
box('TV_Console',(.72,2.02,.86),(2.10,.46,.50),WOOD_MID,bevel=.04)
box('TV_Frame',(.72,2.23,1.62),(1.72,.11,1.02),BLACK,bevel=.055)
box('TV_Screen',(.72,2.16,1.62),(1.52,.035,.82),SCREEN,bevel=.035)
box('TV_Base',(.72,2.05,1.08),(.56,.35,.09),BLACK,bevel=.025)
box('TV_Stem',(.72,2.08,1.22),(.10,.10,.28),BLACK)

# Bedroom rear-left, bed length along Y.
box('Bed_Frame',(-1.72,.92,.78),(1.58,2.05,.32),WOOD_LIGHT,bevel=.04)
box('Mattress',(-1.72,.90,1.01),(1.46,1.91,.30),CREAM,bevel=.10)
box('Blanket',(-1.72,.48,1.20),(1.38,1.02,.13),BLANKET,bevel=.07)
box('Headboard',(-1.72,1.92,1.30),(1.62,.16,1.12),WOOD_MID,bevel=.04)
for x in (-2.05,-1.39):
    box('Pillow_'+str(x),(x,1.55,1.25),(.58,.48,.20),CREAM,rot=(math.radians(-7),0,0),bevel=.10)

# Bedside table and lamp.
box('Bedside_Table',(-2.48,1.45,.94),(.52,.52,.55),WOOD_MID,bevel=.04)
box('Bedside_Drawer',(-2.48,1.17,1.02),(.38,.04,.18),WOOD_DARK,bevel=.02)
bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=.055, depth=.42, location=(-2.48,1.45,1.47))
lampstem=bpy.context.object; lampstem.name='Lamp_Stem'; set_mat(lampstem,METAL)
bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=.24, radius2=.13, depth=.34, location=(-2.48,1.45,1.77))
shade=bpy.context.object; shade.name='Lamp_Shade'; set_mat(shade,LAMP_SHADE)

# Large potted plant by the front-right window.
bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=.26, depth=.40, location=(2.25,-1.55,.89))
pot=bpy.context.object; pot.name='House_Plant_Pot'; set_mat(pot,POT)
for i,(dx,dy,z,s) in enumerate([(-.10,0,1.22,.26),(.12,.04,1.30,.30),(0,-.10,1.48,.25),(.05,.12,1.58,.22),(-.13,.10,1.43,.21)]):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=s, location=(2.25+dx,-1.55+dy,z))
    leaf=bpy.context.object; leaf.name=f'Plant_Leaf_{i}'; leaf.scale=(.75,1.0,1.2); set_mat(leaf,LEAF_L if i%2 else LEAF)

# Bookshelf on left interior wall.
box('Bookcase',(-2.56,-.65,1.42),(.36,1.10,1.58),WOOD_MID,bevel=.03)
for z in (.94,1.38,1.82): box('Shelf_'+str(z),(-2.35,-.65,z),(.12,1.00,.09),WOOD_LIGHT)
book_mats=[BOOK_RED,BOOK_BLUE,BOOK_GOLD,CREAM]
for i in range(10):
    y=-1.05+(i%5)*.20; z=1.12 if i<5 else 1.56
    box(f'Book_{i}',(-2.28,y,z),(.13,.13,.27+(.05 if i%3==0 else 0)),book_mats[i%4],rot=(0,0,random.uniform(-.08,.08)),bevel=.012)

# Wall clock above/left of TV on back wall.
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=.30, depth=.08, location=(-1.52,2.30,2.30), rotation=(math.pi/2,0,0))
clock=bpy.context.object; clock.name='Wall_Clock'; set_mat(clock,CLOCK_FACE)
box('Clock_Hand_H',(-1.52,2.245,2.30),(.18,.035,.025),BLACK,rot=(0,math.radians(25),0))
box('Clock_Hand_M',(-1.52,2.242,2.30),(.025,.035,.21),BLACK,rot=(0,math.radians(-18),0))

# Small storage chest and a pair of decorative baskets.
box('Storage_Chest',(-.85,-1.65,.88),(1.05,.48,.46),WOOD_MID,bevel=.05)
box('Chest_Lid',(-.85,-1.65,1.13),(1.10,.52,.12),WOOD_LIGHT,bevel=.05)
for i,x in enumerate((-.20,.20)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=.16, depth=.25, location=(x,-1.90,.82))
    basket=bpy.context.object; basket.name=f'Basket_{i}'; set_mat(basket,WOOD_LIGHT)

# Warm interior light so furniture is readable through tinted glass.
bpy.ops.object.light_add(type='POINT', location=(.25,-.15,2.45))
interior_light=bpy.context.object; interior_light.name='Interior_Warm_Light'; interior_light.data.energy=135; interior_light.data.color=(1.0,.72,.48); interior_light.data.shadow_soft_size=1.4
bpy.ops.object.light_add(type='POINT', location=(-1.75,1.1,2.15))
bed_light=bpy.context.object; bed_light.name='Bedroom_Warm_Light'; bed_light.data.energy=70; bed_light.data.color=(1.0,.62,.40); bed_light.data.shadow_soft_size=1.0

# -----------------------------------------------------------------------------
# Re-render after furnishing and overwrite final BLEND + GLB.
# -----------------------------------------------------------------------------
preview_ground = box('Preview_Ground_Furnished',(0,0,-.18),(16,16,.20),GROUND)
preview_ground['preview_only']=True

render('preview_perspective.png',(-9,-11,7.4),(0,-.25,2.55),58)
render('preview_front.png',(0,-12.5,3.25),(0,-.55,2.45),62)
render('preview_back.png',(0,12.5,3.6),(0,.5,2.7),62)
render('preview_left.png',(-12.5,0,3.8),(-.3,0,2.8),62)
render('preview_right.png',(12.5,0,3.6),(.3,0,2.55),62)
render('preview_top.png',(0,-.2,15),(0,0,1.2),58)
render('preview_rear_perspective.png',(9,11,7.2),(0,.25,2.7),58)
render('preview_interior_front.png',(1.28,-8.2,2.55),(1.0,-.15,1.55),70)
render('preview_interior_side.png',(8.2,.55,2.55),(.65,.35,1.55),70)

bpy.data.objects.remove(preview_ground, do_unlink=True)
cam.location=(-9,-11,7.4); cam.data.lens=58; look_at(cam,(0,-.25,2.55))
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
furniture_prefixes=('Sofa_','Coffee_','Vase_','Flower_','TV_','Bed_','Mattress','Blanket','Pillow_','Bedside_','Lamp_','House_Plant_','Bookcase','Shelf_','Book_','Wall_Clock','Clock_','Storage_Chest','Chest_','Basket_','Living_Rug')
furniture_count=sum(1 for o in scene.objects if o.type=='MESH' and o.name.startswith(furniture_prefixes))
with open(OUT/'model_report.txt','w',encoding='utf-8') as f:
    f.write('Furnished cottage multiview build\n')
    f.write('Approx dimensions: 7.2m W x 7.0m D including porch x 6.2m H\n')
    f.write(f'Mesh objects: {sum(1 for o in scene.objects if o.type=="MESH")}\n')
    f.write(f'Furniture/decor mesh objects: {furniture_count}\n')
    f.write(f'Vertices: {verts}\nFaces: {faces}\nTriangles approx: {tris}\n')
    f.write('Transparent windows: front, right-side and dormer glass\n')
    f.write('Interior: dusty-pink sofa, coffee table + vase/flowers, TV + console, bed + pillows/blanket, bedside table/lamp, potted plant, wall clock, rug, bookcase/books, storage chest/baskets\n')
    f.write('GLB export: OK\nBLEND save: OK\n')
print('FURNISHED_COTTAGE_BUILD_OK', blend_path)
