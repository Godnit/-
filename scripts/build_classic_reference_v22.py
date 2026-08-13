from pathlib import Path

v20_path = Path(__file__).with_name('build_classic_reference_v20.py')
wrapper = v20_path.read_text(encoding='utf-8')

wrapper = wrapper.replace('output_classic_reference_v20','output_classic_reference_v22')
wrapper = wrapper.replace('classic_reference_v20.blend','classic_reference_v22.blend')
wrapper = wrapper.replace('classic_reference_v20.glb','classic_reference_v22.glb')
wrapper = wrapper.replace('TABS Classic reference v20','TABS Classic reference v22')
wrapper = wrapper.replace("print('V20_OK'", "print('V22_OK'")

# Palette: directly matched to the supplied screenshot regions.
wrapper = wrapper.replace("bg.inputs['Color'].default_value = (0.69,0.865,0.865,1.0)", "bg.inputs['Color'].default_value = (0.66,0.885,0.885,1.0)")
wrapper = wrapper.replace("'grass': mat('Grass',(0.485,0.505,0.140))", "'grass': mat('Grass',(0.485,0.480,0.140))")
wrapper = wrapper.replace("'grass_hill': mat('GrassHill',(0.43,0.47,0.15))", "'grass_hill': mat('GrassHill',(0.42,0.445,0.15))")
wrapper = wrapper.replace("'tree1': mat('Pine1',(0.15,0.26,0.20))", "'tree1': mat('Pine1',(0.105,0.215,0.225))")
wrapper = wrapper.replace("'tree2': mat('Pine2',(0.21,0.33,0.25))", "'tree2': mat('Pine2',(0.155,0.285,0.275))")
wrapper = wrapper.replace("'tree3': mat('Pine3',(0.27,0.39,0.29))", "'tree3': mat('Pine3',(0.205,0.345,0.325))")
wrapper = wrapper.replace("'mountain': mat('Mountain',(0.67,0.78,0.78))", "'mountain': mat('Mountain',(0.61,0.69,0.68))")
wrapper = wrapper.replace("'mountain2': mat('MountainShadow',(0.50,0.66,0.69))", "'mountain2': mat('MountainShadow',(0.46,0.59,0.61))")
wrapper = wrapper.replace("'snow': mat('Snow',(0.86,0.90,0.88))", "'snow': mat('Snow',(0.83,0.87,0.85))")
wrapper = wrapper.replace("depth_scale = 1.92 if y < -4 else (1.53 if y < 65 else 1.15)", "depth_scale = 2.00 if y < -4 else (1.66 if y < 65 else 1.22)")

marker = "ns={'__file__':str(src_path),'__name__':'__main__'}\nexec(compile(src,str(src_path),'exec'),ns,ns)"
if marker not in wrapper:
    raise RuntimeError('V22 V20 execution marker missing')

extra = r'''
# Extend terrain far behind the mountains: no artificial horizontal platform edge.
src = src.replace("box('ValleyGround',(0,48,-0.7),(218,252,1.4),M['grass'],0)",
                  "box('ValleyGround',(0,135,-0.7),(218,450,1.4),M['grass'],0)")

# Remove the broad central green ridge that did not exist in the reference; retain only gentle side rises.
old_hills = """for i,(x,y,sx,sy,sz) in enumerate([
    (-88,42,25,84,1.65),(88,44,25,84,1.65),
    (-65,121,45,39,2.25),(62,121,49,39,2.20),
    (-3,139,64,22,1.90)
]):
    ico('Hill_%02d'%i,(x,y,-2.55),(sx,sy,sz),M['grass_hill'],2)"""
new_hills = """for i,(x,y,sx,sy,sz) in enumerate([
    (-91,48,20,88,1.35),(91,50,20,88,1.35),
    (-82,142,31,43,1.45),(82,142,31,43,1.45)
]):
    ico('Hill_%02d'%i,(x,y,-2.72),(sx,sy,sz),M['grass_hill'],2)"""
if old_hills not in src: raise RuntimeError('V22 runtime hills missing')
src = src.replace(old_hills,new_hills)

# Rear valley clearing: forest rises up the left/right slopes rather than becoming one straight belt.
old_back = """def back_ok(x,y):
    if ((x+5)/21)**2+((y-84)/13)**2<1:return False
    if abs(x)<38 and y<93 and rng.random()<.90:return False
    return True"""
new_back = """def back_ok(x,y):
    if ((x+7)/29.0)**2+((y-95)/19.0)**2<1:return False
    if abs(x)<52 and y<121 and rng.random()<.95:return False
    if abs(x)<30 and y<145 and rng.random()<.78:return False
    return True"""
if old_back not in src: raise RuntimeError('V22 back forest function missing')
src = src.replace(old_back,new_back)

# Mountain masses stay large, but sit farther away and lower in frame with an open cyan sky band.
src = src.replace(
"front_specs=[(-145,242,56,44,20),(-108,243,52,43,25),(-70,247,53,44,23),(-29,251,62,47,30),(18,250,59,46,27),(61,248,62,46,31),(105,244,59,45,28),(144,242,54,43,21)]",
"front_specs=[(-145,276,62,49,22),(-108,277,58,48,27),(-70,281,59,49,25),(-29,285,69,53,33),(18,284,66,52,30),(61,282,69,52,34),(105,278,66,51,31),(144,276,60,48,23)]"
)
src = src.replace(
"back_specs=[(-165,300,70,50,18),(-105,304,72,51,20),(-43,307,74,52,22),(25,307,76,53,21),(91,304,74,51,21),(157,299,70,49,18)]",
"back_specs=[(-165,342,77,56,19),(-105,346,79,57,21),(-43,349,81,58,23),(25,349,83,59,22),(91,346,81,57,22),(157,341,77,55,19)]"
)

# Explicit large foreground-left crescent and right edge pines, matching the target's scale hierarchy.
needle = "for x,y,s,v in trees:add_pine(x,y,s,v)"
addition = """for j,(x,y,s) in enumerate([
    (-94,-34,1.98),(-86,-31,1.92),(-78,-35,2.02),(-70,-30,1.90),(-62,-33,1.91),(-54,-29,1.80),
    (-93,-18,1.76),(-85,-15,1.72),(-77,-19,1.76),(-69,-14,1.67),(-61,-17,1.64),(-53,-12,1.57),
    (-74,-4,1.62),(-66,-1,1.57),(-58,1,1.51),(-50,4,1.46),(-42,7,1.38),(-34,10,1.32),
    (80,-28,1.66),(87,-21,1.60),(94,-12,1.51)
]):
    trees.append((x,y,s,(len(trees)+j)%3))
for x,y,s,v in trees:add_pine(x,y,s,v)"""
if needle not in src: raise RuntimeError('V22 tree emission missing')
src = src.replace(needle,addition)

# Make the lone left-side deciduous tree visible between conifers.
src = src.replace("location=(-45,-3,1.2)", "location=(-42,8,1.35)")
src = src.replace("ico('RoundTree',(-45,-3,3.15),(1.55,1.35,1.25),M['tree2'],1)", "ico('RoundTree',(-42,8,3.45),(1.85,1.62,1.42),M['tree2'],1)")
src = src.replace("ico('RoundTree2',(-46,-2.8,3.05),(.9,.85,.82),M['tree3'],1)", "ico('RoundTree2',(-43.1,8.2,3.35),(1.08,1.0,.92),M['tree3'],1)")

# Larger readable foreground rocks.
src = src.replace("s=rng.uniform(.55,1.05)", "s=rng.uniform(.70,1.25)")

# Keep church small but lift it toward the same upper-third region by looking farther into the valley.
src = src.replace("CX,CY=-7.0,92.0", "CX,CY=-7.0,94.0") if "CX,CY=-7.0,92.0" in src else src
src = src.replace("bpy.ops.object.camera_add(location=(0,-102,40));cam=bpy.context.object;scene.camera=cam;cam.data.type='PERSP';cam.data.lens=44;look_at(cam,(0,45,4.5))",
                  "bpy.ops.object.camera_add(location=(0,-104,43));cam=bpy.context.object;scene.camera=cam;cam.data.type='PERSP';cam.data.lens=44;look_at(cam,(0,55,4.8))")
src = src.replace("render('preview_main.png',(0,-102,40),(0,45,4.5),44)", "render('preview_main.png',(0,-104,43),(0,55,4.8),44)")
src = src.replace("render('preview_closer.png',(-3,-94,39),(-4,51,4.2),47)", "render('preview_closer.png',(-3,-96,41),(-4,60,4.4),47)")
src = src.replace("cam.location=(0,-102,40);cam.data.lens=44;look_at(cam,(0,45,4.5))", "cam.location=(0,-104,43);cam.data.lens=44;look_at(cam,(0,55,4.8))")
'''

wrapper = wrapper.replace(marker, extra + "\n" + marker)

ns={'__file__':str(v20_path),'__name__':'__main__'}
exec(compile(wrapper,str(v20_path),'exec'),ns,ns)
