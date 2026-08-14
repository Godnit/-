package com.godnit.physicsacademy;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.view.View;
import android.view.Window;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

public class MainActivity extends Activity {
    private WebView webView;
    private long lastExitPress = 0L;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        super.onCreate(savedInstanceState);

        if (getActionBar() != null) getActionBar().hide();
        getWindow().setStatusBarColor(Color.rgb(7, 18, 38));
        getWindow().setNavigationBarColor(Color.rgb(5, 11, 22));

        webView = new WebView(this);
        webView.setBackgroundColor(Color.rgb(7, 16, 31));
        webView.setOverScrollMode(View.OVER_SCROLL_NEVER);
        webView.setVerticalScrollBarEnabled(false);
        webView.setHorizontalScrollBarEnabled(false);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setSupportZoom(false);
        settings.setTextZoom(100);

        webView.setWebViewClient(new WebViewClient());
        webView.setWebChromeClient(new WebChromeClient());
        webView.loadUrl("file:///android_asset/index.html");
        setContentView(webView);
    }

    @Override
    public void onBackPressed() {
        if (webView == null) {
            super.onBackPressed();
            return;
        }
        webView.evaluateJavascript(
            "(window.androidBack ? window.androidBack() : 'exit')",
            value -> {
                if (value != null && value.contains("handled")) return;
                long now = System.currentTimeMillis();
                if (now - lastExitPress < 1800) {
                    finish();
                } else {
                    lastExitPress = now;
                    Toast.makeText(this, "اضغط زر الرجوع مرة أخرى للخروج", Toast.LENGTH_SHORT).show();
                }
            }
        );
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.stopLoading();
            webView.destroy();
        }
        super.onDestroy();
    }
}
