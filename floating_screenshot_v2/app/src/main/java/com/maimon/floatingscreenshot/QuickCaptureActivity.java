package com.maimon.floatingscreenshot;

import android.app.Activity;
import android.content.Intent;
import android.media.projection.MediaProjectionManager;
import android.os.Build;
import android.os.Bundle;

/**
 * Invisible helper used only when the Quick Settings tile needs the system
 * MediaProjection consent. It never shows the app UI.
 */
public class QuickCaptureActivity extends Activity {
    private static final int REQ_CAPTURE = 5201;
    private MediaProjectionManager projectionManager;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        overridePendingTransition(0, 0);

        if (ScreenshotService.isReady()) {
            finishAndCapture(850L);
            return;
        }

        projectionManager = (MediaProjectionManager) getSystemService(MEDIA_PROJECTION_SERVICE);
        try {
            startActivityForResult(projectionManager.createScreenCaptureIntent(), REQ_CAPTURE);
        } catch (Throwable e) {
            finish();
            overridePendingTransition(0, 0);
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
                if (Build.VERSION.SDK_INT >= 26) startForegroundService(service);
                else startService(service);
            } catch (Throwable ignored) {
            }

            // Let the foreground MediaProjection service become ready, then capture
            // the screen that was behind the Quick Settings shade.
            finish();
            overridePendingTransition(0, 0);
            getWindow().getDecorView().postDelayed(() -> {
                try {
                    Intent capture = new Intent(getApplicationContext(), ScreenshotService.class)
                            .setAction(ScreenshotService.ACTION_CAPTURE)
                            .putExtra(ScreenshotService.EXTRA_DELAY_MS, 700L);
                    startService(capture);
                } catch (Throwable ignored) {
                }
            }, 350L);
        } else {
            finish();
            overridePendingTransition(0, 0);
        }
    }

    private void finishAndCapture(long delayMs) {
        finish();
        overridePendingTransition(0, 0);
        try {
            Intent capture = new Intent(this, ScreenshotService.class)
                    .setAction(ScreenshotService.ACTION_CAPTURE)
                    .putExtra(ScreenshotService.EXTRA_DELAY_MS, delayMs);
            startService(capture);
        } catch (Throwable ignored) {
        }
    }
}
