package com.maimon.screenshotquicktile;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends Activity {
    private static final String TARGET_PACKAGE = "com.maimon.floatingscreenshot";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER_HORIZONTAL);
        root.setPadding(dp(24), dp(36), dp(24), dp(24));
        root.setBackgroundColor(Color.WHITE);

        TextView title = new TextView(this);
        title.setText("اختصار لقطة الشاشة");
        title.setTextSize(24);
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        title.setTextColor(Color.rgb(30,30,30));
        title.setGravity(Gravity.CENTER);
        root.addView(title, new LinearLayout.LayoutParams(-1, -2));

        TextView info = new TextView(this);
        info.setText("اسحب شريط الإشعارات مرتين، اضغط تحرير، ثم أضف مربع «لقطة شاشة» إلى الاختصارات السريعة. بعد ذلك الضغط عليه يفتح تطبيق اللقطة العائمة مباشرة.");
        info.setTextSize(17);
        info.setTextColor(Color.rgb(70,70,70));
        info.setGravity(Gravity.RIGHT);
        LinearLayout.LayoutParams infoLp = new LinearLayout.LayoutParams(-1, -2);
        infoLp.topMargin = dp(22);
        root.addView(info, infoLp);

        Button open = new Button(this);
        open.setText("فتح تطبيق اللقطة العائمة");
        open.setAllCaps(false);
        LinearLayout.LayoutParams btnLp = new LinearLayout.LayoutParams(-1, dp(54));
        btnLp.topMargin = dp(28);
        root.addView(open, btnLp);

        open.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                Intent launch = getPackageManager().getLaunchIntentForPackage(TARGET_PACKAGE);
                if (launch == null) {
                    Toast.makeText(MainActivity.this, "تطبيق اللقطة العائمة غير مثبت", Toast.LENGTH_LONG).show();
                } else {
                    startActivity(launch);
                }
            }
        });

        setContentView(root);
    }

    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }
}
