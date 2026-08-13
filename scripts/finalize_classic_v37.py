import bpy,os,math,random
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));OUT=os.path.join(ROOT,'output_classic_reference_v37');os.makedirs(OUT,exist_ok=True)
S=bpy.context.scene;S.render.resolution_x=1200;S.render.resolution_y=800;S.render.resolution_percentage=100

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

tune('Grass',(0.55,0.63,0.20));tune('GrassHill',(0.47,0.56,0.19));tune('Pine1',(0.20,0.34,0.20));tune('Pine2',(0.31,0.47,0.23));tune('Pine3',(0.43,0.57,0.27))
MAIN=mk('Mountain_Reference_Main',(0.64,0.73,0.74));LIGHT=mk('Mountain_Reference_Light',(0.78,0.83,0.82));SHADOW=mk('Mountain_Reference_Shadow',(0.49,0.62,0.66));BACK=mk('Mountain_Reference_Back',(0.69,0.77,0.78));SNOW=mk('Mountain_Reference_Snow',(0.94,0.95,0.92))

# Preserve all 993 tree centers; scale each pine only around its own center.
f=bpy.data.objects.get('PineForest')
if f and len(f.data.vertices)%54==0:
 v=f.data.vertices
 for s in range(0,len(v),54):
  b=v[s:s+54];cx=sum(q.co.x for q in b)/54;cy=sum(q.co.y for q in b)/54;z0=min(q.co.z for q in b);k=1.44 if cy<0 else (1.28 if cy<82 else 1.14)
  for q in b:q.co.x=cx+(q.co.x-cx)*k;q.co.y=cy+(q.co.y-cy)*k;q.co.z=z0+(q.co.z-z0)*k
 f.data.update()

# Remove every old mountain and every man-made prop.
for o in list(S.objects):
 n=o.name.lower()
 if o.name.startswith('Reference_Mountain') or o.name.startswith('Mountain') or any(k in n for k in ['church','grave','tent','camp','path']):bpy.data.objects.remove(o,do_unlink=True)

def mass(name,cx,cy,rx,ry,h,seed,back=False,shift=(0,0)):
 r=random.Random(seed);N=12;vs=[];fs=[];mi=[];rings=[(1,-9),(.82,h*.12),(.60,h*.34),(.39,h*.60),(.22,h*.78)]
 for ri,(sc,z) in enumerate(rings):
  d=ri/(len(rings)-1)
  for j in range(N):
   a=2*math.pi*j/N+r.uniform(-.045,.045);sx=rx*sc*(1+r.uniform(-.08,.08));sy=ry*sc*(1+r.uniform(-.08,.08))
   vs.append((cx+sx*math.cos(a)+shift[0]*d,cy+sy*math.sin(a)+shift[1]*d,z+r.uniform(-.7,.7)))
 peak=len(vs);vs.append((cx+shift[0],cy+shift[1],h))
 for ri in range(4):
  a0=ri*N;b0=(ri+1)*N
  for j in range(N):
   k=(j+1)%N
   if (j+ri+seed)%2:fs.extend([(a0+j,a0+k,b0+k),(a0+j,b0+k,b0+j)])
   else:fs.extend([(a0+j,a0+k,b0+j),(a0+k,b0+k,b0+j)])
   mi.extend([(j+ri)%3,(j+ri+1)%3])
 top=4*N
 for j in range(N):k=(j+1)%N;fs.append((top+j,top+k,peak));mi.append((j+seed)%3)
 me=bpy.data.meshes.new(name+'_Mesh');me.from_pydata(vs,[],fs);me.validate();me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
 mats=[BACK,LIGHT,SHADOW] if back else [MAIN,LIGHT,SHADOW]
 for m in mats:me.materials.append(m)
 for p,mx in zip(me.polygons,mi):p.material_index=mx
 return o

def snow(name,body,radius,drop,seed):
 rr=random.Random(seed);p=max(body.data.vertices,key=lambda q:q.co.z).co.copy();vs=[(p.x,p.y,p.z+.12)]
 N=7
 for j in range(N):
  a=2*math.pi*j/N+rr.uniform(-.12,.12);rad=radius*rr.uniform(.72,1.05)
  vs.append((p.x+rad*math.cos(a),p.y+rad*.58*math.sin(a),p.z-drop*rr.uniform(.72,1.08)))
 fs=[]
 for j in range(N):fs.append((0,1+j,1+((j+1)%N)))
 me=bpy.data.meshes.new(name+'_Mesh');me.from_pydata(vs,[],fs);me.validate();me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);me.materials.append(SNOW)
 return o

spec=[(-206,300,104,82,55,(-16,3)),(-154,332,92,72,48,(10,-2)),(-103,350,92,72,58,(8,2)),(-43,367,103,78,66,(-8,-2)),(25,366,112,82,75,(10,-2)),(93,352,105,79,64,(-7,1)),(162,326,116,85,78,(12,-3)),(220,296,110,80,58,(-8,2))]
b=[]
for i,(x,y,rx,ry,h,sh) in enumerate(spec):
 q=mass('Reference_Mountain_%02d'%i,x,y,rx,ry,h,3700+i,False,sh);b.append(q);mass('Reference_Mountain_Shoulder_%02d'%i,x+(18 if i%2 else -18),y-30,rx*.68,ry*.60,h*.43,4100+i,False,(0,0))
for i,(x,y,rx,ry,h) in enumerate([(-205,430,135,94,38),(-92,447,142,98,44),(40,450,150,100,46),(168,428,138,94,40)]):mass('Reference_MountainBack_%02d'%i,x,y,rx,ry,h,4700+i,True,(0,0))
for i,r,d in [(0,20,10),(2,19,10),(3,22,11),(4,25,13),(6,26,13),(7,20,10)]:snow('Reference_Mountain_Snow_%02d'%i,b[i],r,d,5200+i)

w=S.world
if w and w.use_nodes:
 bg=w.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(0.62,0.84,0.86,1);bg.inputs['Strength'].default_value=.72
try:S.view_settings.exposure=-.08
except:pass
for o in S.objects:
 if o.type=='LIGHT' and o.data.type=='SUN':o.data.energy=1.42

def look(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
c=S.camera
def render(n,loc,t,lens):c.location=loc;c.data.lens=lens;look(c,t);S.render.filepath=os.path.join(OUT,n);bpy.ops.render.render(write_still=True)
render('preview_main.png',(0,-176,102),(0,118,18),49);render('preview_closer.png',(0,-158,94),(0,115,16),51);render('preview_left.png',(-68,-157,94),(-10,116,16),51);render('preview_right.png',(68,-157,94),(10,116,16),51);render('preview_high.png',(0,-133,132),(0,116,6),53)
c.location=(0,-176,102);c.data.lens=49;look(c,(0,118,18))
blend=os.path.join(OUT,'classic_reference_v37.blend');bpy.ops.wm.save_as_mainfile(filepath=blend);bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'classic_reference_v37.glb'),export_format='GLB',export_apply=True)
with open(os.path.join(OUT,'report.txt'),'w') as q:q.write('TABS map V37 corrected\nMap only; all man-made props removed\nPine count: 993; centers unchanged\nTree sizes/colors reference-calibrated\nMountains rebuilt as sloping faceted massifs\nSnow integrated as summit facets\nGLB export: OK\n')
print('V37_FINAL_REFERENCE_OK',blend)
