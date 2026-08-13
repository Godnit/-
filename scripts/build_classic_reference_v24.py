from pathlib import Path

src_path = Path(__file__).with_name('build_classic_reference_v16.py')
src = src_path.read_text(encoding='utf-8')

# -----------------------------------------------------------------------------
# V24 deliverables: clean MAP ONLY. No church, graves, tents or path.
# Start from the last self-contained builder (V16), not the nested V17-V23 wrappers.
# -----------------------------------------------------------------------------
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
    ("'snow': mat('Snow',(0.88,0.91,0.89))", "'snow': mat('Snow',(0.825,0.875,0.865))"),
    ("sun=bpy.context.object;sun.data.energy=1.55", "sun=bpy.context.object;sun.data.energy=1.30"),
    ("area=bpy.context.object;area.data.energy=250;area.data.size=70", "area=bpy.context.object;area.data.energy=180;area.data.size=76"),
]
for old,new in repls:
    if old not in src:
        raise RuntimeError('V24 expected fragment missing: '+old[:100])
    src = src.replace(old,new)

# -----------------------------------------------------------------------------
# Nearly-flat valley. Delete the artificial perimeter blobs that read as a green wall.
# -----------------------------------------------------------------------------
hill_start = src.index("# Only soft perimeter rises; center remains flat and spacious.")
hill_end = src.index("# -----------------------------------------------------------------------------\n# Broad, continuous faceted mountain ranges far behind the forest", hill_start)
src = src[:hill_start] + "# V24: flat continuous meadow; no artificial green ridge.\n\n" + src[hill_end:]

# -----------------------------------------------------------------------------
# Mountains: broad low overlapping masses, far behind the forest.
# No giant triangular wall and no snow caps. Their bases are buried below the meadow.
# -----------------------------------------------------------------------------
mount_start = src.index("# -----------------------------------------------------------------------------\n# Broad, continuous faceted mountain ranges far behind the forest")
mount_end = src.index("# -----------------------------------------------------------------------------\n# Packed low-poly forest mesh", mount_start)
new_mountains = r'''# -----------------------------------------------------------------------------
# Broad TABS-like mountain enclosure: overlapping low-poly masses, never a wall.
# -----------------------------------------------------------------------------
mountain_specs = [
    (-168,246,62,38,20,0), (-126,250,64,39,25,1),
    (-82,254,69,41,23,0),  (-34,258,73,43,30,1),
    (18,258,72,43,27,0),   (68,255,71,42,31,1),
    (116,251,66,40,25,0),  (160,247,61,37,21,1),
]
for i,(x,y,sx,sy,sz,var) in enumerate(mountain_specs):
    mm = M['mountain'] if var == 0 else M['mountain2']
    # Main rounded/faceted body.
    ico('Mountain_%02d'%i,(x,y,sz*.28-5.8),(sx,sy,sz),mm,2)
    # Wide shoulder blends the foot into the neighboring mountain and prevents cone silhouettes.
    shx = x + (-1 if i%2==0 else 1)*sx*.32
    ico('MountainShoulder_%02d'%i,(shx,y-5.0,sz*.12-5.7),(sx*.64,sy*.82,sz*.58),M['mountain'],2)

# Lower, paler back layer visible through the gaps only.
for i,(x,y,sx,sy,sz) in enumerate([
    (-180,296,78,42,17),(-112,301,82,44,20),(-38,304,86,45,22),
    (42,304,86,45,21),(118,301,82,44,20),(182,296,76,41,17)
]):
    ico('MountainBack_%02d'%i,(x,y,sz*.20-6.4),(sx,sy,sz),M['mountain2'],2)

'''
src = src[:mount_start] + new_mountains + src[mount_end:]

# -----------------------------------------------------------------------------
# Trees: deterministic 993-tree ring matching the supplied composition.
# Fixed seed + fixed region counts means positions, colors and sizes do not change on rebuild.
# -----------------------------------------------------------------------------
# V16 depth scale is too mild in the foreground and too large in the far belt.
src = src.replace(
    "depth_scale = 1.62 if y < -4 else (1.34 if y < 65 else 1.03)",
    "depth_scale = 1.82 if y < -6 else (1.38 if y < 64 else 0.98)"
)

forest_start = src.index("# Left forest is denser/larger in the reference, especially lower-left.")
forest_emit = src.index("for x,y,s,v in trees:add_pine(x,y,s,v)", forest_start)
forest_after_emit = forest_emit + len("for x,y,s,v in trees:add_pine(x,y,s,v)")
new_forest_distribution = r'''# V24 exact rebuild count: 993 pines. The broad middle stays empty.
# The region boundaries reproduce the visible left crescent, back belt and narrower right wall.
def left_shape(x,y):
    inner = -50.0 + 0.11*max(-10.0,y)
    return x < inner and not open_meadow(x,y)
def right_shape(x,y):
    inner = 53.0 - 0.065*max(-8.0,y)
    return x > inner and not open_meadow(x,y)
def back_shape(x,y):
    # preserve a shallow central recess in the far tree line from the supplied reference
    if abs(x) < 27 and y < 100 and rng.random() < .74: return False
    return not open_meadow(x,y)

place_region(-105,-31,-44,118,300,.84,1.34,left_shape)
place_region(34,105,-40,118,245,.80,1.26,right_shape)
place_region(-103,103,72,154,330,.62,1.02,back_shape)
# Large cropped foreground framing, much heavier on the left than on the right.
place_region(-106,-54,-48,5,90,1.18,1.72,lambda x,y: True)
place_region(79,106,-38,4,28,1.10,1.55,lambda x,y: True)

assert len(trees) == 993, 'V24 pine count changed: %d' % len(trees)
for x,y,s,v in trees:add_pine(x,y,s,v)'''
src = src[:forest_start] + new_forest_distribution + src[forest_after_emit:]

# Keep the one small broad-leaf tree only if it is part of the map silhouette; make it subdued.
src = src.replace("(-45,-3,3.15),(1.55,1.35,1.25)", "(-45,-3,2.95),(1.30,1.15,1.05)")
src = src.replace("(-46,-2.8,3.05),(.9,.85,.82)", "(-46,-2.8,2.88),(.72,.68,.66)")

# -----------------------------------------------------------------------------
# MAP ONLY: remove church, graves, road/path and both colored tent camps.
# -----------------------------------------------------------------------------
landmark_start = src.index("# -----------------------------------------------------------------------------\n# Tiny church / graveyard")
lighting_start = src.index("# -----------------------------------------------------------------------------\n# Lighting and cameras", landmark_start)
src = src[:landmark_start] + "# V24 MAP ONLY: buildings/camps/path intentionally removed.\n\n" + src[lighting_start:]

# Camera: a little higher/wider so the valley floor and tree ring match the supplied map framing.
src = src.replace(
    "bpy.ops.object.camera_add(location=(0,-103,43));cam=bpy.context.object;scene.camera=cam;cam.data.type='PERSP';cam.data.lens=45;look_at(cam,(0,37,4.2))",
    "bpy.ops.object.camera_add(location=(0,-108,47));cam=bpy.context.object;scene.camera=cam;cam.data.type='PERSP';cam.data.lens=47;look_at(cam,(0,44,3.8))"
)
src = src.replace("render('preview_main.png',(0,-103,43),(0,37,4.2),45)", "render('preview_main.png',(0,-108,47),(0,44,3.8),47)")
src = src.replace("render('preview_closer.png',(-3,-93,40),(-4,44,4.0),48)", "render('preview_closer.png',(-3,-98,44),(-4,47,3.7),49)")
src = src.replace("render('preview_left.png',(-49,-83,40),(0,39,4.0),49)", "render('preview_left.png',(-50,-88,44),(0,44,3.8),50)")
src = src.replace("render('preview_right.png',(49,-83,40),(0,39,4.0),49)", "render('preview_right.png',(50,-88,44),(0,44,3.8),50)")
src = src.replace("render('preview_high.png',(0,-76,72),(0,40,.8),50)", "render('preview_high.png',(0,-80,76),(0,45,.5),50)")
src = src.replace("cam.location=(0,-103,43);cam.data.lens=45;look_at(cam,(0,37,4.2))", "cam.location=(0,-108,47);cam.data.lens=47;look_at(cam,(0,44,3.8))")

# Strengthen report so Actions proves this is the map-only pass.
src = src.replace("f.write('Pine count: %d\\n'%len(trees))", "f.write('Pine count: %d\\n'%len(trees)); f.write('Map only: church/graves/tents/path removed\\n'); f.write('Mountain style: broad overlapping TABS-like masses\\n')")

ns={'__file__':str(src_path),'__name__':'__main__'}
exec(compile(src,str(src_path),'exec'),ns,ns)
