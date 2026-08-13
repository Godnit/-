from pathlib import Path

src_path=Path(__file__).with_name('build_classic_reference_v17.py')
src=src_path.read_text(encoding='utf-8')

src=src.replace('output_classic_reference_v17','output_classic_reference_v18')
src=src.replace('classic_reference_v17.blend','classic_reference_v18.blend')
src=src.replace('classic_reference_v17.glb','classic_reference_v18.glb')
src=src.replace('TABS Classic reference v17','TABS Classic reference v18')
src=src.replace("print('V17_OK'", "print('V18_OK'")

# Match the target sky and meadow luminance more closely while preserving darker pines.
repls=[
("bg.inputs['Color'].default_value = (0.59,0.79,0.80,1.0)","bg.inputs['Color'].default_value = (0.665,0.825,0.825,1.0)"),
("bg.inputs['Strength'].default_value = 0.62","bg.inputs['Strength'].default_value = 0.72"),
("'grass': mat('Grass',(0.43,0.48,0.12))","'grass': mat('Grass',(0.50,0.535,0.145))"),
("'grass_hill': mat('GrassHill',(0.39,0.45,0.14))","'grass_hill': mat('GrassHill',(0.45,0.50,0.16))"),
("'tree1': mat('Pine1',(0.16,0.30,0.22))","'tree1': mat('Pine1',(0.15,0.26,0.20))"),
("'tree2': mat('Pine2',(0.22,0.37,0.27))","'tree2': mat('Pine2',(0.21,0.33,0.25))"),
("'tree3': mat('Pine3',(0.28,0.44,0.32))","'tree3': mat('Pine3',(0.27,0.39,0.29))"),
]
for old,new in repls:
    if old not in src:raise RuntimeError('v18 missing '+old)
    src=src.replace(old,new)

# Push mountain masses farther back and lower their peaks so a cyan sky band remains, like the reference.
old_front="front_specs=[(-145,205,52,39,31),(-108,205,48,38,39),(-70,211,49,39,36),(-29,214,58,42,47),(18,213,55,42,42),(61,211,58,42,48),(105,207,55,40,43),(144,205,50,38,32)]"
new_front="front_specs=[(-145,228,54,42,24),(-108,229,50,41,30),(-70,233,51,42,28),(-29,237,60,45,36),(18,236,57,44,32),(61,234,60,44,37),(105,230,57,43,33),(144,228,52,41,25)]"
if old_front not in src:raise RuntimeError('v18 front mountains missing')
src=src.replace(old_front,new_front)
old_back="back_specs=[(-165,247,65,45,27),(-105,251,68,47,30),(-43,254,70,48,33),(25,254,72,49,31),(91,251,70,47,32),(157,246,65,44,27)]"
new_back="back_specs=[(-165,280,68,48,22),(-105,284,70,49,24),(-43,287,72,50,26),(25,287,74,51,25),(91,284,72,49,25),(157,279,68,47,22)]"
if old_back not in src:raise RuntimeError('v18 back mountains missing')
src=src.replace(old_back,new_back)

# Strengthen the descending foreground-left forest crescent.
needle="for j,(x,y,s) in enumerate([(-88,-30,1.80),(-80,-26,1.72),(-72,-31,1.85),(-65,-25,1.68),(-57,-30,1.72),(-91,-15,1.58),(-83,-13,1.56),(-75,-17,1.55),(-67,-12,1.48),(-58,-15,1.46),(-50,-10,1.40)]):"
replacement="for j,(x,y,s) in enumerate([(-88,-30,1.80),(-80,-26,1.72),(-72,-31,1.85),(-65,-25,1.68),(-57,-30,1.72),(-91,-15,1.58),(-83,-13,1.56),(-75,-17,1.55),(-67,-12,1.48),(-58,-15,1.46),(-50,-10,1.40),(-70,-4,1.52),(-62,-3,1.50),(-54,-1,1.45),(-47,2,1.38),(-77,5,1.42),(-68,8,1.38),(-59,10,1.32),(-50,12,1.28)]):"
if needle not in src:raise RuntimeError('v18 foreground cluster missing')
src=src.replace(needle,replacement)

# Bring all blue tents into the lower-left visible area.
src=src.replace("blue=[(-58,-9),(-47,-7),(-36,-6),(-25,-5),(-59,-18),(-48,-17),(-37,-16),(-26,-15)]","blue=[(-58,4),(-47,6),(-36,7),(-25,8),(-59,-6),(-48,-5),(-37,-4),(-26,-3)]")

ns={'__file__':str(src_path),'__name__':'__main__'}
exec(compile(src,str(src_path),'exec'),ns,ns)
