package com.maimon.floatingscreenshot;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

public class QuickCaptureActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        overridePendingTransition(0, 0);

        if (ScreenshotService.isReady()) {
            Intent capture = new Intent(this, ScreenshotService.class)
                    .setAction(ScreenshotService.ACTION_CAPTURE)
                    .putExtra(ScreenshotService.EXTRA_DELAY_MS, 700L);
            startService(capture);
        } else {
            Intent setup = new Intent(this, MainActivity.class)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
            startActivity(setup);
        }
        finish();
        overridePendingTransition(0, 0);
    }
}
