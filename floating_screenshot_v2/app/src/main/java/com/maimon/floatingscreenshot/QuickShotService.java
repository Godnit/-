package com.maimon.floatingscreenshot;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.graphics.Bitmap;
import android.graphics.PixelFormat;
import android.hardware.display.DisplayManager;
import android.hardware.display.VirtualDisplay;
import android.media.Image;
import android.media.ImageReader;
import android.media.MediaScannerConnection;
import android.media.projection.MediaProjection;
import android.media.projection.MediaProjectionManager;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.provider.MediaStore;
import android.util.DisplayMetrics;
import android.view.WindowManager;
import android.widget.Toast;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/**
 * Small service dedicated to the Quick Settings screenshot tile.
 * It intentionally has no app UI and no overlay button.
 */
public class QuickShotService extends Service {
    public static final String ACTION_START = "com.maimon.floatingscreenshot.quick.START";
    public static final String ACTION_CAPTURE = "com.maimon.floatingscreenshot.quick.CAPTURE";
    public static final String EXTRA_RESULT_CODE = "result_code";
    public static final String EXTRA_RESULT_DATA = "result_data";
    public static final String EXTRA_DELAY_MS = "delay_ms";

    private static final String CHANNEL_ID = "quick_capture_min_v25";
    private static final int NOTIFICATION_ID = 7315;
    private static volatile boolean ready = false;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private MediaProjection projection;
    private MediaProjection.Callback projectionCallback;
    private WindowManager windowManager;
    private boolean capturing;

    public static boolean isReady() {
        return ready;
    }

    @Override
    public void onCreate() {
        super.onCreate();
        windowManager = (WindowManager) getSystemService(WINDOW_SERVICE);
        createChannel();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent == null) return START_STICKY;
        String action = intent.getAction();

        if (ACTION_START.equals(action)) {
            startForProjection();
            int resultCode = intent.getIntExtra(EXTRA_RESULT_CODE, 0);
            Intent data;
            if (Build.VERSION.SDK_INT >= 33) {
                data = intent.getParcelableExtra(EXTRA_RESULT_DATA, Intent.class);
            } else {
                data = intent.getParcelableExtra(EXTRA_RESULT_DATA);
            }
            if (resultCode != 0 && data != null) {
                beginProjection(resultCode, data);
            }
            return START_STICKY;
        }

        if (ACTION_CAPTURE.equals(action)) {
            if (!ready || projection == null) return START_STICKY;
            capture(intent.getLongExtra(EXTRA_DELAY_MS, 650L));
            return START_STICKY;
        }

        return START_STICKY;
    }

    private void startForProjection() {
        Notification notification = buildNotification();
        if (Build.VERSION.SDK_INT >= 29) {
            startForeground(NOTIFICATION_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION);
        } else {
            // Android 8/9 only need this briefly to let the background service start reliably.
            startForeground(NOTIFICATION_ID, notification);
        }
    }

    private void beginProjection(int resultCode, Intent data) {
        releaseProjection();
        MediaProjectionManager manager = (MediaProjectionManager) getSystemService(MEDIA_PROJECTION_SERVICE);
        projection = manager.getMediaProjection(resultCode, data);
        if (projection == null) {
            ready = false;
            stopForeground(true);
            return;
        }

        projectionCallback = new MediaProjection.Callback() {
            @Override
            public void onStop() {
                ready = false;
                handler.post(() -> {
                    projection = null;
                    stopForeground(true);
                    stopSelf();
                });
            }
        };
        projection.registerCallback(projectionCallback, handler);
        ready = true;

        // On the user's Android 8/9 device MediaProjection can stay alive without
        // a foreground notification. Android 10+ requires the foreground service.
        if (Build.VERSION.SDK_INT <= 28) {
            stopForeground(true);
        }
    }

    private void capture(long delayMs) {
        if (capturing) return;
        capturing = true;
        handler.postDelayed(this::createFrame, Math.max(450L, delayMs));
    }

    private void createFrame() {
        if (!ready || projection == null) {
            capturing = false;
            return;
        }

        DisplayMetrics metrics = new DisplayMetrics();
        windowManager.getDefaultDisplay().getRealMetrics(metrics);
        int width = metrics.widthPixels;
        int height = metrics.heightPixels;
        int density = metrics.densityDpi;

        final ImageReader reader;
        final VirtualDisplay display;
        try {
            reader = ImageReader.newInstance(width, height, PixelFormat.RGBA_8888, 2);
            display = projection.createVirtualDisplay(
                    "quick-shot",
                    width,
                    height,
                    density,
                    DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
                    reader.getSurface(),
                    null,
                    handler);
        } catch (Throwable e) {
            capturing = false;
            return;
        }

        Session session = new Session(reader, display, width, height);
        handler.postDelayed(() -> acquire(session), 180L);
    }

    private void acquire(Session session) {
        if (!capturing) {
            session.close();
            return;
        }

        Image image = null;
        try {
            image = session.reader.acquireLatestImage();
            if (image == null) {
                if (session.tries++ < 16) {
                    handler.postDelayed(() -> acquire(session), 85L);
                } else {
                    session.close();
                    capturing = false;
                }
                return;
            }

            Bitmap bitmap = bitmapFromImage(image, session.width, session.height);
            image.close();
            image = null;
            session.close();
            if (bitmap == null) {
                capturing = false;
                return;
            }

            new Thread(() -> {
                boolean saved = saveBitmap(bitmap);
                bitmap.recycle();
                handler.post(() -> {
                    capturing = false;
                    if (saved) Toast.makeText(this, "تم ✓", Toast.LENGTH_SHORT).show();
                });
            }, "quick-shot-save").start();
        } catch (Throwable e) {
            if (image != null) {
                try { image.close(); } catch (Throwable ignored) {}
            }
            session.close();
            capturing = false;
        }
    }

    private Bitmap bitmapFromImage(Image image, int width, int height) {
        try {
            Image.Plane plane = image.getPlanes()[0];
            ByteBuffer buffer = plane.getBuffer();
            int pixelStride = plane.getPixelStride();
            int rowStride = plane.getRowStride();
            int rowPadding = rowStride - pixelStride * width;
            int paddedWidth = width + Math.max(0, rowPadding / Math.max(1, pixelStride));
            Bitmap full = Bitmap.createBitmap(paddedWidth, height, Bitmap.Config.ARGB_8888);
            full.copyPixelsFromBuffer(buffer);
            if (paddedWidth == width) return full;
            Bitmap cropped = Bitmap.createBitmap(full, 0, 0, width, height);
            full.recycle();
            return cropped;
        } catch (Throwable e) {
            return null;
        }
    }

    private boolean saveBitmap(Bitmap bitmap) {
        String name = "Screenshot_" + new SimpleDateFormat("yyyy-MM-dd-HH-mm-ss", Locale.US).format(new Date()) + ".png";
        try {
            return Build.VERSION.SDK_INT >= 29 ? saveModern(bitmap, name) : saveLegacy(bitmap, name);
        } catch (Throwable e) {
            return false;
        }
    }

    private boolean saveModern(Bitmap bitmap, String name) throws Exception {
        ContentResolver resolver = getContentResolver();
        ContentValues values = new ContentValues();
        values.put(MediaStore.Images.Media.DISPLAY_NAME, name);
        values.put(MediaStore.Images.Media.MIME_TYPE, "image/png");
        values.put(MediaStore.Images.Media.RELATIVE_PATH, chooseRelativePath());
        values.put(MediaStore.Images.Media.IS_PENDING, 1);
        Uri uri = resolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values);
        if (uri == null) return false;

        boolean ok = false;
        try (OutputStream out = resolver.openOutputStream(uri, "w")) {
            if (out != null) {
                ok = bitmap.compress(Bitmap.CompressFormat.PNG, 100, out);
                out.flush();
            }
        }
        if (!ok) {
            resolver.delete(uri, null, null);
            return false;
        }

        ContentValues done = new ContentValues();
        done.put(MediaStore.Images.Media.IS_PENDING, 0);
        resolver.update(uri, done, null, null);
        try (InputStream in = resolver.openInputStream(uri)) {
            if (in == null || in.read() == -1) {
                resolver.delete(uri, null, null);
                return false;
            }
        }
        return true;
    }

    private boolean saveLegacy(Bitmap bitmap, String name) throws Exception {
        File dir = chooseDirectory();
        if (!dir.exists() && !dir.mkdirs()) return false;
        File file = new File(dir, name);
        boolean ok;
        try (OutputStream out = new FileOutputStream(file)) {
            ok = bitmap.compress(Bitmap.CompressFormat.PNG, 100, out);
            out.flush();
        }
        if (!ok || !file.exists() || file.length() <= 0) return false;
        MediaScannerConnection.scanFile(this, new String[]{file.getAbsolutePath()}, new String[]{"image/png"}, null);
        return true;
    }

    private File chooseDirectory() {
        File pictures = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_PICTURES);
        File dcim = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DCIM);
        File[] candidates = new File[]{
                new File(pictures, "Screenshots"),
                new File(dcim, "Screenshots"),
                new File(pictures, "Screenshot"),
                new File(dcim, "Screenshot"),
                new File(pictures, "ScreenShots"),
                new File(dcim, "ScreenShots")
        };
        for (File candidate : candidates) {
            if (candidate.exists() && candidate.isDirectory()) return candidate;
        }
        return candidates[0];
    }

    private String chooseRelativePath() {
        File chosen = chooseDirectory();
        File pictures = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_PICTURES);
        File dcim = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DCIM);
        if (chosen.getParentFile() != null && chosen.getParentFile().equals(dcim)) {
            return Environment.DIRECTORY_DCIM + "/" + chosen.getName();
        }
        if (chosen.getParentFile() != null && chosen.getParentFile().equals(pictures)) {
            return Environment.DIRECTORY_PICTURES + "/" + chosen.getName();
        }
        return Environment.DIRECTORY_PICTURES + "/Screenshots";
    }

    private Notification buildNotification() {
        Notification.Builder builder = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(this, CHANNEL_ID)
                : new Notification.Builder(this);
        return builder
                .setSmallIcon(R.drawable.ic_stat_capture)
                .setContentTitle("لقطة الشاشة")
                .setContentText("جاهز")
                .setOngoing(true)
                .setShowWhen(false)
                .setLocalOnly(true)
                .setCategory(Notification.CATEGORY_SERVICE)
                .setPriority(Notification.PRIORITY_MIN)
                .build();
    }

    private void createChannel() {
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationManager manager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID,
                    "خدمة لقطة الشاشة",
                    NotificationManager.IMPORTANCE_MIN);
            channel.setShowBadge(false);
            channel.setSound(null, null);
            channel.enableVibration(false);
            manager.createNotificationChannel(channel);
        }
    }

    private void releaseProjection() {
        ready = false;
        if (projection != null) {
            try {
                if (projectionCallback != null) projection.unregisterCallback(projectionCallback);
            } catch (Throwable ignored) {}
            try { projection.stop(); } catch (Throwable ignored) {}
            projection = null;
            projectionCallback = null;
        }
    }

    @Override
    public void onDestroy() {
        releaseProjection();
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    private static class Session {
        final ImageReader reader;
        final VirtualDisplay display;
        final int width;
        final int height;
        int tries;

        Session(ImageReader reader, VirtualDisplay display, int width, int height) {
            this.reader = reader;
            this.display = display;
            this.width = width;
            this.height = height;
        }

        void close() {
            try { display.release(); } catch (Throwable ignored) {}
            try { reader.close(); } catch (Throwable ignored) {}
        }
    }
}
