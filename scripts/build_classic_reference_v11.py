from pathlib import Path

src_path = Path(__file__).with_name('build_classic_reference_v10.py')
src = src_path.read_text(encoding='utf-8')

repls = [
    ("output_classic_reference_v10", "output_classic_reference_v11"),
    ("classic_reference_v10.blend", "classic_reference_v11.blend"),
    ("classic_reference_v10.glb", "classic_reference_v11.glb"),
    ("TABS Classic reference valley v10", "TABS Classic reference valley v11"),
    ("bg.inputs['Strength'].default_value = 0.72", "bg.inputs['Strength'].default_value = 0.55"),
    ("'grass':mat('Grass_Reference',(0.715,0.752,0.425),.98)", "'grass':mat('Grass_Reference',(0.56,0.58,0.18),.98)"),
    ("'grass_hill':mat('Grass_Hill',(0.62,0.70,0.39),.98)", "'grass_hill':mat('Grass_Hill',(0.50,0.56,0.20),.98)"),
    ("'tree_a':mat('Pine_Mint_A',(0.40,0.58,0.47),.98)", "'tree_a':mat('Pine_Mint_A',(0.34,0.53,0.43),.98)"),
    ("'tree_b':mat('Pine_Mint_B',(0.50,0.66,0.53),.98)", "'tree_b':mat('Pine_Mint_B',(0.43,0.61,0.48),.98)"),
    ("'tree_c':mat('Pine_Deep_Aqua',(0.31,0.50,0.41),.98)", "'tree_c':mat('Pine_Deep_Aqua',(0.27,0.45,0.36),.98)"),
    ("'path':mat('Path_Pale_Sand',(0.80,0.76,0.55),.98)", "'path':mat('Path_Pale_Sand',(0.72,0.67,0.45),.98)"),
    ("CX,CY=-5.0,57.0", "CX,CY=-5.0,82.0"),
    ("place_region(-94,-32,-43,86,150,.86,1.45,left_accept)", "place_region(-94,-30,-40,105,180,.92,1.52,left_accept)"),
    ("place_region(38,94,-38,88,132,.82,1.42,right_accept)", "place_region(35,94,-35,108,155,.90,1.48,right_accept)"),
    ("place_region(-84,84,47,116,205,.66,1.22,back_accept)", "place_region(-86,86,56,150,330,.74,1.32,back_accept)"),
    ("place_region(-92,-48,-48,-18,46,1.00,1.58,lambda x,y: True)", "place_region(-88,-45,-34,-4,58,1.30,1.95,lambda x,y: True)"),
    ("place_region(76,96,-35,-8,13,1.00,1.52,lambda x,y: True)", "place_region(74,94,-24,8,18,1.18,1.76,lambda x,y: True)"),
    ("pink_pos=[(43,52),(48,54),(53,52),(46,48),(52,47),(58,49)]", "pink_pos=[(43,73),(48,75),(53,73),(46,69),(52,68),(58,70)]"),
    ("sun=bpy.context.object;sun.name='Sun';sun.data.energy=2.0", "sun=bpy.context.object;sun.name='Sun';sun.data.energy=1.30"),
    ("area=bpy.context.object;area.name='Sky_Fill';area.data.energy=500;area.data.size=65", "area=bpy.context.object;area.name='Sky_Fill';area.data.energy=330;area.data.size=70"),
    ("bpy.ops.object.camera_add(location=(0,-112,47))", "bpy.ops.object.camera_add(location=(0,-116,49))"),
    ("cam=bpy.context.object;cam.name='Camera_Main';scene.camera=cam;cam.data.type='PERSP';cam.data.lens=48", "cam=bpy.context.object;cam.name='Camera_Main';scene.camera=cam;cam.data.type='PERSP';cam.data.lens=50"),
    ("look_at(cam,(0,37,4.5))", "look_at(cam,(0,47,4.8))"),
    ("render('preview_main.png',(0,-112,47),(0,37,4.5),48)", "render('preview_main.png',(0,-116,49),(0,47,4.8),50)"),
    ("render('preview_closer.png',(-3,-96,43),(-4,44,4.0),50)", "render('preview_closer.png',(-3,-101,44),(-4,57,4.2),52)"),
    ("render('preview_left.png',(-50,-86,42),(-2,39,4.0),52)", "render('preview_left.png',(-52,-91,44),(-2,52,4.2),53)"),
    ("render('preview_right.png',(50,-86,42),(1,39,4.0),52)", "render('preview_right.png',(52,-91,44),(1,52,4.2),53)"),
    ("render('preview_high.png',(0,-75,75),(0,32,0.5),52)", "render('preview_high.png',(0,-80,78),(0,45,0.7),53)"),
]
for old,new in repls:
    if old not in src:
        raise RuntimeError('v11 expected fragment missing: '+old[:120])
    src = src.replace(old,new)

# The global look_at replacement above already changes the target on the saved-camera line.
final_cam_old="cam.location=(0,-112,47);cam.data.lens=48;look_at(cam,(0,47,4.8))"
final_cam_new="cam.location=(0,-116,49);cam.data.lens=50;look_at(cam,(0,47,4.8))"
if final_cam_old not in src:
    raise RuntimeError('v11 final camera marker missing')
src = src.replace(final_cam_old,final_cam_new)

# Make all pines visibly larger in the near/mid field, matching the supplied screenshot scale.
needle = "def add_pine(x,y,s,var):\n    add_cylinder"
if needle not in src:
    raise RuntimeError('v11 pine function marker missing')
src = src.replace(needle, "def add_pine(x,y,s,var):\n    s *= 1.16\n    add_cylinder")

# Replace the first mountain row with a farther, lower, more overlapping rounded ridge.
old_mountains = "mountain_specs=[\n    (-127,160,44,24,31),(-99,164,42,25,39),(-70,166,38,24,31),(-44,166,43,25,36),\n    (-12,168,44,27,44),(22,167,42,26,38),(52,166,44,27,42),(86,165,46,26,46),(121,160,43,24,34)\n]"
new_mountains = "mountain_specs=[\n    (-138,210,55,34,27),(-105,212,53,34,34),(-72,214,50,33,30),(-39,214,54,34,35),\n    (-5,216,56,35,40),(30,215,54,34,35),(64,214,56,35,38),(99,212,58,34,40),(137,208,55,33,31)\n]"
if old_mountains not in src:
    raise RuntimeError('v11 mountain list missing')
src = src.replace(old_mountains,new_mountains)
src = src.replace("(x,y,sz*.42-4.0)", "(x,y,sz*.38-7.0)")
src = src.replace("(x-2.0,y-1.5,sz*.78)", "(x-2.0,y-1.5,sz*.69)")
src = src.replace("(sx*.42,sy*.38,sz*.25)", "(sx*.38,sy*.34,sz*.20)")
# Push the second mountain layer even farther back and lower.
src = src.replace("[(-150,183,60,35,32),(-88,188,60,36,29),(83,188,62,36,31),(148,181,60,34,30)]", "[(-158,240,70,42,27),(-90,244,72,43,25),(88,244,74,43,26),(158,238,70,41,26)]")

# Make the path thinner/subtler like the reference.
src = src.replace("1.25,.06,M['path']", ".90,.06,M['path']")
src = src.replace(".72,.065,M['path']", ".58,.065,M['path']")

# Move the church clearing and graveyard with the church so the distant cluster stays coherent.
src = src.replace("((x+6)/17.0)**2+((y-57)/10.0)**2", "((x+6)/17.0)**2+((y-82)/10.0)**2")
src = src.replace("abs(x)<27 and y<58", "abs(x)<27 and y<84")
src = src.replace("[(-12,53),(-10,55),(-13,57),(-11,59),(-15,55),(-16,58),(-9,51),(-14,51)]", "[(-12,78),(-10,80),(-13,82),(-11,84),(-15,80),(-16,83),(-9,76),(-14,76)]")

ns={'__file__':str(src_path),'__name__':'__main__'}
exec(compile(src,str(src_path),'exec'),ns,ns)
