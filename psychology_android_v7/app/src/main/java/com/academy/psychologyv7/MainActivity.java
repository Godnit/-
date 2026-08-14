package com.academy.psychologyv7;

import android.app.Activity;
import android.os.Bundle;
import android.os.SystemClock;
import android.view.View;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

public class MainActivity extends Activity {
    private WebView web;
    private long lastRootBack = 0L;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(0xFF071522);
        getWindow().setNavigationBarColor(0xFF071522);
        web = new WebView(this);
        web.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(true);
        s.setAllowContentAccess(true);
        s.setBuiltInZoomControls(false);
        s.setDisplayZoomControls(false);
        web.setWebViewClient(new WebViewClient());
        setContentView(web);
        web.loadUrl("file:///android_asset/index.html");
    }

    @Override public void onBackPressed() {
        web.evaluateJavascript("(window.appBack?window.appBack():'root')", value -> {
            if (value != null && value.contains("handled")) return;
            long now = SystemClock.elapsedRealtime();
            if (now - lastRootBack < 1800) {
                super.onBackPressed();
            } else {
                lastRootBack = now;
                Toast.makeText(this, "اضغط زر الرجوع مرة أخرى للخروج", Toast.LENGTH_SHORT).show();
            }
        });
    }
}
