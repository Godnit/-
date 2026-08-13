from pathlib import Path

src_path = Path(__file__).with_name('build_classic_reference_v16.py')
src = src_path.read_text(encoding='utf-8')

# V24 map-only final pass, based on the last self-contained builder.
repls = [
    ('output_classic_reference_v16','output_classic_reference_v24'),
    ('classic_reference_v16.blend','classic_reference_v24.blend'),
    ('classic_reference_v16.glb','classic_reference_v24.glb'),
    ('TABS Classic reference v16','TABS Classic reference v24'),
    ("print('V16_OK'", "print('V24_OK'"),
    ("scene.view_settings.exposure = -0.08", "scene.view_settings.exposure = -0.10"),
    ("bg.inputs['Color'].default_value = (0.67,0.87,0.89,1.0)", "bg.inputs['Color'].default_value = (0.69,0.86,0.86,1.0)"),
    ("bg.inputs['Strength'].default_value = 0.78", "bg.inputs['Strength'].default_value = 0.68"),
    ("'grass': mat('Grass',(0.575,0.610,0.235))", "'grass': mat('Grass',(0.545,0.585,0.205))"),
    ("'grass_hill': mat('GrassHill',(0.50,0.56,0.22))", "'grass_hill': mat('GrassHill',(0.485,0.535,0.195))"),
    ("'tree1': mat('Pine1',(0.30,0.48,0.38))", "'tree1': mat('Pine1',(0.205,0.350,0.285))"),
    ("'tree2': mat('Pine2',(0.37,0.55,0.43))", "'tree2': mat('Pine2',(0.275,0.425,0.335))"),
    ("'tree3': mat('Pine3',(0.43,0.60,0.47))", "'tree3': mat('Pine3',(0.345,0.495,0.385))"),
    ("'mountain': mat('Mountain',(0.70,0.80,0.80))", "'mountain': mat('Mountain',(0.625,0.755,0.765))"),
    ("'mountain2': mat('MountainShadow',(0.54,0.70,0.73))", "'mountain2': mat('MountainShadow',(0.505,0.665,0.690))"),
    ("sun=bpy.context.object;sun.data.energy=1.55", "sun=bpy.context.object;sun.data.energy=1.30"),
    ("area=bpy.context.object;area.data.energy=250;area.data.size=70", "area=bpy.context.object;area.data.energy=180;area.data.size=76"),
]
for old,new in repls:
    if old not in src: raise RuntimeError('V24 expected fragment missing: '+old[:100])
    src=src.replace(old,new)

# Flat continuous meadow: remove the artificial perimeter rise objects.
hill_start=src.index("# Only soft perimeter rises; center remains flat and spacious.")
hill_end=src.index("# -----------------------------------------------------------------------------\n# Broad, continuous faceted mountain ranges far behind the forest",hill_start)
src=src[:hill_start]+"# V24 flat continuous meadow.\n\n"+src[hill_end:]

# Connected low-poly mountain terrain. This rises from ground gradually; no wall/base cut.
mount_start=src.index("# -----------------------------------------------------------------------------\n# Broad, continuous faceted mountain ranges far behind the forest")
mount_end=src.index("# -----------------------------------------------------------------------------\n# Packed low-poly forest mesh",mount_start)
new_mountains=r'''# -----------------------------------------------------------------------------
# Connected low-poly mountain terrain, shaped as broad valleys rather than sharp teeth.
# -----------------------------------------------------------------------------
def mountain_heightfield(name,xmin,xmax,ymin,ymax,nx,ny,peaks,mats,seed):
    rr=random.Random(SEED+seed);v=[];f=[];fm=[]
    for j in range(ny+1):
        ty=j/ny;y=ymin+(ymax-ymin)*ty
        front=min(1.0,max(0.0,(ty-.02)/.30))
        back=1.0 if ty<.78 else max(.38,1.0-(ty-.78)/.22*.62)
        for i in range(nx+1):
            tx=i/nx;x=xmin+(xmax-xmin)*tx;h=0.0
            for cx,cy,ph,sx,sy in peaks:
                dx=(x-cx)/sx;dy=(y-cy)/sy
                hh=ph*math.exp(-.5*(dx*dx+dy*dy))
                if hh>h:h=hh
            wob=(rr.random()-.5)*.42*(.25+.75*front)
            z=-.58+h*front*back+wob
            if j==0:z=-.62
            v.append((x,y,z))
    row=nx+1
    for j in range(ny):
        for i in range(nx):
            a=j*row+i;b=a+1;c=a+row+1;d=a+row
            if (i+j)%2:f.extend([(a,b,d),(b,c,d)])
            else:f.extend([(a,b,c),(a,c,d)])
            fm.extend([(i+j)%len(mats),(i+j+1)%len(mats)])
    mesh_obj(name,v,f,mats,fm)

front_peaks=[
(-180,245,14,62,58),(-142,247,19,64,60),(-100,251,17,60,59),
(-56,256,22,67,63),(-10,260,27,72,66),(38,258,23,67,64),
(84,253,24,65,61),(130,249,19,63,59),(176,245,14,61,57)]
mountain_heightfield('MountainRangeFront',-230,230,148,352,24,11,front_peaks,[M['mountain'],M['mountain2']],6100)
back_peaks=[(-190,340,12,80,73),(-116,344,16,84,75),(-38,347,18,88,78),(48,346,17,86,76),(128,342,15,82,73),(192,338,11,76,70)]
mountain_heightfield('MountainRangeBack',-240,240,255,442,22,9,back_peaks,[M['mountain2'],M['mountain']],6200)

'''
src=src[:mount_start]+new_mountains+src[mount_end:]

# Reference-style tree sizes: large cropped foreground, medium side walls, smaller far belt.
src=src.replace("depth_scale = 1.62 if y < -4 else (1.34 if y < 65 else 1.03)","depth_scale = 1.82 if y < -6 else (1.38 if y < 64 else 0.98)")
forest_start=src.index("# Left forest is denser/larger in the reference, especially lower-left.")
forest_emit=src.index("for x,y,s,v in trees:add_pine(x,y,s,v)",forest_start)
forest_after=forest_emit+len("for x,y,s,v in trees:add_pine(x,y,s,v)")
new_forest=r'''# Fixed deterministic 993-pine ring. Same coordinates/colors/scales on every rebuild.
def left_shape(x,y):
    inner=-50.0+.11*max(-10.0,y)
    return x<inner and not open_meadow(x,y)
def right_shape(x,y):
    inner=53.0-.065*max(-8.0,y)
    return x>inner and not open_meadow(x,y)
def back_shape(x,y):
    if abs(x)<27 and y<100 and rng.random()<.74:return False
    return not open_meadow(x,y)
place_region(-105,-31,-44,118,300,.84,1.34,left_shape)
place_region(34,105,-40,118,245,.80,1.26,right_shape)
place_region(-103,103,72,154,330,.62,1.02,back_shape)
place_region(-106,-54,-48,5,90,1.18,1.72,lambda x,y:True)
place_region(79,106,-38,4,28,1.10,1.55,lambda x,y:True)
assert len(trees)==993,'V24 pine count changed: %d'%len(trees)
for x,y,s,v in trees:add_pine(x,y,s,v)'''
src=src[:forest_start]+new_forest+src[forest_after:]

# Subdue the lone broad-leaf tree without changing its reference location.
src=src.replace("(-45,-3,3.15),(1.55,1.35,1.25)","(-45,-3,2.95),(1.30,1.15,1.05)")
src=src.replace("(-46,-2.8,3.05),(.9,.85,.82)","(-46,-2.8,2.88),(.72,.68,.66)")

# MAP ONLY: remove church, graves, path, blue tents and pink tents completely.
landmark_start=src.index("# -----------------------------------------------------------------------------\n# Tiny church / graveyard")
lighting_start=src.index("# -----------------------------------------------------------------------------\n# Lighting and cameras",landmark_start)
src=src[:landmark_start]+"# V24 MAP ONLY: no church, graves, tents or path.\n\n"+src[lighting_start:]

# Camera framing close to supplied map composition.
src=src.replace("bpy.ops.object.camera_add(location=(0,-103,43));cam=bpy.context.object;scene.camera=cam;cam.data.type='PERSP';cam.data.lens=45;look_at(cam,(0,37,4.2))","bpy.ops.object.camera_add(location=(0,-108,47));cam=bpy.context.object;scene.camera=cam;cam.data.type='PERSP';cam.data.lens=47;look_at(cam,(0,44,3.8))")
src=src.replace("render('preview_main.png',(0,-103,43),(0,37,4.2),45)","render('preview_main.png',(0,-108,47),(0,44,3.8),47)")
src=src.replace("render('preview_closer.png',(-3,-93,40),(-4,44,4.0),48)","render('preview_closer.png',(-3,-98,44),(-4,47,3.7),49)")
src=src.replace("render('preview_left.png',(-49,-83,40),(0,39,4.0),49)","render('preview_left.png',(-50,-88,44),(0,44,3.8),50)")
src=src.replace("render('preview_right.png',(49,-83,40),(0,39,4.0),49)","render('preview_right.png',(50,-88,44),(0,44,3.8),50)")
src=src.replace("render('preview_high.png',(0,-76,72),(0,40,.8),50)","render('preview_high.png',(0,-80,76),(0,45,.5),50)")
src=src.replace("cam.location=(0,-103,43);cam.data.lens=45;look_at(cam,(0,37,4.2))","cam.location=(0,-108,47);cam.data.lens=47;look_at(cam,(0,44,3.8))")

src=src.replace("f.write('Pine count: %d\\n'%len(trees))","f.write('Pine count: %d\\n'%len(trees));f.write('Map only: church/graves/tents/path removed\\n');f.write('Mountain style: connected low-poly terrain range\\n')")

ns={'__file__':str(src_path),'__name__':'__main__'}
exec(compile(src,str(src_path),'exec'),ns,ns)
