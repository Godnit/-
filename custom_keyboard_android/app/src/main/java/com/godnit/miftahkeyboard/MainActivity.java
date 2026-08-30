package com.godnit.miftahkeyboard;

import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.provider.Settings;
import android.view.Gravity;
import android.view.View;
import android.view.inputmethod.InputMethodManager;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.SeekBar;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends Activity {
    static final String PREFS = "miftah_prefs";
    private static final int PICK_BACKGROUND = 31;
    private SharedPreferences prefs;
    private EditText bgHex, keyHex, textHex, accentHex, quick1, quick2, quick3;
    private SeekBar radius, height;
    private CheckBox sound, haptic, numberRow, outline;
    private LinearLayout root;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        buildUi();
    }

    private int dp(int v) { return Math.round(v * getResources().getDisplayMetrics().density); }

    private TextView title(String text, int sp) {
        TextView v = new TextView(this);
        v.setText(text); v.setTextSize(sp); v.setTextColor(Color.rgb(30,35,45));
        v.setPadding(0, dp(10), 0, dp(8));
        return v;
    }

    private Button button(String text) {
        Button b = new Button(this); b.setText(text); b.setAllCaps(false);
        b.setTextSize(15); return b;
    }

    private EditText hexField(String label, String value) {
        EditText e = new EditText(this); e.setHint(label); e.setText(value); e.setSingleLine(true);
        root.addView(e, new LinearLayout.LayoutParams(-1, -2)); return e;
    }

    private void buildUi() {
        ScrollView scroll = new ScrollView(this);
        root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(18), dp(18), dp(18), dp(30));
        scroll.addView(root); setContentView(scroll);

        TextView head = title("مفتاح Keyboard", 30); head.setGravity(Gravity.CENTER_HORIZONTAL); root.addView(head);
        TextView sub = title("كيبورد عربي/إنجليزي خاص بك • الحافظة محلية • بدون صلاحية إنترنت", 15);
        sub.setGravity(Gravity.CENTER_HORIZONTAL); root.addView(sub);

        Button enable = button("1) تفعيل الكيبورد من إعدادات الهاتف");
        enable.setOnClickListener(v -> startActivity(new Intent(Settings.ACTION_INPUT_METHOD_SETTINGS)));
        root.addView(enable);
        Button choose = button("2) اختيار مفتاح Keyboard الآن");
        choose.setOnClickListener(v -> ((InputMethodManager)getSystemService(INPUT_METHOD_SERVICE)).showInputMethodPicker());
        root.addView(choose);

        root.addView(title("الثيم والألوان", 21));
        LinearLayout presets = new LinearLayout(this); presets.setOrientation(LinearLayout.HORIZONTAL);
        String[][] themes = {
            {"ليلي","#111722","#283142","#FFFFFF","#6EA8FF"},
            {"بحري","#0D2630","#17495A","#F5FDFF","#49D3C7"},
            {"وردي","#2A1823","#543246","#FFF6FA","#FF83B3"},
            {"هادئ","#EFEFEF","#FFFFFF","#20242B","#5B70FF"}
        };
        for (String[] t: themes) {
            Button b = button(t[0]);
            b.setOnClickListener(v -> { setThemeValues(t[1],t[2],t[3],t[4]); Toast.makeText(this,"تم تطبيق الثيم",Toast.LENGTH_SHORT).show(); });
            presets.addView(b, new LinearLayout.LayoutParams(0,-2,1));
        }
        root.addView(presets);

        bgHex = hexField("لون خلفية الكيبورد", prefs.getString("bg_color", "#111722"));
        keyHex = hexField("لون خلفية الأزرار", prefs.getString("key_color", "#283142"));
        textHex = hexField("لون الأحرف", prefs.getString("text_color", "#FFFFFF"));
        accentHex = hexField("لون التمييز", prefs.getString("accent_color", "#6EA8FF"));

        root.addView(title("استدارة الأزرار", 15));
        radius = new SeekBar(this); radius.setMax(32); radius.setProgress(prefs.getInt("radius", 13)); root.addView(radius);
        root.addView(title("ارتفاع الأزرار", 15));
        height = new SeekBar(this); height.setMax(26); height.setProgress(prefs.getInt("height_extra", 6)); root.addView(height);

        sound = new CheckBox(this); sound.setText("صوت ضغطة خفيف"); sound.setChecked(prefs.getBoolean("sound", false)); root.addView(sound);
        haptic = new CheckBox(this); haptic.setText("اهتزاز عند الضغط"); haptic.setChecked(prefs.getBoolean("haptic", true)); root.addView(haptic);
        numberRow = new CheckBox(this); numberRow.setText("صف الأرقام دائمًا"); numberRow.setChecked(prefs.getBoolean("numbers", true)); root.addView(numberRow);
        outline = new CheckBox(this); outline.setText("حد مميز حول الأزرار"); outline.setChecked(prefs.getBoolean("outline", false)); root.addView(outline);

        LinearLayout bgActions = new LinearLayout(this); bgActions.setOrientation(LinearLayout.HORIZONTAL);
        Button gradient = button("خلفية متدرجة");
        gradient.setOnClickListener(v -> prefs.edit().putString("bg_style","gradient").apply());
        Button photo = button("اختيار صورة خلفية");
        photo.setOnClickListener(v -> {
            Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT); i.setType("image/*"); i.addCategory(Intent.CATEGORY_OPENABLE);
            startActivityForResult(i, PICK_BACKGROUND);
        });
        Button solid = button("لون فقط"); solid.setOnClickListener(v -> prefs.edit().putString("bg_style","solid").apply());
        bgActions.addView(solid,new LinearLayout.LayoutParams(0,-2,1));
        bgActions.addView(gradient,new LinearLayout.LayoutParams(0,-2,1));
        bgActions.addView(photo,new LinearLayout.LayoutParams(0,-2,1)); root.addView(bgActions);

        root.addView(title("عبارات سريعة تظهر داخل الكيبورد", 21));
        quick1 = new EditText(this); quick1.setText(prefs.getString("quick1","السلام عليكم")); root.addView(quick1);
        quick2 = new EditText(this); quick2.setText(prefs.getString("quick2","شكراً لك")); root.addView(quick2);
        quick3 = new EditText(this); quick3.setText(prefs.getString("quick3","تم بإذن الله")); root.addView(quick3);

        Button save = button("حفظ كل التخصيصات");
        save.setOnClickListener(v -> saveAll()); root.addView(save);

        root.addView(title("ميزات النسخة 1.0", 21));
        TextView info = title("• عربي + إنجليزي + رموز وتشكيل عربي\n• سجل حافظة محلي حتى 30 عنصرًا مع تثبيت العناصر\n• إيموجي وعبارات سريعة\n• ثيمات جاهزة + ألوان HEX + صورة خلفية\n• تغيير استدارة وارتفاع الأزرار\n• سحب زر المسافة يمين/يسار لتحريك المؤشر\n• ضغط مطول على الحذف للحذف المستمر\n• تبديل سريع للكيبورد الآخر\n• لا إنترنت ولا تحليلات ولا تسجيل لما تكتبه", 15);
        root.addView(info);
    }

    private void setThemeValues(String bg, String key, String text, String accent) {
        prefs.edit().putString("bg_color",bg).putString("key_color",key).putString("text_color",text).putString("accent_color",accent).apply();
        bgHex.setText(bg); keyHex.setText(key); textHex.setText(text); accentHex.setText(accent);
    }

    private String safeColor(EditText e, String fallback) {
        try { Color.parseColor(e.getText().toString().trim()); return e.getText().toString().trim(); }
        catch (Exception x) { e.setText(fallback); return fallback; }
    }

    private void saveAll() {
        prefs.edit()
            .putString("bg_color", safeColor(bgHex,"#111722"))
            .putString("key_color", safeColor(keyHex,"#283142"))
            .putString("text_color", safeColor(textHex,"#FFFFFF"))
            .putString("accent_color", safeColor(accentHex,"#6EA8FF"))
            .putInt("radius", radius.getProgress())
            .putInt("height_extra", height.getProgress())
            .putBoolean("sound", sound.isChecked())
            .putBoolean("haptic", haptic.isChecked())
            .putBoolean("numbers", numberRow.isChecked())
            .putBoolean("outline", outline.isChecked())
            .putString("quick1", quick1.getText().toString())
            .putString("quick2", quick2.getText().toString())
            .putString("quick3", quick3.getText().toString())
            .apply();
        Toast.makeText(this,"تم الحفظ — أغلق وافتح الكيبورد لتظهر التغييرات",Toast.LENGTH_LONG).show();
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode,resultCode,data);
        if (requestCode == PICK_BACKGROUND && resultCode == RESULT_OK && data != null && data.getData() != null) {
            Uri uri = data.getData();
            try { getContentResolver().takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION); } catch (Exception ignored) {}
            prefs.edit().putString("bg_style","photo").putString("bg_uri",uri.toString()).apply();
            Toast.makeText(this,"تم حفظ صورة الخلفية",Toast.LENGTH_SHORT).show();
        }
    }
}
