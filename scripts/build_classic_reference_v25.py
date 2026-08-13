from pathlib import Path

v24_path = Path(__file__).with_name('build_classic_reference_v24.py')
outer = v24_path.read_text(encoding='utf-8')

outer = outer.replace('output_classic_reference_v24','output_classic_reference_v25')
outer = outer.replace('classic_reference_v24.blend','classic_reference_v25.blend')
outer = outer.replace('classic_reference_v24.glb','classic_reference_v25.glb')
outer = outer.replace('TABS Classic reference v24','TABS Classic reference v25')
outer = outer.replace("print('V24_OK'", "print('V25_OK'")
outer = outer.replace('V24 exact rebuild count', 'V25 exact rebuild count')
outer = outer.replace('V24 pine count changed', 'V25 pine count changed')
outer = outer.replace('V24 MAP ONLY', 'V25 MAP ONLY')

# Replace the V24 mountain blob source-injection with a true connected terrain heightfield.
start = outer.index("new_mountains = r'''", outer.index('# Mountains:'))
body_start = start + len("new_mountains = r'''")
end = outer.index("'''\nsrc = src[:mount_start] + new_mountains + src[mount_end:]", body_start)

terrain_code = r'''# -----------------------------------------------------------------------------
# V25 mountain range: connected low-poly terrain rising gradually from the valley.
# No vertical cut, no giant sphere wall, no repeated sharp teeth.
# -----------------------------------------------------------------------------
def mountain_heightfield(name, xmin, xmax, ymin, ymax, nx, ny, peaks, mats, seed):
    rr = random.Random(SEED + seed)
    verts=[]; faces=[]; fm=[]
    for j in range(ny+1):
        ty=j/ny; y=ymin+(ymax-ymin)*ty
        # front blend starts at ground level, back blend gently lowers again
        front_blend = min(1.0, max(0.0, (ty-0.02)/0.28))
        back_blend = 1.0 if ty < .78 else max(.35, 1.0-(ty-.78)/.22*.65)
        for i in range(nx+1):
            tx=i/nx; x=xmin+(xmax-xmin)*tx
            h=0.0
            # max of broad gaussian masses gives distinct mountains with wide saddles
            for cx,cy,ph,sx,sy in peaks:
                dx=(x-cx)/sx; dy=(y-cy)/sy
                hh=ph*math.exp(-0.5*(dx*dx+dy*dy))
                if hh>h: h=hh
            # subtle deterministic faceting without noisy spikes
            wob=(rr.random()-.5)*0.55*(0.25+0.75*front_blend)
            z=-0.55 + h*front_blend*back_blend + wob
            if j==0: z=-0.60
            verts.append((x,y,z))
    row=nx+1
    for j in range(ny):
        for i in range(nx):
            a=j*row+i; b=a+1; c=a+row+1; d=a+row
            # alternating diagonals make broad low-poly facets
            if (i+j)%2:
                faces.extend([(a,b,d),(b,c,d)])
            else:
                faces.extend([(a,b,c),(a,c,d)])
            fm.extend([(i+j)%len(mats),(i+j+1)%len(mats)])
    return mesh_obj(name,verts,faces,mats,fm)

front_peaks=[
    (-176,245,15,62,58),(-139,246,20,63,60),(-96,250,18,58,58),
    (-52,255,24,66,63),(-6,260,29,72,66),(43,257,24,66,63),
    (88,252,26,65,61),(132,248,20,62,59),(174,244,16,60,56)
]
mountain_heightfield('MountainRangeFront',-225,225,150,350,24,11,front_peaks,[M['mountain'],M['mountain2']],6100)

back_peaks=[
    (-185,338,14,78,72),(-110,342,18,82,74),(-32,345,20,86,76),
    (52,344,18,84,75),(130,340,17,80,72),(190,336,13,72,68)
]
mountain_heightfield('MountainRangeBack',-235,235,255,440,22,9,back_peaks,[M['mountain2'],M['mountain']],6200)

'''
outer = outer[:body_start] + terrain_code + outer[end:]
outer = outer.replace('Mountain style: broad overlapping TABS-like masses', 'Mountain style: connected low-poly terrain range')

ns={'__file__':str(v24_path),'__name__':'__main__'}
exec(compile(outer,str(v24_path),'exec'),ns,ns)
