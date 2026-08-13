import bpy, os, math, random
from mathutils import Vector

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'output_classic_reference_v31')
os.makedirs(OUT,exist_ok=True)
scene=bpy.context.scene
SEED=310826

# Preserve the verified map/tree layout. Delete only prior mountain/background helpers.
for obj in list(scene.objects):
    if obj.name.startswith('Mountain') or obj.name=='BackgroundGround':
        bpy.data.objects.remove(obj,do_unlink=True)

# -----------------------------------------------------------------------------
# Materials: pale blue/grey TABS-like mountain palette with visible faceted planes.
# -----------------------------------------------------------------------------
def make_mat(name,rgb):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    if p:
        p.inputs['Base Color'].default_value=(*rgb,1.0)
        p.inputs['Roughness'].default_value=.98
    m.diffuse_color=(*rgb,1.0)
    return m

M_MAIN=make_mat('Mountain_V31_Main',(0.58,0.70,0.71))
M_LIGHT=make_mat('Mountain_V31_Light',(0.70,0.79,0.78))
M_SHADOW=make_mat('Mountain_V31_Shadow',(0.45,0.60,0.63))
M_DEEP=make_mat('Mountain_V31_Deep',(0.38,0.53,0.57))
M_BACK=make_mat('Mountain_V31_Back',(0.64,0.75,0.76))
MATS=[M_MAIN,M_LIGHT,M_SHADOW,M_DEEP]

def assign(o,m):
    o.data.materials.clear();o.data.materials.append(m)

def box(name,loc,dims,m):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object;o.name=name;o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    assign(o,m);return o

# Continue the same meadow behind the playable field. This hides mountain roots without changing gameplay size.
base_grass=bpy.data.materials.get('Grass')
if base_grass is None: raise RuntimeError('Grass material missing')
box('BackgroundGround',(0,278,-0.72),(230,220,1.44),base_grass)

# -----------------------------------------------------------------------------
# Irregular multi-ring mountain volume.
# Unlike the previous shallow icospheres, this has a real rising silhouette and varied summit.
# -----------------------------------------------------------------------------
def mountain_mass(name,cx,cy,rx,ry,h,seed,lean_x=0.0,lean_y=0.0,back=False):
    rr=random.Random(SEED+seed)
    n=8
    verts=[];faces=[];fm=[]
    # ring scale, z fraction, x/y lean fraction
    rings=[
        (1.00,-5.0,0.00),
        (0.82,h*.17,0.20),
        (0.60,h*.43,0.52),
        (0.38,h*.68,0.80),
    ]
    for ri,(sc,z,lf) in enumerate(rings):
        for j in range(n):
            a=2*math.pi*j/n
            # keep front/back widths broad but irregular; no uniform circular cap
            jitter=1.0+rr.uniform(-.10,.10)
            sx=rx*sc*jitter
            sy=ry*sc*(1.0+rr.uniform(-.08,.08))
            x=cx+lean_x*lf+sx*math.cos(a)
            y=cy+lean_y*lf+sy*math.sin(a)
            zz=z+(0 if ri==0 else rr.uniform(-h*.025,h*.025))
            verts.append((x,y,zz))
    # Main apex and an offset secondary summit produce the broad asymmetric TABS silhouette.
    top0=len(verts)
    verts.append((cx+lean_x+rr.uniform(-rx*.08,rx*.08),cy+lean_y+rr.uniform(-ry*.07,ry*.07),h))
    top1=len(verts)
    sec_side=-1 if seed%2==0 else 1
    verts.append((cx+lean_x+sec_side*rx*.22,cy+lean_y-ry*.03,h*.84+rr.uniform(-h*.025,h*.025)))

    # ring-to-ring low-poly facets
    for ri in range(len(rings)-1):
        a0=ri*n;b0=(ri+1)*n
        for j in range(n):
            k=(j+1)%n
            # Triangulate alternating ways for large readable facets.
            if (j+ri+seed)%2:
                faces.extend([(a0+j,a0+k,b0+j),(a0+k,b0+k,b0+j)])
            else:
                faces.extend([(a0+j,a0+k,b0+k),(a0+j,b0+k,b0+j)])
            # front-left planes lighter; opposite planes darker
            ang=2*math.pi*(j+.5)/n
            light_score=.55*math.cos(ang+math.radians(135))+.45*math.sin(ang+math.radians(135))
            if back:
                mi=0
            elif light_score>.35: mi=1
            elif light_score<-.45: mi=3
            else: mi=2 if (j+ri)%3==0 else 0
            fm.extend([mi,mi])

    # Upper ring to the two summit points. Split sectors between summits instead of one cone apex.
    u0=(len(rings)-1)*n
    for j in range(n):
        k=(j+1)%n
        # left/right sectors favor secondary peak, center sectors main peak
        use_secondary = j in ((1,2,5,6) if sec_side>0 else (0,3,4,7))
        t=top1 if use_secondary else top0
        faces.append((u0+j,u0+k,t))
        ang=2*math.pi*(j+.5)/n
        if back: mi=0
        elif math.cos(ang+math.radians(135))>.25: mi=1
        elif math.cos(ang+math.radians(135))<-.45: mi=3
        else: mi=0
        fm.append(mi)

    # Closed bottom under terrain.
    faces.append(tuple(reversed(range(n))))
    fm.append(3 if not back else 0)

    mesh=bpy.data.meshes.new(name+'_Mesh')
    mesh.from_pydata(verts,[],faces);mesh.validate();mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    mats=[M_BACK] if back else MATS
    for m in mats: mesh.materials.append(m)
    for p,mi in zip(mesh.polygons,fm):
        p.material_index=min(mi,len(mats)-1);p.use_smooth=False
    return obj

# Front enclosure: large but separated masses, with overlapping shoulders like the supplied reference.
front_specs=[
    (-185,235,61,44,34,3101,  8,-4),
    (-139,242,67,47,44,3102, -5,-3),
    (-88,247,70,49,39,3103,  7,-3),
    (-37,252,77,52,52,3104,-10,-4),
    (18,253,73,51,45,3105,  8,-3),
    (70,250,77,51,51,3106, -7,-4),
    (123,244,69,48,43,3107,  6,-3),
    (174,237,62,44,35,3108, -6,-4),
]
for s in front_specs: mountain_mass('Mountain_%02d'%front_specs.index(s),*s,False)

# Distant paler layer, smaller and partially hidden through front gaps.
back_specs=[
    (-185,307,82,55,27,3201,4,-2),(-115,313,86,57,31,3202,-4,-2),
    (-42,318,91,59,35,3203,5,-2),(39,317,90,59,33,3204,-4,-2),
    (117,312,86,56,30,3205,4,-2),(185,305,79,53,26,3206,-4,-2),
]
for i,s in enumerate(back_specs): mountain_mass('MountainBack_%02d'%i,*s,True)

# -----------------------------------------------------------------------------
# Camera + render: tree locations/colors/scales remain untouched from V27.
# -----------------------------------------------------------------------------
def look_at(o,target):
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
cam=scene.camera
if cam is None: raise RuntimeError('Scene camera missing')

def render(name,loc,target,lens):
    cam.location=loc;cam.data.lens=lens;look_at(cam,target)
    scene.render.filepath=os.path.join(OUT,name)
    bpy.ops.render.render(write_still=True)

render('preview_main.png',(0,-108,47),(0,44,3.8),47)
render('preview_closer.png',(-3,-98,44),(-4,47,3.7),49)
render('preview_left.png',(-50,-88,44),(0,44,3.8),50)
render('preview_right.png',(50,-88,44),(0,44,3.8),50)
render('preview_high.png',(0,-80,76),(0,45,.5),50)
cam.location=(0,-108,47);cam.data.lens=47;look_at(cam,(0,44,3.8))

blend=os.path.join(OUT,'classic_reference_v31.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'classic_reference_v31.glb'),export_format='GLB',export_apply=True)

with open(os.path.join(OUT,'report.txt'),'w',encoding='utf-8') as f:
    f.write('TABS reference map v31\n')
    f.write('Pine count: 993; V27 tree mesh preserved unchanged\n')
    f.write('Map only: church/graves/tents/path removed\n')
    f.write('Mountains: irregular multi-ring faceted volumes with asymmetric summits\n')
    f.write('Playable field: 218 x 252 Blender units\n')
    f.write('Mountain objects: %d\n'%sum(1 for o in scene.objects if o.name.startswith('Mountain')))
print('V31_OK',blend)
