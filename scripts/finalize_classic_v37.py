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

# TABS-like meadow and pines: pale yellow-green with cool shadows.
tune('Grass',(0.535,0.605,0.205));tune('GrassHill',(0.49,0.56,0.19))
tune('Pine1',(0.27,0.40,0.245));tune('Pine2',(0.35,0.49,0.285));tune('Pine3',(0.43,0.57,0.325))
MMAIN=mk('Mountain_Reference_Main',(0.73,0.79,0.78))
MLIGHT=mk('Mountain_Reference_Light',(0.87,0.89,0.85))
MSHADOW=mk('Mountain_Reference_Shadow',(0.58,0.68,0.70))
MBACK=mk('Mountain_Reference_Back',(0.69,0.76,0.76))

# Preserve the 993 centers exactly. Only scale every pine around its own center.
f=bpy.data.objects.get('PineForest')
if f and len(f.data.vertices)%54==0:
    vs=f.data.vertices
    for s in range(0,len(vs),54):
        b=vs[s:s+54];cx=sum(q.co.x for q in b)/54;cy=sum(q.co.y for q in b)/54;z0=min(q.co.z for q in b)
        k=1.36 if cy<0 else (1.25 if cy<82 else 1.26)
        for q in b:
            q.co.x=cx+(q.co.x-cx)*k;q.co.y=cy+(q.co.y-cy)*k;q.co.z=z0+(q.co.z-z0)*k
    f.data.update()

# Delete old mountains and all man-made objects.
for o in list(S.objects):
    n=o.name.lower()
    if o.name.startswith('Reference_Mountain') or o.name.startswith('Mountain') or any(k in n for k in ['church','grave','tent','camp','path']):
        bpy.data.objects.remove(o,do_unlink=True)

# Broad rounded low-poly mountain, closer to the soft TABS silhouettes than pointed cones.
def rounded_mountain(name,cx,cy,rx,ry,h,seed,back=False,lean=0.0):
    rr=random.Random(seed)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(cx,cy,-11.0))
    o=bpy.context.object;o.name=name;me=o.data
    for v in me.vertices:
        t=(v.co.z+1.0)*0.5
        radial=1.0-0.30*t
        jitter=1.0+rr.uniform(-0.065,0.065)*(0.35+0.65*(1.0-t))
        v.co.x=v.co.x*rx*radial*jitter + lean*t
        v.co.y=v.co.y*ry*radial*(1.0+rr.uniform(-0.045,0.045))
        v.co.z=t*h + rr.uniform(-0.35,0.35)*(0.25+0.75*(1.0-t))
    me.update()
    mats=[MBACK,MLIGHT,MSHADOW] if back else [MMAIN,MLIGHT,MSHADOW]
    for m in mats:me.materials.append(m)
    # Integrated pale summit faces; no separate snow geometry.
    for p in me.polygons:
        z=sum(me.vertices[i].co.z for i in p.vertices)/len(p.vertices)
        if not back and z>h*0.70 and p.normal.z>0.18:p.material_index=1
        elif p.normal.x>0.23 or p.normal.y<-.28:p.material_index=2
        else:p.material_index=0
        p.use_smooth=False
    return o

# Main enclosure: fewer, broader, farther masses matching the reference skyline.
main=[
 (-220,382,112,88,50,-10),(-158,402,100,82,47,7),(-92,414,104,86,55,6),
 (-22,422,116,90,60,-6),(55,419,110,88,56,7),(130,405,112,86,58,-6),(207,380,122,91,54,8)]
for i,(x,y,rx,ry,h,lean) in enumerate(main):
    rounded_mountain('Reference_Mountain_%02d'%i,x,y,rx,ry,h,6000+i,False,lean)
# Low shoulders blend the mountain feet instead of forming a vertical wall.
shoulders=[(-235,345,125,86,28),(-135,360,120,82,27),(-30,370,128,84,30),(80,366,126,84,29),(185,346,132,88,28)]
for i,(x,y,rx,ry,h) in enumerate(shoulders):rounded_mountain('Reference_Shoulder_%02d'%i,x,y,rx,ry,h,6500+i,False,0)
# Pale distant row through gaps.
for i,(x,y,rx,ry,h) in enumerate([(-205,500,145,100,31),(-80,515,150,102,36),(60,515,155,104,37),(190,497,145,98,32)]):
    rounded_mountain('Reference_MountainBack_%02d'%i,x,y,rx,ry,h,7000+i,True,0)

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

# 16:9 framing matching the supplied screenshot.
render('preview_main.png',(0,-166,78),(0,106,7),49)
render('preview_closer.png',(0,-150,71),(0,103,6),51)
render('preview_left.png',(-66,-150,73),(-8,105,6),51)
render('preview_right.png',(66,-150,73),(8,105,6),51)
render('preview_high.png',(0,-128,112),(0,108,2),53)
c.location=(0,-166,78);c.data.lens=49;look(c,(0,106,7))

blend=os.path.join(OUT,'classic_reference_v37.blend');bpy.ops.wm.save_as_mainfile(filepath=blend)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'classic_reference_v37.glb'),export_format='GLB',export_apply=True)
with open(os.path.join(OUT,'report.txt'),'w',encoding='utf-8') as q:
    q.write('TABS map V37 rounded mountain pass\n')
    q.write('Map only; church/tents/graves/paths removed\n')
    q.write('Pine count: 993; centers unchanged\n')
    q.write('Trees scaled around fixed centers only\n')
    q.write('Mountains: broad rounded low-poly masses, no separate snow meshes\n')
    q.write('Render framing: 1280x720 reference-like 16:9\n')
    q.write('GLB export: OK\n')
print('V37_ROUNDED_REFERENCE_OK',blend)
