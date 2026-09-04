package com.maimon.floatingscreenshot;

import android.app.PendingIntent;
import android.content.Intent;
import android.os.Build;
import android.service.quicksettings.TileService;

/**
 * Quick Settings tile kept intentionally stateless for compatibility with
 * older/OEM SystemUI tile editors.
 */
public class ScreenshotTileService extends TileService {

    @Override
    public void onClick() {
        super.onClick();

        if (ScreenshotService.isReady()) {
            try {
                sendBroadcast(new Intent(Intent.ACTION_CLOSE_SYSTEM_DIALOGS));
            } catch (Throwable ignored) {
            }

            try {
                Intent capture = new Intent(this, ScreenshotService.class)
                        .setAction(ScreenshotService.ACTION_CAPTURE)
                        .putExtra(ScreenshotService.EXTRA_DELAY_MS, 650L);
                startService(capture);
            } catch (Throwable ignored) {
            }
            return;
        }

        // First use (or after Android killed/restarted the projection): ask only
        // for Android's screen-capture consent. The app's normal screen never opens.
        Intent consent = new Intent(this, QuickCaptureActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_NO_ANIMATION);
        try {
            if (Build.VERSION.SDK_INT >= 34) {
                PendingIntent pi = PendingIntent.getActivity(
                        this,
                        9401,
                        consent,
                        PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
                startActivityAndCollapse(pi);
            } else {
                startActivityAndCollapse(consent);
            }
        } catch (Throwable ignored) {
        }
    }
}
