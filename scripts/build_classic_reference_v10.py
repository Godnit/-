import bpy, math, random, os
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'output_classic_reference_v10')
os.makedirs(OUT, exist_ok=True)
SEED = 13082610
random.seed(SEED)

# -----------------------------------------------------------------------------
# Scene
# -----------------------------------------------------------------------------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1024
scene.render.resolution_y = 576
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
try:
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'Medium High Contrast'
    scene.view_settings.exposure = 0.10
    scene.view_settings.gamma = 1.0
except Exception:
    pass
try:
    scene.eevee.use_gtao = True
    scene.eevee.gtao_distance = 7
    scene.eevee.gtao_factor = 1.05
    scene.eevee.use_soft_shadows = True
except Exception:
    pass

world = scene.world
world.use_nodes = True
bg = world.node_tree.nodes.get('Background')
# sampled from the supplied reference sky (~196,227,227)
bg.inputs['Color'].default_value = (0.77, 0.89, 0.89, 1.0)
bg.inputs['Strength'].default_value = 0.72

# -----------------------------------------------------------------------------
# Materials sampled toward the supplied screenshot
# -----------------------------------------------------------------------------
def mat(name, rgb, rough=.95):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    if p:
        p.inputs['Base Color'].default_value=(*rgb,1.0)
        p.inputs['Roughness'].default_value=rough
    m.diffuse_color=(*rgb,1.0)
    return m

M={
    # central field sample ~181/191/109
    'grass':mat('Grass_Reference',(0.715,0.752,0.425),.98),
    'grass_hill':mat('Grass_Hill',(0.62,0.70,0.39),.98),
    # tree samples from left/right forest in reference
    'tree_a':mat('Pine_Mint_A',(0.40,0.58,0.47),.98),
    'tree_b':mat('Pine_Mint_B',(0.50,0.66,0.53),.98),
    'tree_c':mat('Pine_Deep_Aqua',(0.31,0.50,0.41),.98),
    'trunk':mat('Trunk_Muted',(0.34,0.27,0.18),.98),
    'mountain':mat('Mountain_Pale',(0.79,0.84,0.82),.99),
    'mountain_shadow':mat('Mountain_Shadow',(0.56,0.72,0.76),.99),
    'snow':mat('Mountain_Snow',(0.92,0.94,0.91),.99),
    'rock':mat('Rock_Pale',(0.59,0.63,0.65),.98),
    'rock2':mat('Rock_Cool',(0.47,0.55,0.59),.98),
    'path':mat('Path_Pale_Sand',(0.80,0.76,0.55),.98),
    'church':mat('Church_Stone',(0.47,0.53,0.54),.97),
    'church_light':mat('Church_Light',(0.62,0.66,0.63),.97),
    'roof':mat('Church_Roof',(0.24,0.31,0.33),.97),
    'door':mat('Church_Door',(0.34,0.24,0.16),.96),
    'window':mat('Church_Window',(0.10,0.16,0.18),.90),
    'blue':mat('Blue_Tents',(0.04,0.43,0.82),.93),
    'pink':mat('Pink_Tents',(0.93,0.47,0.57),.93),
}

def assign(obj, material):
    if hasattr(obj.data,'materials'):
        obj.data.materials.clear(); obj.data.materials.append(material)

def bevel(obj,width=.04):
    if width<=0:return obj
    mod=obj.modifiers.new('TinyBevel','BEVEL');mod.width=width;mod.segments=1;mod.limit_method='ANGLE'
    bpy.context.view_layer.objects.active=obj
    try:bpy.ops.object.modifier_apply(modifier=mod.name)
    except Exception:pass
    return obj

def box(name,loc,dims,material,rot=(0,0,0),bev=.04):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc,rotation=rot)
    o=bpy.context.object;o.name=name;o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    assign(o,material);bevel(o,bev);return o

def ico(name,loc,scale,material,sub=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=1,location=loc)
    o=bpy.context.object;o.name=name;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    assign(o,material);return o

def mesh_obj(name,verts,faces,materials,face_mats=None):
    me=bpy.data.meshes.new(name+'_Mesh');me.from_pydata(verts,[],faces);me.validate();me.update()
    o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
    for mm in materials:me.materials.append(mm)
    if face_mats:
        for p,mi in zip(me.polygons,face_mats):p.material_index=mi
    return o

def ribbon(name,pts,width,z,material):
    verts=[];faces=[]
    for i,p in enumerate(pts):
        v=Vector((p[0],p[1],z))
        if i==0:t=Vector((pts[1][0]-pts[0][0],pts[1][1]-pts[0][1],0)).normalized()
        elif i==len(pts)-1:t=Vector((pts[-1][0]-pts[-2][0],pts[-1][1]-pts[-2][1],0)).normalized()
        else:t=Vector((pts[i+1][0]-pts[i-1][0],pts[i+1][1]-pts[i-1][1],0)).normalized()
        perp=Vector((-t.y,t.x,0))*width*.5
        verts.extend([tuple(v+perp),tuple(v-perp)])
    for i in range(len(pts)-1):
        a=i*2;faces.append((a,a+1,a+3,a+2))
    return mesh_obj(name,verts,faces,[material])

# -----------------------------------------------------------------------------
# Valley floor: very wide, with no visible platform edge
# -----------------------------------------------------------------------------
box('Valley_Ground',(0,43,-0.85),(206,205,1.7),M['grass'],bev=.45)
# broad, low rolling hills under the perimeter forests
for i,(x,y,sx,sy,sz) in enumerate([
    (-73,31,34,75,3.6),(73,33,34,75,3.6),
    (-52,93,44,40,5.5),(45,94,51,42,5.2),
    (-14,110,50,30,6.0),(65,102,36,33,5.0)
]):
    ico('Valley_Hill_%02d'%i,(x,y,-1.5),(sx,sy,sz),M['grass_hill'],2)

# -----------------------------------------------------------------------------
# Large overlapping low-poly mountains: rounded/faceted like the screenshot
# -----------------------------------------------------------------------------
mountain_specs=[
    (-127,160,44,24,31),(-99,164,42,25,39),(-70,166,38,24,31),(-44,166,43,25,36),
    (-12,168,44,27,44),(22,167,42,26,38),(52,166,44,27,42),(86,165,46,26,46),(121,160,43,24,34)
]
for i,(x,y,sx,sy,sz) in enumerate(mountain_specs):
    mm=M['mountain'] if i%3!=1 else M['mountain_shadow']
    ico('Mountain_%02d'%i,(x,y,sz*.42-4.0),(sx,sy,sz),mm,2)
    # irregular pale summit volume, intentionally broad rather than a sharp cone
    ico('Mountain_Snow_%02d'%i,(x-2.0,y-1.5,sz*.78),(sx*.42,sy*.38,sz*.25),M['snow'],1)

# second distant layer to create the pale valley enclosure seen at far left/right
for i,(x,y,sx,sy,sz) in enumerate([(-150,183,60,35,32),(-88,188,60,36,29),(83,188,62,36,31),(148,181,60,34,30)]):
    ico('Mountain_Back_%02d'%i,(x,y,sz*.34-6),(sx,sy,sz),M['mountain_shadow'],2)

# -----------------------------------------------------------------------------
# Forest packed into one mesh. Layout is deterministic and follows the reference:
# heavy left/right walls, a dense back hillside, huge open center, foreground corner framing.
# -----------------------------------------------------------------------------
Fv=[];Ff=[];Fm=[]

def add_cylinder(cx,cy,cz,r,h,n,mi):
    base=len(Fv)
    z0=cz-h*.5;z1=cz+h*.5
    for j in range(n):
        a=2*math.pi*j/n;Fv.append((cx+r*math.cos(a),cy+r*math.sin(a),z0))
    for j in range(n):
        a=2*math.pi*j/n;Fv.append((cx+r*math.cos(a),cy+r*math.sin(a),z1))
    Ff.append(tuple(base+j for j in range(n)));Fm.append(mi)
    Ff.append(tuple(base+n+j for j in reversed(range(n))));Fm.append(mi)
    for j in range(n):
        k=(j+1)%n;Ff.append((base+j,base+k,base+n+k,base+n+j));Fm.append(mi)

def add_frustum(cx,cy,cz,r1,r2,h,n,mi):
    base=len(Fv);z0=cz-h*.5;z1=cz+h*.5
    for j in range(n):
        a=2*math.pi*j/n;Fv.append((cx+r1*math.cos(a),cy+r1*math.sin(a),z0))
    for j in range(n):
        a=2*math.pi*j/n;Fv.append((cx+r2*math.cos(a),cy+r2*math.sin(a),z1))
    Ff.append(tuple(base+j for j in range(n)));Fm.append(mi)
    Ff.append(tuple(base+n+j for j in reversed(range(n))));Fm.append(mi)
    for j in range(n):
        k=(j+1)%n;Ff.append((base+j,base+k,base+n+k,base+n+j));Fm.append(mi)

def add_pine(x,y,s,var):
    add_cylinder(x,y,.58*s,.13*s,1.16*s,6,0)
    add_frustum(x,y,1.35*s,.82*s,.11*s,1.40*s,7,1+(var%3))
    add_frustum(x,y,2.00*s,.67*s,.08*s,1.20*s,7,1+((var+1)%3))
    add_frustum(x,y,2.58*s,.45*s,.03*s,1.02*s,7,1+((var+2)%3))

def open_field(x,y):
    # clear ellipse matching the giant empty battlefield in the reference
    return ((x-4.0)/54.0)**2 + ((y-10.0)/41.0)**2 < 1.0

rng=random.Random(SEED+100)
tree_positions=[]

def place_region(x0,x1,y0,y1,count,scale_lo,scale_hi,accept=None):
    attempts=0
    while count>0 and attempts<count*80+1000:
        attempts+=1
        x=rng.uniform(x0,x1);y=rng.uniform(y0,y1)
        if accept and not accept(x,y):continue
        # modest minimum spacing; reference forest is packed but readable
        too_close=False
        for px,py,_,_ in tree_positions[-140:]:
            if (x-px)*(x-px)+(y-py)*(y-py)<1.35*1.35:
                too_close=True;break
        if too_close:continue
        s=rng.uniform(scale_lo,scale_hi)
        tree_positions.append((x,y,s,len(tree_positions)%3));count-=1

# Left wall curves inward toward the distant church, exactly where the screenshot is densest.
def left_accept(x,y):
    edge=-44 + 0.17*max(0,y-5)
    return x < edge and not open_field(x,y)
# Right forest border: slightly farther from the center and more open near foreground.
def right_accept(x,y):
    edge=49 - 0.09*max(0,y-5)
    return x > edge and not open_field(x,y)

place_region(-94,-32,-43,86,150,.86,1.45,left_accept)
place_region(38,94,-38,88,132,.82,1.42,right_accept)

# Dense back hillside/forest belt, with a small break around the church and its path.
def back_accept(x,y):
    if ((x+6)/17.0)**2+((y-57)/10.0)**2 < 1.0:return False
    if abs(x)<27 and y<58 and rng.random()<.55:return False
    return True
place_region(-84,84,47,116,205,.66,1.22,back_accept)

# Foreground framing: very dense bottom-left; only a small cropped right-edge group.
place_region(-92,-48,-48,-18,46,1.00,1.58,lambda x,y: True)
place_region(76,96,-35,-8,13,1.00,1.52,lambda x,y: True)

# Mid-distance edge trees that intrude slightly into the meadow.
for _ in range(24):
    side=-1 if rng.random()<.57 else 1
    y=rng.uniform(-8,39)
    x=(rng.uniform(41,54)*side)
    if not open_field(x,y):
        tree_positions.append((x,y,rng.uniform(.76,1.08),len(tree_positions)%3))

for i,(x,y,s,v) in enumerate(tree_positions):add_pine(x,y,s,v)
forest=mesh_obj('Forest_Pines',Fv,Ff,[M['trunk'],M['tree_a'],M['tree_b'],M['tree_c']],Fm)

# Single broad-leaf tree in the left-middle field, as in the supplied screenshot.
# A short trunk plus three faceted crowns.
bpy.ops.mesh.primitive_cylinder_add(vertices=7,radius=.28,depth=2.3,location=(-43,-5,1.15));assign(bpy.context.object,M['trunk'])
ico('RoundTree_Crown_A',(-43,-5,3.05),(1.65,1.45,1.35),M['tree_b'],1)
ico('RoundTree_Crown_B',(-44.1,-4.8,2.85),(1.05,.92,.90),M['tree_a'],1)
ico('RoundTree_Crown_C',(-42.0,-5.1,2.80),(.92,.82,.84),M['tree_c'],1)

# -----------------------------------------------------------------------------
# Scattered field rocks — concentrate left/front and leave the huge center clean.
# -----------------------------------------------------------------------------
rng2=random.Random(SEED+200)
rock_positions=[(-54,-8),(-49,-16),(-44,-12),(-39,4),(-33,14),(-24,10),(-14,15),
                (55,6),(63,-8),(72,-17),(80,-5),(48,28),(20,-23),(7,-31),(-5,-27),
                (31,-10),(39,-30),(-62,6),(-58,15),(-52,21)]
for i,(x,y) in enumerate(rock_positions):
    s=rng2.uniform(.42,.82)
    ico('Rock_%02d'%i,(x,y,.25*s),(1.25*s,.85*s,.55*s),M['rock'] if i%2==0 else M['rock2'],1)
# smaller stones in the far meadow around the church
for i in range(24):
    x=rng2.uniform(-40,42);y=rng2.uniform(36,68)
    if ((x+5)/10)**2+((y-57)/7)**2<1:continue
    s=rng2.uniform(.16,.34)
    ico('FarRock_%02d'%i,(x,y,.15),(1.2*s,.9*s,.65*s),M['rock'],1)

# -----------------------------------------------------------------------------
# Small church and graveyard. Kept intentionally tiny relative to the valley.
# -----------------------------------------------------------------------------
CX,CY=-5.0,57.0
ribbon('Church_Path',[(4,19),(1,27),(-2,34),(0,41),(-3,49),(CX,CY-3.2)],1.25,.06,M['path'])
ribbon('Church_Path_Side',[(CX,CY-2.7),(CX+6,CY-1.0),(CX+9,CY+1.5)],.72,.065,M['path'])
box('Church_Nave',(CX,CY,1.40),(5.7,3.6,2.8),M['church'],bev=.05)
box('Church_Wing',(CX+2.35,CY+.2,1.22),(2.0,2.8,2.45),M['church_light'],bev=.04)
# gable roof mesh
rv=[(CX-3.2,CY-2.05,2.70),(CX+3.2,CY-2.05,2.70),(CX,CY-2.05,4.10),
    (CX-3.2,CY+2.05,2.70),(CX+3.2,CY+2.05,2.70),(CX,CY+2.05,4.10)]
rf=[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)]
mesh_obj('Church_Roof',rv,rf,[M['roof']])
box('Church_Tower',(CX-1.4,CY+.2,4.30),(1.5,1.6,4.6),M['church_light'],bev=.04)
# tower cap
bpy.ops.mesh.primitive_cone_add(vertices=6,radius1=1.05,radius2=.10,depth=2.35,location=(CX-1.4,CY+.2,7.55));assign(bpy.context.object,M['roof'])
box('Church_Door',(CX,CY-1.84,1.15),(.85,.12,1.75),M['door'],bev=.02)
box('Church_Window',(CX+1.75,CY-1.85,1.72),(.62,.10,.82),M['window'],bev=.01)
# sparse small gravestones to left/front of church
for i,(gx,gy) in enumerate([(-12,53),(-10,55),(-13,57),(-11,59),(-15,55),(-16,58),(-9,51),(-14,51)]):
    box('Grave_%02d'%i,(gx,gy,.33),(.32,.20,.65),M['church_light'],bev=.03)

# -----------------------------------------------------------------------------
# Wrong-colored camps from the classic map: blue tents front-left, pink far-right.
# -----------------------------------------------------------------------------
def tent(name,x,y,material,scale=1.0):
    # simple triangular prism tent, visible as the same little colored wedges from the reference
    w=1.55*scale;d=1.7*scale;h=.92*scale
    verts=[(x-w/2,y-d/2,.04),(x+w/2,y-d/2,.04),(x,y-d/2,h),
           (x-w/2,y+d/2,.04),(x+w/2,y+d/2,.04),(x,y+d/2,h)]
    faces=[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)]
    mesh_obj(name,verts,faces,[material])
blue_pos=[(-57,-26),(-45,-25),(-33,-23),(-21,-21),(-61,-34),(-49,-35),(-37,-36),(-25,-34)]
pink_pos=[(43,52),(48,54),(53,52),(46,48),(52,47),(58,49)]
for i,(x,y) in enumerate(blue_pos):tent('BlueTent_%02d'%i,x,y,M['blue'],.92)
for i,(x,y) in enumerate(pink_pos):tent('PinkTent_%02d'%i,x,y,M['pink'],.76)

# -----------------------------------------------------------------------------
# Lighting / camera
# -----------------------------------------------------------------------------
def look_at(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

bpy.ops.object.light_add(type='SUN',location=(-30,-50,70))
sun=bpy.context.object;sun.name='Sun';sun.data.energy=2.0
sun.rotation_euler=(math.radians(28),math.radians(-22),math.radians(-32))
bpy.ops.object.light_add(type='AREA',location=(-15,-22,55))
area=bpy.context.object;area.name='Sky_Fill';area.data.energy=500;area.data.size=65;look_at(area,(0,25,0))

bpy.ops.object.camera_add(location=(0,-112,47))
cam=bpy.context.object;cam.name='Camera_Main';scene.camera=cam;cam.data.type='PERSP';cam.data.lens=48
look_at(cam,(0,37,4.5))

def render(name,loc,target,lens):
    cam.location=loc;cam.data.lens=lens;look_at(cam,target)
    scene.render.filepath=os.path.join(OUT,name)
    bpy.ops.render.render(write_still=True)

# Primary framing closely follows the supplied screenshot.
render('preview_main.png',(0,-112,47),(0,37,4.5),48)
render('preview_closer.png',(-3,-96,43),(-4,44,4.0),50)
render('preview_left.png',(-50,-86,42),(-2,39,4.0),52)
render('preview_right.png',(50,-86,42),(1,39,4.0),52)
render('preview_high.png',(0,-75,75),(0,32,0.5),52)
cam.location=(0,-112,47);cam.data.lens=48;look_at(cam,(0,37,4.5))

# Save the real Blender scene. GLB export is best-effort only; .blend is the required source model.
blend_path=os.path.join(OUT,'classic_reference_v10.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
glb_path=os.path.join(OUT,'classic_reference_v10.glb')
try:
    bpy.ops.export_scene.gltf(filepath=glb_path,export_format='GLB',export_apply=True)
except Exception as e:
    print('GLB export skipped:',repr(e))

mesh_objs=[o for o in scene.objects if o.type=='MESH']
verts=sum(len(o.data.vertices) for o in mesh_objs);polys=sum(len(o.data.polygons) for o in mesh_objs)
with open(os.path.join(OUT,'report.txt'),'w',encoding='utf-8') as f:
    f.write('TABS Classic reference valley v10\n')
    f.write('Primary target: supplied Classic/Pre-Alpha style screenshot.\n')
    f.write('Palette sampled from the supplied image; forest positions are deterministic reference-matched clusters.\n')
    f.write('Pine count: %d\n'%len(tree_positions))
    f.write('Mesh objects: %d\nVertices: %d\nPolygons: %d\n'%(len(mesh_objs),verts,polys))
    f.write('Field dimensions: about 206 x 205 Blender meters.\n')
    f.write('Church retained but intentionally tiny; main priority is field scale, palette, forest density, mountains and camps.\n')
print('CLASSIC_REFERENCE_V10_OK')
print('pines',len(tree_positions))
print(blend_path)
