package com.maimon.floatingscreenshot;

import android.app.PendingIntent;
import android.content.Intent;
import android.graphics.drawable.Icon;
import android.os.Build;
import android.service.quicksettings.Tile;
import android.service.quicksettings.TileService;

public class ScreenshotTileService extends TileService {
    @Override
    public void onStartListening() {
        super.onStartListening();
        updateTileState();
    }

    @Override
    public void onClick() {
        super.onClick();
        Intent target;
        if (ScreenshotService.isReady()) {
            target = new Intent(this, QuickCaptureActivity.class);
        } else {
            target = new Intent(this, MainActivity.class);
        }
        target.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);

        if (Build.VERSION.SDK_INT >= 34) {
            PendingIntent pendingIntent = PendingIntent.getActivity(
                    this,
                    ScreenshotService.isReady() ? 9001 : 9002,
                    target,
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            startActivityAndCollapse(pendingIntent);
        } else {
            startActivityAndCollapse(target);
        }
    }

    private void updateTileState() {
        Tile tile = getQsTile();
        if (tile == null) return;
        try {
            tile.setLabel("لقطة شاشة");
            tile.setIcon(Icon.createWithResource(this, R.drawable.ic_stat_capture));
            tile.setState(ScreenshotService.isReady() ? Tile.STATE_ACTIVE : Tile.STATE_INACTIVE);
            tile.updateTile();
        } catch (Throwable ignored) {
            // Keep tile callbacks deliberately tiny and crash-free for OEM SystemUI editors.
        }
    }
}
