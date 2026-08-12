from pathlib import Path

v5_path = Path(__file__).with_name('build_reference_valley_v5.py')
src = v5_path.read_text(encoding='utf-8')

changes = [
    ("output_reference_valley_v5", "output_reference_valley_v6"),
    ("reference_valley_v5.blend", "reference_valley_v6.blend"),
    ("reference_valley_v5.glb", "reference_valley_v6.glb"),
    ("Reference Valley v5", "Reference Valley v6"),
    ("(0.59, 0.62, 0.23)", "(0.63, 0.62, 0.19)"),
    ("for x0,x1,y0,y1,n in [(-67,-31,-34,66,150),(31,67,-34,66,150)]", "for x0,x1,y0,y1,n in [(-67,-31,-34,66,170),(31,67,-34,66,170)]"),
    ("for _ in range(260):\\n    x=rng.uniform(-72,72); y=rng.uniform(30,72)", "for _ in range(300):\\n    x=rng.uniform(-72,72); y=rng.uniform(30,76)"),
    ("CX,CY=-13.0,30.5", "CX,CY=-5.0,38.0"),
    ("((x+13)/19)**2+((y-33)/11)**2", "((x+5)/19)**2+((y-40)/11)**2"),
    ("mountain_blobs=[(-92,128,34,19,23),(-62,132,36,20,27),(-31,135,34,20,25),(2,137,38,21,30),(36,135,37,21,27),(70,131,38,20,29),(101,127,34,19,23)]", "mountain_blobs=[(-98,165,30,18,18),(-69,169,32,18,21),(-38,172,31,19,20),(-5,174,34,19,23),(29,173,33,19,21),(62,169,33,18,22),(94,165,30,18,18)]"),
    ("(x,y,-2.5)", "(x,y,-5.0)"),
    ("(x-2.0,y-1.0,sz*0.52)", "(x-2.0,y-1.0,sz*0.36)"),
    ("scale=(sx*.36,sy*.32,sz*.22)", "scale=(sx*.34,sy*.30,sz*.18)"),
    ("location=(0,-105,45)", "location=(0,-105,45)"),
    ("cam.data.lens=47\\nlook_at(cam,(0,20,4.0))", "cam.data.lens=44\\nlook_at(cam,(0,24,4.0))"),
    ("render('preview_main.png',(0,-105,45),(0,20,4.0),47)", "render('preview_main.png',(0,-105,45),(0,24,4.0),44)"),
    ("render('preview_closer.png',(-5,-91,42),(-8,23,3.5),50)", "render('preview_closer.png',(-4,-94,42),(-4,31,3.8),48)"),
    ("cam.location=(0,-105,45); cam.data.lens=47; look_at(cam,(0,20,4.0))", "cam.location=(0,-105,45); cam.data.lens=44; look_at(cam,(0,24,4.0))"),
]

for old,new in changes:
    if old == new:
        continue
    if old not in src:
        raise RuntimeError('V6 expected fragment missing: '+old[:100])
    src = src.replace(old,new)

ns={'__file__':str(v5_path),'__name__':'__main__'}
exec(compile(src,str(v5_path),'exec'),ns,ns)
