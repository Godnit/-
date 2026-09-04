package com.maimon.floatingscreenshot;

import android.app.PendingIntent;
import android.content.Intent;
import android.os.Build;
import android.service.quicksettings.TileService;
import android.widget.Toast;

/**
 * Stable Quick Settings screenshot tile.
 * It never opens the normal app screen. If capture permission is needed,
 * only Android's MediaProjection consent screen is shown.
 */
public class QuickScreenshotTileService extends TileService {
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
            } catch (Throwable e) {
                Toast.makeText(this, "تعذر التقاط الشاشة", Toast.LENGTH_SHORT).show();
            }
            return;
        }

        Intent consent = new Intent(this, QuickCaptureActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_NO_ANIMATION);

        try {
            if (Build.VERSION.SDK_INT >= 34) {
                PendingIntent pi = PendingIntent.getActivity(
                        this,
                        9601,
                        consent,
                        PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
                startActivityAndCollapse(pi);
            } else {
                startActivityAndCollapse(consent);
            }
        } catch (Throwable e) {
            Toast.makeText(this, "تعذر طلب إذن لقطة الشاشة", Toast.LENGTH_SHORT).show();
        }
    }
}
