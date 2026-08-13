from pathlib import Path

v27_path=Path(__file__).with_name('build_classic_reference_v27.py')
outer=v27_path.read_text(encoding='utf-8')
outer=outer.replace('output_classic_reference_v27','output_classic_reference_v28')
outer=outer.replace('classic_reference_v27.blend','classic_reference_v28.blend')
outer=outer.replace('classic_reference_v27.glb','classic_reference_v28.glb')
outer=outer.replace('TABS Classic reference v27','TABS Classic reference v28')
outer=outer.replace("print('V27_OK'","print('V28_OK'")
outer=outer.replace('V27 pine count changed','V28 pine count changed')
outer=outer.replace('V27 MAP ONLY','V28 MAP ONLY')

start=outer.index("ridge_code=r'''")+len("ridge_code=r'''")
end=outer.index("'''\nouter=outer[:start]+ridge_code+outer[end:]",start)

mountain_code=r'''# -----------------------------------------------------------------------------
# V28 mountains: broad rounded/faceted masses embedded in extended meadow ground.
# Bases are buried; there is no horizontal mountain cut and no continuous triangular wall.
# -----------------------------------------------------------------------------
# Visual-only continuation of the flat valley beyond the playable 218 x 252 field.
box('BackgroundGround',(0,270,-0.70),(218,192,1.40),M['grass'],0)

front_specs=[
    (-178,220,55,40,14,0),(-137,225,58,42,17,1),(-94,229,58,43,15,0),
    (-51,233,64,45,18,1),(-7,237,69,48,21,0),(41,235,66,47,18,1),
    (88,231,63,45,19,0),(133,226,59,42,16,1),(176,221,54,39,14,0)
]
for i,(x,y,sx,sy,sz,var) in enumerate(front_specs):
    mm=M['mountain'] if var==0 else M['mountain2']
    # Main mountain body; center is below ground so only natural upper slopes are visible.
    ico('Mountain_%02d'%i,(x,y,-5.8),(sx,sy,sz),mm,2)
    # Broad asymmetric shoulder breaks the sphere silhouette into a natural mountain mass.
    off=(-1 if i%2==0 else 1)
    ico('MountainShoulder_%02d'%i,(x+off*sx*.27,y-5.0,-6.2),(sx*.64,sy*.76,sz*.68),M['mountain'],2)

# Distant softer layer, lower and less contrast, visible through the front silhouettes.
for i,(x,y,sx,sy,sz) in enumerate([
    (-185,282,70,44,10),(-120,286,72,45,12),(-52,289,76,47,13),
    (22,289,77,47,12),(96,286,73,45,12),(165,282,69,43,10)
]):
    ico('MountainBack_%02d'%i,(x,y,-5.9),(sx,sy,sz),M['mountain2'],2)

'''
outer=outer[:start]+mountain_code+outer[end:]
outer=outer.replace('Mountain style: closed low-poly ridge with hidden rear wall','Mountain style: broad embedded rounded low-poly masses')

ns={'__file__':str(v27_path),'__name__':'__main__'}
exec(compile(outer,str(v27_path),'exec'),ns,ns)
