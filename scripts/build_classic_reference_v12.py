from pathlib import Path

v11_path = Path(__file__).with_name('build_classic_reference_v11.py')
wrapper = v11_path.read_text(encoding='utf-8')

# Promote all deliverable names to V12 while retaining the stable V11 palette/lighting pass.
wrapper = wrapper.replace('output_classic_reference_v11', 'output_classic_reference_v12')
wrapper = wrapper.replace('classic_reference_v11.blend', 'classic_reference_v12.blend')
wrapper = wrapper.replace('classic_reference_v11.glb', 'classic_reference_v12.glb')
wrapper = wrapper.replace('TABS Classic reference valley v11', 'TABS Classic reference valley v12')

marker = "ns={'__file__':str(src_path),'__name__':'__main__'}\nexec(compile(src,str(src_path),'exec'),ns,ns)"
if marker not in wrapper:
    raise RuntimeError('V12 wrapper execution marker missing')

extra = r'''
# -----------------------------------------------------------------------------
# V12 composition corrections from the supplied Classic/Pre-Alpha screenshot.
# Keep the V11 palette because its rendered field color already closely matches the reference.
# -----------------------------------------------------------------------------

# A much larger empty battle meadow.
src = src.replace(
    "return ((x-4.0)/54.0)**2 + ((y-10.0)/41.0)**2 < 1.0",
    "return ((x-3.0)/63.0)**2 + ((y-18.0)/54.0)**2 < 1.0"
)

# Densify the edge forests while keeping a broad central clearing all the way toward the church.
src = src.replace("place_region(-94,-30,-40,105,180,.92,1.52,left_accept)",
                  "place_region(-94,-30,-40,110,225,.92,1.52,left_accept)")
src = src.replace("place_region(35,94,-35,108,155,.90,1.48,right_accept)",
                  "place_region(35,94,-35,112,205,.90,1.48,right_accept)")
src = src.replace("place_region(-86,86,56,150,330,.74,1.32,back_accept)",
                  "place_region(-88,88,58,154,500,.72,1.30,back_accept)")

old_back = """def back_accept(x,y):
    if ((x+6)/17.0)**2+((y-82)/10.0)**2 < 1.0:return False
    if abs(x)<27 and y<84 and rng.random()<.55:return False
    return True"""
new_back = """def back_accept(x,y):
    # Clean central opening, with forest wrapped around the outer rear hills.
    if ((x+5)/25.0)**2+((y-82)/15.0)**2 < 1.0:return False
    if abs(x)<44 and y<108 and rng.random()<.94:return False
    if abs(x)<31 and y<124 and rng.random()<.68:return False
    return True"""
if old_back not in src:
    raise RuntimeError('V12 back forest block missing')
src = src.replace(old_back,new_back)

# The reference path is only a subtle short curve near the distant church.
src = src.replace(
    "ribbon('Church_Path',[(4,19),(1,27),(-2,34),(0,41),(-3,49),(CX,CY-3.2)],.90,.06,M['path'])",
    "ribbon('Church_Path',[(8,48),(7,56),(3,64),(0,72),(CX,CY-3.2)],.68,.06,M['path'])"
)

# Move the colored tents into the visible portions of the supplied reference framing.
src = src.replace(
    "blue_pos=[(-57,-26),(-45,-25),(-33,-23),(-21,-21),(-61,-34),(-49,-35),(-37,-36),(-25,-34)]",
    "blue_pos=[(-61,5),(-50,7),(-39,8),(-28,10),(-58,-5),(-47,-3),(-36,-2),(-25,0)]"
)
src = src.replace(
    "for i,(x,y) in enumerate(blue_pos):tent('BlueTent_%02d'%i,x,y,M['blue'],.92)",
    "for i,(x,y) in enumerate(blue_pos):tent('BlueTent_%02d'%i,x,y,M['blue'],1.02)"
)
src = src.replace(
    "pink_pos=[(43,73),(48,75),(53,73),(46,69),(52,68),(58,70)]",
    "pink_pos=[(43,61),(48,63),(53,61),(46,57),(52,56),(58,58)]"
)
src = src.replace(
    "for i,(x,y) in enumerate(pink_pos):tent('PinkTent_%02d'%i,x,y,M['pink'],.76)",
    "for i,(x,y) in enumerate(pink_pos):tent('PinkTent_%02d'%i,x,y,M['pink'],.92)"
)

# Replace stretched icospheres with rounded, broad low-poly mountain domes.
old_mountains = """mountain_specs=[
    (-138,210,55,34,27),(-105,212,53,34,34),(-72,214,50,33,30),(-39,214,54,34,35),
    (-5,216,56,35,40),(30,215,54,34,35),(64,214,56,35,38),(99,212,58,34,40),(137,208,55,33,31)
]
for i,(x,y,sx,sy,sz) in enumerate(mountain_specs):
    mm=M['mountain'] if i%3!=1 else M['mountain_shadow']
    ico('Mountain_%02d'%i,(x,y,sz*.38-7.0),(sx,sy,sz),mm,2)
    # irregular pale summit volume, intentionally broad rather than a sharp cone
    ico('Mountain_Snow_%02d'%i,(x-2.0,y-1.5,sz*.69),(sx*.38,sy*.34,sz*.20),M['snow'],1)

# second distant layer to create the pale valley enclosure seen at far left/right
for i,(x,y,sx,sy,sz) in enumerate([(-158,240,70,42,27),(-90,244,72,43,25),(88,244,74,43,26),(158,238,70,41,26)]):
    ico('Mountain_Back_%02d'%i,(x,y,sz*.34-6),(sx,sy,sz),M['mountain_shadow'],2)"""

new_mountains = """def mountain_dome(name,cx,cy,rx,ry,h,seed,back=False):
    rr=random.Random(SEED+7600+seed)
    n=12
    rings=[(1.00,0.00),(.82,.24),(.61,.47),(.40,.67),(.20,.82)]
    verts=[]
    for ring,(scale,zfrac) in enumerate(rings):
        for j in range(n):
            a=2*math.pi*j/n + rr.uniform(-.035,.035)
            sx=rx*scale*(1.0+rr.uniform(-.08,.08))
            sy=ry*scale*(1.0+rr.uniform(-.07,.07))
            # slightly irregular ring heights create the soft faceted TABS silhouette
            z=-5.5+h*zfrac+rr.uniform(-.60,.60)
            verts.append((cx+sx*math.cos(a),cy+sy*math.sin(a),z))
    faces=[];fm=[]
    for ring in range(len(rings)-1):
        a0=ring*n;b0=(ring+1)*n
        for j in range(n):
            k=(j+1)%n
            faces.append((a0+j,a0+k,b0+k));fm.append((j+ring+seed)%2)
            faces.append((a0+j,b0+k,b0+j));fm.append((j+ring+1+seed)%2)
    top0=(len(rings)-1)*n
    faces.append(tuple(top0+j for j in range(n)));fm.append(seed%2)
    mats=[M['mountain_shadow'],M['mountain']] if back else [M['mountain'],M['mountain_shadow']]
    mesh_obj(name,verts,faces,mats,fm)
    if not back and seed%2==0:
        # Broad pale summit patch rather than a sharp snow cone.
        ico(name+'_Snow',(cx-1.4,cy-1.3,-5.5+h*.77),(rx*.18,ry*.15,h*.085),M['snow'],1)

front_mountains=[
    (-132,201,46,34,30),(-99,204,44,34,35),(-66,207,43,33,32),(-33,208,46,34,36),
    (1,210,48,35,39),(36,208,46,34,35),(71,206,48,35,37),(106,203,49,34,38),(140,198,45,32,31)
]
for i,spec in enumerate(front_mountains):mountain_dome('Mountain_%02d'%i,*spec,100+i,False)
back_mountains=[(-153,236,62,42,25),(-88,240,64,43,24),(82,240,65,43,25),(151,233,62,41,25)]
for i,spec in enumerate(back_mountains):mountain_dome('Mountain_Back_%02d'%i,*spec,200+i,True)"""
if old_mountains not in src:
    raise RuntimeError('V12 mountain block missing')
src = src.replace(old_mountains,new_mountains)

# The reference has very few isolated trees in the central foreground.
src = src.replace("for _ in range(24):\n    side=-1 if rng.random()<.57 else 1",
                  "for _ in range(8):\n    side=-1 if rng.random()<.57 else 1")

# Reference-like framing: huge field, small landmark, readable band of sky above mountains.
src = src.replace("render('preview_main.png',(0,-116,49),(0,47,4.8),50)",
                  "render('preview_main.png',(0,-118,47),(0,48,6.5),51)")
src = src.replace("render('preview_closer.png',(-3,-101,44),(-4,57,4.2),52)",
                  "render('preview_closer.png',(-3,-104,43),(-4,55,5.5),53)")
'''

wrapper = wrapper.replace(marker, extra + "\n" + marker)

ns={'__file__':str(v11_path),'__name__':'__main__'}
exec(compile(wrapper,str(v11_path),'exec'),ns,ns)
