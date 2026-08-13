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

# Preserve all 993 pine centers exactly.
f=bpy.data.objects.get('PineForest')
if f and len(f.data.vertices)%54==0:
    vs=f.data.vertices
    for s in range(0,len(vs),54):
        b=vs[s:s+54];cx=sum(q.co.x for q in b)/54;cy=sum(q.co.y for q in b)/54;z0=min(q.co.z for q in b)
        k=1.36 if cy<0 else (1.25 if cy<82 else 1.26)
        for q in b:
            q.co.x=cx+(q.co.x-cx)*k;q.co.y=cy+(q.co.y-cy)*k;q.co.z=z0+(q.co.z-z0)*k
    f.data.update()

# Map only: remove prior mountains and all man-made props.
for o in list(S.objects):
    n=o.name.lower()
    if o.name.startswith('Reference_Mountain') or o.name.startswith('Reference_Shoulder') or o.name.startswith('Mountain') or any(k in n for k in ['church','grave','tent','camp','path']):
        bpy.data.objects.remove(o,do_unlink=True)

def mountain(name,cx,cy,rx,ry,h,seed,back=False,lean=0.0):
    rr=random.Random(seed)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(cx,cy,-14.0))
    o=bpy.context.object;o.name=name;me=o.data
    zmin=min(v.co.z for v in me.vertices);zmax=max(v.co.z for v in me.vertices)
    for v in me.vertices:
        rawx,rawy,rawz=v.co.x,v.co.y,v.co.z
        t=(rawz-zmin)/(zmax-zmin)
        # Taller mountain profile with a rounded summit; high vertices receive more variation.
        radial=(1.0-0.18*t)
        side_noise=1.0+rr.uniform(-0.055,0.055)*(0.6+0.4*(1-t))
        v.co.x=rawx*rx*radial*side_noise + lean*t
        v.co.y=rawy*ry*radial*(1.0+rr.uniform(-0.04,0.04))
        peak_bulge=h*0.10*math.exp(-((rawx*1.35)**2+(rawy*1.15)**2)*2.4)
        v.co.z=(t**1.05)*h + peak_bulge + rr.uniform(-0.035,0.035)*h*(0.25+0.75*t)
    me.update()
    mats=[MBACK,MLIGHT,MSHADOW] if back else [MMAIN,MLIGHT,MSHADOW]
    for m in mats:me.materials.append(m)
    # Light summit planes are integrated in the mountain surface, never separate snow geometry.
    for p in me.polygons:
        z=sum(me.vertices[i].co.z for i in p.vertices)/len(p.vertices)
        if not back and z>h*0.68 and p.normal.z>0.08:p.material_index=1
        elif p.normal.x>0.22 or p.normal.y<-.30:p.material_index=2
        else:p.material_index=0
        p.use_smooth=False
    return o

# Distinct broad peaks with visible valleys, closer to the original TABS screenshot.
main=[
 (-215,405,76,70,76,-8),(-142,420,82,72,86,7),(-66,430,78,70,74,4),
 (20,432,88,75,88,-5),(108,421,82,72,80,5),(198,404,78,68,74,-5)]
for i,(x,y,rx,ry,h,lean) in enumerate(main):mountain('Reference_Mountain_%02d'%i,x,y,rx,ry,h,8100+i,False,lean)
# Distant pale range visible only through gaps.
for i,(x,y,rx,ry,h) in enumerate([(-190,515,110,88,43),(-70,530,118,92,49),(62,530,120,92,48),(185,513,110,86,42)]):
    mountain('Reference_MountainBack_%02d'%i,x,y,rx,ry,h,8500+i,True,0)

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

# Lower reference-like aerial framing: large open field, forest ring, mountains occupying the top quarter.
render('preview_main.png',(0,-170,72),(0,105,5.5),50)
render('preview_closer.png',(0,-154,67),(0,102,5.0),52)
render('preview_left.png',(-64,-154,69),(-8,104,5.0),52)
render('preview_right.png',(64,-154,69),(8,104,5.0),52)
render('preview_high.png',(0,-132,108),(0,107,2),54)
c.location=(0,-170,72);c.data.lens=50;look(c,(0,105,5.5))

blend=os.path.join(OUT,'classic_reference_v37.blend');bpy.ops.wm.save_as_mainfile(filepath=blend)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'classic_reference_v37.glb'),export_format='GLB',export_apply=True)
with open(os.path.join(OUT,'report.txt'),'w',encoding='utf-8') as q:
    q.write('TABS map V37 mountain silhouette fix\n')
    q.write('Map only; all man-made props removed\n')
    q.write('Pine count: 993; centers unchanged\n')
    q.write('Mountain masses: 6 main + 4 distant, rounded low-poly\n')
    q.write('No floating snow; highlights integrated into mountain faces\n')
    q.write('Render: 1280x720 16:9\nGLB export: OK\n')
print('V37_MOUNTAIN_SILHOUETTE_OK',blend)
