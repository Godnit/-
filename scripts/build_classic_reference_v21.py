from pathlib import Path

v20_path = Path(__file__).with_name('build_classic_reference_v20.py')
wrapper = v20_path.read_text(encoding='utf-8')

# Promote deliverable names.
wrapper = wrapper.replace('output_classic_reference_v20','output_classic_reference_v21')
wrapper = wrapper.replace('classic_reference_v20.blend','classic_reference_v21.blend')
wrapper = wrapper.replace('classic_reference_v20.glb','classic_reference_v21.glb')
wrapper = wrapper.replace('TABS Classic reference v20','TABS Classic reference v21')
wrapper = wrapper.replace("print('V20_OK'", "print('V21_OK'")

# Fine palette corrections based on direct pixel comparison with the supplied screenshot.
wrapper = wrapper.replace("bg.inputs['Color'].default_value = (0.69,0.865,0.865,1.0)", "bg.inputs['Color'].default_value = (0.66,0.885,0.885,1.0)")
wrapper = wrapper.replace("'grass': mat('Grass',(0.485,0.505,0.140))", "'grass': mat('Grass',(0.485,0.480,0.140))")
wrapper = wrapper.replace("'grass_hill': mat('GrassHill',(0.43,0.47,0.15))", "'grass_hill': mat('GrassHill',(0.42,0.445,0.15))")
wrapper = wrapper.replace("'tree1': mat('Pine1',(0.15,0.26,0.20))", "'tree1': mat('Pine1',(0.105,0.215,0.205))")
wrapper = wrapper.replace("'tree2': mat('Pine2',(0.21,0.33,0.25))", "'tree2': mat('Pine2',(0.155,0.285,0.255))")
wrapper = wrapper.replace("'tree3': mat('Pine3',(0.27,0.39,0.29))", "'tree3': mat('Pine3',(0.205,0.345,0.305))")
wrapper = wrapper.replace("'mountain': mat('Mountain',(0.67,0.78,0.78))", "'mountain': mat('Mountain',(0.62,0.70,0.69))")
wrapper = wrapper.replace("'mountain2': mat('MountainShadow',(0.50,0.66,0.69))", "'mountain2': mat('MountainShadow',(0.47,0.60,0.62))")
wrapper = wrapper.replace("'snow': mat('Snow',(0.86,0.90,0.88))", "'snow': mat('Snow',(0.84,0.88,0.86))")

# Stronger reference perspective: mid-field border trees also read large, not only the extreme foreground.
wrapper = wrapper.replace("depth_scale = 1.92 if y < -4 else (1.53 if y < 65 else 1.15)", "depth_scale = 2.00 if y < -4 else (1.66 if y < 65 else 1.22)")

marker = "ns={'__file__':str(src_path),'__name__':'__main__'}\nexec(compile(src,str(src_path),'exec'),ns,ns)"
if marker not in wrapper:
    raise RuntimeError('V21 V20 execution marker missing')

extra = r'''
# -----------------------------------------------------------------------------
# V21 geometry/composition corrections after all V20 replacements have been applied.
# -----------------------------------------------------------------------------
# Critical fix: V20's far edge was still visible as a horizontal horizon. Extend terrain well under/behind mountains.
old_ground = "box('ValleyGround',(0,48,-0.7),(218,252,1.4),M['grass'],0)"
new_ground = "box('ValleyGround',(0,130,-0.7),(218,430,1.4),M['grass'],0)"
if old_ground not in src:
    raise RuntimeError('V21 ground line missing')
src = src.replace(old_ground,new_ground)

# Open a broad central rear valley instead of a uniform horizontal wall of pines.
old_back = """def back_ok(x,y):
    if ((x+5)/21)**2+((y-84)/13)**2<1:return False
    if abs(x)<38 and y<93 and rng.random()<.90:return False
    return True"""
new_back = """def back_ok(x,y):
    if ((x+7)/28.0)**2+((y-94)/18.0)**2<1:return False
    if abs(x)<50 and y<118 and rng.random()<.94:return False
    if abs(x)<28 and y<140 and rng.random()<.72:return False
    return True"""
if old_back not in src:
    raise RuntimeError('V21 back forest function missing')
src = src.replace(old_back,new_back)

# Pull mountain masses a little farther back now that the ground continues beneath them.
src = src.replace(
"front_specs=[(-145,242,56,44,20),(-108,243,52,43,25),(-70,247,53,44,23),(-29,251,62,47,30),(18,250,59,46,27),(61,248,62,46,31),(105,244,59,45,28),(144,242,54,43,21)]",
"front_specs=[(-145,258,58,46,21),(-108,259,54,45,26),(-70,263,55,46,24),(-29,267,64,49,31),(18,266,61,48,28),(61,264,64,48,32),(105,260,61,47,29),(144,258,56,45,22)]"
)
src = src.replace(
"back_specs=[(-165,300,70,50,18),(-105,304,72,51,20),(-43,307,74,52,22),(25,307,76,53,21),(91,304,74,51,21),(157,299,70,49,18)]",
"back_specs=[(-165,326,72,52,18),(-105,330,74,53,20),(-43,333,76,54,22),(25,333,78,55,21),(91,330,76,53,21),(157,325,72,51,18)]"
)

# Enlarge/reposition the lone broadleaf tree visible on the left meadow edge and keep it readable.
src = src.replace("location=(-45,-3,1.2)", "location=(-43,7,1.35)")
src = src.replace("ico('RoundTree',(-45,-3,3.15),(1.55,1.35,1.25),M['tree2'],1)", "ico('RoundTree',(-43,7,3.45),(1.85,1.62,1.42),M['tree2'],1)")
src = src.replace("ico('RoundTree2',(-46,-2.8,3.05),(.9,.85,.82),M['tree3'],1)", "ico('RoundTree2',(-44.1,7.2,3.35),(1.08,1.0,.92),M['tree3'],1)")

# Rocks in the supplied screenshot are larger and more readable in the front-left quadrant.
src = src.replace("s=rng.uniform(.55,1.05)", "s=rng.uniform(.68,1.22)")

# Camera framing: slightly higher camera with a farther aim gives the target large meadow while lifting the church.
src = src.replace("bpy.ops.object.camera_add(location=(0,-102,40));cam=bpy.context.object;scene.camera=cam;cam.data.type='PERSP';cam.data.lens=44;look_at(cam,(0,45,4.5))",
                  "bpy.ops.object.camera_add(location=(0,-104,43));cam=bpy.context.object;scene.camera=cam;cam.data.type='PERSP';cam.data.lens=44;look_at(cam,(0,53,4.7))")
src = src.replace("render('preview_main.png',(0,-102,40),(0,45,4.5),44)", "render('preview_main.png',(0,-104,43),(0,53,4.7),44)")
src = src.replace("render('preview_closer.png',(-3,-94,39),(-4,51,4.2),47)", "render('preview_closer.png',(-3,-96,41),(-4,58,4.4),47)")
src = src.replace("cam.location=(0,-102,40);cam.data.lens=44;look_at(cam,(0,45,4.5))", "cam.location=(0,-104,43);cam.data.lens=44;look_at(cam,(0,53,4.7))")
'''

wrapper = wrapper.replace(marker, extra + "\n" + marker)

ns={'__file__':str(v20_path),'__name__':'__main__'}
exec(compile(wrapper,str(v20_path),'exec'),ns,ns)
