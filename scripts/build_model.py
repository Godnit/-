import bpy
import bmesh
import math
import os
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) if '__file__' in globals() else os.getcwd()
OUT = os.path.join(ROOT, 'output')
os.makedirs(OUT, exist_ok=True)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'METERS'
scene.unit_settings.scale_length = 1.0
scene.render.resolution_x = 768
scene.render.resolution_y = 768
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
if bpy.app.version >= (4, 2, 0):
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
else:
    scene.render.engine = 'BLENDER_EEVEE'

def make_mat(name, color, roughness=0.65, metallic=0.0, alpha=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    if 'Alpha' in bsdf.inputs:
        bsdf.inputs['Alpha'].default_value = alpha
    m.diffuse_color = (*color, alpha)
    return m

MAT = {
    'Wall_Main': make_mat('Wall_Main', (0.90, 0.875, 0.79), 0.82),
    'Trim_White': make_mat('Trim_White', (0.97, 0.965, 0.93), 0.68),
    'Roof_Blue': make_mat('Roof_Blue', (0.045, 0.19, 0.36), 0.62),
    'Roof_Blue_Light': make_mat('Roof_Blue_Light', (0.07, 0.25, 0.47), 0.62),
    'Wood': make_mat('Wood', (0.42, 0.20, 0.085), 0.7),
    'Wood_Light': make_mat('Wood_Light', (0.62, 0.31, 0.12), 0.7),
    'Glass': make_mat('Glass', (0.16, 0.34, 0.42), 0.2, 0.0, 0.75),
    'Brick': make_mat('Brick', (0.64, 0.34, 0.14), 0.82),
    'Brick_Light': make_mat('Brick_Light', (0.77, 0.49, 0.24), 0.82),
    'Stone': make_mat('Stone', (0.58, 0.48, 0.39), 0.84),
    'Path': make_mat('Path', (0.69, 0.61, 0.51), 0.88),
    'Grass': make_mat('Grass', (0.28, 0.52, 0.075), 0.9),
    'Shrub': make_mat('Shrub', (0.22, 0.47, 0.055), 0.9),
    'Shrub_Light': make_mat('Shrub_Light', (0.34, 0.60, 0.075), 0.9),
    'Tree_Dark': make_mat('Tree_Dark', (0.18, 0.38, 0.035), 0.9),
    'Flower_Pink': make_mat('Flower_Pink', (0.88, 0.40, 0.55), 0.75),
    'Flower_Yellow': make_mat('Flower_Yellow', (0.95, 0.70, 0.10), 0.75),
    'Flower_White': make_mat('Flower_White', (0.92, 0.90, 0.82), 0.75),
    'Dark': make_mat('Dark', (0.025, 0.025, 0.025), 0.8),
}

def assign(obj, material):
    if obj.data and hasattr(obj.data, 'materials'):
        obj.data.materials.clear(); obj.data.materials.append(material)

def apply_bevel(obj, width=0.025, segments=2):
    if width <= 0: return
    mod = obj.modifiers.new('Bevel', 'BEVEL'); mod.width = width; mod.segments = segments; mod.limit_method = 'ANGLE'
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)

def box(name, loc, dims, material, bevel=0.018, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    obj = bpy.context.object; obj.name = name; obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, material)
    if bevel: apply_bevel(obj, bevel, 2)
    return obj

def cylinder(name, loc, radius, depth, material, vertices=20, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    obj=bpy.context.object; obj.name=name; assign(obj, material)
    if bevel: apply_bevel(obj, bevel, 2)
    return obj

def ico(name, loc, radius, material, subdivisions=2, scale=(1,1,1)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=radius, location=loc)
    obj=bpy.context.object; obj.name=name; obj.scale=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True); assign(obj, material); return obj

def mesh_obj(name, verts, faces, material, bevel=0.0):
    me=bpy.data.meshes.new(name+'_Mesh'); me.from_pydata(verts, [], faces); me.validate(verbose=False); me.update()
    obj=bpy.data.objects.new(name, me); bpy.context.collection.objects.link(obj); assign(obj, material)
    if bevel: apply_bevel(obj, bevel, 2)
    return obj

def tri_prism(name, x0, x1, z0, zpeak, y0, y1, material):
    xc=(x0+x1)*0.5
    verts=[(x0,y0,z0),(x1,y0,z0),(xc,y0,zpeak),(x0,y1,z0),(x1,y1,z0),(xc,y1,zpeak)]
    faces=[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)]
    return mesh_obj(name,verts,faces,material)

def sloped_box(name,p0,p1,width_y,thickness,material,y_center=0.0,bevel=0.012):
    p0=Vector(p0); p1=Vector(p1); d=p1-p0; length=d.length; mid=(p0+p1)*0.5; theta=math.atan2(d.z,d.x)
    return box(name,(mid.x,y_center,mid.z),(length,width_y,thickness),material,bevel,rot=(0,-theta,0))

def roof_panel_x(name,x_eave,x_ridge,y_center,y_depth,z_eave,z_ridge,material):
    return sloped_box(name,(x_eave,0,z_eave),(x_ridge,0,z_ridge),y_depth,0.12,material,y_center)

def roof_shingles_x(prefix,x_eave,x_ridge,y_center,y_depth,z_eave,z_ridge,rows=7,cols=10):
    p0=Vector((x_eave,y_center,z_eave)); p1=Vector((x_ridge,y_center,z_ridge)); d=p1-p0; L=d.length; u=d.normalized(); theta=math.atan2(d.z,d.x)
    tile_len=L/rows*0.92; tile_w=y_depth/cols*0.88
    for r in range(rows):
        s=(r+0.48)*L/rows
        for c in range(cols):
            y=y_center-y_depth/2+(c+0.5)*y_depth/cols; base=p0+u*s
            box(f'{prefix}_{r:02d}_{c:02d}',(base.x,y,base.z+0.055),(tile_len,tile_w,0.055),MAT['Roof_Blue_Light'],0.016,rot=(0,-theta,0))

def roof_panel_y(name,y_eave,y_ridge,x_center,x_depth,z_eave,z_ridge,material):
    p0=Vector((0,y_eave,z_eave)); p1=Vector((0,y_ridge,z_ridge)); d=p1-p0; length=d.length; mid=(p0+p1)/2; theta=math.atan2(d.z,d.y)
    return box(name,(x_center,mid.y,mid.z),(x_depth,length,0.12),material,0.012,rot=(theta,0,0))

def roof_shingles_y(prefix,y_eave,y_ridge,x_center,x_depth,z_eave,z_ridge,rows=5,cols=6):
    p0=Vector((x_center,y_eave,z_eave)); p1=Vector((x_center,y_ridge,z_ridge)); d=p1-p0; L=d.length; u=d.normalized(); theta=math.atan2(d.z,d.y)
    tile_len=L/rows*0.9; tile_w=x_depth/cols*0.86
    for r in range(rows):
        s=(r+0.48)*L/rows
        for c in range(cols):
            x=x_center-x_depth/2+(c+0.5)*x_depth/cols; base=p0+u*s
            box(f'{prefix}_{r:02d}_{c:02d}',(x,base.y,base.z+0.055),(tile_w,tile_len,0.055),MAT['Roof_Blue_Light'],0.014,rot=(theta,0,0))

def window_front(prefix,x,y,z,w,h,shutters=None):
    box(prefix+'_Frame',(x,y,z),(w,0.10,h),MAT['Trim_White'],0.016); box(prefix+'_Glass',(x,y-0.055,z),(w*0.78,0.035,h*0.78),MAT['Glass'],0.006)
    box(prefix+'_MullionV',(x,y-0.075,z),(0.055,0.055,h*0.78),MAT['Trim_White'],0.006); box(prefix+'_MullionH',(x,y-0.075,z),(w*0.78,0.055,0.055),MAT['Trim_White'],0.006)
    box(prefix+'_Sill',(x,y-0.11,z-h*0.52),(w*1.05,0.17,0.10),MAT['Trim_White'],0.012)
    if shutters:
        mat=MAT[shutters]; box(prefix+'_ShutterL',(x-w*0.62,y-0.08,z),(w*0.20,0.09,h*0.92),mat,0.012); box(prefix+'_ShutterR',(x+w*0.62,y-0.08,z),(w*0.20,0.09,h*0.92),mat,0.012)

def window_side(prefix,x,y,z,w,h):
    box(prefix+'_Frame',(x,y,z),(0.10,w,h),MAT['Trim_White'],0.016); box(prefix+'_Glass',(x+0.055,y,z),(0.035,w*0.78,h*0.78),MAT['Glass'],0.006)
    box(prefix+'_MullionV',(x+0.075,y,z),(0.055,0.055,h*0.78),MAT['Trim_White'],0.006); box(prefix+'_MullionH',(x+0.075,y,z),(0.055,w*0.78,0.055),MAT['Trim_White'],0.006)
    box(prefix+'_Sill',(x+0.11,y,z-h*0.52),(0.17,w*1.05,0.10),MAT['Trim_White'],0.012)

def porch_railing_x(prefix,x0,x1,y,z=0.86):
    L=x1-x0; box(prefix+'_Top',((x0+x1)/2,y,z+0.35),(L,0.075,0.10),MAT['Trim_White'],0.01); box(prefix+'_Bottom',((x0+x1)/2,y,z-0.18),(L,0.07,0.08),MAT['Trim_White'],0.01)
    n=max(2,int(L/0.22))
    for i in range(n+1): box(f'{prefix}_Bal_{i:02d}',(x0+i*L/n,y,z+0.05),(0.055,0.055,0.55),MAT['Trim_White'],0.008)

def porch_railing_y(prefix,y0,y1,x,z=0.86):
    L=y1-y0; box(prefix+'_Top',(x,(y0+y1)/2,z+0.35),(0.075,L,0.10),MAT['Trim_White'],0.01); box(prefix+'_Bottom',(x,(y0+y1)/2,z-0.18),(0.07,L,0.08),MAT['Trim_White'],0.01)
    n=max(2,int(L/0.22))
    for i in range(n+1): box(f'{prefix}_Bal_{i:02d}',(x,y0+i*L/n,z+0.05),(0.055,0.055,0.55),MAT['Trim_White'],0.008)

def bush(prefix,loc,radius=0.28,light=False):
    mat=MAT['Shrub_Light'] if light else MAT['Shrub']; x,y,z=loc
    ico(prefix+'_A',(x,y,z),radius,mat,2,(1.0,0.9,0.9)); ico(prefix+'_B',(x+radius*0.45,y+radius*0.10,z+radius*0.15),radius*0.72,mat,2); ico(prefix+'_C',(x-radius*0.40,y-radius*0.08,z+radius*0.10),radius*0.68,mat,2)

def tree(prefix,x,y,scale=1.0):
    cylinder(prefix+'_Trunk',(x,y,0.78*scale),0.12*scale,1.20*scale,MAT['Wood'],18,0.015); base_z=1.55*scale
    clumps=[(0,0,0.48),(0.32,0.08,0.34),(-0.30,0.10,0.35),(0.10,-0.28,0.33),(-0.16,-0.22,0.31),(0.05,0.18,0.32)]
    for i,(ox,oy,r) in enumerate(clumps): ico(f'{prefix}_Leaf_{i:02d}',(x+ox*scale,y+oy*scale,base_z+(0.15 if i==0 else 0)*scale),r*scale,MAT['Tree_Dark'] if i%3==0 else MAT['Shrub_Light'],2)

def flower_cluster(prefix,x,y,matname='Flower_Pink'):
    bush(prefix+'_Bush',(x,y,0.38),0.22,True)
    for i,(ox,oy) in enumerate([(-0.08,-0.06),(0.08,-0.03),(-0.02,0.08),(0.10,0.10)]): ico(f'{prefix}_Flower_{i}',(x+ox,y+oy,0.60),0.045,MAT[matname],1)

box('Base_Soil',(0,0,0.10),(9.4,8.9,0.35),MAT['Stone'],0.16)
box('Base_Grass',(0,0,0.31),(9.05,8.55,0.22),MAT['Grass'],0.13)
for i in range(5): box(f'Path_Slab_{i}',(-2.10,-3.48+i*0.52,0.46),(1.02,0.46,0.10),MAT['Path'],0.035)
for i in range(3): box(f'Path_Side_{i}',(-1.55+i*0.55,-1.48,0.455),(0.50,0.62,0.08),MAT['Path'],0.025)

box('Foundation_Main',(-0.45,0.15,0.58),(4.25,4.55,0.38),MAT['Stone'],0.035)
box('Building_Main',(-0.45,0.15,2.00),(4.15,4.45,2.75),MAT['Wall_Main'],0.025)
tri_prism('Gable_Front',-2.525,1.625,3.375,5.18,-2.095,-2.00,MAT['Wall_Main'])
tri_prism('Gable_Back',-2.525,1.625,3.375,5.18,2.30,2.395,MAT['Wall_Main'])
for i,z in enumerate([0.92,1.18,1.44,1.70,1.96,2.22,2.48,2.74,3.00,3.25]): box(f'Siding_Front_{i:02d}',(-0.45,-2.095,z),(4.05,0.025,0.035),MAT['Trim_White'],0.004)
for i,z in enumerate([3.48,3.72,3.96,4.20,4.44,4.68]):
    half=max(0.28,1.8-(z-3.4)*0.75); box(f'Siding_Gable_{i:02d}',(-0.45,-2.115,z),(half*2,0.025,0.032),MAT['Trim_White'],0.003)
window_front('Window_Front_Lower',-1.13,-2.17,1.78,1.18,1.15,'Wood')
window_front('Window_Front_Upper',-1.13,-2.17,3.72,0.90,0.92,'Roof_Blue')
box('Window_Awning_Bar',(-1.13,-2.32,2.43),(1.52,0.24,0.13),MAT['Wood_Light'],0.025,rot=(math.radians(-12),0,0))
box('Door_Main',(0.72,-2.17,1.40),(0.78,0.10,1.65),MAT['Wood_Light'],0.018)
box('Door_Frame_Top',(0.72,-2.23,2.28),(0.95,0.10,0.10),MAT['Trim_White'],0.01); box('Door_Frame_L',(0.25,-2.23,1.42),(0.10,0.10,1.75),MAT['Trim_White'],0.01); box('Door_Frame_R',(1.19,-2.23,1.42),(0.10,0.10,1.75),MAT['Trim_White'],0.01)
for ix in [-0.17,0.0,0.17]: box(f'Door_Glass_{ix}',(0.72+ix,-2.235,1.80),(0.11,0.035,0.34),MAT['Glass'],0.004)

xL=-2.75; xR=1.85; xr=-0.45; z_e=3.32; z_r=5.35; ymid=0.15; ydepth=4.95
roof_panel_x('Roof_Main_Left',xL,xr,ymid,ydepth,z_e,z_r,MAT['Roof_Blue']); roof_panel_x('Roof_Main_Right',xR,xr,ymid,ydepth,z_e,z_r,MAT['Roof_Blue'])
roof_shingles_x('Tile_Main_Left',xL,xr,ymid,ydepth,z_e,z_r,8,11); roof_shingles_x('Tile_Main_Right',xR,xr,ymid,ydepth,z_e,z_r,8,11)
box('Roof_Main_Ridge',(xr,ymid,z_r+0.07),(0.18,ydepth+0.12,0.18),MAT['Roof_Blue_Light'],0.06)

box('Porch_Deck_Front',(1.60,-2.52,0.72),(2.35,1.06,0.18),MAT['Path'],0.035); box('Porch_Deck_Side',(2.22,-0.65,0.72),(1.10,2.75,0.18),MAT['Path'],0.035)
box('Porch_Step_1',(0.82,-3.20,0.50),(1.10,0.42,0.16),MAT['Path'],0.025); box('Porch_Step_2',(0.82,-2.91,0.62),(0.98,0.38,0.14),MAT['Path'],0.025)
box('Porch_Side_Step_1',(2.88,0.65,0.50),(0.42,0.92,0.16),MAT['Path'],0.025); box('Porch_Side_Step_2',(2.63,0.65,0.62),(0.34,0.82,0.14),MAT['Path'],0.025)
roof_panel_x('Roof_Porch_Side',3.15,1.25,-0.38,4.10,2.75,3.65,MAT['Roof_Blue']); roof_shingles_x('Tile_Porch_Side',3.15,1.25,-0.38,4.10,2.75,3.65,5,10)
post_xy=[(0.55,-2.92),(1.55,-2.92),(2.55,-2.92),(2.90,-1.70),(2.90,-0.55),(2.90,0.65)]
for i,(x,y) in enumerate(post_xy):
    box(f'Porch_Post_{i:02d}',(x,y,1.67),(0.16,0.16,1.98),MAT['Trim_White'],0.018); box(f'Porch_Post_Base_{i:02d}',(x,y,0.82),(0.24,0.24,0.25),MAT['Trim_White'],0.018); box(f'Porch_Post_Cap_{i:02d}',(x,y,2.61),(0.23,0.23,0.15),MAT['Trim_White'],0.018)
box('Porch_Beam_Front',(1.55,-2.92,2.64),(2.15,0.16,0.18),MAT['Trim_White'],0.018); box('Porch_Beam_Side',(2.90,-0.52,2.64),(0.16,2.55,0.18),MAT['Trim_White'],0.018)
porch_railing_x('Railing_Front_L',0.50,0.65,-2.92); porch_railing_x('Railing_Front_R',1.28,2.65,-2.92); porch_railing_y('Railing_Side_A',-2.52,-1.15,2.90); porch_railing_y('Railing_Side_B',-0.70,0.30,2.90)
roof_panel_y('Roof_Porch_Gable_Front',-3.10,-2.60,0.78,1.65,2.73,3.15,MAT['Roof_Blue']); roof_panel_y('Roof_Porch_Gable_Back',-2.10,-2.60,0.78,1.65,2.73,3.15,MAT['Roof_Blue'])
roof_shingles_y('Tile_Porch_Gable_Front',-3.10,-2.60,0.78,1.65,2.73,3.15,3,5); roof_shingles_y('Tile_Porch_Gable_Back',-2.10,-2.60,0.78,1.65,2.73,3.15,3,5)
box('Roof_Porch_Gable_Ridge',(0.78,-2.60,3.22),(1.78,0.15,0.15),MAT['Roof_Blue_Light'],0.05)

box('Dormer_Body',(1.16,0.55,4.15),(1.20,1.34,1.18),MAT['Wall_Main'],0.018)
roof_panel_y('Dormer_Roof_A',-0.30,0.55,1.18,1.55,4.43,5.05,MAT['Roof_Blue']); roof_panel_y('Dormer_Roof_B',1.40,0.55,1.18,1.55,4.43,5.05,MAT['Roof_Blue'])
roof_shingles_y('Dormer_Tile_A',-0.30,0.55,1.18,1.55,4.43,5.05,4,5); roof_shingles_y('Dormer_Tile_B',1.40,0.55,1.18,1.55,4.43,5.05,4,5)
box('Dormer_Ridge',(1.18,0.55,5.11),(1.65,0.14,0.14),MAT['Roof_Blue_Light'],0.05); window_side('Window_Dormer',1.80,0.55,4.23,0.76,0.82); window_side('Window_Right',1.67,-0.25,1.62,0.90,1.02)

box('Chimney_Main',(0.72,1.45,5.55),(0.56,0.56,2.35),MAT['Brick'],0.012)
for i,z in enumerate([4.70,4.95,5.20,5.45,5.70,5.95,6.20,6.45]): box(f'Chimney_Mortar_{i:02d}',(0.72,1.455,z),(0.59,0.59,0.028),MAT['Brick_Light'],0.003)
box('Chimney_Cap',(0.72,1.45,6.78),(0.75,0.75,0.18),MAT['Stone'],0.025); box('Chimney_Flue',(0.72,1.45,6.89),(0.38,0.38,0.16),MAT['Dark'],0.015)

def picket(prefix,x,y,along='x'):
    if along=='x':
        box(prefix,(x,y,0.91),(0.10,0.08,0.95),MAT['Trim_White'],0.018); verts=[(x-0.05,y-0.04,1.385),(x+0.05,y-0.04,1.385),(x,y-0.04,1.52),(x-0.05,y+0.04,1.385),(x+0.05,y+0.04,1.385),(x,y+0.04,1.52)]
    else:
        box(prefix,(x,y,0.91),(0.08,0.10,0.95),MAT['Trim_White'],0.018); verts=[(x-0.04,y-0.05,1.385),(x+0.04,y-0.05,1.385),(x,y,1.52),(x-0.04,y+0.05,1.385),(x+0.04,y+0.05,1.385),(x,y,1.52)]
    faces=[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)]; mesh_obj(prefix+'_Tip',verts,faces,MAT['Trim_White'])

front_y=-4.05
for i,x in enumerate([-4.0+i*0.34 for i in range(25)]):
    if not (-2.72 < x < -1.50): picket(f'Fence_Front_{i:02d}',x,front_y,'x')
box('Fence_Front_Rail_L',(-3.35,front_y,0.95),(1.25,0.07,0.09),MAT['Trim_White'],0.008); box('Fence_Front_Rail_L2',(-3.35,front_y,1.18),(1.25,0.07,0.09),MAT['Trim_White'],0.008)
box('Fence_Front_Rail_R',(1.15,front_y,0.95),(5.00,0.07,0.09),MAT['Trim_White'],0.008); box('Fence_Front_Rail_R2',(1.15,front_y,1.18),(5.00,0.07,0.09),MAT['Trim_White'],0.008)
right_x=4.18
for i,y in enumerate([-3.72+i*0.36 for i in range(22)]): picket(f'Fence_Right_{i:02d}',right_x,y,'y')
box('Fence_Right_Rail',(right_x,-0.05,0.95),(0.07,7.35,0.09),MAT['Trim_White'],0.008); box('Fence_Right_Rail2',(right_x,-0.05,1.18),(0.07,7.35,0.09),MAT['Trim_White'],0.008)
for i,(x,y) in enumerate([(-4.10,front_y),(-2.82,front_y),(-1.42,front_y),(4.18,front_y),(4.18,3.80)]): box(f'Fence_Post_{i:02d}',(x,y,0.93),(0.18,0.18,1.12),MAT['Trim_White'],0.022); box(f'Fence_Post_Cap_{i:02d}',(x,y,1.52),(0.24,0.24,0.12),MAT['Trim_White'],0.018)

for i,x in enumerate([-3.65,-3.15,-2.65]): box(f'Hedge_LeftFront_{i}',(x,-3.05,0.78),(0.48,0.52,0.58),MAT['Shrub'],0.16)
for i,y in enumerate([-2.45,-1.90,-1.35,-0.80]): box(f'Hedge_LeftSide_{i}',(-3.70,y,0.78),(0.52,0.48,0.58),MAT['Shrub'],0.16)
for args in [('Tree_Left',-3.72,0.15,1.0),('Tree_BackLeft',-3.20,2.55,0.85),('Tree_Right',3.75,1.95,0.90)]: tree(*args)
shrubs=[(-2.50,-1.75,0.28),(-2.10,-1.60,0.26),(-1.60,-1.55,0.24),(-0.10,-1.52,0.26),(1.85,-3.05,0.27),(2.35,-3.00,0.25),(3.15,-2.45,0.28),(3.35,-1.65,0.30),(3.35,-0.85,0.27),(3.35,0.35,0.27),(2.70,1.20,0.26),(-2.40,2.65,0.25)]
for i,(x,y,r) in enumerate(shrubs): bush(f'Shrub_{i:02d}',(x,y,0.58),r,i%2==0)
for i,(x,y,mat) in enumerate([(-2.25,-1.35,'Flower_Pink'),(-1.55,-1.30,'Flower_White'),(-0.35,-1.37,'Flower_Yellow'),(1.35,-3.15,'Flower_Pink'),(2.78,-2.78,'Flower_White'),(3.48,-1.20,'Flower_Pink'),(3.25,0.80,'Flower_Yellow')]): flower_cluster(f'FlowerBed_{i:02d}',x,y,mat)

for obj in [o for o in bpy.context.scene.objects if o.type=='MESH']:
    bpy.context.view_layer.objects.active=obj; obj.select_set(True); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bm=bmesh.new(); bm.from_mesh(obj.data); bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-6); bmesh.ops.recalc_face_normals(bm,faces=bm.faces); bm.to_mesh(obj.data); bm.free(); obj.data.update(); obj.select_set(False)

def look_at(obj,target): obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
scene.world.color=(0.88,0.85,0.78)
try:
    scene.world.use_nodes=True; bg=scene.world.node_tree.nodes.get('Background'); bg.inputs['Color'].default_value=(0.90,0.87,0.80,1); bg.inputs['Strength'].default_value=0.8
except Exception: pass
bpy.ops.object.light_add(type='AREA',location=(5.5,-6.5,10.5)); key=bpy.context.object; key.name='Light_Key'; key.data.energy=1050; key.data.shape='DISK'; key.data.size=5.5; look_at(key,(0,0,2.2))
bpy.ops.object.light_add(type='AREA',location=(-5.0,-1.0,7.0)); fill=bpy.context.object; fill.name='Light_Fill'; fill.data.energy=500; fill.data.size=6.0; look_at(fill,(0,0,2.0))
bpy.ops.object.light_add(type='SUN',location=(0,0,8)); sun=bpy.context.object; sun.name='Light_Sun'; sun.data.energy=1.6; sun.rotation_euler=(math.radians(25),math.radians(-20),math.radians(-30))
box('Backdrop_Floor',(0,0,-0.18),(18,18,0.15),make_mat('Backdrop',(0.86,0.83,0.76),0.9),0.04)
bpy.ops.object.camera_add(location=(10.0,-12.0,10.0)); cam=bpy.context.object; cam.name='Camera'; scene.camera=cam; cam.data.type='ORTHO'; cam.data.ortho_scale=11.0; cam.data.lens=48; look_at(cam,(0,0,2.2))

blend_path=os.path.join(OUT,'model.blend'); bpy.ops.wm.save_as_mainfile(filepath=blend_path)
for o in bpy.context.scene.objects: o.select_set(False)
for o in bpy.context.scene.objects:
    if o.type=='MESH' and o.name!='Backdrop_Floor': o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'model.glb'),export_format='GLB',use_selection=True,export_apply=True)
views={'preview_perspective.png':((10,-12,10),(0,0,2.2),11.0),'preview_front.png':((0,-14,5.0),(-0.3,0,2.2),10.3),'preview_back.png':((0,14,5.0),(-0.3,0,2.2),10.3),'preview_left.png':((-14,0,5.0),(0,0,2.2),10.3),'preview_right.png':((14,0,5.0),(0,0,2.2),10.3),'preview_top.png':((0,0,16),(0,0,0),10.7)}
for filename,(pos,target,scale) in views.items():
    cam.location=pos; cam.data.ortho_scale=scale; look_at(cam,target); scene.render.filepath=os.path.join(OUT,filename); bpy.ops.render.render(write_still=True)
cam.location=(10,-12,10); cam.data.ortho_scale=11.0; look_at(cam,(0,0,2.2)); bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print('BUILD_COMPLETE')
