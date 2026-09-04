package com.maimon.floatingscreenshot;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

public class QuickCaptureActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        if (!ScreenshotService.isReady()) {
            Intent setup = new Intent(this, MainActivity.class)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
            startActivity(setup);
            finish();
            return;
        }

        // No UI is ever drawn. This activity exists only so Android/OEM SystemUI
        // collapses Quick Settings reliably before the screenshot is requested.
        finish();
        overridePendingTransition(0, 0);

        Intent capture = new Intent(this, ScreenshotService.class)
                .setAction(ScreenshotService.ACTION_CAPTURE)
                .putExtra(ScreenshotService.EXTRA_DELAY_MS, 1050L);
        startService(capture);
    }
}
