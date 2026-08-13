from pathlib import Path

src_path=Path(__file__).with_name('build_classic_reference_v16.py')
src=src_path.read_text(encoding='utf-8')

# Keep V18 deliverable names.
src=src.replace('output_classic_reference_v16','output_classic_reference_v18')
src=src.replace('classic_reference_v16.blend','classic_reference_v18.blend')
src=src.replace('classic_reference_v16.glb','classic_reference_v18.glb')
src=src.replace('TABS Classic reference v16','TABS map-only reference V18')
src=src.replace("print('V16_OK'", "print('V18_MAP_ONLY_OK'")

# Reference palette: brighter meadow, soft cyan sky, darker varied pines.
repls=[
("bg.inputs['Color'].default_value = (0.67,0.87,0.89,1.0)","bg.inputs['Color'].default_value = (0.59,0.84,0.86,1.0)"),
("bg.inputs['Strength'].default_value = 0.78","bg.inputs['Strength'].default_value = 0.72"),
("'grass': mat('Grass',(0.575,0.610,0.235))","'grass': mat('Grass',(0.55,0.63,0.20))"),
("'grass_hill': mat('GrassHill',(0.50,0.56,0.22))","'grass_hill': mat('GrassHill',(0.47,0.57,0.19))"),
("'tree1': mat('Pine1',(0.30,0.48,0.38))","'tree1': mat('Pine1',(0.19,0.34,0.25))"),
("'tree2': mat('Pine2',(0.37,0.55,0.43))","'tree2': mat('Pine2',(0.28,0.45,0.31))"),
("'tree3': mat('Pine3',(0.43,0.60,0.47))","'tree3': mat('Pine3',(0.39,0.54,0.34))"),
("'mountain': mat('Mountain',(0.70,0.80,0.80))","'mountain': mat('Mountain',(0.72,0.81,0.81))"),
("'mountain2': mat('MountainShadow',(0.54,0.70,0.73))","'mountain2': mat('MountainShadow',(0.57,0.71,0.74))"),
("'snow': mat('Snow',(0.88,0.91,0.89))","'snow': mat('Snow',(0.90,0.92,0.90))"),
("sun=bpy.context.object;sun.data.energy=1.55","sun=bpy.context.object;sun.data.energy=1.45"),
("area=bpy.context.object;area.data.energy=250;area.data.size=70","area=bpy.context.object;area.data.energy=210;area.data.size=85"),
]
for old,new in repls:
    if old not in src: raise RuntimeError('V18 missing expected fragment: '+old)
    src=src.replace(old,new)

# Replace the repeated pointed mountain wall with wide irregular faceted massifs.
start=src.index('# -----------------------------------------------------------------------------\n# Broad, continuous faceted mountain ranges far behind the forest')
end=src.index('# -----------------------------------------------------------------------------\n# Packed low-poly forest mesh',start)
mountains=r'''# -----------------------------------------------------------------------------
# Wide reference-like mountain wall: broad irregular masses, no repeated cones.
# -----------------------------------------------------------------------------
def mountain_range(name,xs,front_y,mid_y,back_y,front_h,peak_h,back_h,mats,seed):
    rr=random.Random(seed);v=[];f=[];fm=[];n=len(xs)
    for x,h in zip(xs,front_h):v.append((x,front_y+rr.uniform(-2,2),h))
    for x,h in zip(xs,[p*.55 for p in peak_h]):v.append((x,mid_y-13+rr.uniform(-3,3),h))
    for x,h in zip(xs,peak_h):v.append((x,mid_y+rr.uniform(-3,3),h))
    for x,h in zip(xs,back_h):v.append((x,back_y+rr.uniform(-2,2),h))
    for r in range(3):
        a=r*n;b=(r+1)*n
        for i in range(n-1):
            if (i+r)%2:
                f.extend([(a+i,a+i+1,b+i+1),(a+i,b+i+1,b+i)])
            else:
                f.extend([(a+i,a+i+1,b+i),(a+i+1,b+i+1,b+i)])
            fm.extend([(i+r)%len(mats),(i+r+1)%len(mats)])
    return mesh_obj(name,v,f,mats,fm)

xs=[-205,-185,-162,-138,-115,-92,-68,-44,-20,4,28,53,79,105,132,158,182,205]
peaks=[18,28,35,32,27,36,42,34,49,44,60,48,39,55,43,31,35,19]
mountain_range('Mountain_Main',xs,188,233,303,[-5,-4,-3,-3,-2,-2,-1,-1,0,0,-1,-1,-2,-2,-3,-3,-4,-5],peaks,[-7,-6,-6,-5,-5,-5,-4,-4,-4,-4,-4,-4,-5,-5,-6,-6,-7,-7],[M['mountain2'],M['mountain']],SEED+10)
xs2=[-220,-190,-160,-130,-100,-70,-40,-10,20,50,80,110,140,170,200,225]
peaks2=[13,20,24,22,28,25,31,27,33,27,30,24,28,21,18,12]
mountain_range('Mountain_Back',xs2,259,298,365,[-8]*len(xs2),peaks2,[-10]*len(xs2),[M['mountain'],M['mountain2']],SEED+20)
for i in (2,6,8,10,13,16):
    x=xs[i];h=peaks[i]
    ico('Snow_%02d'%i,(x,231,h*.88),(14 if i in (8,10,13) else 10,7,h*.12),M['snow'],1)

'''
src=src[:start]+mountains+src[end:]

# Reference forest: large close left crescent, slightly lighter right side, dense rear belt.
src=src.replace("depth_scale = 1.62 if y < -4 else (1.34 if y < 65 else 1.03)","depth_scale = 1.78 if y < -4 else (1.46 if y < 65 else 1.02)")
src=src.replace("place_region(-104,-33,-45,112,255,.90,1.48,lambda x,y:not open_meadow(x,y))","place_region(-107,-31,-48,124,285,.90,1.50,lambda x,y:not open_meadow(x,y))")
src=src.replace("place_region(34,104,-42,112,215,.84,1.38,lambda x,y:not open_meadow(x,y))","place_region(36,107,-45,124,245,.84,1.40,lambda x,y:not open_meadow(x,y))")
src=src.replace("place_region(-101,101,66,148,360,.66,1.10,back_ok)","place_region(-104,104,75,158,315,.64,1.06,back_ok)")
src=src.replace("place_region(-105,-49,-47,-8,80,1.18,1.85,lambda x,y:True)","place_region(-108,-48,-50,-5,95,1.22,1.92,lambda x,y:True)")
src=src.replace("place_region(75,105,-39,8,34,1.05,1.62,lambda x,y:True)","place_region(78,108,-42,10,42,1.10,1.70,lambda x,y:True)")

# Add fixed boundary trees then force a deterministic total count so later edits cannot change density.
needle='for x,y,s,v in trees:add_pine(x,y,s,v)'
extra=r'''for x,y,s in [
 (-55,18,1.08),(-58,30,1.03),(-51,42,1.00),(-61,53,.96),(-48,64,.91),
 (57,27,1.00),(61,39,.96),(56,51,.92),(64,62,.88),(53,72,.85),
 (-45,-12,1.30),(-52,-7,1.40),(-69,-9,1.46),(-79,-17,1.58),(-90,-20,1.66),
 (91,-14,1.42),(100,-10,1.50),(85,-3,1.37)]:
    trees.append((x,y,s,len(trees)%3))
TARGET_TREES=941
if len(trees)>TARGET_TREES: trees=trees[:TARGET_TREES]
while len(trees)<TARGET_TREES:
    side=-1 if len(trees)%2==0 else 1
    x=rng.uniform(57,101)*side;y=rng.uniform(108,153)
    trees.append((x,y,rng.uniform(.65,.95),len(trees)%3))
for x,y,s,v in trees:add_pine(x,y,s,v)'''
if needle not in src:raise RuntimeError('V18 tree emission marker missing')
src=src.replace(needle,extra)

# Remove ALL man-made elements: church, graves, paths, blue/pink camps/tents.
start=src.index('# -----------------------------------------------------------------------------\n# Tiny church / graveyard')
end=src.index('# -----------------------------------------------------------------------------\n# Lighting and cameras',start)
src=src[:start]+"# -----------------------------------------------------------------------------\n# MAP ONLY: church, graves, paths and tents intentionally removed.\n\n"+src[end:]

# Camera closer to original wide elevated TABS view.
src=src.replace("bpy.ops.object.camera_add(location=(0,-103,43));cam=bpy.context.object;scene.camera=cam;cam.data.type='PERSP';cam.data.lens=45;look_at(cam,(0,37,4.2))","bpy.ops.object.camera_add(location=(0,-126,55));cam=bpy.context.object;scene.camera=cam;cam.data.type='PERSP';cam.data.lens=43;look_at(cam,(0,55,5.0))")
src=src.replace("render('preview_main.png',(0,-103,43),(0,37,4.2),45)","render('preview_main.png',(0,-126,55),(0,55,5.0),43)")
src=src.replace("render('preview_closer.png',(-3,-93,40),(-4,44,4.0),48)","render('preview_closer.png',(0,-112,49),(0,60,5.0),45)")
src=src.replace("render('preview_left.png',(-49,-83,40),(0,39,4.0),49)","render('preview_left.png',(-52,-106,49),(-4,60,5.0),47)")
src=src.replace("render('preview_right.png',(49,-83,40),(0,39,4.0),49)","render('preview_right.png',(52,-106,49),(4,60,5.0),47)")
src=src.replace("render('preview_high.png',(0,-76,72),(0,40,.8),50)","render('preview_high.png',(0,-92,84),(0,63,1.0),48)")
src=src.replace("cam.location=(0,-103,43);cam.data.lens=45;look_at(cam,(0,37,4.2))","cam.location=(0,-126,55);cam.data.lens=43;look_at(cam,(0,55,5.0))")

# Report explicitly confirms map-only and fixed tree count.
src=src.replace("f.write('Pine count: %d\\n'%len(trees))","f.write('Man-made objects: 0\\n')\n    f.write('Pine count: %d\\n'%len(trees))")

ns={'__file__':str(src_path),'__name__':'__main__'}
exec(compile(src,str(src_path),'exec'),ns,ns)
