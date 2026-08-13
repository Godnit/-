from pathlib import Path

v13_path = Path(__file__).with_name('build_classic_reference_v13.py')
wrapper = v13_path.read_text(encoding='utf-8')

wrapper = wrapper.replace('output_classic_reference_v13','output_classic_reference_v14')
wrapper = wrapper.replace('classic_reference_v13.blend','classic_reference_v14.blend')
wrapper = wrapper.replace('classic_reference_v13.glb','classic_reference_v14.glb')
wrapper = wrapper.replace('TABS Classic reference valley v13','TABS Classic reference valley v14')

marker = "ns={'__file__':str(src_path),'__name__':'__main__'}\nexec(compile(src,str(src_path),'exec'),ns,ns)"
if marker not in wrapper:
    raise RuntimeError('v14 v13 execution marker missing')

extra = r'''
# V14: second reference-matching pass, based on direct pixel comparison with the supplied screenshot.
# Restore the bright cyan sky but keep terrain/trees darker and more contrasty.
src = src.replace("bg.inputs['Strength'].default_value = 0.56", "bg.inputs['Strength'].default_value = 0.72")
src = src.replace("'grass':mat('Grass_Reference',(0.665,0.700,0.370),.98)", "'grass':mat('Grass_Reference',(0.56,0.59,0.22),.98)")
src = src.replace("'grass_hill':mat('Grass_Hill',(0.55,0.63,0.34),.98)", "'grass_hill':mat('Grass_Hill',(0.50,0.57,0.25),.98)")
src = src.replace("'rock':mat('Rock_Pale',(0.59,0.63,0.65),.98)", "'rock':mat('Rock_Pale',(0.50,0.56,0.61),.98)")
src = src.replace("'rock2':mat('Rock_Cool',(0.47,0.55,0.59),.98)", "'rock2':mat('Rock_Cool',(0.39,0.49,0.56),.98)")
src = src.replace("'mountain':mat('Mountain_Pale',(0.72,0.81,0.80),.99)", "'mountain':mat('Mountain_Pale',(0.70,0.80,0.80),.99)")
src = src.replace("'mountain_shadow':mat('Mountain_Shadow',(0.49,0.66,0.70),.99)", "'mountain_shadow':mat('Mountain_Shadow',(0.52,0.70,0.74),.99)")
src = src.replace("'snow':mat('Mountain_Snow',(0.86,0.90,0.88),.99)", "'snow':mat('Mountain_Snow',(0.88,0.91,0.89),.99)")
src = src.replace("sun=bpy.context.object;sun.name='Sun';sun.data.energy=1.45", "sun=bpy.context.object;sun.name='Sun';sun.data.energy=2.05")
src = src.replace("area=bpy.context.object;area.name='Sky_Fill';area.data.energy=350;area.data.size=72", "area=bpy.context.object;area.name='Sky_Fill';area.data.energy=180;area.data.size=76")

# Fuller, more TABS-like pines. Foreground trees become substantially larger than distant pines.
src = src.replace("s *= 1.22\n    add_cylinder", "s *= (1.58 if y < 8 else (1.36 if y < 68 else 1.16))\n    add_cylinder")
src = src.replace("add_frustum(x,y,1.35*s,.82*s,.11*s,1.40*s,7,1+(var%3))", "add_frustum(x,y,1.35*s,1.02*s,.12*s,1.40*s,7,1+(var%3))")
src = src.replace("add_frustum(x,y,2.00*s,.67*s,.08*s,1.20*s,7,1+((var+1)%3))", "add_frustum(x,y,2.00*s,.82*s,.09*s,1.20*s,7,1+((var+1)%3))")
src = src.replace("add_frustum(x,y,2.58*s,.45*s,.03*s,1.02*s,7,1+((var+2)%3))", "add_frustum(x,y,2.58*s,.57*s,.03*s,1.02*s,7,1+((var+2)%3))")

# V13 mountains were still too close and wall-like. Move them far back and use very broad rounded low-poly masses.
old_mountains = """mountain_specs=[
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
new_mountains = """mountain_specs=[
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
if old_mountains not in src:
    raise RuntimeError('v14 mountain replacement block missing')
src = src.replace(old_mountains,new_mountains)

# Move the visible blue tent formation upward into frame and pink camp farther into the distant right meadow.
src = src.replace("blue_pos=[(-59,-12),(-48,-10),(-37,-9),(-26,-8),(-58,-21),(-47,-20),(-36,-19),(-25,-18)]",
                  "blue_pos=[(-54,-4),(-43,-3),(-32,-2),(-21,-1),(-56,-14),(-45,-13),(-34,-12),(-23,-11)]")
src = src.replace("pink_pos=[(43,100),(48,102),(53,100),(46,96),(52,95),(58,97)]",
                  "pink_pos=[(42,110),(47,112),(52,110),(45,106),(51,105),(57,107)]")

# Lower the camera and aim a little farther into the valley. This matches the reference's larger foreground trees
# and places the church near the upper third instead of the middle.
old_cam = """bpy.ops.object.camera_add(location=(0,-104,45))
cam=bpy.context.object;cam.name='Camera_Main';scene.camera=cam;cam.data.type='PERSP';cam.data.lens=44
look_at(cam,(0,36,4.0))"""
new_cam = """bpy.ops.object.camera_add(location=(0,-100,38))
cam=bpy.context.object;cam.name='Camera_Main';scene.camera=cam;cam.data.type='PERSP';cam.data.lens=43
look_at(cam,(0,48,4.2))"""
if old_cam not in src:
    raise RuntimeError('v14 camera block missing')
src = src.replace(old_cam,new_cam)
src = src.replace("render('preview_main.png',(0,-104,45),(0,36,4.0),44)", "render('preview_main.png',(0,-100,38),(0,48,4.2),43)")
src = src.replace("render('preview_closer.png',(-3,-94,42),(-4,45,4.0),47)", "render('preview_closer.png',(-3,-91,36),(-4,55,4.2),46)")
src = src.replace("render('preview_left.png',(-48,-82,40),(-2,42,4.0),48)", "render('preview_left.png',(-46,-80,37),(-2,51,4.0),47)")
src = src.replace("render('preview_right.png',(48,-82,40),(1,42,4.0),48)", "render('preview_right.png',(46,-80,37),(1,51,4.0),47)")
src = src.replace("render('preview_high.png',(0,-72,72),(0,42,0.7),48)", "render('preview_high.png',(0,-72,70),(0,50,0.8),48)")
src = src.replace("cam.location=(0,-104,45);cam.data.lens=44;look_at(cam,(0,36,4.0))", "cam.location=(0,-100,38);cam.data.lens=43;look_at(cam,(0,48,4.2))")
'''

wrapper = wrapper.replace(marker, extra + "\n" + marker)

ns={'__file__':str(v13_path),'__name__':'__main__'}
exec(compile(wrapper,str(v13_path),'exec'),ns,ns)
