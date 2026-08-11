import bpy, bmesh, math, os, sys
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
OUT=os.path.join(ROOT,'ai-output'); os.makedirs(OUT,exist_ok=True)
args=sys.argv; src=args[args.index('--')+1] if '--' in args else None
if not src or not os.path.exists(src): raise SystemExit(f'INPUT_MESH_NOT_FOUND: {src}')
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene; sc.unit_settings.system='METRIC'; sc.unit_settings.length_unit='METERS'; sc.render.resolution_x=768; sc.render.resolution_y=768; sc.render.resolution_percentage=100; sc.render.image_settings.file_format='PNG'; sc.render.film_transparent=False
sc.render.engine='BLENDER_EEVEE' if bpy.app.version<(4,2,0) else 'BLENDER_EEVEE_NEXT'
try:
 sc.view_settings.view_transform='Standard'; sc.view_settings.look='Medium Low Contrast'; sc.view_settings.exposure=0.10
except: pass
if hasattr(bpy.ops.wm,'obj_import'): bpy.ops.wm.obj_import(filepath=src)
else: bpy.ops.import_scene.obj(filepath=src)
objs=[o for o in sc.objects if o.type=='MESH']
if not objs: raise SystemExit('NO_MESH_AFTER_IMPORT')
bpy.ops.object.select_all(action='DESELECT')
for o in objs:o.select_set(True)
bpy.context.view_layer.objects.active=objs[0]; bpy.ops.object.join(); obj=bpy.context.object; obj.name='AI_Cottage_TripoSR'
bm=bmesh.new(); bm.from_mesh(obj.data); bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-6); bmesh.ops.recalc_face_normals(bm,faces=bm.faces); bm.to_mesh(obj.data); bm.free(); obj.data.update()
def bounds(o):
 p=[o.matrix_world@Vector(c) for c in o.bound_box]; lo=Vector((min(v.x for v in p),min(v.y for v in p),min(v.z for v in p))); hi=Vector((max(v.x for v in p),max(v.y for v in p),max(v.z for v in p))); return lo,hi
lo,hi=bounds(obj); d=hi-lo; s=7.0/max(d.x,d.y,1e-6); obj.scale=(s,s,s); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); lo,hi=bounds(obj); obj.location-=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
def mat(n,c,r=.7):
 m=bpy.data.materials.get(n) or bpy.data.materials.new(n); m.use_nodes=True; p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*c,1); p.inputs['Roughness'].default_value=r; return m
if len(obj.data.materials)==0: obj.data.materials.append(mat('AI_Default',(0.78,.78,.76)))
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,-.12)); floor=bpy.context.object; floor.name='Backdrop'; floor.dimensions=(14,14,.18); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); floor.data.materials.append(mat('Backdrop_Cream',(.94,.925,.88),.95))
sc.world.use_nodes=True; bg=sc.world.node_tree.nodes.get('Background'); bg.inputs['Color'].default_value=(.96,.945,.90,1); bg.inputs['Strength'].default_value=.34
def look(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
def area(n,loc,e,size,col=(1,.97,.91)):
 bpy.ops.object.light_add(type='AREA',location=loc); l=bpy.context.object; l.name=n; l.data.energy=e; l.data.size=size; l.data.color=col; look(l,(0,0,2))
area('Key',(-5,-6,9),720,5.5); area('Fill',(5,-1,7),330,6,(.94,.97,1))
bpy.ops.object.light_add(type='SUN',location=(0,0,8)); sun=bpy.context.object; sun.data.energy=.50; sun.data.angle=math.radians(18); sun.rotation_euler=(math.radians(30),math.radians(-20),math.radians(-35))
bpy.ops.object.camera_add(location=(9.2,-11,8)); cam=bpy.context.object; cam.data.type='ORTHO'; cam.data.ortho_scale=9.4; sc.camera=cam; look(cam,(0,0,2))
blend=os.path.join(OUT,'triposr_model.blend'); bpy.ops.wm.save_as_mainfile(filepath=blend)
bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active=obj; bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'triposr_model.glb'),export_format='GLB',use_selection=True,export_apply=True)
views={'triposr_preview_perspective.png':((9.2,-11,8),(0,0,2),9.4),'triposr_preview_front.png':((0,-13,4.5),(0,0,2),8.8),'triposr_preview_right.png':((13,0,4.5),(0,0,2),8.8),'triposr_preview_top.png':((0,0,15),(0,0,0),9.2)}
for fn,(pos,tgt,scale) in views.items(): cam.location=pos; cam.data.ortho_scale=scale; look(cam,tgt); sc.render.filepath=os.path.join(OUT,fn); bpy.ops.render.render(write_still=True)
lo,hi=bounds(obj); tris=sum(max(1,len(p.vertices)-2) for p in obj.data.polygons)
with open(os.path.join(OUT,'triposr_report.txt'),'w') as f:f.write(f'Vertices: {len(obj.data.vertices)}\nFaces: {len(obj.data.polygons)}\nTriangles approx: {tris}\nBounds min: {tuple(lo)}\nBounds max: {tuple(hi)}\n')
cam.location=(9.2,-11,8); cam.data.ortho_scale=9.4; look(cam,(0,0,2)); bpy.ops.wm.save_as_mainfile(filepath=blend)
print('TRIPOSR_POSTPROCESS_V1_COMPLETE')
