from pathlib import Path

v26_path=Path(__file__).with_name('build_classic_reference_v26.py')
outer=v26_path.read_text(encoding='utf-8')
outer=outer.replace('output_classic_reference_v26','output_classic_reference_v27')
outer=outer.replace('classic_reference_v26.blend','classic_reference_v27.blend')
outer=outer.replace('classic_reference_v26.glb','classic_reference_v27.glb')
outer=outer.replace('TABS Classic reference v26','TABS Classic reference v27')
outer=outer.replace("print('V26_OK'","print('V27_OK'")
outer=outer.replace('V26 pine count changed','V27 pine count changed')
outer=outer.replace('V26 MAP ONLY','V27 MAP ONLY')

start=outer.index("ridge_code=r'''")+len("ridge_code=r'''")
end=outer.index("'''\nouter=outer[:start]+ridge_code+outer[end:]",start)

ridge_code=r'''# -----------------------------------------------------------------------------
# V27 mountains: closed solid low-poly ridge with hidden rear wall, no visible roof.
# -----------------------------------------------------------------------------
def build_ridge(name,xs,front_y,shoulder_y,ridge_y,heights,mats,seed):
    rr=random.Random(SEED+seed);n=len(xs);v=[];f=[];fm=[]
    # row 0: mountain foot, buried at the back edge of the meadow
    for x in xs:v.append((x,front_y,-0.72))
    # row 1: broad foothill shoulder
    for i,x in enumerate(xs):
        h=heights[i]
        v.append((x,shoulder_y+rr.uniform(-1.4,1.4),max(.65,h*.32)+rr.uniform(-.12,.12)))
    # row 2: skyline
    for i,x in enumerate(xs):
        v.append((x,ridge_y+rr.uniform(-2.0,2.0),heights[i]+rr.uniform(-.18,.18)))
    # row 3: rear drop almost directly behind skyline; prevents any roof-like visible plane
    for i,x in enumerate(xs):
        v.append((x,ridge_y+4.0,-7.0))

    # visible front slopes
    for band in (0,1):
        a0=band*n;b0=(band+1)*n
        for i in range(n-1):
            if (i+band)%2:
                f.extend([(a0+i,a0+i+1,b0+i),(a0+i+1,b0+i+1,b0+i)])
            else:
                f.extend([(a0+i,a0+i+1,b0+i+1),(a0+i,b0+i+1,b0+i)])
            fm.extend([(i+band)%len(mats),(i+band+1)%len(mats)])
    # nearly vertical hidden rear closure
    a0=2*n;b0=3*n
    for i in range(n-1):
        f.extend([(a0+i,a0+i+1,b0+i+1),(a0+i,b0+i+1,b0+i)])
        fm.extend([0,0])
    # underside below the ground, closes the solid without entering the visible skyline
    a0=3*n;b0=0
    for i in range(n-1):
        f.extend([(a0+i,a0+i+1,b0+i+1),(a0+i,b0+i+1,b0+i)])
        fm.extend([0,0])
    # end caps
    f.extend([(0,n,2*n,3*n),(n-1,4*n-1,3*n-1,2*n-1)])
    fm.extend([0,0])
    mesh_obj(name,v,f,mats,fm)

xs=[-235,-205,-175,-145,-115,-85,-55,-25,5,35,65,95,125,155,185,215,245]
h=[5.2,6.2,7.8,9.3,8.6,10.2,11.5,10.8,13.2,11.8,10.5,12.7,11.1,9.5,8.0,6.5,5.3]
build_ridge('MountainFront',xs,170,218,286,h,[M['mountain'],M['mountain2']],9100)

# A very subtle second silhouette only in gaps behind the first.
xs2=[-250,-210,-170,-130,-90,-50,-10,30,70,110,150,190,230,260]
h2=[3.6,4.5,5.6,6.7,6.1,7.2,8.0,7.4,8.7,7.6,6.6,5.8,4.5,3.5]
build_ridge('MountainBack',xs2,288,326,378,h2,[M['mountain2']],9200)

'''
outer=outer[:start]+ridge_code+outer[end:]
outer=outer.replace('Mountain style: distant broad sloped skyline','Mountain style: closed low-poly ridge with hidden rear wall')

ns={'__file__':str(v26_path),'__name__':'__main__'}
exec(compile(outer,str(v26_path),'exec'),ns,ns)
