from pathlib import Path

v24_path=Path(__file__).with_name('build_classic_reference_v24.py')
outer=v24_path.read_text(encoding='utf-8')

# Preserve the complete V24 map-only/tree layout and only replace the mountain construction.
outer=outer.replace('output_classic_reference_v24','output_classic_reference_v26')
outer=outer.replace('classic_reference_v24.blend','classic_reference_v26.blend')
outer=outer.replace('classic_reference_v24.glb','classic_reference_v26.glb')
outer=outer.replace('TABS Classic reference v24','TABS Classic reference v26')
outer=outer.replace("print('V24_OK'","print('V26_OK'")
outer=outer.replace('V24 pine count changed','V26 pine count changed')
outer=outer.replace('V24 MAP ONLY','V26 MAP ONLY')

start=outer.index("new_mountains=r'''")+len("new_mountains=r'''")
end=outer.index("'''\nsrc=src[:mount_start]+new_mountains+src[mount_end:]",start)

ridge_code=r'''# -----------------------------------------------------------------------------
# V26 mountains: distant broad skyline, low peaks, sloped fronts, visible sky above.
# -----------------------------------------------------------------------------
def build_ridge(name,xs,front_y,shoulder_y,ridge_y,back_y,heights,mats,seed):
    rr=random.Random(SEED+seed);n=len(xs);v=[];f=[];fm=[]
    for x in xs:v.append((x,front_y,-0.72))
    for i,x in enumerate(xs):
        h=heights[i]
        v.append((x,shoulder_y+rr.uniform(-1.8,1.8),max(.7,h*.33)+rr.uniform(-.18,.18)))
    for i,x in enumerate(xs):
        v.append((x,ridge_y+rr.uniform(-2.5,2.5),heights[i]+rr.uniform(-.25,.25)))
    for x in xs:v.append((x,back_y,-3.5))
    for band in range(3):
        a0=band*n;b0=(band+1)*n
        for i in range(n-1):
            if (i+band)%2:
                f.extend([(a0+i,a0+i+1,b0+i),(a0+i+1,b0+i+1,b0+i)])
            else:
                f.extend([(a0+i,a0+i+1,b0+i+1),(a0+i,b0+i+1,b0+i)])
            fm.extend([(i+band)%len(mats),(i+band+1)%len(mats)])
    mesh_obj(name,v,f,mats,fm)

xs=[-235,-205,-175,-145,-115,-85,-55,-25,5,35,65,95,125,155,185,215,245]
h=[6.5,7.5,9.2,11.0,10.2,12.2,14.0,13.2,16.3,14.5,13.1,15.8,13.7,11.8,10.0,8.0,6.5]
build_ridge('MountainFront',xs,170,215,284,360,h,[M['mountain'],M['mountain2']],8100)

xs2=[-250,-215,-180,-145,-110,-75,-40,-5,30,65,100,135,170,205,240]
h2=[4.5,5.5,6.8,8.0,7.4,8.9,9.8,9.0,10.6,9.5,8.4,9.2,7.8,6.0,4.7]
build_ridge('MountainBack',xs2,274,316,366,445,h2,[M['mountain2']],8200)

'''
outer=outer[:start]+ridge_code+outer[end:]
outer=outer.replace('Mountain style: connected low-poly terrain range','Mountain style: distant broad sloped skyline')

ns={'__file__':str(v24_path),'__name__':'__main__'}
exec(compile(outer,str(v24_path),'exec'),ns,ns)
