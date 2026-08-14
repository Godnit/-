extends Node3D
signal request_back_to_menu

const MAP_SCENE = preload("res://assets/classic_reference_v43.glb")
const HOUSE_SCENE = preload("res://assets/cottage.glb")
const GREEN := Color("#16b88d")
const DARK_GREEN := Color("#164f54")
const GOLD := Color("#f4c760")
const RED := Color("#e35d57")
const PANEL := Color(0.035, 0.12, 0.14, 0.92)

var camera: Camera3D
var camera_target := Vector3(0, 0, -35)
var camera_distance := 92.0
var camera_yaw := 0.0
var camera_pitch := -0.78
var touches: Dictionary = {}
var last_drag := Vector2.ZERO
var last_pinch := 0.0
var dragging := false

var save := ConfigFile.new()
var tasks: Array = []
var built_plots: Array = []
var reservations: Dictionary = {}
var next_id := 1
var coins := 0
var xp := 0
var level := 1
var streak := 0

var task_list: VBoxContainer
var coin_label: Label
var level_label: Label
var streak_label: Label
var house_label: Label
var add_dialog: PanelContainer
var title_edit: LineEdit
var time_spin: SpinBox
var category_option: OptionButton
var ui_root: Control
var tutorial_layer: Control
var tutorial_step := 0
var timer_accum := 0.0

var plots := [
	Vector3(-58,0,-70), Vector3(-34,0,-83), Vector3(-7,0,-90), Vector3(22,0,-86), Vector3(51,0,-72),
	Vector3(-72,0,-44), Vector3(69,0,-42), Vector3(-75,0,-12), Vector3(73,0,-10), Vector3(-60,0,20),
	Vector3(56,0,18), Vector3(-34,0,36), Vector3(0,0,42), Vector3(34,0,35), Vector3(0,0,-57)
]

func _ready() -> void:
	setup_world()
	load_state()
	spawn_saved_world()
	build_ui()
	refresh_tasks_ui()
	check_overdue_tasks()
	if not bool(save.get_value("meta", "tutorial_seen", false)):
		await get_tree().create_timer(0.45).timeout
		start_tutorial()

func setup_world() -> void:
	var map := MAP_SCENE.instantiate()
	map.name = "ClassicMap"
	add_child(map)
	set_shadow_casting_recursive(map)

	var env_node := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("#9adbe2")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("#d8eadb")
	env.ambient_light_energy = 0.70
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.fog_enabled = true
	env.fog_light_color = Color("#b8e2df")
	env.fog_density = 0.0018
	env_node.environment = env
	add_child(env_node)

	var sun := DirectionalLight3D.new()
	sun.name = "Sun"
	sun.light_color = Color("#fff3ca")
	sun.light_energy = 1.55
	sun.rotation_degrees = Vector3(-52, -32, 0)
	sun.shadow_enabled = true
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.directional_shadow_max_distance = 220.0
	sun.shadow_blur = 2.0
	add_child(sun)

	camera = Camera3D.new()
	camera.fov = 52.0
	camera.near = 0.2
	camera.far = 650.0
	add_child(camera)
	update_camera()

func set_shadow_casting_recursive(node: Node) -> void:
	if node is GeometryInstance3D:
		(node as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	for child in node.get_children():
		set_shadow_casting_recursive(child)

func update_camera() -> void:
	var cp := cos(camera_pitch)
	var offset := Vector3(sin(camera_yaw) * cp, -sin(camera_pitch), cos(camera_yaw) * cp) * camera_distance
	camera.global_position = camera_target + offset
	camera.look_at(camera_target + Vector3(0, 2.0, 0), Vector3.UP)

func _process(delta: float) -> void:
	timer_accum += delta
	if timer_accum >= 0.5:
		timer_accum = 0.0
		var now := int(Time.get_unix_time_from_system())
		var changed := false
		for task in tasks:
			if str(task.get("status", "")) == "active" and now >= int(task.get("deadline", 0)):
				fail_task(task)
				changed = true
		if not changed:
			refresh_tasks_ui()

func _unhandled_input(event: InputEvent) -> void:
	if tutorial_layer and is_instance_valid(tutorial_layer):
		return
	if event is InputEventScreenTouch:
		if event.pressed:
			touches[event.index] = event.position
			if touches.size() == 1:
				last_drag = event.position
				dragging = true
		else:
			touches.erase(event.index)
			if touches.size() < 2:
				last_pinch = 0.0
			if touches.is_empty():
				dragging = false
	elif event is InputEventScreenDrag:
		touches[event.index] = event.position
		if touches.size() == 1 and dragging:
			var drag_delta := event.position - last_drag
			last_drag = event.position
			pan_camera(drag_delta)
		elif touches.size() >= 2:
			var ids := touches.keys()
			var p1: Vector2 = touches[ids[0]]
			var p2: Vector2 = touches[ids[1]]
			var dist := p1.distance_to(p2)
			if last_pinch > 0.0:
				camera_distance = clamp(camera_distance - (dist - last_pinch) * 0.12, 42.0, 145.0)
				update_camera()
			last_pinch = dist
	elif event is InputEventMouseButton:
		if event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_UP:
			camera_distance = clamp(camera_distance - 6.0, 42.0, 145.0)
			update_camera()
		elif event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			camera_distance = clamp(camera_distance + 6.0, 42.0, 145.0)
			update_camera()
	elif event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		pan_camera(event.relative)

func pan_camera(delta: Vector2) -> void:
	var right := Vector3(cos(camera_yaw), 0, -sin(camera_yaw))
	var forward := Vector3(sin(camera_yaw), 0, cos(camera_yaw))
	camera_target += (-right * delta.x - forward * delta.y) * (0.055 * camera_distance / 80.0)
	camera_target.x = clamp(camera_target.x, -82.0, 82.0)
	camera_target.z = clamp(camera_target.z, -108.0, 58.0)
	update_camera()

func style(color: Color, radius := 20, border := Color.TRANSPARENT, border_width := 0) -> StyleBoxFlat:
	var box := StyleBoxFlat.new()
	box.bg_color = color
	box.corner_radius_top_left = radius
	box.corner_radius_top_right = radius
	box.corner_radius_bottom_left = radius
	box.corner_radius_bottom_right = radius
	box.border_color = border
	box.border_width_left = border_width
	box.border_width_right = border_width
	box.border_width_top = border_width
	box.border_width_bottom = border_width
	return box

func build_ui() -> void:
	var canvas := CanvasLayer.new()
	canvas.layer = 10
	add_child(canvas)
	ui_root = Control.new()
	ui_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	canvas.add_child(ui_root)

	var top := HBoxContainer.new()
	top.position = Vector2(20, 18)
	top.size = Vector2(940, 64)
	top.add_theme_constant_override("separation", 10)
	ui_root.add_child(top)

	var back := Button.new()
	back.text = "القائمة"
	back.custom_minimum_size = Vector2(110, 58)
	back.add_theme_font_size_override("font_size", 18)
	back.add_theme_color_override("font_color", Color.WHITE)
	back.add_theme_stylebox_override("normal", style(PANEL, 18))
	back.pressed.connect(func(): save_state(); request_back_to_menu.emit())
	top.add_child(back)

	coin_label = make_chip("العملات 0", GOLD)
	level_label = make_chip("المستوى 1", GREEN)
	streak_label = make_chip("السلسلة 0", Color("#ef8a53"))
	house_label = make_chip("البيوت 0", Color("#6f9ed2"))
	top.add_child(coin_label)
	top.add_child(level_label)
	top.add_child(streak_label)
	top.add_child(house_label)

	var task_panel := PanelContainer.new()
	task_panel.position = Vector2(20, 96)
	task_panel.size = Vector2(405, 525)
	task_panel.add_theme_stylebox_override("panel", style(PANEL, 28, Color(1,1,1,0.12), 1))
	ui_root.add_child(task_panel)
	var panel_v := VBoxContainer.new()
	panel_v.add_theme_constant_override("separation", 10)
	task_panel.add_child(panel_v)
	var title := Label.new()
	title.text = "مهام المدينة"
	title.add_theme_font_size_override("font_size", 30)
	title.add_theme_color_override("font_color", Color.WHITE)
	panel_v.add_child(title)
	var info := Label.new()
	info.text = "أنجز المهمة قبل انتهاء الوقت حتى يكتمل البيت."
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.add_theme_font_size_override("font_size", 15)
	info.add_theme_color_override("font_color", Color("#b9d2cf"))
	panel_v.add_child(info)
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	panel_v.add_child(scroll)
	task_list = VBoxContainer.new()
	task_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	task_list.add_theme_constant_override("separation", 8)
	scroll.add_child(task_list)
	var add_button := Button.new()
	add_button.name = "AddTaskButton"
	add_button.text = "+  إضافة مهمة"
	add_button.custom_minimum_size = Vector2(0, 62)
	add_button.add_theme_font_size_override("font_size", 22)
	add_button.add_theme_color_override("font_color", Color.WHITE)
	add_button.add_theme_stylebox_override("normal", style(GREEN, 20))
	add_button.add_theme_stylebox_override("pressed", style(GREEN.darkened(0.15), 20))
	add_button.pressed.connect(show_add_dialog)
	panel_v.add_child(add_button)

	build_add_dialog()
	update_hud()

func make_chip(text: String, color: Color) -> Label:
	var label := Label.new()
	label.text = text
	label.custom_minimum_size = Vector2(155, 58)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.add_theme_font_size_override("font_size", 18)
	label.add_theme_color_override("font_color", Color.WHITE)
	label.add_theme_stylebox_override("normal", style(Color(color.r, color.g, color.b, 0.82), 18))
	return label

func build_add_dialog() -> void:
	add_dialog = PanelContainer.new()
	add_dialog.visible = false
	add_dialog.set_anchors_preset(Control.PRESET_CENTER)
	add_dialog.position = Vector2(-275, -250)
	add_dialog.size = Vector2(550, 500)
	add_dialog.add_theme_stylebox_override("panel", style(Color("#17383d"), 30, Color(1,1,1,0.18), 2))
	ui_root.add_child(add_dialog)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 14)
	add_dialog.add_child(v)
	var head := Label.new()
	head.text = "مهمة جديدة"
	head.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	head.add_theme_font_size_override("font_size", 30)
	head.add_theme_color_override("font_color", Color.WHITE)
	v.add_child(head)
	title_edit = LineEdit.new()
	title_edit.placeholder_text = "مثال: مراجعة الفصل الثالث"
	title_edit.custom_minimum_size = Vector2(0, 58)
	title_edit.add_theme_font_size_override("font_size", 20)
	v.add_child(title_edit)
	category_option = OptionButton.new()
	category_option.add_item("دراسة")
	category_option.add_item("عمل")
	category_option.add_item("صحة")
	category_option.add_item("شخصي")
	category_option.custom_minimum_size = Vector2(0, 52)
	category_option.add_theme_font_size_override("font_size", 19)
	v.add_child(category_option)
	var time_row := HBoxContainer.new()
	v.add_child(time_row)
	var tl := Label.new()
	tl.text = "المدة بالدقائق:"
	tl.add_theme_font_size_override("font_size", 19)
	tl.add_theme_color_override("font_color", Color.WHITE)
	time_row.add_child(tl)
	time_spin = SpinBox.new()
	time_spin.min_value = 1
	time_spin.max_value = 10080
	time_spin.value = 60
	time_spin.custom_minimum_size = Vector2(180, 52)
	time_row.add_child(time_spin)
	var presets := HBoxContainer.new()
	presets.add_theme_constant_override("separation", 8)
	v.add_child(presets)
	for preset in [["15 د",15],["1 س",60],["3 س",180],["يوم",1440]]:
		var pb := Button.new()
		pb.text = str(preset[0])
		pb.custom_minimum_size = Vector2(105, 44)
		pb.add_theme_stylebox_override("normal", style(Color("#24565b"), 14))
		var minutes := int(preset[1])
		pb.pressed.connect(func(): time_spin.value = minutes)
		presets.add_child(pb)
	var note := Label.new()
	note.text = "عند إضافة المهمة يظهر موقع بناء. النجاح يبني بيتاً، وانتهاء الوقت يهدم الموقع."
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	note.add_theme_font_size_override("font_size", 16)
	note.add_theme_color_override("font_color", Color("#c8dcda"))
	v.add_child(note)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 14)
	v.add_child(row)
	var cancel := Button.new()
	cancel.text = "إلغاء"
	cancel.custom_minimum_size = Vector2(180, 56)
	cancel.add_theme_stylebox_override("normal", style(Color("#53666a"), 17))
	cancel.pressed.connect(func(): add_dialog.visible = false)
	row.add_child(cancel)
	var ok := Button.new()
	ok.text = "ابدأ المهمة"
	ok.custom_minimum_size = Vector2(220, 56)
	ok.add_theme_color_override("font_color", Color.WHITE)
	ok.add_theme_stylebox_override("normal", style(GREEN, 17))
	ok.pressed.connect(create_task_from_dialog)
	row.add_child(ok)

func show_add_dialog() -> void:
	add_dialog.visible = true
	title_edit.text = ""
	title_edit.grab_focus()

func create_task_from_dialog() -> void:
	var task_title := title_edit.text.strip_edges()
	if task_title.is_empty():
		show_toast("اكتب اسم المهمة أولاً", RED)
		return
	var plot := find_free_plot()
	if plot < 0:
		show_toast("امتلأت مواقع البناء المتاحة حالياً", RED)
		return
	var now := int(Time.get_unix_time_from_system())
	var task: Dictionary = {
		"id": next_id,
		"title": task_title,
		"deadline": now + int(time_spin.value * 60.0),
		"status": "active",
		"plot": plot,
		"category": category_option.selected
	}
	next_id += 1
	tasks.append(task)
	reservations[plot] = true
	spawn_construction_site(task)
	add_dialog.visible = false
	save_state()
	refresh_tasks_ui()
	show_toast("تم حجز موقع بناء للمهمة", GOLD)

func find_free_plot() -> int:
	for i in range(plots.size()):
		if not reservations.has(i) and not built_plots.has(i):
			return i
	return -1

func refresh_tasks_ui() -> void:
	if not task_list:
		return
	for child in task_list.get_children():
		child.queue_free()
	var active_count := 0
	var now := int(Time.get_unix_time_from_system())
	for task in tasks:
		if str(task.get("status", "")) != "active":
			continue
		active_count += 1
		var card := PanelContainer.new()
		card.add_theme_stylebox_override("panel", style(Color("#173b3f"), 18))
		card.custom_minimum_size = Vector2(0, 96)
		task_list.add_child(card)
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 8)
		card.add_child(row)
		var text_box := VBoxContainer.new()
		text_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(text_box)
		var name_label := Label.new()
		name_label.text = str(task.get("title", "مهمة"))
		name_label.add_theme_font_size_override("font_size", 19)
		name_label.add_theme_color_override("font_color", Color.WHITE)
		name_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		text_box.add_child(name_label)
		var left := max(0, int(task.get("deadline", 0)) - now)
		var timer_label := Label.new()
		timer_label.text = "متبقي: " + format_time(left)
		timer_label.add_theme_font_size_override("font_size", 15)
		timer_label.add_theme_color_override("font_color", GOLD if left > 300 else RED)
		text_box.add_child(timer_label)
		var done := Button.new()
		done.text = "✓"
		done.custom_minimum_size = Vector2(58, 58)
		done.add_theme_font_size_override("font_size", 26)
		done.add_theme_color_override("font_color", Color.WHITE)
		done.add_theme_stylebox_override("normal", style(GREEN, 18))
		done.pressed.connect(func(): complete_task(task))
		row.add_child(done)
	if active_count == 0:
		var empty := Label.new()
		empty.text = "لا توجد مهام الآن\nأضف مهمة ليظهر أول موقع بناء."
		empty.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		empty.add_theme_font_size_override("font_size", 18)
		empty.add_theme_color_override("font_color", Color("#9fc0bd"))
		empty.custom_minimum_size = Vector2(0, 120)
		task_list.add_child(empty)

func format_time(seconds: int) -> String:
	if seconds >= 86400:
		return "%d يوم %d س" % [seconds / 86400, (seconds % 86400) / 3600]
	if seconds >= 3600:
		return "%d:%02d س" % [seconds / 3600, (seconds % 3600) / 60]
	return "%02d:%02d" % [seconds / 60, seconds % 60]

func complete_task(task: Dictionary) -> void:
	if str(task.get("status", "")) != "active":
		return
	task["status"] = "done"
	var plot := int(task.get("plot", 0))
	reservations.erase(plot)
	if not built_plots.has(plot):
		built_plots.append(plot)
	coins += 20 + 5 * int(task.get("category", 0))
	xp += 30
	streak += 1
	while xp >= 100:
		xp -= 100
		level += 1
		show_toast("ارتفع مستواك إلى %d" % level, GOLD)
	remove_site(int(task.get("id", 0)), true)
	build_house_animation(plot)
	Input.vibrate_handheld(45)
	save_state()
	refresh_tasks_ui()
	update_hud()
	show_toast("ممتاز! تحولت المهمة إلى بيت", GREEN)

func fail_task(task: Dictionary) -> void:
	if str(task.get("status", "")) != "active":
		return
	task["status"] = "failed"
	var plot := int(task.get("plot", 0))
	reservations.erase(plot)
	streak = 0
	remove_site(int(task.get("id", 0)), false)
	collapse_site(plot)
	Input.vibrate_handheld(120)
	save_state()
	refresh_tasks_ui()
	update_hud()
	show_toast("انتهى الوقت... انهار موقع البناء", RED)

func check_overdue_tasks() -> void:
	var now := int(Time.get_unix_time_from_system())
	for task in tasks:
		if str(task.get("status", "")) == "active" and now >= int(task.get("deadline", 0)):
			fail_task(task)

func spawn_saved_world() -> void:
	for plot_variant in built_plots:
		var plot := int(plot_variant)
		if plot >= 0 and plot < plots.size():
			spawn_house(plot, false)
	for task in tasks:
		if str(task.get("status", "")) == "active":
			var plot := int(task.get("plot", 0))
			reservations[plot] = true
			spawn_construction_site(task)

func spawn_house(plot: int, animate := true) -> Node3D:
	var house := HOUSE_SCENE.instantiate()
	house.name = "House_%d" % plot
	house.position = plots[plot] + Vector3(0, 0.05, 0)
	house.rotation_degrees.y = float((plot * 47) % 360)
	add_child(house)
	set_shadow_casting_recursive(house)
	if animate:
		house.scale = Vector3(0.08, 0.02, 0.08)
		var tween := create_tween().set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		tween.tween_property(house, "scale", Vector3.ONE, 1.8)
	return house

func build_house_animation(plot: int) -> void:
	spawn_workers(plot)
	spawn_dust(plots[plot], false)
	spawn_house(plot, true)
	camera_target = plots[plot]
	camera_distance = 68.0
	update_camera()

func spawn_construction_site(task: Dictionary) -> void:
	var root := Node3D.new()
	root.name = "Site_%d" % int(task.get("id", 0))
	root.position = plots[int(task.get("plot", 0))]
	add_child(root)
	var wood := StandardMaterial3D.new()
	wood.albedo_color = Color("#9b7447")
	wood.roughness = 0.9
	var pieces := [
		[Vector3(-2.4,0.25,-2.4),Vector3(0.25,0.5,5.0)], [Vector3(2.4,0.25,-2.4),Vector3(0.25,0.5,5.0)],
		[Vector3(0,0.25,-2.4),Vector3(5.0,0.5,0.25)], [Vector3(0,0.25,2.4),Vector3(5.0,0.5,0.25)]
	]
	for piece in pieces:
		var mesh_instance := MeshInstance3D.new()
		var box := BoxMesh.new()
		box.size = piece[1]
		mesh_instance.mesh = box
		mesh_instance.position = piece[0]
		mesh_instance.material_override = wood
		root.add_child(mesh_instance)
	for x in [-2.1, 2.1]:
		for z in [-2.1, 2.1]:
			var post := MeshInstance3D.new()
			var post_mesh := BoxMesh.new()
			post_mesh.size = Vector3(0.22, 2.8, 0.22)
			post.mesh = post_mesh
			post.position = Vector3(x, 1.4, z)
			post.material_override = wood
			root.add_child(post)

func remove_site(id: int, immediate := true) -> void:
	var node := get_node_or_null("Site_%d" % id)
	if not node:
		return
	if immediate:
		node.queue_free()
	else:
		var tween := create_tween()
		tween.tween_property(node, "rotation_degrees", Vector3(28, 0, 15), 0.45)
		tween.parallel().tween_property(node, "scale", Vector3(1, 0.12, 1), 0.65)
		tween.tween_callback(node.queue_free)

func collapse_site(plot: int) -> void:
	spawn_dust(plots[plot], true)
	for i in range(16):
		var debris := MeshInstance3D.new()
		var box := BoxMesh.new()
		box.size = Vector3(randf_range(0.25,0.8), randf_range(0.18,0.7), randf_range(0.25,0.8))
		debris.mesh = box
		debris.position = plots[plot] + Vector3(randf_range(-2.3,2.3), randf_range(0.3,2.6), randf_range(-2.3,2.3))
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color("#8e6b45")
		debris.material_override = mat
		add_child(debris)
		var target := debris.position + Vector3(randf_range(-4,4), -0.3, randf_range(-4,4))
		var tween := create_tween().set_parallel(true)
		tween.tween_property(debris, "position", target, 1.0).set_trans(Tween.TRANS_QUAD)
		tween.tween_property(debris, "rotation_degrees", Vector3(randf()*180,randf()*180,randf()*180), 1.0)
		tween.set_parallel(false)
		tween.tween_callback(debris.queue_free)

func spawn_workers(plot: int) -> void:
	for i in range(3):
		var worker := Node3D.new()
		worker.position = plots[plot] + Vector3(-3 + i * 3, 0, -3)
		add_child(worker)
		var body := MeshInstance3D.new()
		var capsule := CapsuleMesh.new()
		capsule.radius = 0.25
		capsule.height = 1.15
		body.mesh = capsule
		body.position.y = 0.75
		var body_mat := StandardMaterial3D.new()
		body_mat.albedo_color = [Color("#377cc8"), Color("#d56545"), Color("#59a567")][i]
		body.material_override = body_mat
		worker.add_child(body)
		var head := MeshInstance3D.new()
		var sphere := SphereMesh.new()
		sphere.radius = 0.23
		sphere.height = 0.46
		head.mesh = sphere
		head.position.y = 1.48
		var skin := StandardMaterial3D.new()
		skin.albedo_color = Color("#e8b68e")
		head.material_override = skin
		worker.add_child(head)
		var hat := MeshInstance3D.new()
		var cylinder := CylinderMesh.new()
		cylinder.top_radius = 0.31
		cylinder.bottom_radius = 0.31
		cylinder.height = 0.12
		hat.mesh = cylinder
		hat.position.y = 1.73
		var hat_mat := StandardMaterial3D.new()
		hat_mat.albedo_color = GOLD
		hat.material_override = hat_mat
		worker.add_child(hat)
		var tween := create_tween()
		tween.tween_property(worker, "position", plots[plot] + Vector3(3-i*2.5,0,2.8), 1.3)
		tween.tween_property(worker, "position", plots[plot] + Vector3(-2+i*2,0,3.0), 1.15)
		tween.tween_interval(0.25)
		tween.tween_callback(worker.queue_free)

func spawn_dust(pos: Vector3, big := false) -> void:
	var particles := CPUParticles3D.new()
	particles.one_shot = true
	particles.amount = 48 if big else 28
	particles.lifetime = 1.5
	particles.explosiveness = 0.82
	particles.direction = Vector3(0,1,0)
	particles.spread = 72.0
	particles.initial_velocity_min = 1.8
	particles.initial_velocity_max = 5.0 if big else 3.4
	particles.gravity = Vector3(0,-3,0)
	particles.position = pos + Vector3(0,0.2,0)
	var quad := QuadMesh.new()
	quad.size = Vector2(0.65,0.65)
	var dust_mat := StandardMaterial3D.new()
	dust_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	dust_mat.albedo_color = Color(0.65,0.61,0.50,0.55)
	dust_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	quad.material = dust_mat
	particles.mesh = quad
	add_child(particles)
	particles.emitting = true
	get_tree().create_timer(2.2).timeout.connect(particles.queue_free)

func update_hud() -> void:
	if coin_label: coin_label.text = "العملات %d" % coins
	if level_label: level_label.text = "المستوى %d" % level
	if streak_label: streak_label.text = "السلسلة %d" % streak
	if house_label: house_label.text = "البيوت %d" % built_plots.size()

func show_toast(text: String, color: Color) -> void:
	if not ui_root:
		return
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", style(Color(color.r,color.g,color.b,0.95), 20))
	panel.set_anchors_preset(Control.PRESET_CENTER_TOP)
	panel.position = Vector2(-250, 86)
	panel.size = Vector2(500, 62)
	ui_root.add_child(panel)
	var label := Label.new()
	label.text = text
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.add_theme_font_size_override("font_size", 20)
	label.add_theme_color_override("font_color", Color.WHITE)
	panel.add_child(label)
	panel.modulate.a = 0.0
	var tween := create_tween()
	tween.tween_property(panel, "modulate:a", 1.0, 0.18)
	tween.tween_interval(1.65)
	tween.tween_property(panel, "modulate:a", 0.0, 0.25)
	tween.tween_callback(panel.queue_free)

func start_tutorial() -> void:
	tutorial_step = 0
	tutorial_layer = Control.new()
	tutorial_layer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	tutorial_layer.mouse_filter = Control.MOUSE_FILTER_STOP
	ui_root.add_child(tutorial_layer)
	show_tutorial_step()

func show_tutorial_step() -> void:
	for child in tutorial_layer.get_children():
		child.queue_free()
	var dim := ColorRect.new()
	dim.color = Color(0,0,0,0.66)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	tutorial_layer.add_child(dim)
	var highlight := Panel.new()
	highlight.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var border := StyleBoxFlat.new()
	border.bg_color = Color(0,0,0,0)
	border.border_color = GOLD
	border.border_width_left = 4; border.border_width_right = 4; border.border_width_top = 4; border.border_width_bottom = 4
	border.corner_radius_top_left = 22; border.corner_radius_top_right = 22; border.corner_radius_bottom_left = 22; border.corner_radius_bottom_right = 22
	highlight.add_theme_stylebox_override("panel", border)
	if tutorial_step == 1:
		highlight.position = Vector2(440,90); highlight.size = Vector2(810,570)
	elif tutorial_step == 2:
		highlight.position = Vector2(18,95); highlight.size = Vector2(410,530)
	else:
		highlight.position = Vector2(20,18); highlight.size = Vector2(940,65)
	tutorial_layer.add_child(highlight)
	var card := PanelContainer.new()
	card.add_theme_stylebox_override("panel", style(Color("#163a3e"), 26, Color(1,1,1,0.18), 2))
	card.position = Vector2(445, 188)
	card.size = Vector2(610, 325)
	tutorial_layer.add_child(card)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 14)
	card.add_child(v)
	var steps := [
		["مرحباً في مدينة الإنجاز", "هذه ليست قائمة مهام عادية. كل مهمة تنجزها تتحول إلى بيت حقيقي داخل الخريطة."],
		["الخريطة أمامك", "اسحب بإصبع واحد لتحريك المدينة، واستخدم إصبعين للتقريب والإبعاد. البيوت التي تبنيها تبقى محفوظة."],
		["أضف مهمة", "من لوحة المهام اضغط «إضافة مهمة»، اكتب المهمة وحدد مدتها. سيظهر فوراً موقع بناء جديد."],
		["أنجز قبل الوقت", "اضغط علامة الصح عند الانتهاء. سيصل العمال، يظهر غبار البناء، ثم يرتفع البيت أمامك."],
		["احذر انتهاء الوقت", "إذا انتهى الوقت قبل الإنجاز ينهار موقع البناء ويتطاير الحطام وينقطع تسلسل الإنجاز."]
	]
	var heading := Label.new()
	heading.text = str(steps[tutorial_step][0])
	heading.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	heading.add_theme_font_size_override("font_size", 30)
	heading.add_theme_color_override("font_color", GOLD)
	v.add_child(heading)
	var desc := Label.new()
	desc.text = str(steps[tutorial_step][1])
	desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	desc.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	desc.add_theme_font_size_override("font_size", 20)
	desc.add_theme_color_override("font_color", Color.WHITE)
	desc.custom_minimum_size = Vector2(0,145)
	v.add_child(desc)
	var next := Button.new()
	next.text = "التالي" if tutorial_step < steps.size()-1 else "ابدأ الآن"
	next.custom_minimum_size = Vector2(240,58)
	next.add_theme_font_size_override("font_size",21)
	next.add_theme_color_override("font_color",Color.WHITE)
	next.add_theme_stylebox_override("normal",style(GREEN,18))
	next.pressed.connect(next_tutorial)
	v.add_child(next)

func next_tutorial() -> void:
	tutorial_step += 1
	if tutorial_step >= 5:
		tutorial_layer.queue_free()
		tutorial_layer = null
		save.set_value("meta", "tutorial_seen", true)
		save.save("user://task_city.cfg")
		show_toast("ابدأ بمهمة صغيرة وابنِ أول بيت", GREEN)
	else:
		show_tutorial_step()

func save_state() -> void:
	save.set_value("stats", "coins", coins)
	save.set_value("stats", "xp", xp)
	save.set_value("stats", "level", level)
	save.set_value("stats", "streak", streak)
	save.set_value("stats", "next_id", next_id)
	save.set_value("world", "built_plots", built_plots)
	save.set_value("tasks", "data", tasks)
	save.save("user://task_city.cfg")

func load_state() -> void:
	save.load("user://task_city.cfg")
	coins = int(save.get_value("stats", "coins", 0))
	xp = int(save.get_value("stats", "xp", 0))
	level = int(save.get_value("stats", "level", 1))
	streak = int(save.get_value("stats", "streak", 0))
	next_id = int(save.get_value("stats", "next_id", 1))
	var loaded_plots = save.get_value("world", "built_plots", [])
	if loaded_plots is Array:
		built_plots = loaded_plots
	var loaded_tasks = save.get_value("tasks", "data", [])
	if loaded_tasks is Array:
		tasks = loaded_tasks
