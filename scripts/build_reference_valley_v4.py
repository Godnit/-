from pathlib import Path

src_path = Path(__file__).with_name('build_reference_valley_v2.py')
src = src_path.read_text(encoding='utf-8')

repls = [
    ("OUT = os.path.join(ROOT, 'output_reference_valley_v2')", "OUT = os.path.join(ROOT, 'output_reference_valley_v4')"),
    ("scene.render.resolution_x = 1536", "scene.render.resolution_x = 1280"),
    ("scene.render.resolution_y = 864", "scene.render.resolution_y = 720"),
    ("scene.view_settings.exposure = 0.35", "scene.view_settings.exposure = -0.18"),
    ("bg.inputs['Color'].default_value = (0.72, 0.88, 0.90, 1.0)", "bg.inputs['Color'].default_value = (0.62, 0.84, 0.86, 1.0)"),
    ("bg.inputs['Strength'].default_value = 0.75", "bg.inputs['Strength'].default_value = 0.50"),
    ("'grass': mat('Grass_Reference', (0.710, 0.753, 0.431), .98)", "'grass': mat('Grass_Reference', (0.56, 0.64, 0.29), .98)"),
    ("'grass_hill': mat('Grass_Hill', (0.620, 0.700, 0.390), .98)", "'grass_hill': mat('Grass_Hill', (0.50, 0.60, 0.27), .98)"),
    ("'tree_a': mat('Pine_Mint_A', (0.455, 0.610, 0.520), .98)", "'tree_a': mat('Pine_Mint_A', (0.38, 0.56, 0.43), .98)"),
    ("'tree_b': mat('Pine_Mint_B', (0.505, 0.655, 0.555), .98)", "'tree_b': mat('Pine_Mint_B', (0.43, 0.61, 0.47), .98)"),
    ("'tree_c': mat('Pine_Muted_C', (0.385, 0.535, 0.455), .98)", "'tree_c': mat('Pine_Muted_C', (0.32, 0.49, 0.38), .98)"),
    ("'mountain': mat('Mountain_Pale_Blue', (0.700, 0.815, 0.810), .99)", "'mountain': mat('Mountain_Pale_Blue', (0.68, 0.79, 0.80), .99)"),
    ("'mountain_shadow': mat('Mountain_Shadow', (0.580, 0.735, 0.740), .99)", "'mountain_shadow': mat('Mountain_Shadow', (0.56, 0.70, 0.72), .99)"),
    ("'snow': mat('Mountain_Snow', (0.900, 0.925, 0.910), .99)", "'snow': mat('Mountain_Snow', (0.88, 0.91, 0.89), .99)"),
    ("'path': mat('Path_Pale_Sand', (0.780, 0.735, 0.535), .98)", "'path': mat('Path_Pale_Sand', (0.68, 0.61, 0.38), .98)"),
    ("ico('Valley_Hill_%02d'%i,(x,y,0.0),1,M['grass_hill'],scale=(sx,sy,sz),sub=2)", "ico('Valley_Hill_%02d'%i,(x,y,-1.25),1,M['grass_hill'],scale=(sx,sy,0.85),sub=2)"),
    ("(-86,76,30,17,28),(-61,78,32,18,33),(-34,80,31,17,31),(-7,82,29,18,37),\n    (22,81,34,19,34),(51,79,36,19,39),(82,76,32,18,31)", "(-98,112,38,23,30),(-68,116,38,24,34),(-36,119,36,23,32),(0,122,39,25,39),\n    (37,120,39,24,34),(70,116,41,25,37),(100,112,38,23,31)"),
    ("for x0,x1,y0,y1,n in [(-82,-43,-35,57,135),(44,82,-34,57,135)]", "for x0,x1,y0,y1,n in [(-66,-27,-31,64,225),(27,66,-31,64,225)]"),
    ("for _ in range(235):\n    x=rng.uniform(-78,78); y=rng.uniform(32,66)", "for _ in range(460):\n    x=rng.uniform(-74,74); y=rng.uniform(28,82)"),
    ("x=rng.uniform(47,82)*side; y=rng.uniform(-39,-15)", "x=rng.uniform(38,67)*side; y=rng.uniform(-31,-8)"),
    ("sun.data.energy=2.1", "sun.data.energy=1.25"),
    ("area=bpy.context.object; area.name='Sky_Fill'; area.data.energy=850; area.data.size=45", "area=bpy.context.object; area.name='Sky_Fill'; area.data.energy=420; area.data.size=58"),
    ("bpy.ops.object.camera_add(location=(0,-92,48))\ncam=bpy.context.object; cam.name='Camera_Main'; scene.camera=cam\ncam.data.type='PERSP'; cam.data.lens=48\nlook_at(cam,(0,18,3.3))", "bpy.ops.object.camera_add(location=(0,-106,53))\ncam=bpy.context.object; cam.name='Camera_Main'; scene.camera=cam\ncam.data.type='PERSP'; cam.data.lens=47\nlook_at(cam,(0,22,4.0))"),
    ("render('preview_main.png',(0,-92,48),(0,18,3.3),48)", "render('preview_main.png',(0,-106,53),(0,22,4.0),47)"),
    ("render('preview_closer.png',(-5,-82,42),(-7,21,3.0),52)", "render('preview_closer.png',(-4,-94,46),(-8,25,3.5),50)"),
    ("render('preview_left.png',(-54,-74,41),(0,18,3.0),52)", "# preview_left omitted for faster iteration"),
    ("render('preview_right.png',(54,-74,41),(0,18,3.0),52)", "# preview_right omitted for faster iteration"),
    ("render('preview_high.png',(0,-78,67),(0,15,1.0),52)", "render('preview_high.png',(0,-94,69),(0,22,2.0),49)"),
    ("cam.location=(0,-92,48); cam.data.lens=48; look_at(cam,(0,18,3.3))", "cam.location=(0,-106,53); cam.data.lens=47; look_at(cam,(0,22,4.0))"),
    ("blend_path=os.path.join(OUT,'reference_valley_v2.blend')", "blend_path=os.path.join(OUT,'reference_valley_v4.blend')"),
    ("glb_path=os.path.join(OUT,'reference_valley_v2.glb')", "glb_path=os.path.join(OUT,'reference_valley_v4.glb')"),
]

for old,new in repls:
    if old not in src:
        raise RuntimeError('Expected source fragment not found: '+old[:120])
    src=src.replace(old,new)

# Make camps more readable at the reference scale.
src=src.replace("s=rng.uniform(.70,.86)", "s=rng.uniform(1.00,1.18)")
src=src.replace("s=rng.uniform(.63,.78)", "s=rng.uniform(.90,1.05)")

# Keep the true Blender file as the primary deliverable; skip distro glTF exporter.
marker="try:\n    bpy.ops.export_scene.gltf(filepath=glb_path,export_format='GLB',export_apply=True)\nexcept TypeError:\n    bpy.ops.export_scene.gltf(filepath=glb_path,export_format='GLB')\n\nmesh_objs=[o for o in scene.objects if o.type=='MESH']"
if marker not in src: raise RuntimeError('GLB block not found')
src=src.replace(marker,"mesh_objs=[o for o in scene.objects if o.type=='MESH']")
src=src.replace("Reference Valley v2\\n","Reference Valley v4\\n")

ns={'__file__':str(src_path),'__name__':'__main__'}
exec(compile(src,str(src_path),'exec'),ns,ns)
