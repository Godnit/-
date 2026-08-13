from pathlib import Path

src_path = Path(__file__).with_name('build_classic_reference_v10.py')
src = src_path.read_text(encoding='utf-8')

repls = [
    ("output_classic_reference_v10", "output_classic_reference_v13"),
    ("classic_reference_v10.blend", "classic_reference_v13.blend"),
    ("classic_reference_v10.glb", "classic_reference_v13.glb"),
    ("TABS Classic reference valley v10", "TABS Classic reference valley v13"),
    ("scene.view_settings.exposure = 0.10", "scene.view_settings.exposure = -0.02"),
    ("bg.inputs['Strength'].default_value = 0.72", "bg.inputs['Strength'].default_value = 0.56"),
    ("'grass':mat('Grass_Reference',(0.715,0.752,0.425),.98)", "'grass':mat('Grass_Reference',(0.665,0.700,0.370),.98)"),
    ("'grass_hill':mat('Grass_Hill',(0.62,0.70,0.39),.98)", "'grass_hill':mat('Grass_Hill',(0.55,0.63,0.34),.98)"),
    ("'tree_a':mat('Pine_Mint_A',(0.40,0.58,0.47),.98)", "'tree_a':mat('Pine_Mint_A',(0.34,0.52,0.42),.98)"),
    ("'tree_b':mat('Pine_Mint_B',(0.50,0.66,0.53),.98)", "'tree_b':mat('Pine_Mint_B',(0.43,0.59,0.47),.98)"),
    ("'tree_c':mat('Pine_Deep_Aqua',(0.31,0.50,0.41),.98)", "'tree_c':mat('Pine_Deep_Aqua',(0.26,0.44,0.36),.98)"),
    ("'mountain':mat('Mountain_Pale',(0.79,0.84,0.82),.99)", "'mountain':mat('Mountain_Pale',(0.72,0.81,0.80),.99)"),
    ("'mountain_shadow':mat('Mountain_Shadow',(0.56,0.72,0.76),.99)", "'mountain_shadow':mat('Mountain_Shadow',(0.49,0.66,0.70),.99)"),
    ("'snow':mat('Mountain_Snow',(0.92,0.94,0.91),.99)", "'snow':mat('Mountain_Snow',(0.86,0.90,0.88),.99)"),
    ("'path':mat('Path_Pale_Sand',(0.80,0.76,0.55),.98)", "'path':mat('Path_Pale_Sand',(0.72,0.69,0.49),.98)"),
    ("sun=bpy.context.object;sun.name='Sun';sun.data.energy=2.0", "sun=bpy.context.object;sun.name='Sun';sun.data.energy=1.45"),
    ("area=bpy.context.object;area.name='Sky_Fill';area.data.energy=500;area.data.size=65", "area=bpy.context.object;area.name='Sky_Fill';area.data.energy=350;area.data.size=72"),
]
for old,new in repls:
    if old not in src:
        raise RuntimeError('v13 expected fragment missing: '+old[:120])
    src = src.replace(old,new)

# Flatter meadow. Reference center is broad and calm; hills mainly live under perimeter forest.
old_hills = """for i,(x,y,sx,sy,sz) in enumerate([
    (-73,31,34,75,3.6),(73,33,34,75,3.6),
    (-52,93,44,40,5.5),(45,94,51,42,5.2),
    (-14,110,50,30,6.0),(65,102,36,33,5.0)
]):
    ico('Valley_Hill_%02d'%i,(x,y,-1.5),(sx,sy,sz),M['grass_hill'],2)"""
new_hills = """for i,(x,y,sx,sy,sz) in enumerate([
    (-76,38,35,72,2.0),(76,40,35,72,2.0),
    (-55,103,45,38,2.9),(47,105,52,39,2.8),
    (-12,121,54,28,3.1),(66,111,37,31,2.6)
]):
    ico('Valley_Hill_%02d'%i,(x,y,-2.25),(sx,sy,sz),M['grass_hill'],2)"""
if old_hills not in src: raise RuntimeError('v13 hill block missing')
src = src.replace(old_hills,new_hills)

# Replace repeated small mountain bumps with a few broad overlapping rounded masses like the supplied image.
old_mountains = """mountain_specs=[
    (-127,160,44,24,31),(-99,164,42,25,39),(-70,166,38,24,31),(-44,166,43,25,36),
    (-12,168,44,27,44),(22,167,42,26,38),(52,166,44,27,42),(86,165,46,26,46),(121,160,43,24,34)
]
for i,(x,y,sx,sy,sz) in enumerate(mountain_specs):
    mm=M['mountain'] if i%3!=1 else M['mountain_shadow']
    ico('Mountain_%02d'%i,(x,y,sz*.42-4.0),(sx,sy,sz),mm,2)
    # irregular pale summit volume, intentionally broad rather than a sharp cone
    ico('Mountain_Snow_%02d'%i,(x-2.0,y-1.5,sz*.78),(sx*.42,sy*.38,sz*.25),M['snow'],1)

# second distant layer to create the pale valley enclosure seen at far left/right
for i,(x,y,sx,sy,sz) in enumerate([(-150,183,60,35,32),(-88,188,60,36,29),(83,188,62,36,31),(148,181,60,34,30)]):
    ico('Mountain_Back_%02d'%i,(x,y,sz*.34-6),(sx,sy,sz),M['mountain_shadow'],2)"""
new_mountains = """mountain_specs=[
    (-128,193,64,37,35),(-82,202,68,40,39),(-28,207,74,43,48),
    (31,207,70,42,42),(84,204,78,44,53),(137,195,67,38,41)
]
for i,(x,y,sx,sy,sz) in enumerate(mountain_specs):
    mm=M['mountain'] if i%2==0 else M['mountain_shadow']
    ico('Mountain_%02d'%i,(x,y,sz*.34-7.5),(sx,sy,sz),mm,2)
    # broad shoulder volumes remove the repeated pointed rhythm and create the reference's big mountain masses
    shoulder_x=x-sx*.28 if i%2==0 else x+sx*.27
    ico('Mountain_Shoulder_%02d'%i,(shoulder_x,y-4,sz*.20-6.5),(sx*.62,sy*.82,sz*.68),M['mountain'],2)
    if i in (2,4):
        ico('Mountain_Snow_%02d'%i,(x-2.0,y-3.0,sz*.68),(sx*.27,sy*.22,sz*.15),M['snow'],1)
for i,(x,y,sx,sy,sz) in enumerate([(-155,226,78,44,29),(-88,232,76,45,27),(84,232,80,45,28),(154,224,77,43,29)]):
    ico('Mountain_Back_%02d'%i,(x,y,sz*.26-8.0),(sx,sy,sz),M['mountain_shadow'],2)"""
if old_mountains not in src: raise RuntimeError('v13 mountain block missing')
src = src.replace(old_mountains,new_mountains)

# Larger pines and a denser visible perimeter, while preserving the huge empty middle.
src = src.replace(
    "def add_pine(x,y,s,var):\n    add_cylinder",
    "def add_pine(x,y,s,var):\n    s *= 1.22\n    add_cylinder"
)
src = src.replace("return ((x-4.0)/54.0)**2 + ((y-10.0)/41.0)**2 < 1.0",
                  "return ((x-3.0)/55.0)**2 + ((y-13.0)/46.0)**2 < 1.0")
src = src.replace("place_region(-94,-32,-43,86,150,.86,1.45,left_accept)",
                  "place_region(-94,-30,-43,103,215,1.02,1.76,left_accept)")
src = src.replace("place_region(38,94,-38,88,132,.82,1.42,right_accept)",
                  "place_region(36,94,-39,104,190,.98,1.68,right_accept)")
old_back = """def back_accept(x,y):
    if ((x+6)/17.0)**2+((y-57)/10.0)**2 < 1.0:return False
    if abs(x)<27 and y<58 and rng.random()<.55:return False
    return True
place_region(-84,84,47,116,205,.66,1.22,back_accept)"""
new_back = """def back_accept(x,y):
    if ((x+5)/22.0)**2+((y-96)/14.0)**2 < 1.0:return False
    if abs(x)<38 and y<91 and rng.random()<.88:return False
    return True
place_region(-86,86,55,148,330,.78,1.42,back_accept)"""
if old_back not in src: raise RuntimeError('v13 back forest block missing')
src = src.replace(old_back,new_back)
src = src.replace("place_region(-92,-48,-48,-18,46,1.00,1.58,lambda x,y: True)",
                  "place_region(-94,-45,-48,-8,82,1.55,2.25,lambda x,y: True)")
src = src.replace("place_region(76,96,-35,-8,13,1.00,1.52,lambda x,y: True)",
                  "place_region(72,96,-35,7,34,1.35,2.05,lambda x,y: True)")
src = src.replace("for _ in range(24):", "for _ in range(20):")
src = src.replace("rng.uniform(.76,1.08)", "rng.uniform(.95,1.34)")

# Rocks in the screenshot are easy to read, especially front-left; enlarge them slightly.
src = src.replace("s=rng2.uniform(.42,.82)", "s=rng2.uniform(.56,1.02)")

# Push the church and pink camp to the distant upper meadow; shorten/fade the path.
src = src.replace("CX,CY=-5.0,57.0", "CX,CY=-5.0,96.0")
src = src.replace("ribbon('Church_Path',[(4,19),(1,27),(-2,34),(0,41),(-3,49),(CX,CY-3.2)],1.25,.06,M['path'])",
                  "ribbon('Church_Path',[(8,64),(6,73),(2,82),(-1,90),(CX,CY-3.2)],.70,.06,M['path'])")
src = src.replace("ribbon('Church_Path_Side',[(CX,CY-2.7),(CX+6,CY-1.0),(CX+9,CY+1.5)],.72,.065,M['path'])",
                  "ribbon('Church_Path_Side',[(CX,CY-2.7),(CX+5,CY-1.0),(CX+8,CY+1.2)],.50,.065,M['path'])")
src = src.replace("[(-12,53),(-10,55),(-13,57),(-11,59),(-15,55),(-16,58),(-9,51),(-14,51)]",
                  "[(-12,92),(-10,94),(-13,96),(-11,98),(-15,94),(-16,97),(-9,90),(-14,90)]")
src = src.replace("blue_pos=[(-57,-26),(-45,-25),(-33,-23),(-21,-21),(-61,-34),(-49,-35),(-37,-36),(-25,-34)]",
                  "blue_pos=[(-59,-12),(-48,-10),(-37,-9),(-26,-8),(-58,-21),(-47,-20),(-36,-19),(-25,-18)]")
src = src.replace("pink_pos=[(43,52),(48,54),(53,52),(46,48),(52,47),(58,49)]",
                  "pink_pos=[(43,100),(48,102),(53,100),(46,96),(52,95),(58,97)]")
src = src.replace("M['blue'],.92", "M['blue'],1.12")
src = src.replace("M['pink'],.76", "M['pink'],.88")

# Camera: wider and slightly more downward so the church sits near the upper third and foreground trees become large.
old_cam = """bpy.ops.object.camera_add(location=(0,-112,47))
cam=bpy.context.object;cam.name='Camera_Main';scene.camera=cam;cam.data.type='PERSP';cam.data.lens=48
look_at(cam,(0,37,4.5))"""
new_cam = """bpy.ops.object.camera_add(location=(0,-104,45))
cam=bpy.context.object;cam.name='Camera_Main';scene.camera=cam;cam.data.type='PERSP';cam.data.lens=44
look_at(cam,(0,36,4.0))"""
if old_cam not in src: raise RuntimeError('v13 camera setup missing')
src=src.replace(old_cam,new_cam)
src=src.replace("render('preview_main.png',(0,-112,47),(0,37,4.5),48)",
                "render('preview_main.png',(0,-104,45),(0,36,4.0),44)")
src=src.replace("render('preview_closer.png',(-3,-96,43),(-4,44,4.0),50)",
                "render('preview_closer.png',(-3,-94,42),(-4,45,4.0),47)")
src=src.replace("render('preview_left.png',(-50,-86,42),(-2,39,4.0),52)",
                "render('preview_left.png',(-48,-82,40),(-2,42,4.0),48)")
src=src.replace("render('preview_right.png',(50,-86,42),(1,39,4.0),52)",
                "render('preview_right.png',(48,-82,40),(1,42,4.0),48)")
src=src.replace("render('preview_high.png',(0,-75,75),(0,32,0.5),52)",
                "render('preview_high.png',(0,-72,72),(0,42,0.7),48)")
src=src.replace("cam.location=(0,-112,47);cam.data.lens=48;look_at(cam,(0,37,4.5))",
                "cam.location=(0,-104,45);cam.data.lens=44;look_at(cam,(0,36,4.0))")

ns={'__file__':str(src_path),'__name__':'__main__'}
exec(compile(src,str(src_path),'exec'),ns,ns)
