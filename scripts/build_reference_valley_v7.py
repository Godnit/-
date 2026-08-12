from pathlib import Path

v6_path = Path(__file__).with_name('build_reference_valley_v6.py')
src = v6_path.read_text(encoding='utf-8')

# Promote the already-correct field/forest/church composition to V7.
src = src.replace('output_reference_valley_v6', 'output_reference_valley_v7')
src = src.replace('reference_valley_v6.blend', 'reference_valley_v7.blend')
src = src.replace('reference_valley_v6.glb', 'reference_valley_v7.glb')
src = src.replace('Reference Valley v6', 'Reference Valley v7')

# Change the V6 mountain list into a farther, lower and more irregular peak sequence.
old = "mountain_blobs=[(-98,165,30,18,18),(-69,169,32,18,21),(-38,172,31,19,20),(-5,174,34,19,23),(29,173,33,19,21),(62,169,33,18,22),(94,165,30,18,18)]"
new = "mountain_specs2=[(-100,158,30,17,20),(-70,161,33,18,25),(-39,163,31,18,23),(-7,165,34,19,28),(25,164,33,18,25),(58,161,34,18,27),(92,158,30,17,21)]"
if old not in src:
    raise RuntimeError('V7 mountain list target missing')
src = src.replace(old, new)

# V6 operates on the textual V5 builder. Inject a rewrite there after V6 has applied its own patches.
insert_at = "# These two values live in the V2 source that V5 patches, not literally in V5 itself."
mountain_rewrite = (
    "src=src.replace(\"for i,(x,y,sx,sy,sz) in enumerate(mountain_blobs):\",\"for i,(x,y,rx,dy,h) in enumerate(mountain_specs2):\")\n"
    "src=src.replace(\"ico('MountainDome_%02d'%i,(x,y,-5.0),1,M['mountain'] if i%2==0 else M['mountain_shadow'],scale=(sx,sy,sz),sub=2)\",\"mountain_mesh('Mountain_%02d'%i,x,y,-5.0,rx,dy,h,300+i)\")\n"
    "src=src.replace(\"    ico('MountainCap_%02d'%i,(x-2.0,y-1.0,sz*0.36),1,M['snow'],scale=(sx*.34,sy*.30,sz*.18),sub=1)\\n\",\"\")\n"
)
if insert_at not in src:
    raise RuntimeError('V7 insertion point missing')
src = src.replace(insert_at, mountain_rewrite + "\n" + insert_at)

# Brighten only the background atmosphere. Keep the grass unchanged because V6 already matched it closely.
needle = "ns={'__file__':str(v5_path),'__name__':'__main__'}"
extra = (
    "src=src.replace(\"bg.inputs['Strength'].default_value = 0.52\",\"bg.inputs['Strength'].default_value = 0.64\")\n"
    "src=src.replace(\"bg.inputs['Color'].default_value = (0.61, 0.84, 0.86, 1.0)\",\"bg.inputs['Color'].default_value = (0.66, 0.87, 0.88, 1.0)\")\n"
)
if needle not in src:
    raise RuntimeError('V7 execution marker missing')
src = src.replace(needle, extra + needle)

ns = {'__file__': str(v6_path), '__name__': '__main__'}
exec(compile(src, str(v6_path), 'exec'), ns, ns)
