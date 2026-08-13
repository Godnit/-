from pathlib import Path

src_path = Path(__file__).with_name('build_classic_reference_v16.py')
src = src_path.read_text(encoding='utf-8')

# Deliverable names
src = src.replace('output_classic_reference_v16','output_classic_reference_v17')
src = src.replace('classic_reference_v16.blend','classic_reference_v17.blend')
src = src.replace('classic_reference_v16.glb','classic_reference_v17.glb')
src = src.replace('TABS Classic reference v16','TABS Classic reference v17')
src = src.replace("print('V16_OK'", "print('V17_OK'")

# Palette calibrated against the supplied reference pixels.
repls = [
("bg.inputs['Color'].default_value = (0.67,0.87,0.89,1.0)", "bg.inputs['Color'].default_value = (0.59,0.79,0.80,1.0)"),
("bg.inputs['Strength'].default_value = 0.78", "bg.inputs['Strength'].default_value = 0.62"),
("'grass': mat('Grass',(0.575,0.610,0.235))", "'grass': mat('Grass',(0.43,0.48,0.12))"),
("'grass_hill': mat('GrassHill',(0.50,0.56,0.22))", "'grass_hill': mat('GrassHill',(0.39,0.45,0.14))"),
("'tree1': mat('Pine1',(0.30,0.48,0.38))", "'tree1': mat('Pine1',(0.16,0.30,0.22))"),
("'tree2': mat('Pine2',(0.37,0.55,0.43))", "'tree2': mat('Pine2',(0.22,0.37,0.27))"),
("'tree3': mat('Pine3',(0.43,0.60,0.47))", "'tree3': mat('Pine3',(0.28,0.44,0.32))"),
("'mountain': mat('Mountain',(0.70,0.80,0.80))", "'mountain': mat('Mountain',(0.61,0.72,0.72))"),
("'mountain2': mat('MountainShadow',(0.54,0.70,0.73))", "'mountain2': mat('MountainShadow',(0.45,0.61,0.64))"),
("'snow': mat('Snow',(0.88,0.91,0.89))", "'snow': mat('Snow',(0.80,0.85,0.83))"),
("'rock': mat('Rock',(0.49,0.55,0.60))", "'rock': mat('Rock',(0.40,0.46,0.51))"),
("'rock2': mat('Rock2',(0.39,0.48,0.54))", "'rock2': mat('Rock2',(0.31,0.39,0.45))"),
("'path': mat('Path',(0.68,0.66,0.39))", "'path': mat('Path',(0.55,0.55,0.26))"),
("sun=bpy.context.object;sun.data.energy=1.55", "sun=bpy.context.object;sun.data.energy=1.38"),
("area=bpy.context.object;area.data.energy=250;area.data.size=70", "area=bpy.context.object;area.data.energy=190;area.data.size=72"),
]
for old,new in repls:
    if old not in src: raise RuntimeError('v17 expected fragment missing: '+old)
    src=src.replace(old,new)

# Replace continuous stripe-like ridges with overlapping rounded/faceted mountain masses.
old_mountains = '''xs=[-190,-166,-142,-118,-94,-70,-46,-22,2,26,50,74,98,122,146,170,194]
ys=[214,217,220,219,223,221,226,230,228,233,230,227,232,228,223,218,215]
hs=[20,27,34,31,40,35,44,53,47,57,48,43,59,51,42,31,21]
ridge('MountainFront',xs,ys,hs,158,300,[M['mountain'],M['mountain2']])
xs2=[-210,-176,-142,-108,-74,-40,-6,28,62,96,130,164,202]
ys2=[280,283,287,285,290,289,293,291,294,290,287,283,280]
hs2=[17,23,29,26,34,30,38,33,36,31,33,24,17]
ridge('MountainBack',xs2,ys2,hs2,240,370,[M['mountain2']])
# Small snow facets on several tall peaks.
sv=[];sf=[]
for idx in (4,7,9,12):
    x=xs[idx];y=ys[idx]-1;h=hs[idx];b=len(sv)
    sv.extend([(x-6,y,h-7),(x,y-.5,h+.3),(x+6,y,h-6),(x,y-3,h-11)])
    sf.extend([(b,b+1,b+3),(b+1,b+2,b+3)])
mesh_obj('SnowFacets',sv,sf,[M['snow']])'''
new_mountains = '''def mountain_mass(name,cx,cy,rx,ry,h,seed,back=False):
    rr=random.Random(SEED+5000+seed);n=10;v=[];f=[];fm=[]
    rings=[(1.00,-7.0),(.70,h*.28),(.40,h*.58)]
    for ri,(sc,z) in enumerate(rings):
        for j in range(n):
            a=2*math.pi*j/n + rr.uniform(-.04,.04)
            sx=rx*sc*(1+rr.uniform(-.08,.08));sy=ry*sc*(1+rr.uniform(-.08,.08))
            v.append((cx+sx*math.cos(a),cy+sy*math.sin(a),z+rr.uniform(-.7,.7)))
    peak=len(v);v.append((cx+rr.uniform(-3,3),cy+rr.uniform(-2,2),h))
    for ri in range(2):
        a0=ri*n;b0=(ri+1)*n
        for j in range(n):
            k=(j+1)%n
            f.append((a0+j,a0+k,b0+k));fm.append((j+ri+seed)%2)
            f.append((a0+j,b0+k,b0+j));fm.append((j+ri+seed+1)%2)
    top=2*n
    for j in range(n):
        k=(j+1)%n;f.append((top+j,top+k,peak));fm.append((j+seed)%2)
    mats=[M['mountain2'],M['mountain']] if back else [M['mountain'],M['mountain2']]
    mesh_obj(name,v,f,mats,fm)

front_specs=[(-145,205,52,39,31),(-108,205,48,38,39),(-70,211,49,39,36),(-29,214,58,42,47),(18,213,55,42,42),(61,211,58,42,48),(105,207,55,40,43),(144,205,50,38,32)]
for i,s in enumerate(front_specs):mountain_mass('Mountain_%02d'%i,*s,100+i,False)
back_specs=[(-165,247,65,45,27),(-105,251,68,47,30),(-43,254,70,48,33),(25,254,72,49,31),(91,251,70,47,32),(157,246,65,44,27)]
for i,s in enumerate(back_specs):mountain_mass('MountainBack_%02d'%i,*s,200+i,True)
# Pale summit facets integrated into only the tallest peaks.
for i in (1,3,5,6):
    x,y,rx,ry,h=front_specs[i]
    ico('Snow_%02d'%i,(x-1.5,y-2,h*.80),(rx*.19,ry*.17,h*.10),M['snow'],1)'''
if old_mountains not in src: raise RuntimeError('v17 mountain block missing')
src=src.replace(old_mountains,new_mountains)

# Bigger visible pines, especially front-left and side borders.
src=src.replace("depth_scale = 1.62 if y < -4 else (1.34 if y < 65 else 1.03)", "depth_scale = 1.88 if y < -4 else (1.50 if y < 65 else 1.13)")
# Add a reference-like foreground-left crescent of large pines before the forest mesh is emitted.
needle="for x,y,s,v in trees:add_pine(x,y,s,v)"
addition='''for j,(x,y,s) in enumerate([(-88,-30,1.80),(-80,-26,1.72),(-72,-31,1.85),(-65,-25,1.68),(-57,-30,1.72),(-91,-15,1.58),(-83,-13,1.56),(-75,-17,1.55),(-67,-12,1.48),(-58,-15,1.46),(-50,-10,1.40)]):
    trees.append((x,y,s,(len(trees)+j)%3))
for x,y,s,v in trees:add_pine(x,y,s,v)'''
if needle not in src:raise RuntimeError('v17 tree emit block missing')
src=src.replace(needle,addition)

# Church sits a little farther back, as in the supplied screenshot.
src=src.replace('CX,CY=-7.0,82.0','CX,CY=-7.0,91.0')
src=src.replace("[(7,54),(5,61),(1,69),(-3,76),(CX,CY-2.7)]", "[(8,62),(5,69),(1,77),(-3,85),(CX,CY-2.7)]")
src=src.replace("[(-14,79),(-12,81),(-15,83),(-11,85),(-16,86),(-10,77),(-17,80)]", "[(-14,88),(-12,90),(-15,92),(-11,94),(-16,95),(-10,86),(-17,89)]")
src=src.replace("pink=[(43,78),(48,80),(53,78),(46,74),(52,73),(58,75)]", "pink=[(43,90),(48,92),(53,90),(46,86),(52,85),(58,87)]")

# Slightly lower camera makes the foreground trees larger and the church higher in frame.
src=src.replace("bpy.ops.object.camera_add(location=(0,-103,43));cam=bpy.context.object;scene.camera=cam;cam.data.type='PERSP';cam.data.lens=45;look_at(cam,(0,37,4.2))", "bpy.ops.object.camera_add(location=(0,-101,39));cam=bpy.context.object;scene.camera=cam;cam.data.type='PERSP';cam.data.lens=44;look_at(cam,(0,43,4.5))")
src=src.replace("render('preview_main.png',(0,-103,43),(0,37,4.2),45)", "render('preview_main.png',(0,-101,39),(0,43,4.5),44)")
src=src.replace("cam.location=(0,-103,43);cam.data.lens=45;look_at(cam,(0,37,4.2))", "cam.location=(0,-101,39);cam.data.lens=44;look_at(cam,(0,43,4.5))")

ns={'__file__':str(src_path),'__name__':'__main__'}
exec(compile(src,str(src_path),'exec'),ns,ns)
