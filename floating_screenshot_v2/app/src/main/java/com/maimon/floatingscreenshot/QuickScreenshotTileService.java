package com.maimon.floatingscreenshot;

import android.app.PendingIntent;
import android.content.Intent;
import android.os.Build;
import android.service.quicksettings.TileService;

/** Fresh tile component so SystemUI treats it as a clean shortcut after updates. */
public class QuickScreenshotTileService extends TileService {
    @Override
    public void onClick() {
        super.onClick();

        if (QuickShotService.isReady()) {
            try {
                sendBroadcast(new Intent(Intent.ACTION_CLOSE_SYSTEM_DIALOGS));
            } catch (Throwable ignored) {}

            try {
                Intent capture = new Intent(this, QuickShotService.class)
                        .setAction(QuickShotService.ACTION_CAPTURE)
                        .putExtra(QuickShotService.EXTRA_DELAY_MS, 650L);
                startService(capture);
            } catch (Throwable ignored) {}
            return;
        }

        // No app screen: only Android's own capture-consent dialog is shown when needed.
        Intent consent = new Intent(this, QuickCaptureActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_NO_ANIMATION);
        try {
            if (Build.VERSION.SDK_INT >= 34) {
                PendingIntent pi = PendingIntent.getActivity(
                        this,
                        9501,
                        consent,
                        PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
                startActivityAndCollapse(pi);
            } else {
                startActivityAndCollapse(consent);
            }
        } catch (Throwable ignored) {}
    }
}
