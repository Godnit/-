import bpy, math, random, os
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'output_classic_reference_v16')
os.makedirs(OUT, exist_ok=True)
SEED = 130826
rng = random.Random(SEED)

# -----------------------------------------------------------------------------
# Scene / renderer
# -----------------------------------------------------------------------------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
scene.render.resolution_x = 1024
scene.render.resolution_y = 576
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.camera = None
try:
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'Medium High Contrast'
    scene.view_settings.exposure = -0.08
    scene.view_settings.gamma = 1.0
except Exception:
    pass
try:
    scene.world.color = (0.73,0.88,0.89)
    scene.eevee.use_gtao = True
    scene.eevee.gtao_distance = 4
    scene.eevee.gtao_factor = 0.75
    scene.eevee.use_soft_shadows = True
except Exception:
    pass
world = scene.world
world.use_nodes = True
bg = world.node_tree.nodes.get('Background')
bg.inputs['Color'].default_value = (0.67,0.87,0.89,1.0)
bg.inputs['Strength'].default_value = 0.78

# -----------------------------------------------------------------------------
# Materials sampled toward the supplied TABS Classic screenshot
# -----------------------------------------------------------------------------
def mat(name, rgb, rough=.98):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*rgb,1.0)
    p.inputs['Roughness'].default_value = rough
    m.diffuse_color = (*rgb,1.0)
    return m

M = {
    'grass': mat('Grass',(0.575,0.610,0.235)),
    'grass_hill': mat('GrassHill',(0.50,0.56,0.22)),
    'tree1': mat('Pine1',(0.30,0.48,0.38)),
    'tree2': mat('Pine2',(0.37,0.55,0.43)),
    'tree3': mat('Pine3',(0.43,0.60,0.47)),
    'trunk': mat('Trunk',(0.31,0.25,0.17)),
    'mountain': mat('Mountain',(0.70,0.80,0.80)),
    'mountain2': mat('MountainShadow',(0.54,0.70,0.73)),
    'snow': mat('Snow',(0.88,0.91,0.89)),
    'rock': mat('Rock',(0.49,0.55,0.60)),
    'rock2': mat('Rock2',(0.39,0.48,0.54)),
    'path': mat('Path',(0.68,0.66,0.39)),
    'church': mat('ChurchStone',(0.43,0.49,0.49)),
    'church2': mat('ChurchLight',(0.56,0.61,0.59)),
    'roof': mat('ChurchRoof',(0.20,0.27,0.29)),
    'door': mat('Door',(0.30,0.20,0.13)),
    'blue': mat('BlueTent',(0.04,0.39,0.76)),
    'pink': mat('PinkTent',(0.91,0.43,0.50)),
}

def assign(o,m):
    o.data.materials.clear(); o.data.materials.append(m)

def box(name, loc, dims, material, bevel=.02):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o=bpy.context.object; o.name=name; o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    assign(o,material)
    if bevel:
        mod=o.modifiers.new('Bevel','BEVEL');mod.width=bevel;mod.segments=1
    return o

def ico(name, loc, scale, material, sub=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=1,location=loc)
    o=bpy.context.object;o.name=name;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    assign(o,material);return o

def mesh_obj(name, verts, faces, materials, face_mats=None):
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
        q=Vector((-t.y,t.x,0))*width*.5
        verts += [tuple(v+q),tuple(v-q)]
    for i in range(len(pts)-1):
        a=i*2;faces.append((a,a+1,a+3,a+2))
    return mesh_obj(name,verts,faces,[material])

# -----------------------------------------------------------------------------
# Huge, nearly flat valley floor
# -----------------------------------------------------------------------------
box('ValleyGround',(0,48,-0.7),(218,252,1.4),M['grass'],0)
# Only soft perimeter rises; center remains flat and spacious.
for i,(x,y,sx,sy,sz) in enumerate([
    (-86,38,26,82,2.2),(86,40,26,82,2.2),
    (-64,116,44,39,3.0),(61,116,48,39,3.0),
    (-3,135,62,23,2.6)
]):
    ico('Hill_%02d'%i,(x,y,-2.25),(sx,sy,sz),M['grass_hill'],2)

# -----------------------------------------------------------------------------
# Broad, continuous faceted mountain ranges far behind the forest
# -----------------------------------------------------------------------------
def ridge(name,xs,ys,hs,front_y,back_y,mats):
    v=[];f=[];mi=[]
    for x in xs:v.append((x,front_y,-5.0))
    for x,y,h in zip(xs,ys,hs):v.append((x,y,h))
    for x in xs:v.append((x,back_y,-8.0))
    n=len(xs)
    for i in range(n-1):
        f.append((i,i+1,n+i));mi.append(i%len(mats))
        f.append((i+1,n+i+1,n+i));mi.append((i+1)%len(mats))
        f.append((n+i,n+i+1,2*n+i+1,2*n+i));mi.append((i+1)%len(mats))
    return mesh_obj(name,v,f,mats,mi)

xs=[-190,-166,-142,-118,-94,-70,-46,-22,2,26,50,74,98,122,146,170,194]
ys=[214,217,220,219,223,221,226,230,228,233,230,227,232,228,223,218,215]
hs=[20,27,34,31,40,35,44,53,47,57,48,43,59,51,42,31,21]
ridge('MountainFront',xs,ys,hs,158,300,[M['mountain'],M['mountain2']])
xs2=[-210,-176,-142,-108,-74,-40,-6,28,62,96,130,164,202]
ys2=[280,283,287,285,290,289,293,291,294,290,287,283,280]
hs2=[17,23,29,26,34,30,38,33,36,31,33,24,17]
ridge('MountainBack',xs2,ys2,hs2,240,370,[M['mountain2']])
# Small snow facets on several tall peaks.
sv=[];sf=[]
for idx in (4,7,9,12):
    x=xs[idx];y=ys[idx]-1;h=hs[idx];b=len(sv)
    sv.extend([(x-6,y,h-7),(x,y-.5,h+.3),(x+6,y,h-6),(x,y-3,h-11)])
    sf.extend([(b,b+1,b+3),(b+1,b+2,b+3)])
mesh_obj('SnowFacets',sv,sf,[M['snow']])

# -----------------------------------------------------------------------------
# Packed low-poly forest mesh for mobile-friendly thousands of cones
# -----------------------------------------------------------------------------
forest_verts=[];forest_faces=[];forest_mats=[M['trunk'],M['tree1'],M['tree2'],M['tree3']];forest_fm=[]

def add_cyl(x,y,z,r,d,n,matidx):
    b=len(forest_verts)
    for zz in (z-d*.5,z+d*.5):
        for i in range(n):
            a=2*math.pi*i/n;forest_verts.append((x+r*math.cos(a),y+r*math.sin(a),zz))
    for i in range(n):
        j=(i+1)%n;forest_faces.append((b+i,b+j,b+n+j,b+n+i));forest_fm.append(matidx)

def add_frustum(x,y,z,r1,r2,d,n,matidx):
    b=len(forest_verts)
    for r,zz in ((r1,z-d*.5),(r2,z+d*.5)):
        for i in range(n):
            a=2*math.pi*i/n;forest_verts.append((x+r*math.cos(a),y+r*math.sin(a),zz))
    for i in range(n):
        j=(i+1)%n;forest_faces.append((b+i,b+j,b+n+j,b+n+i));forest_fm.append(matidx)
    forest_faces.append(tuple(b+n+i for i in range(n)));forest_fm.append(matidx)

def add_pine(x,y,s,var):
    # Strong perspective scale: huge near trees, medium side trees, compact distant belt.
    depth_scale = 1.62 if y < -4 else (1.34 if y < 65 else 1.03)
    s*=depth_scale
    add_cyl(x,y,.58*s,.13*s,1.16*s,6,0)
    add_frustum(x,y,1.35*s,1.02*s,.12*s,1.42*s,7,1+(var%3))
    add_frustum(x,y,2.04*s,.83*s,.09*s,1.22*s,7,1+((var+1)%3))
    add_frustum(x,y,2.65*s,.58*s,.02*s,1.08*s,7,1+((var+2)%3))

# Central open meadow boundary.
def open_meadow(x,y):
    return ((x-1)/57.0)**2 + ((y-20)/49.0)**2 < 1.0

trees=[]
def place_region(x0,x1,y0,y1,n,s0,s1,accept):
    tries=0
    while n>0 and tries<200000:
        tries+=1;x=rng.uniform(x0,x1);y=rng.uniform(y0,y1)
        if accept(x,y):
            trees.append((x,y,rng.uniform(s0,s1),len(trees)%3));n-=1

# Left forest is denser/larger in the reference, especially lower-left.
place_region(-104,-33,-45,112,255,.90,1.48,lambda x,y:not open_meadow(x,y))
place_region(34,104,-42,112,215,.84,1.38,lambda x,y:not open_meadow(x,y))
# Back belt: dense but with a church clearing and wide central valley opening.
def back_ok(x,y):
    if ((x+5)/21)**2+((y-84)/13)**2<1:return False
    if abs(x)<38 and y<93 and rng.random()<.90:return False
    return True
place_region(-101,101,66,148,360,.66,1.10,back_ok)
# Explicit near-left and near-right cropped clusters.
place_region(-105,-49,-47,-8,80,1.18,1.85,lambda x,y:True)
place_region(75,105,-39,8,34,1.05,1.62,lambda x,y:True)
# Sparse transition trees outside the clean ellipse only.
for _ in range(38):
    side=-1 if rng.random()<.58 else 1
    x=rng.uniform(48,76)*side;y=rng.uniform(6,55)
    if not open_meadow(x,y):trees.append((x,y,rng.uniform(.75,1.10),len(trees)%3))

for x,y,s,v in trees:add_pine(x,y,s,v)
forest=mesh_obj('PineForest',forest_verts,forest_faces,forest_mats,forest_fm)

# Single broadleaf tree visible in left mid-field.
bpy.ops.mesh.primitive_cylinder_add(vertices=7,radius=.28,depth=2.4,location=(-45,-3,1.2));assign(bpy.context.object,M['trunk'])
ico('RoundTree',(-45,-3,3.15),(1.55,1.35,1.25),M['tree2'],1)
ico('RoundTree2',(-46,-2.8,3.05),(.9,.85,.82),M['tree3'],1)

# -----------------------------------------------------------------------------
# Scattered rocks with reference-biased left foreground cluster
# -----------------------------------------------------------------------------
rock_positions=[(-56,-6),(-51,-1),(-46,3),(-39,5),(-33,10),(-66,4),(-71,10),(-60,15),
                (-24,22),(-7,18),(18,26),(47,15),(67,7),(77,19),(86,34),(56,42),
                (-31,39),(-48,34),(-61,30),(4,47),(33,53),(-10,58),(74,57),(51,67)]
for i,(x,y) in enumerate(rock_positions):
    s=rng.uniform(.55,1.05);ico('Rock_%02d'%i,(x,y,.35*s),(1.10*s,.72*s,.52*s),M['rock'] if i%3 else M['rock2'],1)
for i in range(18):
    x=rng.uniform(-65,75);y=rng.uniform(7,72)
    if rng.random()<.65 and open_meadow(x,y):
        s=rng.uniform(.30,.58);ico('TinyRock_%02d'%i,(x,y,.24*s),(.92*s,.68*s,.48*s),M['rock'],1)

# -----------------------------------------------------------------------------
# Tiny church / graveyard, kept subordinate to the valley
# -----------------------------------------------------------------------------
CX,CY=-7.0,82.0
ribbon('ChurchPath',[(7,54),(5,61),(1,69),(-3,76),(CX,CY-2.7)],.72,.035,M['path'])
box('ChurchBody',(CX,CY,1.35),(5.9,3.7,2.7),M['church'],.04)
# gable roof
rv=[(CX-3.2,CY-2.05,2.7),(CX+3.2,CY-2.05,2.7),(CX,CY-2.05,4.05),(CX-3.2,CY+2.05,2.7),(CX+3.2,CY+2.05,2.7),(CX,CY+2.05,4.05)]
rf=[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)]
mesh_obj('ChurchRoof',rv,rf,[M['roof']])
box('ChurchTower',(CX-1.35,CY+.15,4.15),(1.35,1.45,4.3),M['church2'],.03)
bpy.ops.mesh.primitive_cone_add(vertices=6,radius1=.95,radius2=.08,depth=2.15,location=(CX-1.35,CY+.15,7.35));assign(bpy.context.object,M['roof'])
box('ChurchDoor',(CX,CY-1.7,1.05),(.75,.1,1.55),M['door'],.01)
for i,(gx,gy) in enumerate([(-14,79),(-12,81),(-15,83),(-11,85),(-16,86),(-10,77),(-17,80)]):
    box('Grave_%02d'%i,(gx,gy,.30),(.28,.18,.58),M['church2'],.01)

# -----------------------------------------------------------------------------
# Colored classic tents
# -----------------------------------------------------------------------------
def tent(name,x,y,m,s=1):
    w=1.55*s;d=1.75*s;h=.95*s
    v=[(x-w/2,y-d/2,.03),(x+w/2,y-d/2,.03),(x,y-d/2,h),(x-w/2,y+d/2,.03),(x+w/2,y+d/2,.03),(x,y+d/2,h)]
    f=[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)]
    mesh_obj(name,v,f,[m])
blue=[(-58,-9),(-47,-7),(-36,-6),(-25,-5),(-59,-18),(-48,-17),(-37,-16),(-26,-15)]
pink=[(43,78),(48,80),(53,78),(46,74),(52,73),(58,75)]
for i,p in enumerate(blue):tent('BlueTent_%02d'%i,*p,M['blue'],1.08)
for i,p in enumerate(pink):tent('PinkTent_%02d'%i,*p,M['pink'],.82)

# -----------------------------------------------------------------------------
# Lighting and cameras
# -----------------------------------------------------------------------------
def look_at(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.light_add(type='SUN',location=(-40,-60,80));sun=bpy.context.object;sun.data.energy=1.55;sun.rotation_euler=(math.radians(30),math.radians(-18),math.radians(-34))
bpy.ops.object.light_add(type='AREA',location=(-25,-25,58));area=bpy.context.object;area.data.energy=250;area.data.size=70;look_at(area,(0,35,0))
bpy.ops.object.camera_add(location=(0,-103,43));cam=bpy.context.object;scene.camera=cam;cam.data.type='PERSP';cam.data.lens=45;look_at(cam,(0,37,4.2))

def render(name,loc,target,lens):
    cam.location=loc;cam.data.lens=lens;look_at(cam,target);scene.render.filepath=os.path.join(OUT,name);bpy.ops.render.render(write_still=True)

render('preview_main.png',(0,-103,43),(0,37,4.2),45)
render('preview_closer.png',(-3,-93,40),(-4,44,4.0),48)
render('preview_left.png',(-49,-83,40),(0,39,4.0),49)
render('preview_right.png',(49,-83,40),(0,39,4.0),49)
render('preview_high.png',(0,-76,72),(0,40,.8),50)
cam.location=(0,-103,43);cam.data.lens=45;look_at(cam,(0,37,4.2))

blend=os.path.join(OUT,'classic_reference_v16.blend');bpy.ops.wm.save_as_mainfile(filepath=blend)
try:bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'classic_reference_v16.glb'),export_format='GLB',export_apply=True)
except Exception as e:print('GLB skipped',repr(e))
mesh_objs=[o for o in scene.objects if o.type=='MESH']
with open(os.path.join(OUT,'report.txt'),'w') as f:
    f.write('TABS Classic reference v16\n')
    f.write('Pine count: %d\n'%len(trees))
    f.write('Field: 218 x 252 Blender units\n')
    f.write('Mesh objects: %d\n'%len(mesh_objs))
print('V16_OK',len(trees),blend)
