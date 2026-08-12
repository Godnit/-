from pathlib import Path

src_path = Path(__file__).with_name('build_reference_valley_v2.py')
src = src_path.read_text(encoding='utf-8')

repls = [
("OUT = os.path.join(ROOT, 'output_reference_valley_v2')", "OUT = os.path.join(ROOT, 'output_reference_valley_v5')"),
("scene.render.resolution_x = 1536", "scene.render.resolution_x = 1024"),
("scene.render.resolution_y = 864", "scene.render.resolution_y = 576"),
("scene.view_settings.exposure = 0.35", "scene.view_settings.exposure = 0.0"),
("bg.inputs['Color'].default_value = (0.72, 0.88, 0.90, 1.0)", "bg.inputs['Color'].default_value = (0.61, 0.84, 0.86, 1.0)"),
("bg.inputs['Strength'].default_value = 0.75", "bg.inputs['Strength'].default_value = 0.52"),
("'grass': mat('Grass_Reference', (0.710, 0.753, 0.431), .98)", "'grass': mat('Grass_Reference', (0.59, 0.62, 0.23), .98)"),
("'grass_hill': mat('Grass_Hill', (0.620, 0.700, 0.390), .98)", "'grass_hill': mat('Grass_Hill', (0.50, 0.57, 0.22), .98)"),
("'tree_a': mat('Pine_Mint_A', (0.455, 0.610, 0.520), .98)", "'tree_a': mat('Pine_Mint_A', (0.36, 0.55, 0.44), .98)"),
("'tree_b': mat('Pine_Mint_B', (0.505, 0.655, 0.555), .98)", "'tree_b': mat('Pine_Mint_B', (0.43, 0.62, 0.49), .98)"),
("'tree_c': mat('Pine_Muted_C', (0.385, 0.535, 0.455), .98)", "'tree_c': mat('Pine_Muted_C', (0.30, 0.48, 0.38), .98)"),
("'mountain': mat('Mountain_Pale_Blue', (0.700, 0.815, 0.810), .99)", "'mountain': mat('Mountain_Pale_Blue', (0.67, 0.78, 0.79), .99)"),
("'mountain_shadow': mat('Mountain_Shadow', (0.580, 0.735, 0.740), .99)", "'mountain_shadow': mat('Mountain_Shadow', (0.54, 0.69, 0.72), .99)"),
("'snow': mat('Mountain_Snow', (0.900, 0.925, 0.910), .99)", "'snow': mat('Mountain_Snow', (0.88, 0.91, 0.89), .99)"),
("'path': mat('Path_Pale_Sand', (0.780, 0.735, 0.535), .98)", "'path': mat('Path_Pale_Sand', (0.73, 0.67, 0.43), .98)"),
("ico('Valley_Hill_%02d'%i,(x,y,0.0),1,M['grass_hill'],scale=(sx,sy,sz),sub=2)", "ico('Valley_Hill_%02d'%i,(x,y,-1.0),1,M['grass_hill'],scale=(sx,sy,1.0),sub=2)"),
("for x0,x1,y0,y1,n in [(-82,-43,-35,57,135),(44,82,-34,57,135)]", "for x0,x1,y0,y1,n in [(-67,-31,-34,66,150),(31,67,-34,66,150)]"),
("for _ in range(235):\n    x=rng.uniform(-78,78); y=rng.uniform(32,66)", "for _ in range(260):\n    x=rng.uniform(-72,72); y=rng.uniform(30,72)"),
("for _ in range(70):", "for _ in range(50):"),
("x=rng.uniform(47,82)*side; y=rng.uniform(-39,-15)", "x=rng.uniform(40,68)*side; y=rng.uniform(-34,-11)"),
("for _ in range(38):", "for _ in range(30):"),
("sun.data.energy=2.1", "sun.data.energy=1.30"),
("area=bpy.context.object; area.name='Sky_Fill'; area.data.energy=850; area.data.size=45", "area=bpy.context.object; area.name='Sky_Fill'; area.data.energy=450; area.data.size=58"),
("bpy.ops.object.camera_add(location=(0,-92,48))\ncam=bpy.context.object; cam.name='Camera_Main'; scene.camera=cam\ncam.data.type='PERSP'; cam.data.lens=48\nlook_at(cam,(0,18,3.3))", "bpy.ops.object.camera_add(location=(0,-105,45))\ncam=bpy.context.object; cam.name='Camera_Main'; scene.camera=cam\ncam.data.type='PERSP'; cam.data.lens=47\nlook_at(cam,(0,20,4.0))"),
("render('preview_main.png',(0,-92,48),(0,18,3.3),48)", "render('preview_main.png',(0,-105,45),(0,20,4.0),47)"),
("render('preview_closer.png',(-5,-82,42),(-7,21,3.0),52)", "render('preview_closer.png',(-5,-91,42),(-8,23,3.5),50)"),
("render('preview_left.png',(-54,-74,41),(0,18,3.0),52)", "# preview_left omitted"),
("render('preview_right.png',(54,-74,41),(0,18,3.0),52)", "# preview_right omitted"),
("render('preview_high.png',(0,-78,67),(0,15,1.0),52)", "# preview_high omitted"),
("cam.location=(0,-92,48); cam.data.lens=48; look_at(cam,(0,18,3.3))", "cam.location=(0,-105,45); cam.data.lens=47; look_at(cam,(0,20,4.0))"),
("blend_path=os.path.join(OUT,'reference_valley_v2.blend')", "blend_path=os.path.join(OUT,'reference_valley_v5.blend')"),
("glb_path=os.path.join(OUT,'reference_valley_v2.glb')", "glb_path=os.path.join(OUT,'reference_valley_v5.glb')")]

for old,new in repls:
    if old not in src: raise RuntimeError('Expected source fragment not found: '+old[:120])
    src=src.replace(old,new)

old_mountains="mountain_specs=[\n    (-86,76,30,17,28),(-61,78,32,18,33),(-34,80,31,17,31),(-7,82,29,18,37),\n    (22,81,34,19,34),(51,79,36,19,39),(82,76,32,18,31)\n]\nfor i,(x,y,rx,dy,h) in enumerate(mountain_specs):\n    mountain_mesh('Mountain_%02d'%i,x,y,-0.2,rx,dy,h,100+i)"
new_mountains="mountain_blobs=[(-92,128,34,19,23),(-62,132,36,20,27),(-31,135,34,20,25),(2,137,38,21,30),(36,135,37,21,27),(70,131,38,20,29),(101,127,34,19,23)]\nfor i,(x,y,sx,sy,sz) in enumerate(mountain_blobs):\n    ico('MountainDome_%02d'%i,(x,y,-2.5),1,M['mountain'] if i%2==0 else M['mountain_shadow'],scale=(sx,sy,sz),sub=2)\n    ico('MountainCap_%02d'%i,(x-2.0,y-1.0,sz*0.52),1,M['snow'],scale=(sx*.36,sy*.32,sz*.22),sub=1)"
if old_mountains not in src: raise RuntimeError('Mountain block not found')
src=src.replace(old_mountains,new_mountains)
src=src.replace("s=rng.uniform(.70,.86)","s=rng.uniform(.95,1.10)")
src=src.replace("s=rng.uniform(.63,.78)","s=rng.uniform(.82,.98)")
marker="try:\n    bpy.ops.export_scene.gltf(filepath=glb_path,export_format='GLB',export_apply=True)\nexcept TypeError:\n    bpy.ops.export_scene.gltf(filepath=glb_path,export_format='GLB')\n\nmesh_objs=[o for o in scene.objects if o.type=='MESH']"
if marker not in src: raise RuntimeError('GLB block not found')
src=src.replace(marker,"mesh_objs=[o for o in scene.objects if o.type=='MESH']")
src=src.replace("Reference Valley v2\\n","Reference Valley v5\\n")
ns={'__file__':str(src_path),'__name__':'__main__'}
exec(compile(src,str(src_path),'exec'),ns,ns)
