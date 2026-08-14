from pathlib import Path
base=Path(__file__).with_name('build_model.py')
src=base.read_text(encoding='utf-8')
src=src.replace("scene.world.color = (0.82, 0.80, 0.74)","if scene.world is None:\n    scene.world = bpy.data.worlds.new('World')\nscene.world.color = (0.82, 0.80, 0.74)")
exec(compile(src,str(base),'exec'),{'__file__':str(base),'__name__':'__main__'})
