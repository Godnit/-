from pathlib import Path

src_path = Path(__file__).with_name('build_classic_reference_v16.py')
src = src_path.read_text(encoding='utf-8')

# -----------------------------------------------------------------------------
# V20: one clean correction pass applied directly to the stable self-contained V16 scene.
# No nested wrappers. Priorities: reference palette, large foreground pines, huge empty meadow,
# distant rounded mountains, tiny church, correct tent depth and camera framing.
# -----------------------------------------------------------------------------
repls = [
    ('output_classic_reference_v16','output_classic_reference_v20'),
    ('classic_reference_v16.blend','classic_reference_v20.blend'),
    ('classic_reference_v16.glb','classic_reference_v20.glb'),
    ('TABS Classic reference v16','TABS Classic reference v20'),
    ("print('V16_OK'", "print('V20_OK'"),
    ("bg.inputs['Color'].default_value = (0.67,0.87,0.89,1.0)", "bg.inputs['Color'].default_value = (0.69,0.865,0.865,1.0)"),
    ("bg.inputs['Strength'].default_value = 0.78", "bg.inputs['Strength'].default_value = 0.77"),
    ("'grass': mat('Grass',(0.575,0.610,0.235))", "'grass': mat('Grass',(0.485,0.505,0.140))"),
    ("'grass_hill': mat('GrassHill',(0.50,0.56,0.22))", "'grass_hill': mat('GrassHill',(0.43,0.47,0.15))"),
    ("'tree1': mat('Pine1',(0.30,0.48,0.38))", "'tree1': mat('Pine1',(0.15,0.26,0.20))"),
    ("'tree2': mat('Pine2',(0.37,0.55,0.43))", "'tree2': mat('Pine2',(0.21,0.33,0.25))"),
    ("'tree3': mat('Pine3',(0.43,0.60,0.47))", "'tree3': mat('Pine3',(0.27,0.39,0.29))"),
    ("'mountain': mat('Mountain',(0.70,0.80,0.80))", "'mountain': mat('Mountain',(0.67,0.78,0.78))"),
    ("'mountain2': mat('MountainShadow',(0.54,0.70,0.73))", "'mountain2': mat('MountainShadow',(0.50,0.66,0.69))"),
    ("'snow': mat('Snow',(0.88,0.91,0.89))", "'snow': mat('Snow',(0.86,0.90,0.88))"),
    ("'rock': mat('Rock',(0.49,0.55,0.60))", "'rock': mat('Rock',(0.43,0.49,0.54))"),
    ("'rock2': mat('Rock2',(0.39,0.48,0.54))", "'rock2': mat('Rock2',(0.34,0.42,0.48))"),
    ("'path': mat('Path',(0.68,0.66,0.39))", "'path': mat('Path',(0.56,0.57,0.29))"),
    ("sun=bpy.context.object;sun.data.energy=1.55", "sun=bpy.context.object;sun.data.energy=1.45"),
    ("area=bpy.context.object;area.data.energy=250;area.data.size=70", "area=bpy.context.object;area.data.energy=205;area.data.size=72"),
]
for old,new in repls:
    if old not in src:
        raise RuntimeError('V20 expected source fragment missing: '+old)
    src = src.replace(old,new)

# Flatter middle: preserve broad map dimensions but soften perimeter hill domes.
old_hills = """for i,(x,y,sx,sy,sz) in enumerate([
    (-86,38,26,82,2.2),(86,40,26,82,2.2),
    (-64,116,44,39,3.0),(61,116,48,39,3.0),
    (-3,135,62,23,2.6)
]):
    ico('Hill_%02d'%i,(x,y,-2.25),(sx,sy,sz),M['grass_hill'],2)"""
new_hills = """for i,(x,y,sx,sy,sz) in enumerate([
    (-88,42,25,84,1.65),(88,44,25,84,1.65),
    (-65,121,45,39,2.25),(62,121,49,39,2.20),
    (-3,139,64,22,1.90)
]):
    ico('Hill_%02d'%i,(x,y,-2.55),(sx,sy,sz),M['grass_hill'],2)"""
if old_hills not in src:
    raise RuntimeError('V20 hill block missing')
src = src.replace(old_hills,new_hills)

# Replace V16 ridge with rounded/faceted, overlapping low-poly mountain masses.
old_mountains = """xs=[-190,-166,-142,-118,-94,-70,-46,-22,2,26,50,74,98,122,146,170,194]
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
mesh_obj('SnowFacets',sv,sf,[M['snow']])"""
new_mountains = """def mountain_mass(name,cx,cy,rx,ry,h,seed,back=False):
    rr=random.Random(SEED+5000+seed); n=10; v=[]; f=[]; fm=[]
    rings=[(1.00,-7.0),(.70,h*.27),(.40,h*.57)]
    for ri,(sc,z) in enumerate(rings):
        for j in range(n):
            a=2*math.pi*j/n + rr.uniform(-.04,.04)
            sx=rx*sc*(1+rr.uniform(-.08,.08)); sy=ry*sc*(1+rr.uniform(-.08,.08))
            v.append((cx+sx*math.cos(a),cy+sy*math.sin(a),z+rr.uniform(-.6,.6)))
    peak=len(v); v.append((cx+rr.uniform(-3,3),cy+rr.uniform(-2,2),h))
    for ri in range(2):
        a0=ri*n; b0=(ri+1)*n
        for j in range(n):
            k=(j+1)%n
            f.append((a0+j,a0+k,b0+k)); fm.append((j+ri+seed)%2)
            f.append((a0+j,b0+k,b0+j)); fm.append((j+ri+seed+1)%2)
    top=2*n
    for j in range(n):
        k=(j+1)%n; f.append((top+j,top+k,peak)); fm.append((j+seed)%2)
    mats=[M['mountain2'],M['mountain']] if back else [M['mountain'],M['mountain2']]
    mesh_obj(name,v,f,mats,fm)

front_specs=[(-145,242,56,44,20),(-108,243,52,43,25),(-70,247,53,44,23),(-29,251,62,47,30),(18,250,59,46,27),(61,248,62,46,31),(105,244,59,45,28),(144,242,54,43,21)]
for i,s in enumerate(front_specs): mountain_mass('Mountain_%02d'%i,*s,100+i,False)
back_specs=[(-165,300,70,50,18),(-105,304,72,51,20),(-43,307,74,52,22),(25,307,76,53,21),(91,304,74,51,21),(157,299,70,49,18)]
for i,s in enumerate(back_specs): mountain_mass('MountainBack_%02d'%i,*s,200+i,True)
for i in (1,3,5,6):
    x,y,rx,ry,h=front_specs[i]
    ico('Snow_%02d'%i,(x-1.5,y-2,h*.80),(rx*.18,ry*.16,h*.09),M['snow'],1)"""
if old_mountains not in src:
    raise RuntimeError('V20 mountain block missing')
src = src.replace(old_mountains,new_mountains)

# Pine proportions: wider foliage tiers and strongly larger near-camera trees.
src = src.replace("depth_scale = 1.62 if y < -4 else (1.34 if y < 65 else 1.03)", "depth_scale = 1.92 if y < -4 else (1.53 if y < 65 else 1.15)")
src = src.replace("add_frustum(x,y,1.35*s,1.02*s,.12*s,1.42*s,7,1+(var%3))", "add_frustum(x,y,1.35*s,1.10*s,.12*s,1.42*s,7,1+(var%3))")
src = src.replace("add_frustum(x,y,2.04*s,.83*s,.09*s,1.22*s,7,1+((var+1)%3))", "add_frustum(x,y,2.04*s,.90*s,.09*s,1.22*s,7,1+((var+1)%3))")
src = src.replace("add_frustum(x,y,2.65*s,.58*s,.02*s,1.08*s,7,1+((var+2)%3))", "add_frustum(x,y,2.65*s,.63*s,.02*s,1.08*s,7,1+((var+2)%3))")

# Make perimeter forest denser; keep the middle ellipse empty.
src = src.replace("place_region(-104,-33,-45,112,255,.90,1.48,lambda x,y:not open_meadow(x,y))", "place_region(-104,-31,-45,122,330,.92,1.55,lambda x,y:not open_meadow(x,y))")
src = src.replace("place_region(34,104,-42,112,215,.84,1.38,lambda x,y:not open_meadow(x,y))", "place_region(32,104,-42,122,285,.88,1.48,lambda x,y:not open_meadow(x,y))")
src = src.replace("place_region(-101,101,66,148,360,.66,1.10,back_ok)", "place_region(-103,103,67,154,455,.68,1.16,back_ok)")

# Explicit reference-like large pine crescent at front-left and a smaller right-edge group.
needle = "for x,y,s,v in trees:add_pine(x,y,s,v)"
addition = """for j,(x,y,s) in enumerate([
    (-92,-32,1.90),(-84,-29,1.84),(-76,-33,1.94),(-68,-28,1.82),(-60,-31,1.84),(-52,-27,1.72),
    (-91,-17,1.68),(-83,-14,1.65),(-75,-18,1.68),(-67,-13,1.60),(-59,-16,1.57),(-51,-11,1.50),
    (-72,-3,1.54),(-64,0,1.50),(-56,2,1.45),(-48,5,1.40),(-40,8,1.32),
    (80,-27,1.60),(87,-20,1.54),(93,-11,1.46)
]):
    trees.append((x,y,s,(len(trees)+j)%3))
for x,y,s,v in trees:add_pine(x,y,s,v)"""
if needle not in src:
    raise RuntimeError('V20 tree emission marker missing')
src = src.replace(needle,addition)

# Tiny landmark deeper into the map, while keeping the same logical design.
src = src.replace("CX,CY=-7.0,82.0", "CX,CY=-7.0,92.0")
src = src.replace("[(7,54),(5,61),(1,69),(-3,76),(CX,CY-2.7)]", "[(8,63),(5,70),(1,78),(-3,86),(CX,CY-2.7)]")
src = src.replace("[(-14,79),(-12,81),(-15,83),(-11,85),(-16,86),(-10,77),(-17,80)]", "[(-14,89),(-12,91),(-15,93),(-11,95),(-16,96),(-10,87),(-17,90)]")

# Colored camps in the same apparent depth as target.
src = src.replace("blue=[(-58,-9),(-47,-7),(-36,-6),(-25,-5),(-59,-18),(-48,-17),(-37,-16),(-26,-15)]", "blue=[(-58,4),(-47,6),(-36,7),(-25,8),(-59,-6),(-48,-5),(-37,-4),(-26,-3)]")
src = src.replace("pink=[(43,78),(48,80),(53,78),(46,74),(52,73),(58,75)]", "pink=[(43,91),(48,93),(53,91),(46,87),(52,86),(58,88)]")

# Camera: lower and aimed farther forward. Large front trees enter frame; church stays in upper third.
old_cam = "bpy.ops.object.camera_add(location=(0,-103,43));cam=bpy.context.object;scene.camera=cam;cam.data.type='PERSP';cam.data.lens=45;look_at(cam,(0,37,4.2))"
new_cam = "bpy.ops.object.camera_add(location=(0,-102,40));cam=bpy.context.object;scene.camera=cam;cam.data.type='PERSP';cam.data.lens=44;look_at(cam,(0,45,4.5))"
if old_cam not in src:
    raise RuntimeError('V20 camera setup missing')
src = src.replace(old_cam,new_cam)
src = src.replace("render('preview_main.png',(0,-103,43),(0,37,4.2),45)", "render('preview_main.png',(0,-102,40),(0,45,4.5),44)")
src = src.replace("render('preview_closer.png',(-3,-93,40),(-4,44,4.0),48)", "render('preview_closer.png',(-3,-94,39),(-4,51,4.2),47)")
src = src.replace("render('preview_left.png',(-49,-83,40),(0,39,4.0),49)", "render('preview_left.png',(-49,-84,39),(0,46,4.0),48)")
src = src.replace("render('preview_right.png',(49,-83,40),(0,39,4.0),49)", "render('preview_right.png',(49,-84,39),(0,46,4.0),48)")
src = src.replace("render('preview_high.png',(0,-76,72),(0,40,.8),50)", "render('preview_high.png',(0,-76,70),(0,47,.8),49)")
src = src.replace("cam.location=(0,-103,43);cam.data.lens=45;look_at(cam,(0,37,4.2))", "cam.location=(0,-102,40);cam.data.lens=44;look_at(cam,(0,45,4.5))")

ns={'__file__':str(src_path),'__name__':'__main__'}
exec(compile(src,str(src_path),'exec'),ns,ns)
