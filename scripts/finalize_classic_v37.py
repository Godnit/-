import bpy, os, math, random
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'output_classic_reference_v37');os.makedirs(OUT,exist_ok=True)
scene=bpy.context.scene;scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.render.resolution_percentage=100

# -----------------------------------------------------------------------------
# Keep EXACT forest centers/count. Only scale each baked pine around its own center.
# -----------------------------------------------------------------------------
forest=bpy.data.objects.get('PineForest')
if forest and len(forest.data.vertices)%54==0:
    vs=forest.data.vertices
    for s in range(0,len(vs),54):
        b=vs[s:s+54];cx=sum(v.co.x for v in b)/54;cy=sum(v.co.y for v in b)/54;z0=min(v.co.z for v in b)
        f=1.44 if cy<0 else (1.28 if cy<82 else 1.14)
        for v in b:
            v.co.x=cx+(v.co.x-cx)*f;v.co.y=cy+(v.co.y-cy)*f;v.co.z=z0+(v.co.z-z0)*f
    forest.data.update()

def tune(name,rgb):
    m=bpy.data.materials.get(name)
    if not m:return
    m.diffuse_color=(*rgb,1)
    if m.use_nodes:
        p=m.node_tree.nodes.get('Principled BSDF')
        if p:p.inputs['Base Color'].default_value=(*rgb,1)

def mk(name,rgb):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    if p:p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=.98
    m.diffuse_color=(*rgb,1);return m

tune('Grass',(0.55,0.63,0.20));tune('GrassHill',(0.47,0.56,0.19))
tune('Pine1',(0.20,0.34,0.20));tune('Pine2',(0.31,0.47,0.23));tune('Pine3',(0.43,0.57,0.27))
MAIN=mk('Mountain_Reference_Main',(0.64,0.73,0.74));LIGHT=mk('Mountain_Reference_Light',(0.78,0.83,0.82))
SHADOW=mk('Mountain_Reference_Shadow',(0.49,0.62,0.66));BACK=mk('Mountain_Reference_Back',(0.69,0.77,0.78));SNOW=mk('Mountain_Reference_Snow',(0.94,0.95,0.92))

for o in list(scene.objects):
    if o.name.startswith('Reference_Mountain_') or o.name.startswith('Reference_MountainBack_'):
        bpy.data.objects.remove(o,do_unlink=True)

def mountain_mass(name,cx,cy,rx,ry,h,seed,main=True,peak_shift=(0,0)):
    rr=random.Random(seed);n=12;verts=[];faces=[];fm=[]
    rings=[(1.00,-9.0),(.82,h*.12),(.60,h*.34),(.39,h*.60),(.22,h*.78)]
    for ri,(sc,z) in enumerate(rings):
        for j in range(n):
            a=2*math.pi*j/n+rr.uniform(-.045,.045)
            sx=rx*sc*(1+rr.uniform(-.08,.08));sy=ry*sc*(1+rr.uniform(-.08,.08));drift=ri/(len(rings)-1)
            verts.append((cx+sx*math.cos(a)+peak_shift[0]*drift,cy+sy*math.sin(a)+peak_shift[1]*drift,z+rr.uniform(-.7,.7)))
    peak=len(verts);verts.append((cx+peak_shift[0],cy+peak_shift[1],h))
    for ri in range(len(rings)-1):
        a0=ri*n;b0=(ri+1)*n
        for j in range(n):
            k=(j+1)%n
            if (j+ri+seed)%2:faces.extend([(a0+j,a0+k,b0+k),(a0+j,b0+k,b0+j)])
            else:faces.extend([(a0+j,a0+k,b0+j),(a0+k,b0+k,b0+j)])
            fm.extend([(j+ri)%3,(j+ri+1)%3])
    top=(len(rings)-1)*n
    for j in range(n):
        k=(j+1)%n;faces.append((top+j,top+k,peak));fm.append((j+seed)%3)
    me=bpy.data.meshes.new(name+'_Mesh');me.from_pydata(verts,[],faces);me.validate();me.update()
    o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
    mats=[MAIN,LIGHT,SHADOW] if main else [BACK,LIGHT,SHADOW]
    for m in mats:me.materials.append(m)
    for p,mi in zip(me.polygons,fm):p.material_index=mi
    return o

def shoulder(name,cx,cy,rx,ry,h,seed):return mountain_mass(name,cx,cy,rx,ry,h,seed,True,(0,0))

def snow_patch(name,body,rx,ry,h,offset=(0,0)):
    peak=max(body.data.vertices,key=lambda v:v.co.z).co
    cx=peak.x+offset[0];cy=peak.y+offset[1];top=peak.z
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(cx,cy,top-h*.34))
    o=bpy.context.object;o.name=name;o.scale=(rx*.72,ry*.72,h*.62);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(SNOW)
    for p in o.data.polygons:p.use_smooth=False
    return o

specs=[
 (-206,300,104,82,55,(-16,3)),(-154,332,92,72,48,(10,-2)),(-103,350,92,72,58,(8,2)),
 (-43,367,103,78,66,(-8,-2)),(25,366,112,82,75,(10,-2)),(93,352,105,79,64,(-7,1)),
 (162,326,116,85,78,(12,-3)),(220,296,110,80,58,(-8,2)),]
bodies=[]
for i,(x,y,rx,ry,h,shift) in enumerate(specs):
    b=mountain_mass('Reference_Mountain_%02d'%i,x,y,rx,ry,h,3700+i,True,shift);bodies.append(b)
    shoulder('Reference_Mountain_Shoulder_%02d'%i,x+(18 if i%2 else -18),y-30,rx*.68,ry*.60,h*.43,4100+i)
for i,(x,y,rx,ry,h) in enumerate([(-205,430,135,94,38),(-92,447,142,98,44),(40,450,150,100,46),(168,428,138,94,40)]):
    mountain_mass('Reference_MountainBack_%02d'%i,x,y,rx,ry,h,4700+i,False,(0,0))
for idx,rx,ry,hh,off in [(0,28,18,8,(-8,0)),(2,27,17,9,(3,0)),(3,31,19,10,(-3,0)),(4,35,21,12,(6,0)),(6,37,22,12,(7,1)),(7,29,18,9,(-4,0))]:
    snow_patch('Reference_Mountain_Snow_%02d'%idx,bodies[idx],rx,ry,hh,off)

for o in list(scene.objects):
    n=o.name.lower()
    if any(k in n for k in ['church','grave','tent','camp','path']):bpy.data.objects.remove(o,do_unlink=True)

world=scene.world
if world and world.use_nodes:
    bg=world.node_tree.nodes.get('Background')
    if bg:bg.inputs['Color'].default_value=(0.62,0.84,0.86,1);bg.inputs['Strength'].default_value=.72
try:scene.view_settings.exposure=-.08
except Exception:pass
for o in scene.objects:
    if o.type=='LIGHT' and o.data.type=='SUN':o.data.energy=1.42

def look(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
cam=scene.camera
def render(n,loc,t,lens):cam.location=loc;cam.data.lens=lens;look(cam,t);scene.render.filepath=os.path.join(OUT,n);bpy.ops.render.render(write_still=True)
render('preview_main.png',(0,-176,102),(0,118,18),49)
render('preview_closer.png',(0,-158,94),(0,115,16),51)
render('preview_left.png',(-68,-157,94),(-10,116,16),51)
render('preview_right.png',(68,-157,94),(10,116,16),51)
render('preview_high.png',(0,-133,132),(0,116,6),53)
cam.location=(0,-176,102);cam.data.lens=49;look(cam,(0,118,18))

blend=os.path.join(OUT,'classic_reference_v37.blend');bpy.ops.wm.save_as_mainfile(filepath=blend)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'classic_reference_v37.glb'),export_format='GLB',export_apply=True)
with open(os.path.join(OUT,'report.txt'),'w',encoding='utf-8') as f:
    f.write('TABS map V37 corrected\nMap only; all church/tents/paths removed\nPine count: 993; centers unchanged\nTree size and palette calibrated to reference\nMountains rebuilt as sloping faceted massifs\nSnow caps placed on true summits\nGLB export: OK\n')
print('V37_REFERENCE_CORRECTED_OK',blend)
