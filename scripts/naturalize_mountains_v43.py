import bpy, os, math, random
from mathutils import Vector

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'output_classic_reference_v43')
os.makedirs(OUT,exist_ok=True)
scene=bpy.context.scene
scene.render.resolution_x=1024
scene.render.resolution_y=576
scene.render.resolution_percentage=100
rng=random.Random(430826)
CX,CY=0.0,48.0

# Remove V42 mountain props only; keep floating island, forest and meadow intact.
for o in list(scene.objects):
    if o.name.startswith('Mountain'):
        bpy.data.objects.remove(o,do_unlink=True)


def mat(name,rgb):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    if p:
        p.inputs['Base Color'].default_value=(*rgb,1)
        p.inputs['Roughness'].default_value=.96
    m.diffuse_color=(*rgb,1)
    return m

rock_lo=mat('V43_RockLow',(0.52,0.59,0.59))
rock_mid=mat('V43_RockMid',(0.61,0.68,0.68))
rock_hi=mat('V43_RockHigh',(0.70,0.76,0.75))
rock_shadow=mat('V43_RockShadow',(0.43,0.50,0.51))
snow=mat('V43_Snow',(0.88,0.90,0.87))
base_green=mat('V43_BaseGreen',(0.43,0.51,0.33))
M=[base_green,rock_lo,rock_mid,rock_hi,rock_shadow,snow]


def build_mass(name,cx,cy,rx,ry,h,seed,rot=0.0,snowy=True):
    """Asymmetric broad mountain. Only ~45 large faces; no dense triangle tessellation."""
    rr=random.Random(seed)
    n=9
    # fixed angle profile gives each side different width; each ring gets its own variation
    base_profile=[1.08,.96,1.13,.92,1.05,.88,1.12,.95,1.02]
    rings=[]
    verts=[]
    # contour rings shift progressively sideways/backward, creating a sloped mountain mass
    ring_specs=[
        (1.00,0.00, 0.00, 0.00),
        (0.76,0.24, rx*0.07, -ry*0.03),
        (0.49,0.55, rx*0.12,  ry*0.02),
        (0.28,0.79, rx*0.08,  ry*0.07),
    ]
    for r,(sc,zf,dx,dy) in enumerate(ring_specs):
        ring=[]
        for k in range(n):
            a=2*math.pi*k/n+rot
            prof=base_profile[(k+seed)%n]*(1.0+rr.uniform(-0.07,0.07))
            # non-horizontal contours create shoulders and gullies
            z=h*zf
            if r>0:
                z+=h*(0.035*math.sin(a*2.0+seed*.01)+rr.uniform(-0.025,0.025))
            x=cx+dx+rx*sc*prof*math.cos(a)
            y=cy+dy+ry*sc*(2.0-prof)*math.sin(a)
            ring.append(len(verts));verts.append((x,y,max(.02,z)))
        rings.append(ring)

    # three ridge points form an irregular crest instead of a cone tip
    crest=[]
    crest_data=[(-.16,-.02,.95),(.04,.05,1.04),(.19,.00,.91)]
    cr=rot+0.35
    for fx,fy,fz in crest_data:
        x=cx+rx*fx*math.cos(cr)-ry*fy*math.sin(cr)+rx*.08
        y=cy+rx*fx*math.sin(cr)+ry*fy*math.cos(cr)+ry*.07
        crest.append(len(verts));verts.append((x,y,h*fz))

    faces=[];fm=[]
    # broad QUADS on body, one material per altitude band with rare shadow panels
    for r in range(3):
        ra,rn=rings[r],rings[r+1]
        for k in range(n):
            j=(k+1)%n
            faces.append((ra[k],ra[j],rn[j],rn[k]))
            if r==0: mi=0 if k in (0,4,7) else 1
            elif r==1: mi=1 if k not in (2,6) else 4
            else: mi=2 if k not in (1,5) else 3
            fm.append(mi)

    # upper shoulder to ridge: only nine large faces
    top=rings[3]
    # divide the ring among 3 crest vertices
    for k in range(n):
        j=(k+1)%n
        c=crest[(k//3)%3]
        faces.append((top[k],top[j],c))
        if snowy and k in (0,1,2,5,6): fm.append(5)
        else: fm.append(3 if k not in (3,7) else 4)
    # connect ridge itself with one top face
    faces.append(tuple(crest));fm.append(5 if snowy else 3)

    me=bpy.data.meshes.new(name+'_Mesh')
    me.from_pydata(verts,[],faces);me.validate();me.update()
    ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
    for mm in M: me.materials.append(mm)
    for p,mi in zip(me.polygons,fm):
        p.material_index=mi
        # smooth lower body to hide internal triangulation, retain faceted upper silhouette
        p.use_smooth=(p.center.z < h*.72)
    return ob

# front curved range: overlapping asymmetric masses, positions follow an arc
specs=[
 (20,17,19,15,14,.10,False),
 (36,25,27,21,23,-.05,True),
 (55,29,31,24,31,.08,True),
 (75,22,25,19,22,-.12,False),
 (96,31,34,25,34,.04,True),
 (118,27,30,22,28,-.09,True),
 (140,23,26,20,22,.11,False),
 (158,16,19,15,15,-.05,False),
]
for i,(deg,off,rx,ry,h,rot,sn) in enumerate(specs):
    a=math.radians(deg)
    x=CX+(104+off)*math.cos(a)
    y=CY+(113+off*.72)*math.sin(a)
    build_mass('MountainNaturalV43_%02d'%i,x,y,rx,ry,h,43000+i,rot,sn)

# three rear massifs add depth but remain broad and pale
for i,(deg,h,rx,ry) in enumerate(((44,18,25,19),(91,21,28,21),(134,17,23,18))):
    a=math.radians(deg)
    x=CX+145*math.cos(a);y=CY+150*math.sin(a)
    ob=build_mass('MountainRearV43_%02d'%i,x,y,rx,ry,h,43500+i,.03,i==1)
    ob.scale.z=.92

# -----------------------------------------------------------------------------
# Make the mountain-side pines visibly comparable to the rest, but still varied.
# V42 already enlarged them once; V43 adds a modest second correction only far rear.
# -----------------------------------------------------------------------------
forest=bpy.data.objects.get('PineForest')
if forest is None or forest.type!='MESH' or len(forest.data.vertices)%54:
    raise RuntimeError('PineForest topology missing/unexpected')
vs=forest.data.vertices
pine_count=len(vs)//54
rr=random.Random(43993)
rear2=0
for start in range(0,len(vs),54):
    block=vs[start:start+54]
    cx=sum(v.co.x for v in block)/54.0
    cy=sum(v.co.y for v in block)/54.0
    z0=min(v.co.z for v in block)
    if cy>105:
        factor=rr.uniform(1.09,1.20)
    elif cy>88:
        factor=rr.uniform(1.04,1.12)
    else:
        continue
    rear2+=1
    for v in block:
        v.co.x=cx+(v.co.x-cx)*factor
        v.co.y=cy+(v.co.y-cy)*factor
        v.co.z=z0+(v.co.z-z0)*factor
forest.data.update()

# retain warm tree palette and softer reference-like environment
world=scene.world
if world:
    world.use_nodes=True
    bg=world.node_tree.nodes.get('Background')
    if bg:
        bg.inputs['Color'].default_value=(0.67,0.83,0.87,1)
        bg.inputs['Strength'].default_value=.80
for o in scene.objects:
    if o.type=='LIGHT' and o.data.type=='SUN':
        o.data.energy=1.65;o.data.angle=math.radians(20)

# render/export
def look_at(o,t): o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
cam=scene.camera
if cam is None: raise RuntimeError('Camera missing')
def render(name,loc,target,lens):
    cam.location=loc;cam.data.lens=lens;look_at(cam,target)
    scene.render.filepath=os.path.join(OUT,name);bpy.ops.render.render(write_still=True)

render('preview_main.png',(0,-520,235),(0,58,-1.5),40)
render('preview_mountains.png',(0,-150,78),(0,132,15),50)
render('preview_high.png',(0,-285,305),(0,60,-1),44)
render('preview_left.png',(-330,-285,150),(0,60,1),43)
render('preview_right.png',(330,-285,150),(0,60,1),43)
render('preview_closer.png',(0,-315,128),(0,60,3.5),42)
cam.location=(0,-520,235);cam.data.lens=40;look_at(cam,(0,58,-1.5))

blend=os.path.join(OUT,'classic_reference_v43.blend')
bpy.ops.wm.save_as_mainfile(filepath=blend)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'classic_reference_v43.glb'),export_format='GLB',export_apply=True)
with open(os.path.join(OUT,'report.txt'),'w',encoding='utf-8') as f:
    f.write('Classic Reference V43 natural mountains\n')
    f.write('Pine count: %d unchanged\n'%pine_count)
    f.write('Far rear pines additionally enlarged, varied, centers unchanged: %d\n'%rear2)
    f.write('Mountains: 8 front + 3 rear asymmetric broad masses on curved arc\n')
    f.write('Mountain body uses broad quads and smooth lower shading; no dense triangle mosaic\n')
    f.write('Floating island and meadow preserved\n')
print('V43_OK',blend)
