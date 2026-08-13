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
# Keep the V11 color pass, but make the map read as one huge empty meadow framed by forest.
# -----------------------------------------------------------------------------

src = src.replace(
    "return ((x-4.0)/54.0)**2 + ((y-10.0)/41.0)**2 < 1.0",
    "return ((x-3.0)/63.0)**2 + ((y-18.0)/54.0)**2 < 1.0"
)

old_back = """def back_accept(x,y):
    if ((x+6)/17.0)**2+((y-82)/10.0)**2 < 1.0:return False
    if abs(x)<27 and y<84 and rng.random()<.55:return False
    return True"""
new_back = """def back_accept(x,y):
    # Broad clearing around the tiny church plus a long clean central meadow.
    if ((x+5)/24.0)**2+((y-92)/16.0)**2 < 1.0:return False
    if abs(x)<43 and y<108 and rng.random()<.93:return False
    if abs(x)<30 and y<124 and rng.random()<.66:return False
    return True"""
if old_back not in src:
    raise RuntimeError('V12 back forest block missing')
src = src.replace(old_back,new_back)

# Push the small landmark deeper into the valley and move its graveyard with it.
src = src.replace("CX,CY=-5.0,82.0", "CX,CY=-5.0,92.0")
src = src.replace("[(-12,78),(-10,80),(-13,82),(-11,84),(-15,80),(-16,83),(-9,76),(-14,76)]",
                  "[(-12,88),(-10,90),(-13,92),(-11,94),(-15,90),(-16,93),(-9,86),(-14,86)]")

# The reference path is only a faint short curve near the church, not a foreground road.
src = src.replace(
    "ribbon('Church_Path',[(4,19),(1,27),(-2,34),(0,41),(-3,49),(CX,CY-3.2)],.90,.06,M['path'])",
    "ribbon('Church_Path',[(7,55),(5,65),(1,74),(-2,83),(CX,CY-3.2)],.72,.06,M['path'])"
)

# Place the colored tents where they are visible in the supplied reference framing.
src = src.replace(
    "blue_pos=[(-57,-26),(-45,-25),(-33,-23),(-21,-21),(-61,-34),(-49,-35),(-37,-36),(-25,-34)]",
    "blue_pos=[(-61,-9),(-50,-7),(-39,-6),(-28,-5),(-58,-18),(-47,-17),(-36,-16),(-25,-15)]"
)
src = src.replace(
    "for i,(x,y) in enumerate(blue_pos):tent('BlueTent_%02d'%i,x,y,M['blue'],.92)",
    "for i,(x,y) in enumerate(blue_pos):tent('BlueTent_%02d'%i,x,y,M['blue'],1.05)"
)

# Replace the giant stretched icosphere mountains with broad sloped faceted masses.
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

new_mountains = """def mountain_mass(name,cx,cy,rx,ry,h,seed,back=False):
    rr=random.Random(SEED+7000+seed)
    n=12
    verts=[]
    # Three irregular sloped rings. There are no vertical cliff walls.
    for ring,(scale,zfrac) in enumerate([(1.0,0.0),(.63,.42),(.30,.72)]):
        for j in range(n):
            a=2*math.pi*j/n + rr.uniform(-.035,.035)
            sx=rx*scale*(1.0+rr.uniform(-.09,.09))
            sy=ry*scale*(1.0+rr.uniform(-.08,.08))
            z=-5.0 + h*zfrac + rr.uniform(-.7,.7)
            verts.append((cx+sx*math.cos(a),cy+sy*math.sin(a),z))
    peak=len(verts)
    verts.append((cx+rr.uniform(-3.0,3.0),cy+rr.uniform(-1.7,1.7),-5.0+h))
    faces=[]; fm=[]
    for ring in range(2):
        a0=ring*n; b0=(ring+1)*n
        for j in range(n):
            k=(j+1)%n
            faces.append((a0+j,a0+k,b0+k)); fm.append((j+ring+seed)%2)
            faces.append((a0+j,b0+k,b0+j)); fm.append((j+ring+1+seed)%2)
    top0=2*n
    for j in range(n):
        k=(j+1)%n
        faces.append((top0+j,top0+k,peak)); fm.append((j+seed)%2)
    mats=[M['mountain_shadow'],M['mountain']] if back else [M['mountain'],M['mountain_shadow']]
    mesh_obj(name,verts,faces,mats,fm)
    if not back and seed%2==0:
        # Small low-poly snow cap, kept well inside the mountain silhouette.
        ico(name+'_Snow',(cx-1.3,cy-1.2,-5.0+h*.84),(rx*.20,ry*.17,h*.12),M['snow'],1)

front_mountains=[
    (-126,184,47,31,30),(-94,187,44,31,37),(-62,190,43,30,33),(-29,191,46,31,38),
    (5,193,48,32,43),(40,191,46,31,37),(74,189,48,32,41),(109,186,49,31,42),(139,182,45,29,32)
]
for i,spec in enumerate(front_mountains):mountain_mass('Mountain_%02d'%i,*spec,100+i,False)
for i,spec in enumerate([(-151,218,62,39,27),(-87,223,63,40,25),(82,223,65,40,26),(150,216,62,38,27)]):
    mountain_mass('Mountain_Back_%02d'%i,*spec,200+i,True)"""
if old_mountains not in src:
    raise RuntimeError('V12 mountain block missing')
src = src.replace(old_mountains,new_mountains)

# Reduce distant central saplings: the reference meadow is conspicuously empty.
src = src.replace("for _ in range(24):\n    side=-1 if rng.random()<.57 else 1",
                  "for _ in range(10):\n    side=-1 if rng.random()<.57 else 1")

# A little more sky in the primary frame and a slightly smaller distant landmark.
src = src.replace("render('preview_main.png',(0,-116,49),(0,47,4.8),50)",
                  "render('preview_main.png',(0,-118,48),(0,52,6.0),51)")
src = src.replace("render('preview_closer.png',(-3,-101,44),(-4,57,4.2),52)",
                  "render('preview_closer.png',(-3,-104,44),(-4,61,5.0),53)")
'''

wrapper = wrapper.replace(marker, extra + "\n" + marker)

ns={'__file__':str(v11_path),'__name__':'__main__'}
exec(compile(wrapper,str(v11_path),'exec'),ns,ns)
