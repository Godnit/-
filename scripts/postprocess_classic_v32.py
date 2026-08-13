import bpy, os, math, random
from mathutils import Vector

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'output_classic_reference_v32')
os.makedirs(OUT,exist_ok=True)
scene=bpy.context.scene
SEED=320826

# Keep the accepted map-only/tree layout and rebuild only the distant mountains.
for obj in list(scene.objects):
    if obj.name.startswith('Mountain') or obj.name=='BackgroundGround':
        bpy.data.objects.remove(obj,do_unlink=True)


def make_mat(name,rgb):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    if p:
        p.inputs['Base Color'].default_value=(*rgb,1.0)
        p.inputs['Roughness'].default_value=.98
    m.diffuse_color=(*rgb,1.0)
    return m

# Much closer to the supplied image: pale almost-white faces with cool blue-grey facets.
M_MAIN=make_mat('Mountain_V32_Main',(0.78,0.82,0.80))
M_LIGHT=make_mat('Mountain_V32_Light',(0.87,0.88,0.84))
M_SHADOW=make_mat('Mountain_V32_Shadow',(0.59,0.69,0.71))
M_DEEP=make_mat('Mountain_V32_Deep',(0.48,0.61,0.65))
M_BACK=make_mat('Mountain_V32_Back',(0.70,0.77,0.77))
MATS=[M_MAIN,M_LIGHT,M_SHADOW,M_DEEP]

# Infinite-looking continuation of the meadow: use one huge plane so no cube side / green horizon slab is visible.
grass=bpy.data.materials.get('Grass')
if grass is None: raise RuntimeError('Grass material missing')
bpy.ops.mesh.primitive_plane_add(size=2,location=(0,620,-0.055))
g=bpy.context.object;g.name='BackgroundGround';g.scale=(360,720,1)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
g.data.materials.append(grass)
for p in g.data.polygons:p.use_smooth=False


def mountain_mass(name,cx,cy,rx,ry,h,seed,lean_x=0.0,lean_y=0.0,back=False):
    rr=random.Random(SEED+seed);n=10;verts=[];faces=[];fm=[]
    # Wide low-poly body. Lower rings stay broad so the silhouette is a rounded mountain mass,
    # not a pyramid. Base ring is buried under the meadow.
    rings=[(1.00,-3.2,0.00),(0.84,h*.16,.18),(0.64,h*.40,.48),(0.43,h*.65,.76)]
    for ri,(sc,z,lf) in enumerate(rings):
        for j in range(n):
            a=2*math.pi*j/n
            jx=1+rr.uniform(-.075,.075);jy=1+rr.uniform(-.06,.06)
            verts.append((cx+lean_x*lf+rx*sc*jx*math.cos(a),
                          cy+lean_y*lf+ry*sc*jy*math.sin(a),
                          z+(0 if ri==0 else rr.uniform(-h*.018,h*.018))))
    top0=len(verts);verts.append((cx+lean_x+rr.uniform(-rx*.05,rx*.05),cy+lean_y,h))
    top1=len(verts);side=-1 if seed%2==0 else 1
    verts.append((cx+lean_x+side*rx*.20,cy+lean_y-ry*.02,h*.86))
    for ri in range(len(rings)-1):
        a0=ri*n;b0=(ri+1)*n
        for j in range(n):
            k=(j+1)%n
            if (j+ri)%2:
                faces.extend([(a0+j,a0+k,b0+j),(a0+k,b0+k,b0+j)])
            else:
                faces.extend([(a0+j,a0+k,b0+k),(a0+j,b0+k,b0+j)])
            if back: mi=0
            else:
                ang=2*math.pi*(j+.5)/n
                score=math.cos(ang+math.radians(145))
                mi=1 if score>.42 else (3 if score<-.52 else (2 if (j+ri)%3==0 else 0))
            fm.extend([mi,mi])
    u0=(len(rings)-1)*n
    for j in range(n):
        k=(j+1)%n
        use2=(j in (1,2,6,7)) if side>0 else (j in (0,3,5,8))
        faces.append((u0+j,u0+k,top1 if use2 else top0))
        if back: fm.append(0)
        else:
            score=math.cos(2*math.pi*(j+.5)/n+math.radians(145))
            fm.append(1 if score>.25 else (3 if score<-.50 else 0))
    faces.append(tuple(reversed(range(n))));fm.append(0)
    mesh=bpy.data.meshes.new(name+'_Mesh');mesh.from_pydata(verts,[],faces);mesh.validate();mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    mats=[M_BACK] if back else MATS
    for m in mats:mesh.materials.append(m)
    for p,mi in zip(mesh.polygons,fm):p.material_index=min(mi,len(mats)-1);p.use_smooth=False
    return obj

# Distant front range: broad, rounded and low in the frame, with one dominant right dome.
front=[
(-220,292,86,61,27,4101, 5,-2),
(-162,288,92,64,34,4102,-6,-2),
(-100,292,94,65,31,4103, 6,-2),
(-35,298,101,69,39,4104,-7,-3),
( 38,297,96,67,34,4105, 5,-2),
(108,292,103,70,41,4106,-6,-3),
(178,288,94,65,35,4107, 5,-2),
(235,293,84,60,28,4108,-4,-2),
]
for i,s in enumerate(front):mountain_mass('Mountain_%02d'%i,*s,False)

# A low, softer rear silhouette through gaps only.
back=[
(-220,376,112,74,22,4201,3,-2),(-135,382,118,77,27,4202,-3,-2),
(-45,386,123,80,29,4203,3,-2),(52,385,123,80,28,4204,-3,-2),
(145,380,117,76,25,4205,3,-2),(225,375,108,72,21,4206,-3,-2),
]
for i,s in enumerate(back):mountain_mass('MountainBack_%02d'%i,*s,True)


def look_at(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
cam=scene.camera
if cam is None:raise RuntimeError('Scene camera missing')

def render(name,loc,target,lens):
    cam.location=loc;cam.data.lens=lens;look_at(cam,target)
    scene.render.filepath=os.path.join(OUT,name);bpy.ops.render.render(write_still=True)

render('preview_main.png',(0,-108,47),(0,44,3.8),47)
render('preview_closer.png',(-3,-98,44),(-4,47,3.7),49)
render('preview_left.png',(-50,-88,44),(0,44,3.8),50)
render('preview_right.png',(50,-88,44),(0,44,3.8),50)
render('preview_high.png',(0,-80,76),(0,45,.5),50)
cam.location=(0,-108,47);cam.data.lens=47;look_at(cam,(0,44,3.8))

blend=os.path.join(OUT,'classic_reference_v32.blend');bpy.ops.wm.save_as_mainfile(filepath=blend)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'classic_reference_v32.glb'),export_format='GLB',export_apply=True)
with open(os.path.join(OUT,'report.txt'),'w',encoding='utf-8') as f:
    f.write('TABS reference map v32\n')
    f.write('Pine count: 993; tree positions/scales/colors preserved\n')
    f.write('Map only: church/graves/tents/path removed\n')
    f.write('Mountains: distant broad rounded pale masses, blue-grey facets, no green horizon slab\n')
    f.write('Playable field: 218 x 252 Blender units\n')
print('V32_OK',blend)
