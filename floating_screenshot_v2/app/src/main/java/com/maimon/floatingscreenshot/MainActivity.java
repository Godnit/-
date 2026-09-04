package com.maimon.floatingscreenshot;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.media.projection.MediaProjectionManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends Activity {
    private static final int REQ_CAPTURE = 4101;
    private static final int REQ_NOTIFICATIONS = 4102;
    private static final int REQ_STORAGE = 4103;
    private static final int REQ_OVERLAY = 4104;

    private MediaProjectionManager projectionManager;
    private TextView statusText;
    private boolean pendingSetupAfterPermission;
    private boolean pendingShowBubble;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        projectionManager = (MediaProjectionManager) getSystemService(MEDIA_PROJECTION_SERVICE);
        buildUi();
    }

    @Override
    protected void onResume() {
        super.onResume();
        updateStatus();
        if (pendingShowBubble && Settings.canDrawOverlays(this)) {
            pendingShowBubble = false;
            if (ScreenshotService.isReady()) {
                Intent i = new Intent(this, ScreenshotService.class).setAction(ScreenshotService.ACTION_SHOW_BUBBLE);
                startService(i);
            } else {
                beginSetup(true);
            }
        }
    }

    private void buildUi() {
        if (Build.VERSION.SDK_INT >= 17) {
            getWindow().getDecorView().setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
        }

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(20), dp(26), dp(20), dp(20));
        root.setBackgroundColor(Color.WHITE);
        root.setGravity(Gravity.TOP);

        TextView title = new TextView(this);
        title.setText("اللقطة العائمة");
        title.setTextSize(26);
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        title.setTextColor(Color.rgb(20, 20, 20));
        title.setGravity(Gravity.RIGHT);
        root.addView(title, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        TextView subtitle = new TextView(this);
        subtitle.setText("نسخة محسنة: اختصار ثابت في الإعدادات السريعة، وضغطة واحدة ترفع القائمة ثم تلتقط الشاشة مباشرة.");
        subtitle.setTextSize(15);
        subtitle.setTextColor(Color.rgb(85, 85, 85));
        subtitle.setGravity(Gravity.RIGHT);
        subtitle.setLineSpacing(0, 1.2f);
        LinearLayout.LayoutParams subLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        subLp.topMargin = dp(8);
        root.addView(subtitle, subLp);

        statusText = new TextView(this);
        statusText.setTextSize(16);
        statusText.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        statusText.setGravity(Gravity.RIGHT);
        LinearLayout.LayoutParams statusLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        statusLp.topMargin = dp(24);
        statusLp.bottomMargin = dp(16);
        root.addView(statusText, statusLp);

        Button setup = makeButton("تجهيز الالتقاط السريع");
        setup.setOnClickListener(v -> beginSetup(false));
        root.addView(setup, buttonLp());

        Button bubble = makeButton("تشغيل زر اللقطة العائم");
        bubble.setOnClickListener(v -> enableFloatingButton());
        root.addView(bubble, buttonLp());

        Button test = makeButton("اختبار لقطة الآن");
        test.setOnClickListener(v -> {
            if (ScreenshotService.isReady()) {
                Intent i = new Intent(this, ScreenshotService.class).setAction(ScreenshotService.ACTION_CAPTURE);
                i.putExtra(ScreenshotService.EXTRA_DELAY_MS, 250L);
                startService(i);
                moveTaskToBack(true);
            } else {
                beginSetup(false);
            }
        });
        root.addView(test, buttonLp());

        Button stop = makeButton("إيقاف خدمة اللقطة");
        stop.setOnClickListener(v -> {
            Intent i = new Intent(this, ScreenshotService.class).setAction(ScreenshotService.ACTION_STOP);
            startService(i);
            updateStatus();
        });
        root.addView(stop, buttonLp());

        TextView help = new TextView(this);
        help.setText("بعد التجهيز: اسحب شريط الإشعارات ← تحرير ← اسحب «لقطة شاشة» إلى الصفحة الأولى. عند الضغط عليه لن يفتح التطبيق؛ سترتفع لوحة الاختصارات ثم تُحفظ اللقطة تلقائيًا. بعد إعادة تشغيل الهاتف قد تحتاج فتح التطبيق مرة واحدة لتجهيز إذن تسجيل الشاشة من جديد.");
        help.setTextSize(14);
        help.setTextColor(Color.rgb(95, 95, 95));
        help.setGravity(Gravity.RIGHT);
        help.setLineSpacing(0, 1.25f);
        LinearLayout.LayoutParams helpLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        helpLp.topMargin = dp(22);
        root.addView(help, helpLp);

        setContentView(root);
        updateStatus();
    }

    private Button makeButton(String text) {
        Button b = new Button(this);
        b.setText(text);
        b.setAllCaps(false);
        b.setTextSize(16);
        b.setGravity(Gravity.CENTER);
        return b;
    }

    private LinearLayout.LayoutParams buttonLp() {
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(54));
        lp.topMargin = dp(8);
        return lp;
    }

    private void updateStatus() {
        if (statusText == null) return;
        if (ScreenshotService.isReady()) {
            statusText.setText("الحالة: جاهز ✓ — اختصار لقطة الشاشة يعمل مباشرة");
            statusText.setTextColor(Color.rgb(20, 125, 70));
        } else {
            statusText.setText("الحالة: يحتاج تجهيز إذن التقاط الشاشة");
            statusText.setTextColor(Color.rgb(190, 90, 20));
        }
    }

    private void beginSetup(boolean showBubbleAfter) {
        pendingShowBubble = showBubbleAfter;

        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            pendingSetupAfterPermission = true;
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, REQ_NOTIFICATIONS);
            return;
        }

        if (Build.VERSION.SDK_INT <= 28 && checkSelfPermission(Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) {
            pendingSetupAfterPermission = true;
            requestPermissions(new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE}, REQ_STORAGE);
            return;
        }

        if (showBubbleAfter && !Settings.canDrawOverlays(this)) {
            pendingShowBubble = true;
            Intent overlay = new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:" + getPackageName()));
            startActivityForResult(overlay, REQ_OVERLAY);
            return;
        }

        if (ScreenshotService.isReady()) {
            if (showBubbleAfter) {
                Intent i = new Intent(this, ScreenshotService.class).setAction(ScreenshotService.ACTION_SHOW_BUBBLE);
                startService(i);
            }
            updateStatus();
            Toast.makeText(this, "الالتقاط السريع جاهز", Toast.LENGTH_SHORT).show();
            return;
        }

        startActivityForResult(projectionManager.createScreenCaptureIntent(), REQ_CAPTURE);
    }

    private void enableFloatingButton() {
        if (!Settings.canDrawOverlays(this)) {
            pendingShowBubble = true;
            Intent overlay = new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:" + getPackageName()));
            startActivityForResult(overlay, REQ_OVERLAY);
        } else {
            beginSetup(true);
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQ_CAPTURE) {
            if (resultCode == RESULT_OK && data != null) {
                Intent service = new Intent(this, ScreenshotService.class)
                        .setAction(ScreenshotService.ACTION_START)
                        .putExtra(ScreenshotService.EXTRA_RESULT_CODE, resultCode)
                        .putExtra(ScreenshotService.EXTRA_RESULT_DATA, data)
                        .putExtra(ScreenshotService.EXTRA_SHOW_BUBBLE, pendingShowBubble && Settings.canDrawOverlays(this));
                if (Build.VERSION.SDK_INT >= 26) startForegroundService(service);
                else startService(service);
                Toast.makeText(this, "تم التجهيز. الآن الاختصار يلتقط مباشرة", Toast.LENGTH_LONG).show();
                statusText.postDelayed(this::updateStatus, 600);
            } else {
                Toast.makeText(this, "يلزم السماح بالتقاط الشاشة حتى يعمل الاختصار", Toast.LENGTH_LONG).show();
            }
        } else if (requestCode == REQ_OVERLAY) {
            if (Settings.canDrawOverlays(this)) {
                beginSetup(true);
            } else {
                pendingShowBubble = false;
                Toast.makeText(this, "يمكنك استخدام اختصار لقطة الشاشة حتى بدون الزر العائم", Toast.LENGTH_LONG).show();
            }
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQ_NOTIFICATIONS || requestCode == REQ_STORAGE) {
            boolean granted = grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED;
            if (!granted && requestCode == REQ_STORAGE) {
                Toast.makeText(this, "يلزم إذن التخزين لحفظ اللقطات على هذا الإصدار من أندرويد", Toast.LENGTH_LONG).show();
                pendingSetupAfterPermission = false;
                return;
            }
            if (pendingSetupAfterPermission) {
                pendingSetupAfterPermission = false;
                beginSetup(pendingShowBubble);
            }
        }
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
