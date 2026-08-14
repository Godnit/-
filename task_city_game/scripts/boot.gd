extends Node

const C_GREEN := Color("#16b88d")
const C_GREEN_D := Color("#164f54")
const C_GOLD := Color("#f4c760")
const C_BG := Color("#10292e")
const C_PANEL := Color("#e8efd1")

var root_ui: Control
var splash: Control
var menu: Control
var loading_label: Label
var progress_bar: ProgressBar
var game: Node
var save := ConfigFile.new()

func _ready() -> void:
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
	build_splash()
	load_save()
	await get_tree().create_timer(0.35).timeout
	animate_loading()

func load_save() -> void:
	save.load("user://task_city.cfg")

func panel_style(color: Color, radius := 24, border := Color.TRANSPARENT, border_w := 0) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = color
	s.corner_radius_top_left = radius
	s.corner_radius_top_right = radius
	s.corner_radius_bottom_left = radius
	s.corner_radius_bottom_right = radius
	s.border_color = border
	s.border_width_left = border_w
	s.border_width_right = border_w
	s.border_width_top = border_w
	s.border_width_bottom = border_w
	return s

func button_style(color: Color, hover: Color) -> Dictionary:
	return {"normal": panel_style(color, 20), "hover": panel_style(hover, 20), "pressed": panel_style(color.darkened(0.15), 20)}

func make_button(text: String, min_size := Vector2(270, 64)) -> Button:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size = min_size
	b.add_theme_font_size_override("font_size", 24)
	b.add_theme_color_override("font_color", Color.WHITE)
	var st := button_style(C_GREEN, C_GREEN.lightened(0.08))
	b.add_theme_stylebox_override("normal", st.normal)
	b.add_theme_stylebox_override("hover", st.hover)
	b.add_theme_stylebox_override("pressed", st.pressed)
	return b

func build_splash() -> void:
	root_ui = Control.new()
	root_ui.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(root_ui)
	var bg := ColorRect.new()
	bg.color = C_BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root_ui.add_child(bg)
	splash = Control.new()
	splash.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root_ui.add_child(splash)
	var center := VBoxContainer.new()
	center.alignment = BoxContainer.ALIGNMENT_CENTER
	center.set_anchors_preset(Control.PRESET_CENTER)
	center.position = Vector2(-300, -170)
	center.size = Vector2(600, 340)
	splash.add_child(center)
	var icon := Label.new()
	icon.text = "✓  🏠"
	icon.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	icon.add_theme_font_size_override("font_size", 68)
	icon.add_theme_color_override("font_color", C_GOLD)
	center.add_child(icon)
	var title := Label.new()
	title.text = "مدينة الإنجاز"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 54)
	title.add_theme_color_override("font_color", Color("#f4f0dc"))
	center.add_child(title)
	var sub := Label.new()
	sub.text = "أنجز مهامك... وابنِ مدينتك"
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sub.add_theme_font_size_override("font_size", 22)
	sub.add_theme_color_override("font_color", Color("#a8cac7"))
	center.add_child(sub)
	progress_bar = ProgressBar.new()
	progress_bar.custom_minimum_size = Vector2(520, 18)
	progress_bar.show_percentage = false
	progress_bar.min_value = 0
	progress_bar.max_value = 100
	progress_bar.value = 4
	progress_bar.add_theme_stylebox_override("background", panel_style(Color("#24474b"), 9))
	progress_bar.add_theme_stylebox_override("fill", panel_style(C_GREEN, 9))
	center.add_child(progress_bar)
	loading_label = Label.new()
	loading_label.text = "تهيئة المدينة..."
	loading_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	loading_label.add_theme_font_size_override("font_size", 18)
	loading_label.add_theme_color_override("font_color", Color("#c4d9d6"))
	center.add_child(loading_label)

func animate_loading() -> void:
	var stages = [[18,"تحميل الخريطة..."],[42,"تجهيز المباني..."],[66,"تجهيز نظام المهام..."],[86,"تشغيل الإضاءة والظلال..."],[100,"جاهز!"]]
	for st in stages:
		loading_label.text = st[1]
		var tw := create_tween()
		tw.tween_property(progress_bar, "value", st[0], 0.22)
		await tw.finished
	await get_tree().create_timer(0.18).timeout
	show_menu()

func show_menu() -> void:
	if splash: splash.queue_free()
	menu = Control.new()
	menu.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root_ui.add_child(menu)
	var sky := ColorRect.new()
	sky.color = Color("#163c43")
	sky.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	menu.add_child(sky)
	var glow := ColorRect.new()
	glow.color = Color(0.09,0.72,0.56,0.12)
	glow.position = Vector2(80, 80)
	glow.size = Vector2(480, 480)
	menu.add_child(glow)
	var card := PanelContainer.new()
	card.add_theme_stylebox_override("panel", panel_style(Color(0.06,0.16,0.18,0.92), 34, Color(1,1,1,0.12), 2))
	card.set_anchors_preset(Control.PRESET_CENTER)
	card.position = Vector2(-360,-275)
	card.size = Vector2(720,550)
	menu.add_child(card)
	var vb := VBoxContainer.new()
	vb.alignment = BoxContainer.ALIGNMENT_CENTER
	vb.add_theme_constant_override("separation", 18)
	card.add_child(vb)
	var t := Label.new(); t.text = "مدينة الإنجاز"; t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; t.add_theme_font_size_override("font_size", 58); t.add_theme_color_override("font_color", Color("#f3f0d9")); vb.add_child(t)
	var d := Label.new(); d.text = "كل مهمة تنجزها تصبح بيتاً حقيقياً في مدينتك"; d.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; d.add_theme_font_size_override("font_size", 21); d.add_theme_color_override("font_color", Color("#b9d3cf")); vb.add_child(d)
	var start := make_button("ابدأ بناء مدينتي")
	start.pressed.connect(start_game)
	vb.add_child(start)
	var continue_b := make_button("متابعة المدينة")
	continue_b.pressed.connect(start_game)
	vb.add_child(continue_b)
	var how := make_button("كيف ألعب؟", Vector2(270,56))
	how.pressed.connect(func(): save.set_value("meta","tutorial_seen",false); save.save("user://task_city.cfg"); start_game())
	vb.add_child(how)
	var footer := Label.new(); footer.text = "خطط • أنجز • ابنِ • طوّر"; footer.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; footer.add_theme_font_size_override("font_size", 17); footer.add_theme_color_override("font_color", C_GOLD); vb.add_child(footer)

func start_game() -> void:
	if menu: menu.queue_free()
	root_ui.visible = false
	var script := load("res://scripts/game.gd")
	game = Node3D.new()
	game.set_script(script)
	add_child(game)
	game.request_back_to_menu.connect(return_to_menu)

func return_to_menu() -> void:
	if is_instance_valid(game): game.queue_free()
	root_ui.visible = true
	show_menu()
