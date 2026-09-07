extends Node3D

const LEVELS := 20
const SAVE := "user://portal_gates.save"
const SPEED := 4.8
const GRAVITY := 18.0
const JUMP := 6.0
const LOOK := 0.0045

var root3d: Node3D
var player: CharacterBody3D
var cam: Camera3D
var ui: Control
var portal_a: Node3D
var portal_b: Node3D
var view_a: SubViewport
var view_b: SubViewport
var pcam_a: Camera3D
var pcam_b: Camera3D
var exit_area: Area3D
var exit_visual: Node3D
var cubes: Array[RigidBody3D] = []
var switches: Array[Area3D] = []
var lasers: Array[Node3D] = []
var movers: Array[AnimatableBody3D] = []
var hazards: Array[Area3D] = []
var unlocked := 1
var level := 1
var level_time := 0.0
var required := 0
var won := false
var portal_cd := 0.0
var held: RigidBody3D
var move_vec := Vector2.ZERO
var look_id := -1
var move_id := -1
var last_look := Vector2.ZERO
var pitch := -0.12
var level_label: Label
var objective: Label
var time_label: Label
var toast: Label
var menu: Control
var select: Control
var mats := {}

func _ready():
    _make_mats()
    unlocked = _load_save()
    _loading()

func _make_mats():
    mats.floor = _mat("#263244")
    mats.wall = _mat("#354257")
    mats.trim = _mat("#8ca0b7")
    mats.cube = _mat("#d8e7f6")
    mats.a = _glow("#2bdcff")
    mats.b = _glow("#ff9d42")
    mats.danger = _glow("#ff3d5f")
    mats.goal = _glow("#7dffae")

func _mat(c):
    var m=StandardMaterial3D.new(); m.albedo_color=Color(c); m.roughness=.72; return m
func _glow(c):
    var m=_mat(c); m.emission_enabled=true; m.emission=Color(c); m.emission_energy_multiplier=2.5; return m

func _loading():
    var layer=Control.new(); layer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); add_child(layer)
    var bg=ColorRect.new(); bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); bg.color=Color("#050a12"); layer.add_child(bg)
    var title=Label.new(); title.text="PORTAL GATES"; title.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER; title.add_theme_font_size_override("font_size",46); title.position=Vector2(0,220); title.size=Vector2(1280,70); layer.add_child(title)
    var sub=Label.new(); sub.text="INITIALIZING CHAMBERS..."; sub.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER; sub.position=Vector2(0,300); sub.size=Vector2(1280,40); sub.modulate=Color("#7f9ab5"); layer.add_child(sub)
    var bar=ColorRect.new(); bar.color=Color("#16283a"); bar.position=Vector2(320,380); bar.size=Vector2(640,12); layer.add_child(bar)
    var fill=ColorRect.new(); fill.name="Fill"; fill.color=Color("#2bdcff"); fill.size=Vector2(1,12); bar.add_child(fill)
    for i in 5:
        await get_tree().create_timer(.16).timeout
        fill.size.x=640.0*(i+1)/5.0
    layer.queue_free(); _menu()

func _menu():
    _clear_ui(); menu=Control.new(); menu.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); add_child(menu)
    var bg=ColorRect.new(); bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); bg.color=Color("#07101b"); menu.add_child(bg)
    var t=Label.new(); t.text="PORTAL GATES"; t.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER; t.add_theme_font_size_override("font_size",54); t.position=Vector2(0,160); t.size=Vector2(1280,80); menu.add_child(t)
    var s=Label.new(); s.text="THE EXIT IS NEVER WHERE YOU EXPECT"; s.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER; s.modulate=Color("#7f9ab5"); s.position=Vector2(0,235); s.size=Vector2(1280,45); menu.add_child(s)
    var play=_btn("PLAY",Vector2(470,330),Vector2(340,64),22); play.pressed.connect(func():_start(unlocked)); menu.add_child(play)
    var levels=_btn("LEVEL SELECT",Vector2(470,405),Vector2(340,58),18); levels.pressed.connect(_select); menu.add_child(levels)
    var info=Label.new(); info.text="20 SOLVABLE CHAMBERS  •  PORTALS  •  CUBES  •  LASERS"; info.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER; info.modulate=Color("#5e748d"); info.position=Vector2(0,510); info.size=Vector2(1280,40); menu.add_child(info)

func _select():
    _clear_ui(); select=Control.new(); select.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); add_child(select)
    var bg=ColorRect.new(); bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); bg.color=Color("#07101b"); select.add_child(bg)
    var title=Label.new(); title.text="SELECT CHAMBER"; title.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER; title.add_theme_font_size_override("font_size",34); title.position=Vector2(0,35); title.size=Vector2(1280,60); select.add_child(title)
    var grid=GridContainer.new(); grid.columns=5; grid.position=Vector2(280,130); grid.size=Vector2(720,400); grid.add_theme_constant_override("h_separation",18); grid.add_theme_constant_override("v_separation",18); select.add_child(grid)
    for n in range(1,LEVELS+1):
        var b=_btn("%02d"%n,Vector2.ZERO,Vector2(120,72),20); b.disabled=n>unlocked; if b.disabled:b.text="LOCKED"; else:b.pressed.connect(func(x=n):_start(x)); grid.add_child(b)
    var back=_btn("BACK",Vector2(25,25),Vector2(120,50),16); back.pressed.connect(_menu); select.add_child(back)

func _btn(text,pos,size,font):
    var b=Button.new(); b.text=text; b.position=pos; b.size=size; b.add_theme_font_size_override("font_size",font); b.add_theme_stylebox_override("normal",_style(Color("#132238"),Color("#29435d"))); b.add_theme_stylebox_override("hover",_style(Color("#1a3852"),Color("#2bdcff"))); return b
func _style(bg,border):
    var s=StyleBoxFlat.new(); s.bg_color=bg; s.border_color=border; s.set_border_width_all(2); s.set_corner_radius_all(10); return s
func _clear_ui():
    if menu: menu.queue_free(); menu=null
    if select: select.queue_free(); select=null
    if ui: ui.queue_free(); ui=null

func _start(n):
    _clear_ui(); level=clampi(n,1,LEVELS); won=false; held=null; cubes.clear(); switches.clear(); lasers.clear(); movers.clear(); hazards.clear(); portal_cd=0
    if root3d: root3d.queue_free()
    _world(); _hud(); _build_level(level); level_time=0

func _world():
    root3d=Node3D.new(); add_child(root3d)
    var env=WorldEnvironment.new(); var e=Environment.new(); e.background_mode=Environment.BG_COLOR; e.background_color=Color("#07101a"); e.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR; e.ambient_light_color=Color("#9bb7cc"); e.ambient_light_energy=.55; env.environment=e; root3d.add_child(env)
    var sun=DirectionalLight3D.new(); sun.rotation_degrees=Vector3(-55,-25,0); sun.light_energy=1.1; sun.shadow_enabled=true; root3d.add_child(sun)
    player=CharacterBody3D.new(); player.name="Player"; root3d.add_child(player)
    var pc=CollisionShape3D.new(); var ps=CapsuleShape3D.new(); ps.radius=.34; ps.height=1.35; pc.shape=ps; player.add_child(pc)
    cam=Camera3D.new(); cam.current=true; cam.fov=74; cam.position=Vector3(0,.15,0); player.add_child(cam)
    _portals()

func _portals():
    portal_a=_portal("A",mats.a); portal_b=_portal("B",mats.b); root3d.add_child(portal_a); root3d.add_child(portal_b); portal_a.visible=false; portal_b.visible=false
    view_a=_view("ViewA"); view_b=_view("ViewB"); pcam_a=view_a.get_node("Camera"); pcam_b=view_b.get_node("Camera"); pcam_a.cull_mask=1; pcam_b.cull_mask=1
    _surface(portal_a.get_child(1),view_a.get_texture()); _surface(portal_b.get_child(1),view_b.get_texture())

func _portal(name,mat):
    var n=Node3D.new(); n.name="Portal"+name
    var frame=MeshInstance3D.new(); var tor=TorusMesh.new(); tor.inner_radius=.52; tor.outer_radius=.65; tor.rings=20; tor.ring_segments=12; frame.mesh=tor; frame.material_override=mat; frame.rotation_degrees.x=90; frame.layers=2; n.add_child(frame)
    var surf=MeshInstance3D.new(); var q=QuadMesh.new(); q.size=Vector2(1.1,1.9); surf.mesh=q; surf.position.z=.01; surf.layers=2; n.add_child(surf); return n
func _view(name):
    var v=SubViewport.new(); v.name=name; v.size=Vector2i(384,384); v.render_target_update_mode=SubViewport.UPDATE_ALWAYS; v.transparent_bg=true; v.world_3d=get_viewport().world_3d; add_child(v)
    var c=Camera3D.new(); c.name="Camera"; c.current=true; c.fov=74; v.add_child(c); return v
func _surface(node,tex):
    var sh=Shader.new(); sh.code="shader_type spatial; render_mode unshaded,cull_disabled; uniform sampler2D tex; void fragment(){vec3 c=texture(tex,UV).rgb;ALBEDO=c;EMISSION=c;}"
    var sm=ShaderMaterial.new(); sm.shader=sh; sm.set_shader_parameter("tex",tex); node.material_override=sm

func _build_level(id):
    var d=_data(id); var w=d.w; var z=d.z; _room(w,z); player.position=d.start; required=d.req; objective.text=d.text
    for a in d.walls:_box(a.p,a.s,mats.wall,a.r)
    for p in d.cubes:_cube(p)
    for p in d.switches:_switch(p)
    for l in d.lasers:_laser(l)
    for m in d.movers:_mover(m)
    for h in d.hazards:_hazard(h)
    _exit(d.exit)
    if d.a!=Vector3.INF:portal_a.position=d.a; portal_a.rotation_degrees=d.ar; portal_a.visible=true
    if d.b!=Vector3.INF:portal_b.position=d.b; portal_b.rotation_degrees=d.br; portal_b.visible=true

func _room(w,z):
    _box(Vector3(0,-.3,0),Vector3(w,.6,z),mats.floor); _box(Vector3(0,4.2,0),Vector3(w,.5,z),mats.wall); _box(Vector3(-w/2,2,0),Vector3(.5,4.5,z),mats.wall); _box(Vector3(w/2,2,0),Vector3(.5,4.5,z),mats.wall); _box(Vector3(0,2,-z/2),Vector3(w,4.5,.5),mats.wall); _box(Vector3(0,2,z/2),Vector3(w,4.5,.5),mats.wall)
func _box(p,s,mat,r=0.0):
    var b=StaticBody3D.new(); b.position=p; b.rotation.y=r; root3d.add_child(b); var m=MeshInstance3D.new(); var bm=BoxMesh.new(); bm.size=s; m.mesh=bm; m.material_override=mat; b.add_child(m); var c=CollisionShape3D.new(); var bs=BoxShape3D.new(); bs.size=s; c.shape=bs; b.add_child(c); return b
func _cube(p):
    var b=RigidBody3D.new(); b.position=p; b.mass=1.5; b.linear_damp=3; b.angular_damp=5; b.set_meta("cube",true); root3d.add_child(b); var m=MeshInstance3D.new(); var bm=BoxMesh.new(); bm.size=Vector3(.7,.7,.7); m.mesh=bm; m.material_override=mats.cube; b.add_child(m); var c=CollisionShape3D.new(); var bs=BoxShape3D.new(); bs.size=Vector3(.7,.7,.7); c.shape=bs; b.add_child(c); cubes.append(b)
func _switch(p):
    var a=Area3D.new(); a.position=p; root3d.add_child(a); var m=MeshInstance3D.new(); var cm=CylinderMesh.new(); cm.top_radius=.34; cm.bottom_radius=.34; cm.height=.18; m.mesh=cm; m.material_override=mats.b; a.add_child(m); var c=CollisionShape3D.new(); var cs=CylinderShape3D.new(); cs.radius=.42; cs.height=.28; c.shape=cs; a.add_child(c); switches.append(a)
func _laser(x):
    var n=MeshInstance3D.new(); var cm=CylinderMesh.new(); cm.top_radius=.045; cm.bottom_radius=.045; cm.height=x.l; n.mesh=cm; n.material_override=mats.danger; n.position=x.p; n.rotation_degrees=x.r; root3d.add_child(n); lasers.append(n)
func _mover(x):
    var n=AnimatableBody3D.new(); n.position=x.a; n.set_meta("a",x.a); n.set_meta("b",x.b); n.set_meta("t",0.0); n.set_meta("speed",x.sp); root3d.add_child(n); var m=MeshInstance3D.new(); var bm=BoxMesh.new(); bm.size=x.s; m.mesh=bm; m.material_override=mats.trim; n.add_child(m); var c=CollisionShape3D.new(); var bs=BoxShape3D.new(); bs.size=x.s; c.shape=bs; n.add_child(c); movers.append(n)
func _hazard(p):
    var a=Area3D.new(); a.position=p; root3d.add_child(a); var m=MeshInstance3D.new(); var sm=SphereMesh.new(); sm.radius=.38; sm.height=.76; m.mesh=sm; m.material_override=mats.danger; a.add_child(m); var c=CollisionShape3D.new(); var ss=SphereShape3D.new(); ss.radius=.5; c.shape=ss; a.add_child(c); a.body_entered.connect(func(b):if b==player:_reset()); hazards.append(a)
func _exit(p):
    exit_area=Area3D.new(); exit_area.position=p; root3d.add_child(exit_area); var c=CollisionShape3D.new(); var bs=BoxShape3D.new(); bs.size=Vector3(1.6,2.8,.9); c.shape=bs; exit_area.add_child(c); exit_area.body_entered.connect(func(b):if b==player:_finish())
    exit_visual=Node3D.new(); exit_visual.position=p; root3d.add_child(exit_visual); var m=MeshInstance3D.new(); var bm=BoxMesh.new(); bm.size=Vector3(1.8,3.2,.25); m.mesh=bm; m.material_override=mats.trim; exit_visual.add_child(m); var inner=MeshInstance3D.new(); var ib=BoxMesh.new(); ib.size=Vector3(1.3,2.7,.1); inner.mesh=ib; inner.material_override=mats.floor; inner.position.z=.16; exit_visual.add_child(inner)

func _hud():
    ui=Control.new(); ui.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); add_child(ui)
    level_label=Label.new(); level_label.text="CHAMBER %02d"%level; level_label.position=Vector2(22,18); level_label.add_theme_font_size_override("font_size",22); ui.add_child(level_label)
    time_label=Label.new(); time_label.position=Vector2(22,50); time_label.modulate=Color("#8199b2"); ui.add_child(time_label)
    objective=Label.new(); objective.position=Vector2(22,82); objective.size=Vector2(520,70); objective.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART; objective.modulate=Color("#cbd9e7"); ui.add_child(objective)
    toast=Label.new(); toast.position=Vector2(0,130); toast.size=Vector2(1280,45); toast.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER; toast.add_theme_font_size_override("font_size",20); toast.modulate=Color("#7dffae"); ui.add_child(toast)
    var r=_btn("RESET",Vector2(1000,20),Vector2(115,55),15); r.pressed.connect(_reset_level); ui.add_child(r)
    var p=_btn("II",Vector2(1130,20),Vector2(110,55),23); p.pressed.connect(_pause); ui.add_child(p)
    var joy=Control.new(); joy.position=Vector2(25,500); joy.size=Vector2(230,190); joy.gui_input.connect(_move_input); ui.add_child(joy)
    var ring=ColorRect.new(); ring.color=Color(0.08,.16,.24,.55); ring.position=Vector2(10,10); ring.size=Vector2(180,180); ring.mouse_filter=Control.MOUSE_FILTER_IGNORE; joy.add_child(ring)
    var stick=ColorRect.new(); stick.name="Stick"; stick.color=Color(.18,.65,.8,.8); stick.position=Vector2(65,65); stick.size=Vector2(70,70); stick.mouse_filter=Control.MOUSE_FILTER_IGNORE; joy.add_child(stick)
    var look_zone=Control.new(); look_zone.position=Vector2(300,100); look_zone.size=Vector2(670,580); look_zone.gui_input.connect(_look_input); ui.add_child(look_zone)
    var j=_btn("JUMP",Vector2(1060,570),Vector2(190,60),16); j.pressed.connect(_jump); ui.add_child(j)
    var use=_btn("USE",Vector2(1060,500),Vector2(190,60),16); use.pressed.connect(_use); ui.add_child(use)
    var a=_btn("A",Vector2(900,590),Vector2(70,60),20); a.pressed.connect(func():_place(false)); ui.add_child(a)
    var b=_btn("B",Vector2(980,590),Vector2(70,60),20); b.pressed.connect(func():_place(true)); ui.add_child(b)

func _process(dt):
    if not player or won:return
    level_time+=dt; portal_cd=maxf(0,portal_cd-dt); time_label.text="TIME  %05.1f"%level_time; _move(dt); _portcam(); _movers(dt); _hazards(dt); _switches(); _teleport()
func _move(dt):
    var v=Input.get_vector("move_left","move_right","move_forward","move_back"); if move_vec.length()>.05:v=move_vec
    var wish=cam.global_transform.basis.x*v.x+(-cam.global_transform.basis.z)*v.y; wish.y=0; if wish.length()>1:wish=wish.normalized(); player.velocity.x=move_toward(player.velocity.x,wish.x*SPEED,18*dt); player.velocity.z=move_toward(player.velocity.z,wish.z*SPEED,18*dt); if not player.is_on_floor():player.velocity.y-=GRAVITY*dt; else:player.velocity.y=-.1; player.move_and_slide(); if player.position.y< -3:_reset()
func _jump():if player and player.is_on_floor():player.velocity.y=JUMP
func _use():
    var h=_ray(4); if h.is_empty():return
    var c=h.collider
    if c is RigidBody3D and c.get_meta("cube",false):
        if held==c:_drop()
        elif held==null:_pick(c)
func _pick(c):held=c; held.freeze=true
func _drop():held.freeze=false; held.global_position=cam.global_position+(-cam.global_transform.basis.z*1.7)-Vector3(0,.2,0); held=null
func _place(second):
    if portal_cd>0:return
    var h=_ray(15); if h.is_empty():_say("NO VALID SURFACE");return
    var p=portal_b if second else portal_a; p.global_position=h.position+h.normal*.05; p.global_basis=_basis(h.normal); p.visible=true; _say("PORTAL B PLACED" if second else "PORTAL A PLACED")
func _basis(n):
    var f=-n; var up=Vector3.UP; if abs(f.dot(up))>.94:up=Vector3.FORWARD; var r=up.cross(f).normalized(); up=f.cross(r).normalized(); return Basis(r,up,-f).orthonormalized()
func _ray(dist):
    var q=PhysicsRayQueryParameters3D.create(cam.global_position,cam.global_position-cam.global_transform.basis.z*dist); q.exclude=[player]; return get_world_3d().direct_space_state.intersect_ray(q)
func _portcam():
    if not portal_a.visible or not portal_b.visible:return
    _onecam(portal_a,portal_b,pcam_a); _onecam(portal_b,portal_a,pcam_b)
func _onecam(src,dst,c):
    var rel=src.global_transform.affine_inverse()*cam.global_transform; var flip=Transform3D(Basis(Vector3.UP,PI),Vector3.ZERO); c.global_transform=dst.global_transform*flip*rel; c.fov=cam.fov
func _teleport():
    if portal_cd>0 or not portal_a.visible or not portal_b.visible:return
    if _try(player,portal_a,portal_b):return
    if _try(player,portal_b,portal_a):return
    for c in cubes:
        if is_instance_valid(c) and c!=held:
            if _try(c,portal_a,portal_b):return
            if _try(c,portal_b,portal_a):return
func _try(body,src,dst):
    var local=src.global_transform.affine_inverse()*body.global_transform
    if local.origin.z>.05 or local.origin.z<-.85 or abs(local.origin.x)>.7 or abs(local.origin.y-.9)>1.15:return false
    var rel=src.global_transform.affine_inverse()*body.global_transform; var flip=Transform3D(Basis(Vector3.UP,PI),Vector3.ZERO); body.global_transform=dst.global_transform*flip*rel; if body is CharacterBody3D:body.velocity=-dst.global_transform.basis.z; portal_cd=.35; _say("PORTAL TRANSFER"); return true
func _movers(dt):
    for n in movers:
        var t=float(n.get_meta("t"))+dt*float(n.get_meta("speed")); n.set_meta("t",t); n.position=n.get_meta("a").lerp(n.get_meta("b"),(sin(t)+1)/2)
func _hazards(dt):
    for a in hazards:
        if is_instance_valid(a):a.rotation.y+=dt*1.5
    for l in lasers:
        var p=l.to_local(player.global_position); if abs(p.x)<.45 and abs(p.z)<.45 and abs(p.y)<.5:_reset();return
func _switches():
    var count=0
    for s in switches:
        var on=player.global_position.distance_to(s.global_position)<.65
        for c in cubes:
            if is_instance_valid(c) and c.global_position.distance_to(s.global_position)<.65:on=true
        s.get_child(0).material_override=mats.goal if on else mats.b
        if on:count+=1
    if required>0 and count>=required:exit_area.set_meta("open",true)
    elif required==0:exit_area.set_meta("open",true)
func _finish():
    if not exit_area.get_meta("open",false):_say("EXIT LOCKED");return
    if won:return
    won=true
    if level==unlocked and unlocked<LEVELS:unlocked+=1
    _save();_win_panel()
func _win_panel():
    var p=ColorRect.new(); p.color=Color(.02,.05,.08,.96); p.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); ui.add_child(p)
    var t=Label.new(); t.text="CHAMBER CLEARED"; t.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER; t.add_theme_font_size_override("font_size",40); t.position=Vector2(0,170); t.size=Vector2(1280,60); p.add_child(t)
    var st=Label.new(); st.text="TIME  %05.1fs\n\nNEXT  %02d / %02d"%[level_time,min(level+1,LEVELS),LEVELS]; st.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER; st.position=Vector2(0,245); st.size=Vector2(1280,120); st.add_theme_font_size_override("font_size",20); p.add_child(st)
    var n=_btn("NEXT",Vector2(450,410),Vector2(180,60),18); n.disabled=level>=LEVELS; n.pressed.connect(func():_start(level+1)); p.add_child(n)
    var r=_btn("REPLAY",Vector2(650,410),Vector2(180,60),18); r.pressed.connect(func():_start(level)); p.add_child(r)
    var m=_btn("MENU",Vector2(550,490),Vector2(180,55),17); m.pressed.connect(_menu); p.add_child(m)
func _reset():
    var d=_data(level); player.position=d.start; player.velocity=Vector3.ZERO
func _reset_level():_start(level)
func _say(s):toast.text=s;toast.modulate.a=1;var tw=create_tween();tw.tween_interval(1);tw.tween_property(toast,"modulate:a",0,.4)
func _pause():
    get_tree().paused=true; var p=ColorRect.new();p.color=Color(.02,.04,.07,.95);p.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);ui.add_child(p);var t=Label.new();t.text="PAUSED";t.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;t.add_theme_font_size_override("font_size",38);t.position=Vector2(0,180);t.size=Vector2(1280,60);p.add_child(t);var r=_btn("RESUME",Vector2(455,300),Vector2(170,60),18);r.pressed.connect(func():p.queue_free();get_tree().paused=false);p.add_child(r);var m=_btn("MENU",Vector2(655,300),Vector2(170,60),18);m.pressed.connect(func():get_tree().paused=false;_menu());p.add_child(m)
func _move_input(e):
    if e is InputEventScreenTouch:
        if e.pressed:move_id=e.index;move_vec=Vector2.ZERO
        elif e.index==move_id:move_id=-1;move_vec=Vector2.ZERO
    elif e is InputEventScreenDrag and e.index==move_id:move_vec=(e.position-Vector2(100,100)).limit_length(75)/75
func _look_input(e):
    if e is InputEventScreenTouch:
        if e.pressed:look_id=e.index;last_look=e.position
        elif e.index==look_id:look_id=-1
    elif e is InputEventScreenDrag and e.index==look_id:
        var d=e.position-last_look;last_look=e.position;_look(d)
func _look(d):player.rotate_y(-d.x*LOOK);pitch=clampf(pitch-d.y*LOOK,-1.35,1.35);cam.rotation.x=pitch
func _unhandled_input(e):
    if e is InputEventKey and e.pressed:
        if e.keycode==KEY_ESCAPE and player:_pause()
        elif e.keycode==KEY_F:_place(false)
        elif e.keycode==KEY_G:_place(true)
    if e is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):_look(e.relative)

func _data(id):
    var w=18.0+min(id*.55,8.0);var z=18.0+min(id*.65,10.0);var d={"w":w,"z":z,"start":Vector3(-w*.34,1.65,z*.34),"exit":Vector3(w*.34,1.2,-z*.34),"req":0,"walls":[],"cubes":[],"switches":[],"lasers":[],"movers":[],"hazards":[],"a":Vector3.INF,"b":Vector3.INF,"ar":Vector3.ZERO,"br":Vector3.ZERO,"text":"Reach the green exit."}
    if id>=2:d.walls.append({"p":Vector3(0,2,2),"s":Vector3(w*.58,4,.55),"r":0.0});d.text="Use the wall to route around the chamber."
    if id>=3:d.cubes.append(Vector3(-2.5,.45,0));d.switches.append(Vector3(2.4,.1,-1));d.req=1;d.text="Put the cube on the switch, then reach the exit."
    if id>=4:d.a=Vector3(-w*.32,1.25,0);d.b=Vector3(w*.32,1.25,0);d.ar=Vector3(0,90,0);d.br=Vector3(0,-90,0);d.text="A and B are linked. Use the portal to cross the chamber."
    if id>=5:d.lasers.append({"p":Vector3(0,1.2,-2.4),"r":Vector3(90,0,0),"l":7.0});d.text="Bypass the laser using a portal route."
    if id>=6:d.cubes.append(Vector3(1.8,.45,-3.4));d.switches.append(Vector3(-1.8,.1,-3.4));d.req=1;d.text="Carry the cube to the distant switch."
    if id>=7:d.movers.append({"a":Vector3(-3,.6,-4),"b":Vector3(3,.6,-4),"s":Vector3(2.4,.4,2.4),"sp":.8});d.text="Time the moving platform."
    if id>=8:d.hazards += [Vector3(0,1,0),Vector3(3,1,3)];d.text="Avoid red energy orbs."
    if id>=9:d.walls += [{"p":Vector3(-3,2,-4),"s":Vector3(.6,4,8),"r":0.0},{"p":Vector3(3,2,4),"s":Vector3(.6,4,8),"r":0.0}];d.text="The chamber is split; portals are the intended shortcut."
    if id>=10:d.cubes.append(Vector3(0,.45,4));d.switches.append(Vector3(-5,.1,-5));d.req=1;d.a=Vector3(-5,1.25,-2);d.b=Vector3(5,1.25,2);d.ar=Vector3(0,90,0);d.br=Vector3(0,-90,0);d.text="Move the cube through the portal link."
    if id>=11:d.lasers += [{"p":Vector3(-2,1.5,0),"r":Vector3(0,0,90),"l":6.0},{"p":Vector3(2,1.5,0),"r":Vector3(0,0,90),"l":6.0}];d.text="Two beams guard the corridor."
    if id>=12:d.movers.append({"a":Vector3(-5,.6,-1),"b":Vector3(5,.6,-1),"s":Vector3(2,.4,2),"sp":1.1});d.text="Ride the moving platform, then portal."
    if id>=13:
        for x in [-4.5,-1.5,1.5,4.5]:
            d.hazards.append(Vector3(x,1,1.5))
        d.text="Thread between the hazards."
    if id>=14:d.cubes += [Vector3(-4,.45,-5),Vector3(4,.45,5)];d.switches += [Vector3(-4,.1,5),Vector3(4,.1,-5)];d.req=2;d.text="Both switches must stay pressed."
    if id>=15:d.walls += [{"p":Vector3(0,2,-5),"s":Vector3(10,4,.55),"r":0.0},{"p":Vector3(0,2,5),"s":Vector3(10,4,.55),"r":0.0}];d.a=Vector3(-7,1.25,0);d.b=Vector3(7,1.25,0);d.ar=Vector3(0,90,0);d.br=Vector3(0,-90,0);d.text="Long corridor: build a portal shortcut."
    if id>=16:d.lasers += [{"p":Vector3(0,2,-6),"r":Vector3(0,0,90),"l":10.0},{"p":Vector3(0,2,6),"r":Vector3(0,0,90),"l":10.0}];d.text="Use the portal to bypass the two beams."
    if id>=17:d.movers.append({"a":Vector3(-6,.6,-4),"b":Vector3(6,2.8,4),"s":Vector3(2.2,.4,2.2),"sp":.9});d.text="Moving geometry changes the route."
    if id>=18:
        for x in [-6,-3,0,3,6]:
            d.hazards.append(Vector3(x,1,0))
        d.text="Final hazard gauntlet."
    if id>=19:d.cubes += [Vector3(-5,.45,-4.5),Vector3(5,.45,-4.5)];d.switches += [Vector3(-5,.1,4.5),Vector3(5,.1,4.5)];d.req=2;d.a=Vector3(-7,1.25,0);d.b=Vector3(7,1.25,0);d.ar=Vector3(0,90,0);d.br=Vector3(0,-90,0);d.text="Two cubes, two switches, hazards and a portal shortcut."
    if id==20:d.walls.append({"p":Vector3(0,2,0),"s":Vector3(.8,4,12),"r":0.0});d.cubes += [Vector3(-6,.45,-6),Vector3(6,.45,-6)];d.switches += [Vector3(-6,.1,6),Vector3(6,.1,6)];d.req=2;d.text="THE FINAL CHAMBER: two switches and a central divider."
    return d

func _save():
    var f=FileAccess.open(SAVE,FileAccess.WRITE);if f:f.store_var(unlocked);f.close()
func _load_save():
    if not FileAccess.file_exists(SAVE):return 1
    var f=FileAccess.open(SAVE,FileAccess.READ);if not f:return 1
    var n=f.get_var();f.close();return clampi(n if typeof(n)==TYPE_INT else 1,1,LEVELS)
