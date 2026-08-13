from pathlib import Path

v24_path=Path(__file__).with_name('build_classic_reference_v24.py')
outer=v24_path.read_text(encoding='utf-8')

# Keep the verified V24 map-only layout/tree placement. Change only the mountain treatment
# and its palette so the distant range matches the supplied reference: very broad, rounded,
# pale low-poly masses rather than repeated sharp triangular peaks.
outer=outer.replace('output_classic_reference_v24','output_classic_reference_v29')
outer=outer.replace('classic_reference_v24.blend','classic_reference_v29.blend')
outer=outer.replace('classic_reference_v24.glb','classic_reference_v29.glb')
outer=outer.replace('TABS Classic reference v24','TABS Classic reference v29')
outer=outer.replace("print('V24_OK'","print('V29_OK'")
outer=outer.replace('V24 pine count changed','V29 pine count changed')
outer=outer.replace('V24 MAP ONLY','V29 MAP ONLY')

# Lighter grey/cyan mountain palette like the user's screenshot.
outer=outer.replace(
    "(\"'mountain': mat('Mountain',(0.70,0.80,0.80))\", \"'mountain': mat('Mountain',(0.625,0.755,0.765))\")",
    "(\"'mountain': mat('Mountain',(0.70,0.80,0.80))\", \"'mountain': mat('Mountain',(0.765,0.825,0.825))\")"
)
outer=outer.replace(
    "(\"'mountain2': mat('MountainShadow',(0.54,0.70,0.73))\", \"'mountain2': mat('MountainShadow',(0.505,0.665,0.690))\")",
    "(\"'mountain2': mat('MountainShadow',(0.54,0.70,0.73))\", \"'mountain2': mat('MountainShadow',(0.610,0.710,0.735))\")"
)

start=outer.index("new_mountains=r'''")+len("new_mountains=r'''")
end=outer.index("'''\nsrc=src[:mount_start]+new_mountains+src[mount_end:]",start)

mountains=r'''# -----------------------------------------------------------------------------
# V29 mountains: huge soft low-poly masses like the supplied reference image.
# The mountains are intentionally broad and rounded. Their bases are deeply buried in
# an extended meadow so there is no straight wall/cut and no repeating saw-tooth ridge.
# -----------------------------------------------------------------------------
box('BackgroundGround',(0,280,-0.72),(218,230,1.44),M['grass'],0)

# Front range: seven overlapping major masses. The center/right peaks are the largest,
# matching the reference where a few huge pale mountains dominate the horizon.
front_specs=[
    (-195,254,78,58,37),
    (-137,250,86,61,43),
    (-73,255,88,63,39),
    (-5,260,96,67,46),
    (70,257,92,65,43),
    (142,251,88,62,47),
    (207,254,79,58,38),
]
for i,(x,y,sx,sy,sz) in enumerate(front_specs):
    mat_main=M['mountain'] if i%3!=1 else M['mountain2']
    # Main rounded mountain body.
    ico('Mountain_%02d'%i,(x,y,-10.5),(sx,sy,sz),mat_main,2)
    # Low broad shoulder makes the silhouette irregular and less spherical without creating a peak.
    side=-1 if i%2==0 else 1
    ico('MountainShoulderA_%02d'%i,(x+side*sx*.30,y-6.0,-11.8),(sx*.66,sy*.78,sz*.64),M['mountain'],2)
    ico('MountainShoulderB_%02d'%i,(x-side*sx*.25,y+2.0,-12.3),(sx*.54,sy*.66,sz*.52),M['mountain2'],2)

# A softer rear layer gives depth through the gaps while staying lower than the front skyline.
back_specs=[
    (-205,326,95,66,29),(-125,331,101,69,33),(-40,335,106,72,35),
    (52,334,106,71,34),(138,330,100,68,32),(215,326,93,65,28)
]
for i,(x,y,sx,sy,sz) in enumerate(back_specs):
    ico('MountainBack_%02d'%i,(x,y,-12.8),(sx,sy,sz),M['mountain2'],2)

'''
outer=outer[:start]+mountains+outer[end:]
outer=outer.replace('Mountain style: connected low-poly terrain range','Mountain style: broad rounded pale low-poly masses matching reference')

ns={'__file__':str(v24_path),'__name__':'__main__'}
exec(compile(outer,str(v24_path),'exec'),ns,ns)
