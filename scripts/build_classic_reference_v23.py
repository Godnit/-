from pathlib import Path

v22_path=Path(__file__).with_name('build_classic_reference_v22.py')
outer=v22_path.read_text(encoding='utf-8')

outer=outer.replace('output_classic_reference_v22','output_classic_reference_v23')
outer=outer.replace('classic_reference_v22.blend','classic_reference_v23.blend')
outer=outer.replace('classic_reference_v22.glb','classic_reference_v23.glb')
outer=outer.replace('TABS Classic reference v22','TABS Classic reference v23')
outer=outer.replace("print('V22_OK'", "print('V23_OK'")

# Remove the artificial broad green ridge entirely; the reference reads as one continuous valley floor
# flowing into forested mountain foothills.
old_new_hills="""new_hills = \"\"\"for i,(x,y,sx,sy,sz) in enumerate([
    (-91,48,20,88,1.35),(91,50,20,88,1.35),
    (-82,142,31,43,1.45),(82,142,31,43,1.45)
]):
    ico('Hill_%02d'%i,(x,y,-2.72),(sx,sy,sz),M['grass_hill'],2)\"\"\""""
new_new_hills="""new_hills = \"\"\"for i,(x,y,sx,sy,sz) in enumerate([]):
    ico('Hill_%02d'%i,(x,y,-2.72),(sx,sy,sz),M['grass_hill'],2)\"\"\""""
if old_new_hills not in outer:
    raise RuntimeError('V23 hill replacement literal missing')
outer=outer.replace(old_new_hills,new_new_hills)

# Push the optional church landmark farther into the upper meadow. It is intentionally subordinate;
# the user's stated priorities are field scale, colors and forest placement.
outer=outer.replace('src = src.replace("CX,CY=-7.0,92.0", "CX,CY=-7.0,94.0") if "CX,CY=-7.0,92.0" in src else src',
                    'src = src.replace("CX,CY=-7.0,92.0", "CX,CY=-7.0,120.0") if "CX,CY=-7.0,92.0" in src else src')

# Short path near the distant landmark instead of a long bright line through the center.
outer=outer.replace("[(8,63),(5,70),(1,78),(-3,86),(CX,CY-2.7)]", "[(5,94),(2,102),(-2,110),(CX,CY-2.7)]")

# Move graves and pink camp with the farther landmark.
outer=outer.replace("[(-14,89),(-12,91),(-15,93),(-11,95),(-16,96),(-10,87),(-17,90)]", "[(-14,116),(-12,118),(-15,120),(-11,122),(-16,123),(-10,114),(-17,117)]")
outer=outer.replace("pink=[(43,91),(48,93),(53,91),(46,87),(52,86),(58,88)]", "pink=[(43,120),(48,122),(53,120),(46,116),(52,115),(58,117)]")

# Make the complete blue formation readable in the same lower-left region as the reference.
outer=outer.replace("blue=[(-58,4),(-47,6),(-36,7),(-25,8),(-59,-6),(-48,-5),(-37,-4),(-26,-3)]", "blue=[(-63,14),(-51,15),(-39,16),(-27,17),(-61,3),(-49,4),(-37,5),(-25,6)]")

ns={'__file__':str(v22_path),'__name__':'__main__'}
exec(compile(outer,str(v22_path),'exec'),ns,ns)
