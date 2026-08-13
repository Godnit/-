from pathlib import Path

v14_path = Path(__file__).with_name('build_classic_reference_v14.py')
outer = v14_path.read_text(encoding='utf-8')

outer = outer.replace('output_classic_reference_v14','output_classic_reference_v15')
outer = outer.replace('classic_reference_v14.blend','classic_reference_v15.blend')
outer = outer.replace('classic_reference_v14.glb','classic_reference_v15.glb')
outer = outer.replace('TABS Classic reference valley v14','TABS Classic reference valley v15')

outer_marker = "ns={'__file__':str(v13_path),'__name__':'__main__'}\nexec(compile(wrapper,str(v13_path),'exec'),ns,ns)"
if outer_marker not in outer:
    raise RuntimeError('v15 outer v14 execution marker missing')

patch_code = r'''
nested_marker = "ns={'__file__':str(src_path),'__name__':'__main__'}\nexec(compile(src,str(src_path),'exec'),ns,ns)"
if nested_marker not in wrapper:
    raise RuntimeError('v15 nested v13 execution marker missing')

v15_extra = r"""
# V15: remove the wall-like mountain masses and correct the over-bright terrain.
src = src.replace("scene.view_settings.exposure = -0.02", "scene.view_settings.exposure = 0.0")
src = src.replace("'grass':mat('Grass_Reference',(0.56,0.59,0.22),.98)", "'grass':mat('Grass_Reference',(0.54,0.57,0.18),.98)")
src = src.replace("'grass_hill':mat('Grass_Hill',(0.50,0.57,0.25),.98)", "'grass_hill':mat('Grass_Hill',(0.48,0.54,0.22),.98)")
src = src.replace("sun=bpy.context.object;sun.name='Sun';sun.data.energy=2.05", "sun=bpy.context.object;sun.name='Sun';sun.data.energy=1.30")
src = src.replace("area=bpy.context.object;area.name='Sky_Fill';area.data.energy=180;area.data.size=76", "area=bpy.context.object;area.name='Sky_Fill';area.data.energy=220;area.data.size=76")

# Increase actual tree silhouette size to the reference: very large foreground pines, substantial mid/back pines.
src = src.replace("s *= (1.58 if y < 8 else (1.36 if y < 68 else 1.16))", "s *= (1.82 if y < 8 else (1.50 if y < 70 else 1.30))")

# Add a deliberate cropped foreground-left pine cluster, matching the reference's large trees entering the image edge.
needle = "for i,(x,y,s,v) in enumerate(tree_positions):add_pine(x,y,s,v)"
addition = """# Explicit near-camera left cluster from the supplied reference framing.
for j,(x,y,s) in enumerate([(-89,-34,2.15),(-82,-30,2.05),(-75,-35,2.20),(-69,-28,1.95),(-63,-33,2.05),(-86,-20,1.90),(-78,-18,1.85),(-70,-21,1.75),(-61,-18,1.72)]):
    tree_positions.append((x,y,s,(len(tree_positions)+j)%3))

for i,(x,y,s,v) in enumerate(tree_positions):add_pine(x,y,s,v)"""
if needle not in src: raise RuntimeError('v15 tree emission marker missing')
src = src.replace(needle,addition)

# Replace the huge icosphere mountains with a continuous low-poly mountain ridge.
old_mountains = """mountain_specs=[
    (-142,258,88,78,56),(-80,270,92,82,64),(-12,278,100,88,76),
    (58,275,94,84,67),(126,262,92,80,70)
]
for i,(x,y,sx,sy,sz) in enumerate(mountain_specs):
    mm=M['mountain'] if i in (0,2,4) else M['mountain_shadow']
    ico('Mountain_%02d'%i,(x,y,sz*.12-10.0),(sx,sy,sz),mm,2)
    # lower shoulder mass gives a long gentle foothill slope instead of a vertical mountain wall
    ox=x+(-1 if i%2==0 else 1)*sx*.30
    ico('Mountain_Shoulder_%02d'%i,(ox,y-12,sz*.02-9.0),(sx*.62,sy*.82,sz*.58),M['mountain'],2)
    if i in (1,2,4):
        ico('Mountain_Snow_%02d'%i,(x-3.0,y-9.0,sz*.68),(sx*.23,sy*.19,sz*.12),M['snow'],1)
for i,(x,y,sx,sy,sz) in enumerate([(-170,315,92,86,42),(-92,325,98,90,40),(85,326,100,90,41),(170,312,94,84,43)]):
    ico('Mountain_Back_%02d'%i,(x,y,sz*.05-12.0),(sx,sy,sz),M['mountain_shadow'],2)"""
new_mountains = """ridge_x=[-185,-160,-136,-112,-88,-64,-40,-16,8,32,56,80,104,128,152,176,196]
ridge_h=[18,24,31,28,36,31,39,47,42,50,43,39,52,45,37,27,18]
ridge_y=[246,249,252,250,256,253,259,264,261,267,262,258,264,258,253,249,246]
front_y=178.0
back_y=330.0
verts=[]
for x in ridge_x: verts.append((x,front_y,-4.5))
for x,y,h in zip(ridge_x,ridge_y,ridge_h): verts.append((x,y,h))
for x in ridge_x: verts.append((x,back_y,-8.0))
n=len(ridge_x)
faces=[]; fm=[]
for i in range(n-1):
    faces.append((i,i+1,n+i)); fm.append(i%2)
    faces.append((i+1,n+i+1,n+i)); fm.append((i+1)%2)
    faces.append((n+i,n+i+1,2*n+i+1,2*n+i)); fm.append((i+1)%2)
mesh_obj('Mountain_Ridge',verts,faces,[M['mountain'],M['mountain_shadow']],fm)
rx2=[-205,-170,-135,-100,-65,-30,5,40,75,110,145,180,210]
rh2=[15,23,28,25,31,27,34,30,33,28,30,22,15]
ry2=[315,320,323,321,327,325,330,328,331,326,324,319,316]
v2=[]
for x in rx2:v2.append((x,265,-10))
for x,y,h in zip(rx2,ry2,rh2):v2.append((x,y,h))
for x in rx2:v2.append((x,390,-12))
n2=len(rx2);f2=[];m2=[]
for i in range(n2-1):
    f2.append((i,i+1,n2+i));m2.append(0)
    f2.append((i+1,n2+i+1,n2+i));m2.append(0)
    f2.append((n2+i,n2+i+1,2*n2+i+1,2*n2+i));m2.append(0)
mesh_obj('Mountain_Back_Ridge',v2,f2,[M['mountain_shadow']],m2)
snow_verts=[];snow_faces=[]
for idx in (6,7,9,12):
    x=ridge_x[idx];y=ridge_y[idx]-1;h=ridge_h[idx]
    b=len(snow_verts)
    snow_verts.extend([(x-6,y,h-7),(x,y-.5,h+.3),(x+6,y,h-6),(x,y-3,h-11)])
    snow_faces.extend([(b,b+1,b+3),(b+1,b+2,b+3)])
mesh_obj('Mountain_Snow_Facets',snow_verts,snow_faces,[M['snow']])"""
if old_mountains not in src:
    raise RuntimeError('v15 mountain block missing')
src = src.replace(old_mountains,new_mountains)

src = src.replace("'path':mat('Path_Pale_Sand',(0.72,0.69,0.49),.98)", "'path':mat('Path_Pale_Sand',(0.61,0.62,0.34),.98)")
"""

wrapper = wrapper.replace(nested_marker, v15_extra + "\n" + nested_marker)
'''

outer = outer.replace(outer_marker, patch_code + "\n" + outer_marker)

ns={'__file__':str(v14_path),'__name__':'__main__'}
exec(compile(outer,str(v14_path),'exec'),ns,ns)
