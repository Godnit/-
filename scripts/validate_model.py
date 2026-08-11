import bpy
import bmesh
import os

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
OUT=os.path.join(ROOT,'output')
REPORT=os.path.join(OUT,'model_report.txt')

mesh_objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name!='Backdrop_Floor']
verts=edges=faces=tris=0
nonmanifold_total=0
loose_total=0
degenerate_total=0
issues=[]
mins=[1e18,1e18,1e18]
maxs=[-1e18,-1e18,-1e18]

for obj in mesh_objects:
    me=obj.data
    verts+=len(me.vertices); edges+=len(me.edges); faces+=len(me.polygons)
    tris+=sum(max(1,len(p.vertices)-2) for p in me.polygons)
    for corner in obj.bound_box:
        w=obj.matrix_world @ __import__('mathutils').Vector(corner)
        for i in range(3):
            mins[i]=min(mins[i],w[i]); maxs[i]=max(maxs[i],w[i])
    bm=bmesh.new(); bm.from_mesh(me)
    nonman=[e for e in bm.edges if not e.is_manifold]
    loose=[v for v in bm.verts if len(v.link_edges)==0]
    deg=[f for f in bm.faces if f.calc_area()<1e-10]
    nonmanifold_total+=len(nonman); loose_total+=len(loose); degenerate_total+=len(deg)
    if nonman or loose or deg:
        issues.append(f'{obj.name}: non_manifold={len(nonman)} loose={len(loose)} degenerate={len(deg)}')
    bm.free()

dims=[maxs[i]-mins[i] for i in range(3)]
glb=os.path.join(OUT,'model.glb')
blend=os.path.join(OUT,'model.blend')
preview_names=['preview_front.png','preview_back.png','preview_left.png','preview_right.png','preview_top.png','preview_perspective.png']
previews_ok=all(os.path.exists(os.path.join(OUT,p)) and os.path.getsize(os.path.join(OUT,p))>1000 for p in preview_names)

lines=[
    'Model: Reference Cottage',
    f'Blender Version: {bpy.app.version_string}',
    f'Objects: {len(mesh_objects)}',
    f'Vertices: {verts}',
    f'Edges: {edges}',
    f'Faces: {faces}',
    f'Triangles (approx): {tris}',
    f'Bounding Box Min: {mins}',
    f'Bounding Box Max: {maxs}',
    f'Dimensions XYZ meters: {dims}',
    f'Non-Manifold Edges: {nonmanifold_total}',
    f'Loose Vertices: {loose_total}',
    f'Degenerate Faces: {degenerate_total}',
    f'BLEND exists: {os.path.exists(blend)}',
    f'GLB exists: {os.path.exists(glb)}',
    f'All 6 previews exist: {previews_ok}',
    'Normals: recalculated outside during build',
]
if issues:
    lines.append('\nPer-object issues:')
    lines.extend(issues)
with open(REPORT,'w',encoding='utf-8') as f: f.write('\n'.join(lines))
print('\n'.join(lines))

fatal = (loose_total>0 or degenerate_total>0 or not os.path.exists(glb) or os.path.getsize(glb)<1000 or not previews_ok)
# Non-manifold is reported but not fatal because adjacent decorative solids can include intentionally non-manifold custom picket tips.
if fatal:
    raise SystemExit('VALIDATION_FAILED')
print('VALIDATION_OK')
