package com.maimon.floatingscreenshot;

import android.content.Intent;
import android.service.quicksettings.TileService;
import android.widget.Toast;

/**
 * Quick Settings tile deliberately kept almost stateless.
 *
 * Important for older/OEM SystemUI implementations: do not call updateTile()
 * while the user is editing/dragging tiles. Some devices become unstable or
 * refuse to keep the tile in the requested page when a custom tile changes
 * state during the editor session.
 */
public class ScreenshotTileService extends TileService {

    @Override
    public void onClick() {
        super.onClick();

        // Never open an Activity from the tile. Capture must happen over the
        // screen the user is currently viewing.
        if (!ScreenshotService.isReady()) {
            Toast.makeText(this, "جهّز الالتقاط مرة واحدة من التطبيق", Toast.LENGTH_SHORT).show();
            return;
        }

        // On the user's Android version this closes the notification/quick
        // settings shade without launching our app. On newer builds it may be
        // restricted, so keep it guarded and still request the capture.
        try {
            sendBroadcast(new Intent(Intent.ACTION_CLOSE_SYSTEM_DIALOGS));
        } catch (Throwable ignored) {
        }

        try {
            Intent capture = new Intent(this, ScreenshotService.class)
                    .setAction(ScreenshotService.ACTION_CAPTURE)
                    // Give SystemUI enough time to fully disappear before the frame is read.
                    .putExtra(ScreenshotService.EXTRA_DELAY_MS, 650L);
            startService(capture);
        } catch (Throwable e) {
            Toast.makeText(this, "تعذر التقاط الشاشة", Toast.LENGTH_SHORT).show();
        }
    }
}
