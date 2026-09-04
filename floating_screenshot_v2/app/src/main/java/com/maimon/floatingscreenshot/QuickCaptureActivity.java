package com.maimon.floatingscreenshot;

import android.app.Activity;
import android.content.Intent;
import android.media.projection.MediaProjectionManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;

/**
 * Invisible helper used only for Android's screen-capture consent dialog.
 * The normal app UI is never opened from the Quick Settings tile.
 */
public class QuickCaptureActivity extends Activity {
    private static final int REQ_CAPTURE = 5201;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private MediaProjectionManager projectionManager;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        overridePendingTransition(0, 0);

        if (ScreenshotService.isReady()) {
            finishSilently();
            requestCapture(700L);
            return;
        }

        projectionManager = (MediaProjectionManager) getSystemService(MEDIA_PROJECTION_SERVICE);
        try {
            startActivityForResult(projectionManager.createScreenCaptureIntent(), REQ_CAPTURE);
        } catch (Throwable e) {
            finishSilently();
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != REQ_CAPTURE) return;

        if (resultCode == RESULT_OK && data != null) {
            Intent service = new Intent(this, ScreenshotService.class)
                    .setAction(ScreenshotService.ACTION_START)
                    .putExtra(ScreenshotService.EXTRA_RESULT_CODE, resultCode)
                    .putExtra(ScreenshotService.EXTRA_RESULT_DATA, data)
                    .putExtra(ScreenshotService.EXTRA_SHOW_BUBBLE, false);

            try {
                if (Build.VERSION.SDK_INT >= 26) {
                    startForegroundService(service);
                } else {
                    startService(service);
                }
            } catch (Throwable e) {
                finishSilently();
                return;
            }

            finishSilently();
            handler.postDelayed(() -> requestCapture(700L), 450L);
        } else {
            finishSilently();
        }
    }

    private void requestCapture(long delayMs) {
        try {
            Intent capture = new Intent(getApplicationContext(), ScreenshotService.class)
                    .setAction(ScreenshotService.ACTION_CAPTURE)
                    .putExtra(ScreenshotService.EXTRA_DELAY_MS, delayMs);
            startService(capture);
        } catch (Throwable ignored) {
        }
    }

    private void finishSilently() {
        try { finish(); } catch (Throwable ignored) {}
        try { overridePendingTransition(0, 0); } catch (Throwable ignored) {}
    }
}
