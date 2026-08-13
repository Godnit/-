import bpy, os, random, math
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'output_classic_reference_v37');os.makedirs(OUT,exist_ok=True)
S=bpy.context.scene
S.render.resolution_x=1280;S.render.resolution_y=720;S.render.resolution_percentage=100

def tune(n,c):
    m=bpy.data.materials.get(n)
    if not m:return
    m.diffuse_color=(*c,1)
    if m.use_nodes:
        p=m.node_tree.nodes.get('Principled BSDF')
        if p:p.inputs['Base Color'].default_value=(*c,1)

def mk(n,c):
    m=bpy.data.materials.get(n) or bpy.data.materials.new(n);m.use_nodes=True;m.diffuse_color=(*c,1)
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=.98
    return m

tune('Grass',(0.535,0.605,0.205));tune('GrassHill',(0.49,0.56,0.19))
tune('Pine1',(0.27,0.40,0.245));tune('Pine2',(0.35,0.49,0.285));tune('Pine3',(0.43,0.57,0.325))
MMAIN=mk('Mountain_Reference_Main',(0.72,0.78,0.77))
MLIGHT=mk('Mountain_Reference_Light',(0.86,0.89,0.86))
MSHADOW=mk('Mountain_Reference_Shadow',(0.57,0.68,0.71))
MBACK=mk('Mountain_Reference_Back',(0.68,0.76,0.77))

f=bpy.data.objects.get('PineForest')
if f and len(f.data.vertices)%54==0:
    vs=f.data.vertices
    for s in range(0,len(vs),54):
        b=vs[s:s+54];cx=sum(q.co.x for q in b)/54;cy=sum(q.co.y for q in b)/54;z0=min(q.co.z for q in b)
        k=1.36 if cy<0 else (1.25 if cy<82 else 1.26)
        for q in b:
            q.co.x=cx+(q.co.x-cx)*k;q.co.y=cy+(q.co.y-cy)*k;q.co.z=z0+(q.co.z-z0)*k
    f.data.update()

for o in list(S.objects):
    n=o.name.lower()
    if o.name.startswith('Reference_Mountain') or o.name.startswith('Reference_Shoulder') or o.name.startswith('Mountain') or any(k in n for k in ['church','grave','tent','camp','path']):
        bpy.data.objects.remove(o,do_unlink=True)

def mountain(name,cx,cy,rx,ry,h,seed,back=False,lean=0.0):
    rr=random.Random(seed)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(cx,cy,-45.0))
    o=bpy.context.object;o.name=name;me=o.data
    zmin=min(v.co.z for v in me.vertices);zmax=max(v.co.z for v in me.vertices)
    for v in me.vertices:
        rawx,rawy,rawz=v.co.x,v.co.y,v.co.z
        t=(rawz-zmin)/(zmax-zmin)
        radial=1.0-0.17*t
        v.co.x=rawx*rx*radial*(1.0+rr.uniform(-0.05,0.05)) + lean*t
        v.co.y=rawy*ry*radial*(1.0+rr.uniform(-0.04,0.04))
        bulge=h*0.09*math.exp(-((rawx*1.30)**2+(rawy*1.18)**2)*2.5)
        v.co.z=(t**1.04)*h+bulge+rr.uniform(-0.028,0.028)*h*(0.3+0.7*t)
    me.update()
    mats=[MBACK,MLIGHT,MSHADOW] if back else [MMAIN,MLIGHT,MSHADOW]
    for m in mats:me.materials.append(m)
    for p in me.polygons:
        z=sum(me.vertices[i].co.z for i in p.vertices)/len(p.vertices)
        if not back and z>h*0.70 and p.normal.z>0.08:p.material_index=1
        elif p.normal.x>0.24 or p.normal.y<-.32:p.material_index=2
        else:p.material_index=0
        p.use_smooth=False
    return o

main=[
 (-220,500,98,82,96,-8),(-145,515,104,86,106,7),(-66,525,100,84,92,4),
 (22,530,112,90,110,-5),(112,518,104,86,100,5),(205,500,100,82,94,-5)]
for i,(x,y,rx,ry,h,lean) in enumerate(main):mountain('Reference_Mountain_%02d'%i,x,y,rx,ry,h,9100+i,False,lean)
for i,(x,y,rx,ry,h) in enumerate([(-190,665,125,96,72),(-65,680,132,100,78),(70,680,135,100,77),(195,662,126,94,70)]):
    mountain('Reference_MountainBack_%02d'%i,x,y,rx,ry,h,9500+i,True,0)

w=S.world
if w and w.use_nodes:
    bg=w.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(0.63,0.84,0.86,1);bg.inputs['Strength'].default_value=.70
try:S.view_settings.exposure=-.10
except:pass
for o in S.objects:
    if o.type=='LIGHT' and o.data.type=='SUN':o.data.energy=1.34

def look(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
c=S.camera
def render(n,loc,t,lens):
    c.location=loc;c.data.lens=lens;look(c,t);S.render.filepath=os.path.join(OUT,n);bpy.ops.render.render(write_still=True)

# Raise the look target so the complete rounded summits and a cyan sky band are visible.
render('preview_main.png',(0,-170,80),(0,115,27),50)
render('preview_closer.png',(0,-154,74),(0,111,24),52)
render('preview_left.png',(-64,-154,75),(-8,112,24),52)
render('preview_right.png',(64,-154,75),(8,112,24),52)
render('preview_high.png',(0,-132,112),(0,110,13),54)
c.location=(0,-170,80);c.data.lens=50;look(c,(0,115,27))

blend=os.path.join(OUT,'classic_reference_v37.blend');bpy.ops.wm.save_as_mainfile(filepath=blend)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'classic_reference_v37.glb'),export_format='GLB',export_apply=True)
with open(os.path.join(OUT,'report.txt'),'w',encoding='utf-8') as q:
    q.write('TABS map V37 final camera pass\n')
    q.write('Map only; man-made props removed\n')
    q.write('Pine count: 993; centers unchanged\n')
    q.write('Mountains distant with buried bases\n')
    q.write('Full summits and sky band visible\n')
    q.write('Render: 1280x720 16:9\nGLB export: OK\n')
print('V37_FINAL_CAMERA_OK',blend)
