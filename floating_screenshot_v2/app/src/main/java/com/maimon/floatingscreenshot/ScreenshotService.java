package com.maimon.floatingscreenshot;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.graphics.drawable.GradientDrawable;
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
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewConfiguration;
import android.view.WindowManager;
import android.widget.ImageView;
import android.widget.Toast;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public class ScreenshotService extends Service {
    public static final String ACTION_START = "com.maimon.floatingscreenshot.START";
    public static final String ACTION_STOP = "com.maimon.floatingscreenshot.STOP";
    public static final String ACTION_CAPTURE = "com.maimon.floatingscreenshot.CAPTURE";
    public static final String ACTION_SHOW_BUBBLE = "com.maimon.floatingscreenshot.SHOW_BUBBLE";

    public static final String EXTRA_RESULT_CODE = "result_code";
    public static final String EXTRA_RESULT_DATA = "result_data";
    public static final String EXTRA_SHOW_BUBBLE = "show_bubble";
    public static final String EXTRA_DELAY_MS = "delay_ms";

    private static final String CHANNEL_ID = "floating_capture";
    private static final int NOTIFICATION_ID = 7301;
    private static volatile boolean ready = false;

    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private MediaProjection mediaProjection;
    private MediaProjection.Callback projectionCallback;
    private WindowManager windowManager;
    private ImageView floatingButton;
    private WindowManager.LayoutParams floatingParams;
    private boolean capturing;

    public static boolean isReady() {
        return ready;
    }

    @Override
    public void onCreate() {
        super.onCreate();
        windowManager = (WindowManager) getSystemService(WINDOW_SERVICE);
        createNotificationChannel();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent == null) return START_STICKY;
        String action = intent.getAction();

        if (ACTION_STOP.equals(action)) {
            stopEverything();
            return START_NOT_STICKY;
        }

        if (ACTION_START.equals(action)) {
            startAsForeground();
            int resultCode = intent.getIntExtra(EXTRA_RESULT_CODE, 0);
            Intent resultData;
            if (Build.VERSION.SDK_INT >= 33) {
                resultData = intent.getParcelableExtra(EXTRA_RESULT_DATA, Intent.class);
            } else {
                resultData = intent.getParcelableExtra(EXTRA_RESULT_DATA);
            }
            if (resultCode != 0 && resultData != null) {
                startProjection(resultCode, resultData);
                if (intent.getBooleanExtra(EXTRA_SHOW_BUBBLE, false)) showFloatingButton();
            }
            return START_STICKY;
        }

        if (ACTION_SHOW_BUBBLE.equals(action)) {
            if (ready) showFloatingButton();
            return START_STICKY;
        }

        if (ACTION_CAPTURE.equals(action)) {
            if (!ready || mediaProjection == null) {
                Toast.makeText(this, "جهّز الالتقاط أولًا", Toast.LENGTH_SHORT).show();
                return START_STICKY;
            }
            requestCapture(intent.getLongExtra(EXTRA_DELAY_MS, 250L));
            return START_STICKY;
        }

        return START_STICKY;
    }

    private void startAsForeground() {
        Notification notification = buildNotification();
        if (Build.VERSION.SDK_INT >= 29) {
            startForeground(NOTIFICATION_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION);
        } else {
            startForeground(NOTIFICATION_ID, notification);
        }
    }

    private void startProjection(int resultCode, Intent resultData) {
        releaseProjection();
        MediaProjectionManager manager = (MediaProjectionManager) getSystemService(MEDIA_PROJECTION_SERVICE);
        mediaProjection = manager.getMediaProjection(resultCode, resultData);
        if (mediaProjection == null) {
            ready = false;
            Toast.makeText(this, "تعذر بدء الالتقاط", Toast.LENGTH_SHORT).show();
            return;
        }

        projectionCallback = new MediaProjection.Callback() {
            @Override
            public void onStop() {
                ready = false;
                mainHandler.post(() -> {
                    removeFloatingButton();
                    stopSelf();
                });
            }
        };
        mediaProjection.registerCallback(projectionCallback, mainHandler);
        ready = true;
    }

    private void requestCapture(long delayMs) {
        if (capturing) return;
        capturing = true;
        setFloatingVisible(false);
        mainHandler.postDelayed(this::beginCaptureSession, Math.max(180L, delayMs));
    }

    private void beginCaptureSession() {
        if (!ready || mediaProjection == null) {
            finishCapture(false, "غير جاهز");
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
            display = mediaProjection.createVirtualDisplay(
                    "floating-screenshot",
                    width,
                    height,
                    density,
                    DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
                    reader.getSurface(),
                    null,
                    mainHandler);
        } catch (Throwable e) {
            finishCapture(false, "فشل الالتقاط");
            return;
        }

        CaptureSession session = new CaptureSession(reader, display, width, height);
        mainHandler.postDelayed(() -> tryAcquire(session), 180L);
    }

    private void tryAcquire(CaptureSession session) {
        if (!capturing) {
            session.close();
            return;
        }

        Image image = null;
        try {
            image = session.reader.acquireLatestImage();
            if (image == null) {
                if (session.tries++ < 16) {
                    mainHandler.postDelayed(() -> tryAcquire(session), 90L);
                } else {
                    session.close();
                    finishCapture(false, "أعد المحاولة");
                }
                return;
            }

            Bitmap bitmap = bitmapFromImage(image, session.width, session.height);
            image.close();
            image = null;
            session.close();

            if (bitmap == null) {
                finishCapture(false, "فشل الالتقاط");
                return;
            }

            new Thread(() -> {
                boolean ok = saveBitmap(bitmap);
                bitmap.recycle();
                mainHandler.post(() -> finishCapture(ok, ok ? null : "فشل الحفظ"));
            }, "screenshot-save").start();
        } catch (Throwable e) {
            if (image != null) {
                try { image.close(); } catch (Throwable ignored) {}
            }
            session.close();
            finishCapture(false, "فشل الالتقاط");
        }
    }

    private Bitmap bitmapFromImage(Image image, int width, int height) {
        try {
            Image.Plane[] planes = image.getPlanes();
            if (planes == null || planes.length == 0) return null;
            Image.Plane plane = planes[0];
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
        String name = "Screenshot_" + new SimpleDateFormat("yyyyMMdd_HHmmss_SSS", Locale.US).format(new Date()) + ".png";
        try {
            if (Build.VERSION.SDK_INT >= 29) {
                return saveModern(bitmap, name);
            } else {
                return saveLegacy(bitmap, name);
            }
        } catch (Throwable e) {
            return false;
        }
    }

    private boolean saveModern(Bitmap bitmap, String name) throws Exception {
        ContentResolver resolver = getContentResolver();
        String relativePath = chooseExistingScreenshotRelativePath();

        ContentValues values = new ContentValues();
        values.put(MediaStore.Images.Media.DISPLAY_NAME, name);
        values.put(MediaStore.Images.Media.MIME_TYPE, "image/png");
        values.put(MediaStore.Images.Media.RELATIVE_PATH, relativePath);
        values.put(MediaStore.Images.Media.IS_PENDING, 1);

        Uri uri = resolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values);
        if (uri == null) return false;

        boolean compressed = false;
        try (OutputStream out = resolver.openOutputStream(uri, "w")) {
            if (out != null) {
                compressed = bitmap.compress(Bitmap.CompressFormat.PNG, 100, out);
                out.flush();
            }
        }

        if (!compressed) {
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
        File dir = chooseExistingScreenshotDirectory();
        if (!dir.exists() && !dir.mkdirs()) return false;

        File file = new File(dir, name);
        boolean compressed;
        try (OutputStream out = new FileOutputStream(file)) {
            compressed = bitmap.compress(Bitmap.CompressFormat.PNG, 100, out);
            out.flush();
        }

        if (!compressed || !file.exists() || file.length() <= 0) {
            try { file.delete(); } catch (Throwable ignored) {}
            return false;
        }

        MediaScannerConnection.scanFile(
                this,
                new String[]{file.getAbsolutePath()},
                new String[]{"image/png"},
                null);
        return true;
    }

    private File chooseExistingScreenshotDirectory() {
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

    private String chooseExistingScreenshotRelativePath() {
        File chosen = chooseExistingScreenshotDirectory();
        File pictures = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_PICTURES);
        File dcim = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DCIM);
        String name = chosen.getName();
        if (chosen.getParentFile() != null && chosen.getParentFile().equals(dcim)) {
            return Environment.DIRECTORY_DCIM + "/" + name;
        }
        if (chosen.getParentFile() != null && chosen.getParentFile().equals(pictures)) {
            return Environment.DIRECTORY_PICTURES + "/" + name;
        }
        return Environment.DIRECTORY_PICTURES + "/Screenshots";
    }

    private void finishCapture(boolean success, String error) {
        capturing = false;
        mainHandler.postDelayed(() -> setFloatingVisible(true), 170L);
        if (success) {
            Toast.makeText(this, "تم ✓", Toast.LENGTH_SHORT).show();
        } else if (error != null) {
            Toast.makeText(this, error, Toast.LENGTH_SHORT).show();
        }
    }

    private void showFloatingButton() {
        if (floatingButton != null || !android.provider.Settings.canDrawOverlays(this)) return;

        ImageView button = new ImageView(this);
        button.setImageResource(R.drawable.ic_stat_capture);
        button.setPadding(dp(13), dp(13), dp(13), dp(13));
        button.setColorFilter(Color.WHITE);
        GradientDrawable bg = new GradientDrawable();
        bg.setShape(GradientDrawable.OVAL);
        bg.setColor(Color.rgb(37, 99, 235));
        bg.setStroke(dp(1), Color.argb(50, 0, 0, 0));
        button.setBackground(bg);
        if (Build.VERSION.SDK_INT >= 21) button.setElevation(dp(7));

        int type = Build.VERSION.SDK_INT >= 26
                ? WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
                : WindowManager.LayoutParams.TYPE_PHONE;
        floatingParams = new WindowManager.LayoutParams(
                dp(58), dp(58), type,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE | WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT);
        floatingParams.gravity = Gravity.TOP | Gravity.START;
        floatingParams.x = dp(12);
        floatingParams.y = dp(180);

        final int slop = ViewConfiguration.get(this).getScaledTouchSlop();
        button.setOnTouchListener(new View.OnTouchListener() {
            float downRawX, downRawY;
            int downX, downY;
            boolean moved;

            @Override
            public boolean onTouch(View v, MotionEvent event) {
                switch (event.getActionMasked()) {
                    case MotionEvent.ACTION_DOWN:
                        downRawX = event.getRawX();
                        downRawY = event.getRawY();
                        downX = floatingParams.x;
                        downY = floatingParams.y;
                        moved = false;
                        return true;
                    case MotionEvent.ACTION_MOVE:
                        float dx = event.getRawX() - downRawX;
                        float dy = event.getRawY() - downRawY;
                        if (Math.abs(dx) > slop || Math.abs(dy) > slop) moved = true;
                        floatingParams.x = downX + Math.round(dx);
                        floatingParams.y = downY + Math.round(dy);
                        try { windowManager.updateViewLayout(button, floatingParams); } catch (Throwable ignored) {}
                        return true;
                    case MotionEvent.ACTION_UP:
                        if (!moved) requestCapture(220L);
                        return true;
                    default:
                        return true;
                }
            }
        });

        floatingButton = button;
        try {
            windowManager.addView(button, floatingParams);
        } catch (Throwable e) {
            floatingButton = null;
        }
    }

    private void setFloatingVisible(boolean visible) {
        if (floatingButton != null) floatingButton.setVisibility(visible ? View.VISIBLE : View.INVISIBLE);
    }

    private void removeFloatingButton() {
        if (floatingButton != null) {
            try { windowManager.removeView(floatingButton); } catch (Throwable ignored) {}
            floatingButton = null;
        }
    }

    private void releaseProjection() {
        ready = false;
        if (mediaProjection != null) {
            try {
                if (projectionCallback != null) mediaProjection.unregisterCallback(projectionCallback);
            } catch (Throwable ignored) {}
            try { mediaProjection.stop(); } catch (Throwable ignored) {}
            mediaProjection = null;
            projectionCallback = null;
        }
    }

    private void stopEverything() {
        capturing = false;
        removeFloatingButton();
        releaseProjection();
        stopForeground(true);
        stopSelf();
    }

    @Override
    public void onDestroy() {
        removeFloatingButton();
        releaseProjection();
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    private Notification buildNotification() {
        Intent open = new Intent(this, MainActivity.class);
        PendingIntent pending = PendingIntent.getActivity(
                this,
                0,
                open,
                PendingIntent.FLAG_UPDATE_CURRENT | (Build.VERSION.SDK_INT >= 23 ? PendingIntent.FLAG_IMMUTABLE : 0));
        Notification.Builder b = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(this, CHANNEL_ID)
                : new Notification.Builder(this);
        return b.setSmallIcon(R.drawable.ic_stat_capture)
                .setContentTitle("اللقطة العائمة")
                .setContentText("الالتقاط السريع جاهز")
                .setContentIntent(pending)
                .setOngoing(true)
                .setCategory(Notification.CATEGORY_SERVICE)
                .build();
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID,
                    "اللقطة العائمة",
                    NotificationManager.IMPORTANCE_LOW);
            channel.setDescription("إبقاء الالتقاط السريع جاهزًا");
            channel.setShowBadge(false);
            nm.createNotificationChannel(channel);
        }
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private static class CaptureSession {
        final ImageReader reader;
        final VirtualDisplay display;
        final int width;
        final int height;
        int tries;

        CaptureSession(ImageReader reader, VirtualDisplay display, int width, int height) {
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
