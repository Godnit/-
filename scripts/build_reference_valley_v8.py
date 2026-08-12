from pathlib import Path

src_path = Path(__file__).with_name('build_reference_valley_v2.py')
src = src_path.read_text(encoding='utf-8')

repls = [
    ("OUT = os.path.join(ROOT, 'output_reference_valley_v2')", "OUT = os.path.join(ROOT, 'output_reference_valley_v8')"),
    ("scene.render.resolution_x = 1536", "scene.render.resolution_x = 1024"),
    ("scene.render.resolution_y = 864", "scene.render.resolution_y = 576"),
    ("scene.view_settings.exposure = 0.35", "scene.view_settings.exposure = 0.0"),
    ("bg.inputs['Color'].default_value = (0.72, 0.88, 0.90, 1.0)", "bg.inputs['Color'].default_value = (0.66, 0.87, 0.88, 1.0)"),
    ("bg.inputs['Strength'].default_value = 0.75", "bg.inputs['Strength'].default_value = 0.64"),
    ("'grass': mat('Grass_Reference', (0.710, 0.753, 0.431), .98)", "'grass': mat('Grass_Reference', (0.63, 0.62, 0.19), .98)"),
    ("'grass_hill': mat('Grass_Hill', (0.620, 0.700, 0.390), .98)", "'grass_hill': mat('Grass_Hill', (0.50, 0.57, 0.22), .98)"),
    ("'tree_a': mat('Pine_Mint_A', (0.455, 0.610, 0.520), .98)", "'tree_a': mat('Pine_Mint_A', (0.36, 0.55, 0.44), .98)"),
    ("'tree_b': mat('Pine_Mint_B', (0.505, 0.655, 0.555), .98)", "'tree_b': mat('Pine_Mint_B', (0.43, 0.62, 0.49), .98)"),
    ("'tree_c': mat('Pine_Muted_C', (0.385, 0.535, 0.455), .98)", "'tree_c': mat('Pine_Muted_C', (0.30, 0.48, 0.38), .98)"),
    ("'mountain': mat('Mountain_Pale_Blue', (0.700, 0.815, 0.810), .99)", "'mountain': mat('Mountain_Pale_Blue', (0.70, 0.80, 0.80), .99)"),
    ("'mountain_shadow': mat('Mountain_Shadow', (0.580, 0.735, 0.740), .99)", "'mountain_shadow': mat('Mountain_Shadow', (0.56, 0.70, 0.72), .99)"),
    ("'snow': mat('Mountain_Snow', (0.900, 0.925, 0.910), .99)", "'snow': mat('Mountain_Snow', (0.90, 0.92, 0.90), .99)"),
    ("'path': mat('Path_Pale_Sand', (0.780, 0.735, 0.535), .98)", "'path': mat('Path_Pale_Sand', (0.73, 0.67, 0.43), .98)"),
    ("ico('Valley_Hill_%02d'%i,(x,y,0.0),1,M['grass_hill'],scale=(sx,sy,sz),sub=2)", "ico('Valley_Hill_%02d'%i,(x,y,-1.0),1,M['grass_hill'],scale=(sx,sy,1.0),sub=2)"),
    ("for x0,x1,y0,y1,n in [(-82,-43,-35,57,135),(44,82,-34,57,135)]", "for x0,x1,y0,y1,n in [(-67,-31,-34,66,170),(31,67,-34,66,170)]"),
    ("for _ in range(235):\n    x=rng.uniform(-78,78); y=rng.uniform(32,66)", "for _ in range(300):\n    x=rng.uniform(-72,72); y=rng.uniform(30,76)"),
    ("for _ in range(70):", "for _ in range(50):"),
    ("x=rng.uniform(47,82)*side; y=rng.uniform(-39,-15)", "x=rng.uniform(40,68)*side; y=rng.uniform(-34,-11)"),
    ("for _ in range(38):", "for _ in range(30):"),
    ("CX,CY=-13.0,30.5", "CX,CY=-5.0,38.0"),
    ("((x+13)/19)**2+((y-33)/11)**2", "((x+5)/19)**2+((y-40)/11)**2"),
    ("sun.data.energy=2.1", "sun.data.energy=1.30"),
    ("area=bpy.context.object; area.name='Sky_Fill'; area.data.energy=850; area.data.size=45", "area=bpy.context.object; area.name='Sky_Fill'; area.data.energy=450; area.data.size=58"),
    ("bpy.ops.object.camera_add(location=(0,-92,48))\ncam=bpy.context.object; cam.name='Camera_Main'; scene.camera=cam\ncam.data.type='PERSP'; cam.data.lens=48\nlook_at(cam,(0,18,3.3))", "bpy.ops.object.camera_add(location=(0,-105,45))\ncam=bpy.context.object; cam.name='Camera_Main'; scene.camera=cam\ncam.data.type='PERSP'; cam.data.lens=44\nlook_at(cam,(0,24,4.0))"),
    ("render('preview_main.png',(0,-92,48),(0,18,3.3),48)", "render('preview_main.png',(0,-105,45),(0,24,4.0),44)"),
    ("render('preview_closer.png',(-5,-82,42),(-7,21,3.0),52)", "render('preview_closer.png',(-4,-94,42),(-4,31,3.8),48)"),
    ("render('preview_left.png',(-54,-74,41),(0,18,3.0),52)", "# preview_left omitted"),
    ("render('preview_right.png',(54,-74,41),(0,18,3.0),52)", "# preview_right omitted"),
    ("render('preview_high.png',(0,-78,67),(0,15,1.0),52)", "# preview_high omitted"),
    ("cam.location=(0,-92,48); cam.data.lens=48; look_at(cam,(0,18,3.3))", "cam.location=(0,-105,45); cam.data.lens=44; look_at(cam,(0,24,4.0))"),
    ("blend_path=os.path.join(OUT,'reference_valley_v2.blend')", "blend_path=os.path.join(OUT,'reference_valley_v8.blend')"),
    ("glb_path=os.path.join(OUT,'reference_valley_v2.glb')", "glb_path=os.path.join(OUT,'reference_valley_v8.glb')"),
]

for old,new in repls:
    if old not in src:
        raise RuntimeError('V8 expected source fragment missing: '+old[:120])
    src = src.replace(old,new)

# Replace the separated mountain objects with one broad, irregular faceted mountain ridge.
old_mountains = "mountain_specs=[\n    (-86,76,30,17,28),(-61,78,32,18,33),(-34,80,31,17,31),(-7,82,29,18,37),\n    (22,81,34,19,34),(51,79,36,19,39),(82,76,32,18,31)\n]\nfor i,(x,y,rx,dy,h) in enumerate(mountain_specs):\n    mountain_mesh('Mountain_%02d'%i,x,y,-0.2,rx,dy,h,100+i)"
new_mountains = "ridge_x=[-115,-96,-78,-60,-42,-24,-7,10,28,46,64,82,101,118]\nridge_h=[11,17,23,18,26,22,31,25,29,21,27,20,16,10]\nridge_y=[151,149,153,150,154,151,156,152,155,150,154,151,149,152]\nfront_y=119.0\nback_y=179.0\nrv=[]\nfor x in ridge_x: rv.append((x,front_y,-2.2))\nfor x,y,h in zip(ridge_x,ridge_y,ridge_h): rv.append((x,y,h))\nfor x in ridge_x: rv.append((x,back_y,-3.5))\nrn=len(ridge_x)\nrf=[]; rfm=[]\nfor i in range(rn-1):\n    # front slopes are triangulated to create visible faceting rather than a smooth wall\n    rf.append((i,i+1,rn+i)); rfm.append((i+1)%2)\n    rf.append((i+1,rn+i+1,rn+i)); rfm.append(i%2)\n    rf.append((rn+i,rn+i+1,2*rn+i+1,2*rn+i)); rfm.append((i+1)%2)\nmesh_obj('Mountain_Ridge',rv,rf,[M['mountain'],M['mountain_shadow']],rfm)\n# Small irregular pale summit facets, integrated into the ridge silhouette.\nsnow_v=[]; snow_f=[]\nfor i in range(1,rn-2,2):\n    x=ridge_x[i]; y=ridge_y[i]-0.35; h=ridge_h[i]\n    b=len(snow_v)\n    snow_v.extend([(x-5.0,y,h-3.8),(x,y-0.2,h+0.15),(x+5.0,y,h-3.4),(x,y-1.0,h-6.2)])\n    snow_f.extend([(b,b+1,b+3),(b+1,b+2,b+3)])\nmesh_obj('Mountain_Snow_Facets',snow_v,snow_f,[M['snow']])"
if old_mountains not in src:
    raise RuntimeError('V8 original mountain block missing')
src = src.replace(old_mountains,new_mountains)

# Keep the Blender scene as the primary real 3D deliverable; skip the unreliable distro GLB exporter.
marker = "try:\n    bpy.ops.export_scene.gltf(filepath=glb_path,export_format='GLB',export_apply=True)\nexcept TypeError:\n    bpy.ops.export_scene.gltf(filepath=glb_path,export_format='GLB')\n\nmesh_objs=[o for o in scene.objects if o.type=='MESH']"
if marker not in src:
    raise RuntimeError('V8 GLB block missing')
src = src.replace(marker,"mesh_objs=[o for o in scene.objects if o.type=='MESH']")
src = src.replace("Reference Valley v2\\n","Reference Valley v8\\n")

ns={'__file__':str(src_path),'__name__':'__main__'}
exec(compile(src,str(src_path),'exec'),ns,ns)
