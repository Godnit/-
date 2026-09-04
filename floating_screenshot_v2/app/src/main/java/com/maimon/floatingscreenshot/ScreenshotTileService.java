package com.maimon.floatingscreenshot;

import android.app.PendingIntent;
import android.content.Intent;
import android.os.Build;
import android.service.quicksettings.Tile;
import android.service.quicksettings.TileService;

public class ScreenshotTileService extends TileService {
    @Override
    public void onTileAdded() {
        super.onTileAdded();
        publishStableState();
    }

    @Override
    public void onStartListening() {
        super.onStartListening();
        publishStableState();
    }

    @Override
    public void onClick() {
        super.onClick();

        Intent target = ScreenshotService.isReady()
                ? new Intent(this, QuickCaptureActivity.class)
                : new Intent(this, MainActivity.class);
        target.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);

        try {
            if (Build.VERSION.SDK_INT >= 34) {
                PendingIntent pendingIntent = PendingIntent.getActivity(
                        this,
                        ScreenshotService.isReady() ? 9101 : 9102,
                        target,
                        PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
                startActivityAndCollapse(pendingIntent);
            } else {
                startActivityAndCollapse(target);
            }
        } catch (Throwable ignored) {
            // Keep SystemUI stable even on OEM implementations with buggy tile editors.
        }
    }

    private void publishStableState() {
        Tile tile = getQsTile();
        if (tile == null) return;
        try {
            // Keep the tile deliberately simple. The manifest supplies icon + label.
            // Some older OEM SystemUI editors become unstable when the tile changes
            // icon/label dynamically while the user is dragging it between pages.
            tile.setState(Tile.STATE_INACTIVE);
            tile.updateTile();
        } catch (Throwable ignored) {
        }
    }
}
