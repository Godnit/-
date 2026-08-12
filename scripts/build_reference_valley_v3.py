from pathlib import Path

src_path = Path(__file__).with_name('build_reference_valley_v2.py')
src = src_path.read_text(encoding='utf-8')

repls = {
    "scene.view_settings.exposure = 0.35": "scene.view_settings.exposure = -0.85",
    "bg.inputs['Color'].default_value = (0.72, 0.88, 0.90, 1.0)": "bg.inputs['Color'].default_value = (0.56, 0.78, 0.80, 1.0)",
    "bg.inputs['Strength'].default_value = 0.75": "bg.inputs['Strength'].default_value = 0.38",
    "'grass': mat('Grass_Reference', (0.710, 0.753, 0.431), .98)": "'grass': mat('Grass_Reference', (0.43, 0.53, 0.20), .98)",
    "'grass_hill': mat('Grass_Hill', (0.620, 0.700, 0.390), .98)": "'grass_hill': mat('Grass_Hill', (0.38, 0.49, 0.19), .98)",
    "'tree_a': mat('Pine_Mint_A', (0.455, 0.610, 0.520), .98)": "'tree_a': mat('Pine_Mint_A', (0.28, 0.44, 0.34), .98)",
    "'tree_b': mat('Pine_Mint_B', (0.505, 0.655, 0.555), .98)": "'tree_b': mat('Pine_Mint_B', (0.34, 0.50, 0.39), .98)",
    "'tree_c': mat('Pine_Muted_C', (0.385, 0.535, 0.455), .98)": "'tree_c': mat('Pine_Muted_C', (0.23, 0.38, 0.30), .98)",
    "'mountain': mat('Mountain_Pale_Blue', (0.700, 0.815, 0.810), .99)": "'mountain': mat('Mountain_Pale_Blue', (0.55, 0.68, 0.69), .99)",
    "'mountain_shadow': mat('Mountain_Shadow', (0.580, 0.735, 0.740), .99)": "'mountain_shadow': mat('Mountain_Shadow', (0.43, 0.59, 0.62), .99)",
    "'snow': mat('Mountain_Snow', (0.900, 0.925, 0.910), .99)": "'snow': mat('Mountain_Snow', (0.78, 0.84, 0.82), .99)",
    "(-86,76,30,17,28),(-61,78,32,18,33),(-34,80,31,17,31),(-7,82,29,18,37),\n    (22,81,34,19,34),(51,79,36,19,39),(82,76,32,18,31)": "(-86,93,30,17,25),(-61,95,32,18,29),(-34,97,31,17,28),(-7,99,29,18,32),\n    (22,98,34,19,30),(51,96,36,19,34),(82,93,32,18,28)",
    "for x0,x1,y0,y1,n in [(-82,-43,-35,57,135),(44,82,-34,57,135)]": "for x0,x1,y0,y1,n in [(-66,-29,-31,58,190),(29,66,-31,58,190)]",
    "for _ in range(235):\n    x=rng.uniform(-78,78); y=rng.uniform(32,66)": "for _ in range(330):\n    x=rng.uniform(-70,70); y=rng.uniform(27,62)",
    "x=rng.uniform(47,82)*side; y=rng.uniform(-39,-15)": "x=rng.uniform(37,66)*side; y=rng.uniform(-31,-10)",
    "sun.data.energy=2.1": "sun.data.energy=1.15",
    "area=bpy.context.object; area.name='Sky_Fill'; area.data.energy=850; area.data.size=45": "area=bpy.context.object; area.name='Sky_Fill'; area.data.energy=260; area.data.size=55",
    "bpy.ops.object.camera_add(location=(0,-92,48))": "bpy.ops.object.camera_add(location=(0,-103,51))",
    "look_at(cam,(0,18,3.3))": "look_at(cam,(0,19,4.0))",
    "render('preview_main.png',(0,-92,48),(0,18,3.3),48)": "render('preview_main.png',(0,-103,51),(0,19,4.0),46)",
    "render('preview_closer.png',(-5,-82,42),(-7,21,3.0),52)": "render('preview_closer.png',(-5,-92,45),(-7,22,3.5),50)",
    "render('preview_left.png',(-54,-74,41),(0,18,3.0),52)": "render('preview_left.png',(-58,-84,44),(0,19,3.5),50)",
    "render('preview_right.png',(54,-74,41),(0,18,3.0),52)": "render('preview_right.png',(58,-84,44),(0,19,3.5),50)",
    "render('preview_high.png',(0,-78,67),(0,15,1.0),52)": "render('preview_high.png',(0,-90,66),(0,18,2.0),48)",
    "cam.location=(0,-92,48); cam.data.lens=48; look_at(cam,(0,18,3.3))": "cam.location=(0,-103,51); cam.data.lens=46; look_at(cam,(0,19,4.0))",
    "OUT = os.path.join(ROOT, 'output_reference_valley_v2')": "OUT = os.path.join(ROOT, 'output_reference_valley_v3')",
    "blend_path=os.path.join(OUT,'reference_valley_v2.blend')": "blend_path=os.path.join(OUT,'reference_valley_v3.blend')",
    "glb_path=os.path.join(OUT,'reference_valley_v2.glb')": "glb_path=os.path.join(OUT,'reference_valley_v3.glb')",
}

for old, new in repls.items():
    if old not in src:
        raise RuntimeError('Expected source fragment not found: ' + old[:120])
    src = src.replace(old, new)

# The distro Blender glTF exporter can be unavailable in headless mode. Save the .blend and
# write the report before attempting optional GLB export so a valid model is never lost.
marker = "try:\n    bpy.ops.export_scene.gltf(filepath=glb_path,export_format='GLB',export_apply=True)\nexcept TypeError:\n    bpy.ops.export_scene.gltf(filepath=glb_path,export_format='GLB')\n\nmesh_objs=[o for o in scene.objects if o.type=='MESH']"
replacement = "mesh_objs=[o for o in scene.objects if o.type=='MESH']"
if marker not in src:
    raise RuntimeError('GLB export block not found')
src = src.replace(marker, replacement)
src = src.replace("Reference Valley v2\\n", "Reference Valley v3\\n")

namespace = {'__file__': str(src_path), '__name__': '__main__'}
exec(compile(src, str(src_path), 'exec'), namespace, namespace)
