package com.maimon.floatingscreenshot;

import android.app.Activity;
import android.content.Intent;
import android.media.projection.MediaProjectionManager;
import android.os.Build;
import android.os.Bundle;

/** Invisible helper used only for Android's MediaProjection consent dialog. */
public class QuickCaptureActivity extends Activity {
    private static final int REQ_CAPTURE = 5201;
    private MediaProjectionManager projectionManager;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        overridePendingTransition(0, 0);

        if (QuickShotService.isReady()) {
            finishAndCapture(750L);
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
            Intent service = new Intent(this, QuickShotService.class)
                    .setAction(QuickShotService.ACTION_START)
                    .putExtra(QuickShotService.EXTRA_RESULT_CODE, resultCode)
                    .putExtra(QuickShotService.EXTRA_RESULT_DATA, data);
            try {
                if (Build.VERSION.SDK_INT >= 26) startForegroundService(service);
                else startService(service);
            } catch (Throwable ignored) {}

            finishSilently();
            getWindow().getDecorView().postDelayed(() -> {
                try {
                    Intent capture = new Intent(getApplicationContext(), QuickShotService.class)
                            .setAction(QuickShotService.ACTION_CAPTURE)
                            .putExtra(QuickShotService.EXTRA_DELAY_MS, 650L);
                    startService(capture);
                } catch (Throwable ignored) {}
            }, 350L);
        } else {
            finishSilently();
        }
    }

    private void finishAndCapture(long delayMs) {
        finishSilently();
        try {
            Intent capture = new Intent(this, QuickShotService.class)
                    .setAction(QuickShotService.ACTION_CAPTURE)
                    .putExtra(QuickShotService.EXTRA_DELAY_MS, delayMs);
            startService(capture);
        } catch (Throwable ignored) {}
    }

    private void finishSilently() {
        finish();
        overridePendingTransition(0, 0);
    }
}
