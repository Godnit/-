package com.godnit.miftahkeyboard;

import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.drawable.BitmapDrawable;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.StateListDrawable;
import android.inputmethodservice.InputMethodService;
import android.media.AudioManager;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;
import android.util.Base64;
import android.view.Gravity;
import android.view.HapticFeedbackConstants;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.View;
import android.view.inputmethod.InputConnection;
import android.widget.Button;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

public class MiftahKeyboardService extends InputMethodService {
    private SharedPreferences prefs;
    private LinearLayout root;
    private ClipboardManager clipboard;
    private final List<String> history = new ArrayList<>();
    private final Set<String> pinned = new LinkedHashSet<>();
    private boolean ar = true, shifted = false, symbols = false;
    private String panel = "keys";
    private final Handler handler = new Handler(Looper.getMainLooper());
    private Runnable repeatDelete;
    private float spaceDownX;

    @Override public void onCreate() {
        super.onCreate();
        prefs = getSharedPreferences(MainActivity.PREFS, MODE_PRIVATE);
        clipboard = (ClipboardManager)getSystemService(CLIPBOARD_SERVICE);
        loadClipboardHistory();
        clipboard.addPrimaryClipChangedListener(this::captureClipboard);
    }

    @Override public View onCreateInputView() { return buildKeyboard(); }
    @Override public void onStartInputView(android.view.inputmethod.EditorInfo info, boolean restarting) {
        super.onStartInputView(info,restarting);
        setInputView(buildKeyboard());
    }

    private int dp(int v) { return Math.round(v * getResources().getDisplayMetrics().density); }
    private int color(String key, String fallback) {
        try { return Color.parseColor(prefs.getString(key,fallback)); } catch(Exception e) { return Color.parseColor(fallback); }
    }

    private View buildKeyboard() {
        root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(4),dp(4),dp(4),dp(5));
        applyKeyboardBackground(root);
        root.addView(toolbar());
        if (panel.equals("clipboard")) buildClipboardPanel();
        else if (panel.equals("emoji")) buildEmojiPanel();
        else if (panel.equals("quick")) buildQuickPanel();
        else buildKeyPanel();
        return root;
    }

    private void applyKeyboardBackground(LinearLayout v) {
        String style = prefs.getString("bg_style","gradient");
        int bg = color("bg_color","#111722");
        int accent = color("accent_color","#6EA8FF");
        if (style.equals("photo")) {
            String s = prefs.getString("bg_uri","");
            try (InputStream in = getContentResolver().openInputStream(Uri.parse(s))) {
                Bitmap bitmap = BitmapFactory.decodeStream(in);
                BitmapDrawable d = new BitmapDrawable(getResources(), bitmap); d.setAlpha(185); v.setBackground(d); return;
            } catch(Exception ignored) {}
        }
        GradientDrawable g = new GradientDrawable(style.equals("gradient") ? GradientDrawable.Orientation.TL_BR : GradientDrawable.Orientation.LEFT_RIGHT,
                style.equals("gradient") ? new int[]{bg, blend(bg,accent,0.22f)} : new int[]{bg,bg});
        v.setBackground(g);
    }

    private int blend(int a, int b, float f) {
        int r=(int)(Color.red(a)*(1-f)+Color.red(b)*f), g=(int)(Color.green(a)*(1-f)+Color.green(b)*f), bl=(int)(Color.blue(a)*(1-f)+Color.blue(b)*f);
        return Color.rgb(r,g,bl);
    }

    private LinearLayout toolbar() {
        LinearLayout bar = new LinearLayout(this); bar.setOrientation(LinearLayout.HORIZONTAL); bar.setGravity(Gravity.CENTER);
        String[][] items = {{"📋","clipboard"},{"😊","emoji"},{"★","quick"},{ar?"EN":"ع","lang"},{"⌨","next"},{"⚙","settings"}};
        for(String[] i:items) {
            Button b = mini(i[0]);
            b.setOnClickListener(v -> {
                if(i[1].equals("lang")){ ar=!ar; shifted=false; symbols=false; panel="keys"; }
                else if(i[1].equals("next")){ try { switchToNextInputMethod(false); } catch(Exception ignored){} return; }
                else if(i[1].equals("settings")){ Intent in=new Intent(this,MainActivity.class); in.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK); startActivity(in); return; }
                else panel = panel.equals(i[1]) ? "keys" : i[1];
                setInputView(buildKeyboard());
            });
            bar.addView(b,new LinearLayout.LayoutParams(0,dp(42),1));
        }
        return bar;
    }

    private Button mini(String text) {
        Button b = new Button(this); b.setText(text); b.setAllCaps(false); b.setTextSize(16); b.setTextColor(color("text_color","#FFFFFF"));
        b.setPadding(1,1,1,1); b.setBackground(keyDrawable(true)); return b;
    }

    private void buildKeyPanel() {
        if (prefs.getBoolean("numbers",true)) addRow(new String[]{"1","2","3","4","5","6","7","8","9","0"});
        if(symbols) {
            addRow(new String[]{"!","@","#","$","%","^","&","*","(", ")"});
            addRow(new String[]{"+","-","=","_","/","\\","|","~","`"});
            addRow(new String[]{"[","]","{","}","<",">",":",";","?"});
            addBottom(); return;
        }
        if(ar) {
            addRow(new String[]{"ض","ص","ث","ق","ف","غ","ع","ه","خ","ح","ج","د"});
            addRow(new String[]{"ش","س","ي","ب","ل","ا","ت","ن","م","ك","ط"});
            addRow(new String[]{"ئ","ء","ؤ","ر","لا","ى","ة","و","ز","ظ"});
            addRow(new String[]{"َ","ً","ُ","ٌ","ِ","ٍ","ْ","ّ","ـ"});
        } else {
            addRow(chars(shifted?"QWERTYUIOP":"qwertyuiop"));
            addRow(chars(shifted?"ASDFGHJKL":"asdfghjkl"));
            String[] last = chars(shifted?"ZXCVBNM":"zxcvbnm");
            LinearLayout row = row(); row.addView(key("{SHIFT}"),new LinearLayout.LayoutParams(0,keyH(),1.25f));
            for(String s:last) row.addView(key(s),new LinearLayout.LayoutParams(0,keyH(),1));
            row.addView(key("{BKSP}"),new LinearLayout.LayoutParams(0,keyH(),1.25f)); root.addView(row);
        }
        addBottom();
    }

    private String[] chars(String s) {
        String[] out=new String[s.length()]; for(int i=0;i<s.length();i++) out[i]=String.valueOf(s.charAt(i)); return out;
    }

    private void addBottom() {
        LinearLayout row=row();
        row.addView(key("{SYM}"),new LinearLayout.LayoutParams(0,keyH(),1.15f));
        row.addView(key(ar?"،":","),new LinearLayout.LayoutParams(0,keyH(),0.8f));
        row.addView(key("{SPACE}"),new LinearLayout.LayoutParams(0,keyH(),3.4f));
        row.addView(key("."),new LinearLayout.LayoutParams(0,keyH(),0.8f));
        if(ar) row.addView(key("{BKSP}"),new LinearLayout.LayoutParams(0,keyH(),1.05f));
        row.addView(key("{ENTER}"),new LinearLayout.LayoutParams(0,keyH(),1.05f)); root.addView(row);
    }

    private int keyH(){ return dp(46 + prefs.getInt("height_extra",6)); }
    private LinearLayout row(){ LinearLayout r=new LinearLayout(this); r.setOrientation(LinearLayout.HORIZONTAL); r.setGravity(Gravity.CENTER); return r; }
    private void addRow(String[] keys){ LinearLayout r=row(); for(String s:keys) r.addView(key(s),new LinearLayout.LayoutParams(0,keyH(),1)); root.addView(r); }

    private Button key(String code) {
        Button b=new Button(this); b.setTag(code); b.setAllCaps(false); b.setText(label(code)); b.setTextSize(code.equals("{SPACE}")?12:18);
        b.setTextColor(color("text_color","#FFFFFF")); b.setGravity(Gravity.CENTER); b.setPadding(1,1,1,1); b.setBackground(keyDrawable(false));
        if(code.equals("{BKSP}")) configureBackspace(b);
        else if(code.equals("{SPACE}")) configureSpace(b);
        else b.setOnClickListener(v -> press(code,v));
        return b;
    }

    private String label(String code) {
        switch(code){case "{BKSP}":return "⌫";case "{ENTER}":return "↵";case "{SPACE}":return ar?"العربية • اسحب لتحريك المؤشر":"English • swipe cursor";case "{SYM}":return symbols?"ABC":"?123";case "{SHIFT}":return shifted?"⇧":"⇧";default:return code;}
    }

    private StateListDrawable keyDrawable(boolean accentKey) {
        int normal = accentKey ? blend(color("key_color","#283142"),color("accent_color","#6EA8FF"),0.25f) : color("key_color","#283142");
        int pressed = blend(normal,color("accent_color","#6EA8FF"),0.45f);
        StateListDrawable state = new StateListDrawable(); state.addState(new int[]{android.R.attr.state_pressed}, shape(pressed)); state.addState(new int[]{},shape(normal)); return state;
    }
    private GradientDrawable shape(int fill) {
        GradientDrawable g=new GradientDrawable(); g.setColor(fill); g.setCornerRadius(dp(prefs.getInt("radius",13)));
        if(prefs.getBoolean("outline",false)) g.setStroke(dp(1),color("accent_color","#6EA8FF")); return g;
    }

    private void feedback(View v) {
        if(prefs.getBoolean("haptic",true)) v.performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP);
        if(prefs.getBoolean("sound",false)) ((AudioManager)getSystemService(AUDIO_SERVICE)).playSoundEffect(AudioManager.FX_KEY_CLICK,0.18f);
    }

    private void press(String code, View v) {
        feedback(v); InputConnection ic=getCurrentInputConnection(); if(ic==null)return;
        if(code.equals("{ENTER}")){ ic.sendKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN,KeyEvent.KEYCODE_ENTER)); ic.sendKeyEvent(new KeyEvent(KeyEvent.ACTION_UP,KeyEvent.KEYCODE_ENTER)); }
        else if(code.equals("{SYM}")){ symbols=!symbols; panel="keys"; setInputView(buildKeyboard()); }
        else if(code.equals("{SHIFT}")){ shifted=!shifted; setInputView(buildKeyboard()); }
        else ic.commitText(code,1);
    }

    private void configureBackspace(Button b) {
        b.setOnTouchListener((v,e)->{
            if(e.getAction()==MotionEvent.ACTION_DOWN){ feedback(v); deleteOne(); repeatDelete=()->{ deleteOne(); handler.postDelayed(repeatDelete,65); }; handler.postDelayed(repeatDelete,340); return true; }
            if(e.getAction()==MotionEvent.ACTION_UP||e.getAction()==MotionEvent.ACTION_CANCEL){ if(repeatDelete!=null)handler.removeCallbacks(repeatDelete); return true; }
            return false;
        });
    }
    private void deleteOne(){ InputConnection ic=getCurrentInputConnection(); if(ic!=null) ic.deleteSurroundingText(1,0); }

    private void configureSpace(Button b) {
        b.setOnTouchListener((v,e)->{
            if(e.getAction()==MotionEvent.ACTION_DOWN){ spaceDownX=e.getX(); feedback(v); return true; }
            if(e.getAction()==MotionEvent.ACTION_UP){ float dx=e.getX()-spaceDownX; InputConnection ic=getCurrentInputConnection(); if(ic==null)return true;
                if(Math.abs(dx)>dp(34)){ int key=dx>0?KeyEvent.KEYCODE_DPAD_RIGHT:KeyEvent.KEYCODE_DPAD_LEFT; int n=Math.min(6,Math.max(1,(int)(Math.abs(dx)/dp(34)))); for(int i=0;i<n;i++){ic.sendKeyEvent(new KeyEvent(KeyEvent.ACTION_DOWN,key));ic.sendKeyEvent(new KeyEvent(KeyEvent.ACTION_UP,key));} }
                else ic.commitText(" ",1); return true; }
            return true;
        });
    }

    private void buildEmojiPanel() {
        root.addView(panelTitle("الإيموجي — اضغط لإدراج الرمز"));
        String[] em={"😀","😂","😍","🥰","😎","😭","😡","🤔","👍","👎","👏","🙏","❤️","💔","🔥","✨","✅","❌","⭐","🎉","💯","😊","😉","😅","🤝","👌","💪","🙌","🌹","☕","📌","📱","💻","🎮","🚗","✈️","🌙","☀️","🎁","💡"};
        for(int i=0;i<em.length;i+=8){ LinearLayout r=row(); for(int j=i;j<Math.min(i+8,em.length);j++){ Button b=key(em[j]); r.addView(b,new LinearLayout.LayoutParams(0,keyH(),1)); } root.addView(r); }
    }

    private TextView panelTitle(String t){ TextView v=new TextView(this);v.setText(t);v.setTextColor(color("text_color","#FFFFFF"));v.setTextSize(14);v.setGravity(Gravity.CENTER);v.setPadding(4,dp(6),4,dp(6));return v; }

    private void buildQuickPanel() {
        root.addView(panelTitle("عباراتك السريعة"));
        String[] q={prefs.getString("quick1","السلام عليكم"),prefs.getString("quick2","شكراً لك"),prefs.getString("quick3","تم بإذن الله")};
        for(String s:q){ if(s.trim().isEmpty())continue; Button b=key(s); b.setTextSize(16); b.setOnClickListener(v->{ InputConnection ic=getCurrentInputConnection(); if(ic!=null)ic.commitText(s,1); feedback(v); }); root.addView(b,new LinearLayout.LayoutParams(-1,keyH())); }
    }

    private void captureClipboard() {
        try {
            if(!clipboard.hasPrimaryClip())return; ClipData c=clipboard.getPrimaryClip(); if(c==null||c.getItemCount()==0)return;
            CharSequence cs=c.getItemAt(0).coerceToText(this); if(cs==null)return; String s=cs.toString().trim(); if(s.isEmpty())return;
            history.remove(s); history.add(0,s); while(history.size()>30) history.remove(history.size()-1); saveClipboardHistory();
            if(panel.equals("clipboard")) setInputView(buildKeyboard());
        } catch(Exception ignored){}
    }

    private void buildClipboardPanel() {
        captureClipboard(); root.addView(panelTitle("الحافظة • اضغط للصق • ضغط مطوّل للتثبيت"));
        LinearLayout actions=row(); Button clear=mini("مسح السجل"); clear.setOnClickListener(v->{ history.clear(); pinned.clear(); saveClipboardHistory(); setInputView(buildKeyboard()); });
        Button current=mini("إضافة الحالي"); current.setOnClickListener(v->{ captureClipboard(); setInputView(buildKeyboard()); }); actions.addView(clear,new LinearLayout.LayoutParams(0,dp(42),1));actions.addView(current,new LinearLayout.LayoutParams(0,dp(42),1));root.addView(actions);
        List<String> shown=new ArrayList<>(); for(String p:pinned) if(history.contains(p))shown.add(p); for(String h:history) if(!shown.contains(h))shown.add(h);
        if(shown.isEmpty()){ root.addView(panelTitle("لا يوجد نص في السجل بعد")); return; }
        HorizontalScrollView hsv=new HorizontalScrollView(this); LinearLayout list=new LinearLayout(this); list.setOrientation(LinearLayout.HORIZONTAL);
        for(String s:shown){ Button b=key(shortText(s)); if(pinned.contains(s))b.setText("📌 "+shortText(s)); b.setTextSize(14);
            b.setOnClickListener(v->{InputConnection ic=getCurrentInputConnection();if(ic!=null)ic.commitText(s,1);feedback(v);});
            b.setOnLongClickListener(v->{if(pinned.contains(s))pinned.remove(s);else pinned.add(s);saveClipboardHistory();setInputView(buildKeyboard());return true;});
            list.addView(b,new LinearLayout.LayoutParams(dp(170),dp(72))); }
        hsv.addView(list); root.addView(hsv,new LinearLayout.LayoutParams(-1,dp(78)));
    }

    private String shortText(String s){ String x=s.replace('\n',' '); return x.length()>32?x.substring(0,32)+"…":x; }

    private void loadClipboardHistory() {
        history.clear(); pinned.clear(); decodeList(prefs.getString("clip_history",""),history); List<String> ps=new ArrayList<>(); decodeList(prefs.getString("clip_pinned",""),ps); pinned.addAll(ps);
    }
    private void saveClipboardHistory(){ prefs.edit().putString("clip_history",encodeList(history)).putString("clip_pinned",encodeList(new ArrayList<>(pinned))).apply(); }
    private String encodeList(List<String> list){ StringBuilder b=new StringBuilder(); for(String s:list){ if(b.length()>0)b.append('\n'); b.append(Base64.encodeToString(s.getBytes(StandardCharsets.UTF_8),Base64.NO_WRAP)); } return b.toString(); }
    private void decodeList(String raw,List<String> out){ if(raw.isEmpty())return; for(String line:raw.split("\\n")){try{out.add(new String(Base64.decode(line,Base64.NO_WRAP),StandardCharsets.UTF_8));}catch(Exception ignored){}} }
}
