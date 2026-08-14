import bpy, bmesh
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output_cottage_multiview'
blend=OUT/'cottage_multiview.blend'
if not blend.exists(): raise SystemExit('Missing blend')
bpy.ops.wm.open_mainfile(filepath=str(blend))
nonman=loose=deg=0
meshes=0
for o in bpy.context.scene.objects:
    if o.type!='MESH': continue
    meshes+=1
    bm=bmesh.new(); bm.from_mesh(o.data)
    nonman += sum(1 for e in bm.edges if not e.is_manifold)
    loose += sum(1 for v in bm.verts if not v.link_edges)
    deg += sum(1 for f in bm.faces if f.calc_area()<1e-8)
    bm.free()
report=OUT/'validation_report.txt'
report.write_text(f'Mesh objects: {meshes}\nNon-manifold edges: {nonman}\nLoose vertices: {loose}\nDegenerate faces: {deg}\nGLB exists: {(OUT/"cottage_multiview.glb").exists()}\n',encoding='utf-8')
print(report.read_text())
if loose or deg: raise SystemExit(2)
if not (OUT/'cottage_multiview.glb').exists(): raise SystemExit(3)
