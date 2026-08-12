from pathlib import Path

v8_path = Path(__file__).with_name('build_reference_valley_v8.py')
src = v8_path.read_text(encoding='utf-8')

src = src.replace('output_reference_valley_v8', 'output_reference_valley_v9')
src = src.replace('reference_valley_v8.blend', 'reference_valley_v9.blend')
src = src.replace('reference_valley_v8.glb', 'reference_valley_v9.glb')
src = src.replace('Reference Valley v8', 'Reference Valley v9')

# Push the focal building/camps farther into the valley, as in the supplied reference.
src = src.replace('CX,CY=-5.0,38.0', 'CX,CY=-5.0,50.0')
src = src.replace('((x+5)/19)**2+((y-40)/11)**2', '((x+5)/19)**2+((y-52)/11)**2')
src = src.replace('for _ in range(300):\\n    x=rng.uniform(-72,72); y=rng.uniform(30,76)', 'for _ in range(410):\\n    x=rng.uniform(-72,72); y=rng.uniform(30,104)')

# Lower and push the mountain ridge back so a band of sky remains visible above it.
src = src.replace('ridge_h=[11,17,23,18,26,22,31,25,29,21,27,20,16,10]', 'ridge_h=[8,13,18,14,20,17,23,19,22,16,20,15,12,8]')
src = src.replace('ridge_y=[151,149,153,150,154,151,156,152,155,150,154,151,149,152]', 'ridge_y=[171,169,173,170,174,171,176,172,175,170,174,171,169,172]')
src = src.replace('front_y=119.0', 'front_y=142.0')
src = src.replace('back_y=179.0', 'back_y=205.0')

# Aim the camera slightly farther into the scene to reproduce the broad reference framing.
src = src.replace("look_at(cam,(0,24,4.0))", "look_at(cam,(0,29,4.5))")
src = src.replace("render('preview_main.png',(0,-105,45),(0,24,4.0),44)", "render('preview_main.png',(0,-105,45),(0,29,4.5),44)")
src = src.replace("cam.location=(0,-105,45); cam.data.lens=44; look_at(cam,(0,24,4.0))", "cam.location=(0,-105,45); cam.data.lens=44; look_at(cam,(0,29,4.5))")
src = src.replace("render('preview_closer.png',(-4,-94,42),(-4,31,3.8),48)", "render('preview_closer.png',(-4,-94,42),(-4,38,4.0),48)")

# Inject V2-source changes that V8 did not need: extend the valley floor all the way to the mountain foothills,
# and move the pink camp farther back to match the reference depth.
needle = "ns={'__file__':str(src_path),'__name__':'__main__'}"
extra = (
    "src=src.replace(\"box('Valley_Ground',(0,8,-0.75),(190,132,1.5),M['grass'],bev=.35)\",\"box('Valley_Ground',(0,36,-0.75),(190,188,1.5),M['grass'],bev=.35)\")\n"
    "src=src.replace(\"pink_positions=[(36,28),(41,29),(46,27),(39,23),(45,22),(50,24)]\",\"pink_positions=[(36,40),(41,41),(46,39),(39,35),(45,34),(50,36)]\")\n"
)
if needle not in src:
    raise RuntimeError('V9 execution marker missing')
src = src.replace(needle, extra + needle)

ns={'__file__':str(v8_path),'__name__':'__main__'}
exec(compile(src,str(v8_path),'exec'),ns,ns)
