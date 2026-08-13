from pathlib import Path
src_path=Path(__file__).with_name('build_classic_reference_v18.py')
src=src_path.read_text(encoding='utf-8')

src=src.replace('output_classic_reference_v18','output_classic_reference_v19')
src=src.replace('classic_reference_v18.blend','classic_reference_v19.blend')
src=src.replace('classic_reference_v18.glb','classic_reference_v19.glb')
src=src.replace('TABS Classic reference v18','TABS Classic reference v19')
src=src.replace("print('V18_OK'", "print('V19_OK'")

# More cyan daylight at the very top like the supplied screenshot.
src=src.replace("bg.inputs['Color'].default_value = (0.665,0.825,0.825,1.0)","bg.inputs['Color'].default_value = (0.69,0.865,0.865,1.0)")
src=src.replace("bg.inputs['Strength'].default_value = 0.72","bg.inputs['Strength'].default_value = 0.77")
# Compensate grass slightly so the meadow remains near the sampled target value.
src=src.replace("'grass': mat('Grass',(0.50,0.535,0.145))","'grass': mat('Grass',(0.485,0.505,0.14))")
src=src.replace("'grass_hill': mat('GrassHill',(0.45,0.50,0.16))","'grass_hill': mat('GrassHill',(0.43,0.47,0.15))")

# Lower/farther mountains: preserve their broad masses but expose a clean sky band.
old_front="front_specs=[(-145,228,54,42,24),(-108,229,50,41,30),(-70,233,51,42,28),(-29,237,60,45,36),(18,236,57,44,32),(61,234,60,44,37),(105,230,57,43,33),(144,228,52,41,25)]"
new_front="front_specs=[(-145,242,56,44,20),(-108,243,52,43,25),(-70,247,53,44,23),(-29,251,62,47,30),(18,250,59,46,27),(61,248,62,46,31),(105,244,59,45,28),(144,242,54,43,21)]"
if old_front not in src:raise RuntimeError('v19 front mountains missing')
src=src.replace(old_front,new_front)
old_back="back_specs=[(-165,280,68,48,22),(-105,284,70,49,24),(-43,287,72,50,26),(25,287,74,51,25),(91,284,72,49,25),(157,279,68,47,22)]"
new_back="back_specs=[(-165,300,70,50,18),(-105,304,72,51,20),(-43,307,74,52,22),(25,307,76,53,21),(91,304,74,51,21),(157,299,70,49,18)]"
if old_back not in src:raise RuntimeError('v19 back mountains missing')
src=src.replace(old_back,new_back)

# Add the conspicuous large left/front tree wall from the reference and a smaller right-edge counterpart.
needle="for x,y,s,v in trees:add_pine(x,y,s,v)"
addition='''for j,(x,y,s) in enumerate([(-64,-30,2.05),(-57,-27,1.98),(-50,-24,1.92),(-43,-22,1.86),(-36,-19,1.76),(-61,-14,1.80),(-53,-12,1.74),(-45,-10,1.68),(-37,-7,1.58),(-29,-6,1.48),(78,-26,1.65),(85,-19,1.58),(91,-10,1.48)]):
    trees.append((x,y,s,(len(trees)+j)%3))
for x,y,s,v in trees:add_pine(x,y,s,v)'''
if needle not in src:raise RuntimeError('v19 tree emit missing')
src=src.replace(needle,addition)

ns={'__file__':str(src_path),'__name__':'__main__'}
exec(compile(src,str(src_path),'exec'),ns,ns)
