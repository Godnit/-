import bpy, math, random, os
from pathlib import Path
from mathutils import Vector

# -----------------------------------------------------------------------------
# Build the proven V9 scene first, then reconstruct the important TABS Legacy
# landmarks / skyline / camps using several reference views.
# -----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
V9 = Path(__file__).with_name('build_reference_valley_v9.py')
exec(compile(V9.read_text(encoding='utf-8'), str(V9), 'exec'), globals(), globals())

base_ns = globals().get('ns', {})
scene = bpy.context.scene
M = base_ns.get('M', {})
box = base_ns.get('box')
cyl = base_ns.get('cyl')
cone = base_ns.get('cone')
ico = base_ns.get('ico')
mesh_obj = base_ns.get('mesh_obj')
ribbon = base_ns.get('ribbon')
pine = base_ns.get('pine')
look_at = base_ns.get('look_at')
assign = base_ns.get('assign')
if not all((box,cyl,cone,ico,mesh_obj,ribbon,pine,look_at,assign)):
    raise RuntimeError('V9 helper namespace not available')

OUT = ROOT / 'output_tabs_legacy_v10'
OUT.mkdir(parents=True, exist_ok=True)
SEED = 13082610
rng = random.Random(SEED)

# -----------------------------------------------------------------------------
# Palette: match the supplied TABS screenshot more closely.
# -----------------------------------------------------------------------------
def set_color(mat, rgb, rough=None):
    if not mat: return
    mat.diffuse_color = (*rgb, 1.0)
    if mat.use_nodes:
        bs = mat.node_tree.nodes.get('Principled BSDF')
        if bs:
            bs.inputs['Base Color'].default_value = (*rgb,1.0)
            if rough is not None and 'Roughness' in bs.inputs:
                bs.inputs['Roughness'].default_value = rough

set_color(M.get('grass'), (0.610,0.690,0.315), .98)
set_color(M.get('grass_hill'), (0.480,0.600,0.330), .98)
set_color(M.get('tree_a'), (0.440,0.625,0.445), .98)
set_color(M.get('tree_b'), (0.505,0.680,0.485), .98)
set_color(M.get('tree_c'), (0.355,0.545,0.385), .98)
set_color(M.get('mountain'), (0.760,0.810,0.795), .99)
set_color(M.get('mountain_shadow'), (0.610,0.725,0.735), .99)
set_color(M.get('snow'), (0.900,0.925,0.900), .99)
set_color(M.get('rock'), (0.540,0.565,0.590), .98)
set_color(M.get('rock2'), (0.430,0.470,0.505), .98)
set_color(M.get('path'), (0.745,0.715,0.500), .98)
set_color(M.get('church'), (0.390,0.435,0.440), .96)
set_color(M.get('church_light'), (0.515,0.555,0.545), .96)
set_color(M.get('roof'), (0.215,0.255,0.270), .97)
set_color(M.get('blue'), (0.055,0.400,0.745), .92)
set_color(M.get('pink'), (0.930,0.455,0.510), .92)

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
try:
    scene.view_settings.view_transform='Standard'
    scene.view_settings.look='Medium High Contrast'
    scene.view_settings.exposure=-0.05
    scene.view_settings.gamma=1.0
    scene.eevee.use_gtao=True
    scene.eevee.gtao_distance=8
    scene.eevee.gtao_factor=0.72
    scene.eevee.use_soft_shadows=True
except Exception:
    pass
scene.world.use_nodes=True
bg=scene.world.node_tree.nodes.get('Background')
if bg:
    bg.inputs['Color'].default_value=(0.575,0.835,0.855,1.0)
    bg.inputs['Strength'].default_value=0.68

# -----------------------------------------------------------------------------
# Cleanup selected V9 features which were too schematic.
# -----------------------------------------------------------------------------
def remove_if(pred):
    for o in list(scene.objects):
        if pred(o):
            bpy.data.objects.remove(o, do_unlink=True)

remove_if(lambda o: o.name.startswith('Mountain_Ridge') or o.name.startswith('Mountain_Snow_Facets'))
remove_if(lambda o: o.name.startswith('Church_') or o.name.startswith('Grave') or o.name.startswith('Tomb') or o.name.startswith('Statue') or o.name.startswith('Cross_'))
remove_if(lambda o: 'Tent' in o.name or 'Camp' in o.name)
remove_if(lambda o: o.name.startswith('Rock_') or o.name.startswith('FieldRock_'))

# enlarge the playable glade without changing the reference composition
vg=scene.objects.get('Valley_Ground')
if vg:
    vg.location.y=25.0
    vg.dimensions=(226.0,214.0,1.5)
    bpy.context.view_layer.objects.active=vg
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# -----------------------------------------------------------------------------
# Broad faceted mountain masses: back wall + side shoulders.
# -----------------------------------------------------------------------------
def mountain_mass(name,cx,cy,rx,ry,h,seed,front_tint=False):
    rr=random.Random(SEED+seed)
    n=10
    verts=[]
    for i in range(n):
        a=2*math.pi*i/n
        verts.append((cx+rx*(.88+rr.uniform(-.08,.08))*math.cos(a),
                      cy+ry*(.88+rr.uniform(-.08,.08))*math.sin(a),
                      -2.0+rr.uniform(-.7,.5)))
    for i in range(n):
        a=2*math.pi*i/n+.12
        verts.append((cx+rx*.55*(.9+rr.uniform(-.1,.1))*math.cos(a),
                      cy+ry*.55*(.9+rr.uniform(-.1,.1))*math.sin(a),
                      h*.52+rr.uniform(-1.0,1.0)))
    peaks=[]
    for px,py,pz in [(-.13,-.05,1.0),(.16,.06,.91),(.02,-.14,.84)]:
        peaks.append(len(verts)); verts.append((cx+rx*px,cy+ry*py,h*pz))
    faces=[]; mids=[]
    for i in range(n):
        j=(i+1)%n
        faces.append((i,j,n+j,n+i)); mids.append((i+seed)%2)
        p=peaks[i%3]
        faces.append((n+i,n+j,p)); mids.append((i+1+seed)%2)
    o=mesh_obj(name,verts,faces,[M['mountain'],M['mountain_shadow']],mids)
    # broad snow facets rather than a cone cap
    sv=[]; sf=[]
    for k,pidx in enumerate(peaks):
        p=Vector(verts[pidx]); b=len(sv)
        sv.extend([tuple(p+Vector((-rx*.17,-ry*.04,-h*.13))),tuple(p),tuple(p+Vector((rx*.18,ry*.02,-h*.12))),tuple(p+Vector((0,-ry*.13,-h*.22)))])
        sf.extend([(b,b+1,b+3),(b+1,b+2,b+3)])
    mesh_obj(name+'_Snow',sv,sf,[M['snow']])
    return o

# back range, spaced so forms overlap into one continuous valley wall
back_specs=[
 (-150,205,58,34,58),(-113,200,54,32,67),(-76,204,58,34,73),(-36,207,58,34,64),
 (6,205,61,35,79),(52,202,62,34,71),(98,205,58,34,76),(142,203,55,32,62)
]
for i,s in enumerate(back_specs): mountain_mass('LegacyMountain_Back_%02d'%i,*s,100+i)
# side shoulders visible from the default high camera
side_specs=[
 (-142,118,56,42,58),(-135,62,54,45,48),(-128,8,50,45,39),
 (142,120,60,43,60),(136,67,56,45,50),(130,12,51,45,41)
]
for i,s in enumerate(side_specs): mountain_mass('LegacyMountain_Side_%02d'%i,*s,200+i)

# turquoise river/chasm glimpse through the back-left mountains
water_mat=bpy.data.materials.get('Legacy_River') or bpy.data.materials.new('Legacy_River')
water_mat.use_nodes=True
pbs=water_mat.node_tree.nodes.get('Principled BSDF')
if pbs:
    pbs.inputs['Base Color'].default_value=(0.18,0.62,0.73,1)
    pbs.inputs['Roughness'].default_value=.42
ribbon('Legacy_Back_River',[(-62,155),(-55,168),(-48,183),(-42,198)],5.0,-.25,water_mat)

# -----------------------------------------------------------------------------
# Rebuild forest placement to frame the arena more like the references.
# Existing V9 trees stay, but we add dense foreground / side belts.
# -----------------------------------------------------------------------------
existing_ids=[]
for o in scene.objects:
    if o.name.startswith('Pine_'):
        existing_ids.append(o.name)
# scale the stylized pines slightly taller, closer to TABS proportions
for o in scene.objects:
    if o.name.startswith('Pine_'):
        o.scale.z*=1.10

# extra border trees, deterministic and outside the big central ellipse
def open_glade(x,y):
    return ((x-2.0)/74.0)**2+((y-18.0)/58.0)**2 < 1.0

tree_id=2000
for _ in range(420):
    # choose one of four border bands
    band=rng.randrange(4)
    if band==0:
        x=rng.uniform(-105,-72); y=rng.uniform(-55,118)
    elif band==1:
        x=rng.uniform(72,105); y=rng.uniform(-55,118)
    elif band==2:
        x=rng.uniform(-104,104); y=rng.uniform(82,145)
    else:
        side=-1 if rng.random()<.5 else 1
        x=rng.uniform(62,105)*side; y=rng.uniform(-62,-30)
    if open_glade(x,y): continue
    pine('LegacyPine_%04d'%tree_id,x,y,rng.uniform(.85,1.55),tree_id)
    tree_id+=1

# a few distinctive broadleaf trees visible in the user reference
leaf_mat=M['tree_b']; leaf_dark=M['tree_c']; trunk=M['trunk']
def broad_tree(name,x,y,s=1.0):
    cyl(name+'_Trunk',(x,y,1.35*s),.32*s,2.7*s,trunk,vertices=7)
    ico(name+'_CrownA',(x,y,3.4*s),1.55*s,leaf_mat,scale=(1.2,1.0,.95),sub=1)
    ico(name+'_CrownB',(x-.8*s,y+.15*s,3.25*s),.95*s,leaf_dark,scale=(1.0,.9,.9),sub=1)
    ico(name+'_CrownC',(x+.65*s,y-.1*s,3.3*s),.9*s,leaf_mat,scale=(1.0,.9,.9),sub=1)
for i,(x,y,s) in enumerate([(-62,-10,1.2),(-88,42,1.0),(80,53,.92),(92,12,1.08)]): broad_tree('LegacyBroad_%02d'%i,x,y,s)

# -----------------------------------------------------------------------------
# TABS Legacy church, graveyard and monument.
# -----------------------------------------------------------------------------
CX,CY=-4.0,67.0
stone=M['church']; stone2=M['church_light']; roof=M['roof']; window=M['window']; door=M['door']; path=M['path']

# paths from arena to church / graveyard
ribbon('Legacy_Path_Main',[(0,4),(-3,17),(-8,30),(-3,43),(CX,CY-7)],1.8,.065,path)
ribbon('Legacy_Path_Loop',[(CX,CY-6),(CX-11,CY-4),(CX-13,CY+1),(CX-8,CY+5),(CX+2,CY+5),(CX+8,CY+2)],1.0,.067,path)
ribbon('Legacy_Path_Right',[(CX+6,CY-1),(CX+17,CY+3),(CX+29,CY+5)],.95,.067,path)

# nave and transept
box('LegacyChurch_Nave',(CX,CY,2.45),(10.0,6.2,4.9),stone,bev=.10)
box('LegacyChurch_Transept',(CX+3.0,CY+.7,2.2),(5.0,8.2,4.4),stone2,bev=.08)
# tower at front-left, matching multi-angle references
box('LegacyChurch_Tower',(CX-3.2,CY-2.2,5.1),(3.2,3.4,10.2),stone,bev=.08)
# tower bands
for z in (2.0,4.3,7.1,9.2): box('LegacyChurch_TowerBand_%02d'%int(z*10),(CX-3.2,CY-2.2,z),(3.55,3.7,.22),stone2,bev=.03)
# steeple
cone('LegacyChurch_Spire',(CX-3.2,CY-2.2,12.1),2.15,0,5.0,roof,vertices=8)
# tower window openings
for z in (5.5,8.0):
    box('LegacyChurch_TowerWinF_%02d'%int(z*10),(CX-3.2,CY-3.93,z),(1.0,.08,1.8),window,bev=.02)
    box('LegacyChurch_TowerWinL_%02d'%int(z*10),(CX-4.83,CY-2.2,z),(.08,1.0,1.8),window,bev=.02)

# gable roof helper along Y
def gable_roof(name,cx,cy,w,d,z,h,mat):
    x0=cx-w/2; x1=cx+w/2; y0=cy-d/2; y1=cy+d/2; xm=cx
    v=[(x0,y0,z),(x1,y0,z),(xm,y0,z+h),(x0,y1,z),(x1,y1,z),(xm,y1,z+h)]
    f=[(0,1,2),(3,5,4),(0,3,5,2),(1,2,5,4),(0,1,4,3)]
    return mesh_obj(name,v,f,[mat])
gable_roof('LegacyChurch_RoofMain',CX,CY,11.0,7.2,4.8,2.7,roof)
gable_roof('LegacyChurch_RoofWing',CX+3.0,CY+.7,5.6,9.0,4.25,2.15,roof)
# front door and nave windows
box('LegacyChurch_Door',(CX,CY-3.12,1.45),(1.6,.12,2.8),door,bev=.03)
for x in (CX-1.7,CX+1.6,CX+4.3):
    box('LegacyChurch_Window_%s'%str(x),(x,CY-3.13,2.65),(1.05,.10,2.0),window,bev=.02)
# side tall blue windows seen in close reference
for y in (CY-1.1,CY+1.2): box('LegacyChurch_SideWindow_%s'%str(y),(CX+5.05,y,2.7),(.09,1.0,2.1),window,bev=.02)

# graveyard around church: tombstones and crosses
for i in range(34):
    angle=rng.uniform(0,math.tau); rr=rng.uniform(7.0,16.0)
    x=CX+math.cos(angle)*rr; y=CY+math.sin(angle)*rr*.62
    if y<CY-7 and abs(x-CX)<5: continue
    h=rng.uniform(.65,1.4); w=rng.uniform(.45,.75)
    o=box('LegacyGrave_%02d'%i,(x,y,h/2),(w,.28,h),stone2,rot=(0,0,rng.uniform(-.15,.15)),bev=.05)
    if i%5==0:
        box('LegacyCrossV_%02d'%i,(x,y,h+.25),(.16,.18,.9),stone2,bev=.02)
        box('LegacyCrossH_%02d'%i,(x,y,h+.40),(.65,.18,.15),stone2,bev=.02)
# poacher monument / statue in front of church
box('LegacyMonument_Base',(CX-8.3,CY-5.8,.55),(2.2,2.2,1.1),stone2,bev=.08)
cyl('LegacyMonument_Column',(CX-8.3,CY-5.8,2.6),.45,3.0,stone,vertices=8)
ico('LegacyMonument_Statue',(CX-8.3,CY-5.8,4.55),.72,stone2,scale=(.55,.45,1.4),sub=1)

# ruined structure and crater on right side of church, visible in extra references
box('LegacyRuin_WallA',(31,78,1.5),(6.5,.8,3.0),stone,rot=(0,0,.10),bev=.04)
box('LegacyRuin_WallB',(34,81,1.2),(.8,5.4,2.4),stone2,rot=(0,0,-.10),bev=.04)
# crater as dark flattened low-poly disk
crater_mat=bpy.data.materials.get('Legacy_Crater') or bpy.data.materials.new('Legacy_Crater')
crater_mat.use_nodes=True
cb=crater_mat.node_tree.nodes.get('Principled BSDF')
if cb: cb.inputs['Base Color'].default_value=(.18,.15,.13,1); cb.inputs['Roughness'].default_value=.98
bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=4.0,depth=.10,location=(40,76,.04))
scene.objects.active if False else None
cr=bpy.context.object; cr.name='Legacy_Crater'; assign(cr,crater_mat); cr.scale=(1.35,.8,1)

# -----------------------------------------------------------------------------
# Red / blue camps: actual A-frame tents, positioned like the reference thumbnail.
# -----------------------------------------------------------------------------
def tent(name,x,y,angle,material,scale=1.0):
    w=4.3*scale; d=5.6*scale; h=2.5*scale
    verts=[(-w/2,-d/2,0),(w/2,-d/2,0),(0,-d/2,h),(-w/2,d/2,0),(w/2,d/2,0),(0,d/2,h)]
    faces=[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)]
    o=mesh_obj(name,verts,faces,[material]); o.location=(x,y,.05); o.rotation_euler[2]=angle
    # pale entrance pole
    cyl(name+'_Pole',(x,y-d*.52,.9*scale),.07*scale,1.8*scale,M['pole'],vertices=6)
    return o

blue_positions=[(-73,-23,-.14),(-61,-12,.09),(-52,-28,.17),(-44,-9,-.07),(-37,-25,.12),(-68,-40,.08),(-50,-44,-.12)]
pink_positions=[(58,58,.12),(66,61,-.10),(73,57,.10),(61,49,-.08),(70,47,.08),(78,51,-.12)]
for i,(x,y,a) in enumerate(blue_positions): tent('Legacy_BlueTent_%02d'%i,x,y,a,M['blue'],.82)
for i,(x,y,a) in enumerate(pink_positions): tent('Legacy_RedTent_%02d'%i,x,y,a,M['pink'],.82)

# -----------------------------------------------------------------------------
# Rocks: sparse field rocks + denser edges, matching the visible pattern.
# -----------------------------------------------------------------------------
for i in range(58):
    # keep center sparse
    for _attempt in range(20):
        x=rng.uniform(-92,92); y=rng.uniform(-50,115)
        if rng.random()<.65 and ((x/60.0)**2+((y-12)/52.0)**2)<.65: continue
        break
    r=rng.uniform(.35,1.05)
    ico('LegacyRock_%02d'%i,(x,y,.22*r),r,M['rock'] if i%3 else M['rock2'],scale=(1.25,.85,.60),sub=1)

# -----------------------------------------------------------------------------
# Lighting: soft, pale TABS daylight with readable tree shadows.
# -----------------------------------------------------------------------------
for o in list(scene.objects):
    if o.type=='LIGHT': bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.light_add(type='SUN',location=(0,-40,90))
sun=bpy.context.object; sun.name='Legacy_Sun'; sun.data.energy=1.15; sun.data.angle=math.radians(14); sun.rotation_euler=(math.radians(31),math.radians(-16),math.radians(-31))
bpy.ops.object.light_add(type='AREA',location=(-30,-55,80))
fill=bpy.context.object; fill.name='Legacy_SkyFill'; fill.data.energy=430; fill.data.size=75; fill.data.color=(.84,.94,1.0); look_at(fill,(0,28,0))

# -----------------------------------------------------------------------------
# Camera views / outputs. Default view matches the supplied screenshot framing.
# -----------------------------------------------------------------------------
cam=scene.camera
if not cam:
    bpy.ops.object.camera_add(); cam=bpy.context.object; scene.camera=cam
cam.data.type='PERSP'

def render(fn,pos,target,lens):
    cam.location=pos; cam.data.lens=lens; look_at(cam,target)
    scene.render.filepath=str(OUT/fn); bpy.ops.render.render(write_still=True)

render('preview_main.png',(0,-165,78),(0,38,5.0),47)
render('preview_left.png',(-112,-110,70),(-2,45,4.0),52)
render('preview_right.png',(112,-108,69),(2,45,4.0),52)
render('preview_top.png',(0,15,245),(0,18,0),50)
render('preview_church.png',(-38,15,30),(CX,CY,4.0),58)
render('preview_back.png',(0,190,62),(0,40,3.5),52)
# restore default
cam.location=(0,-165,78); cam.data.lens=47; look_at(cam,(0,38,5.0))

# save Blender and export GLB
blend_path=OUT/'tabs_legacy_reference_v10.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
for o in scene.objects: o.select_set(False)
for o in scene.objects:
    if o.type=='MESH': o.select_set(True)
glb_path=OUT/'tabs_legacy_reference_v10.glb'
glb_ok=True
try:
    bpy.ops.export_scene.gltf(filepath=str(glb_path),export_format='GLB',use_selection=True,export_apply=True)
except Exception as e:
    glb_ok=False
    print('GLB export failed:',e)

# report
mesh_objs=[o for o in scene.objects if o.type=='MESH']
verts=sum(len(o.data.vertices) for o in mesh_objs)
faces=sum(len(o.data.polygons) for o in mesh_objs)
tri=sum(len(p.vertices)-2 for o in mesh_objs for p in o.data.polygons)
trees=len({o.name.split('_')[0]+'_'+o.name.split('_')[1] if o.name.startswith('LegacyPine_') else o.name.split('_')[0] for o in mesh_objs if o.name.startswith('Pine_') or o.name.startswith('LegacyPine_')})
report=(
    'TABS Legacy reference map v10\n'
    'Reference basis: supplied screenshot + Legacy/Classic multi-angle screenshots\n'
    'Approximate playable glade: 220 m x 190 m\n'
    'Full modeled environment including mountains: ~400 m x 360 m\n'
    f'Mesh objects: {len(mesh_objs)}\nVertices: {verts}\nFaces: {faces}\nTriangles approx: {tri}\n'
    f'GLB export: {glb_ok}\n'
    'Key landmarks: church, graveyard, statue, ruins/crater, red camp, blue camp, river glimpse, mountain ring, forest border\n'
)
(OUT/'report.txt').write_text(report,encoding='utf-8')
print(report)
print('TABS_LEGACY_V10_COMPLETE')
