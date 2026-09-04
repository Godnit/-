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
                Toast.makeText(this, "افتح اللقطة العائمة مرة واحدة واضغط تجهيز الالتقاط السريع", Toast.LENGTH_LONG).show();
                return START_STICKY;
            }
            long delay = intent.getLongExtra(EXTRA_DELAY_MS, 250L);
            requestCapture(delay);
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
            Toast.makeText(this, "تعذر بدء التقاط الشاشة", Toast.LENGTH_LONG).show();
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
        long safeDelay = Math.max(120L, delayMs);
        mainHandler.postDelayed(this::beginCaptureSession, safeDelay);
    }

    private void beginCaptureSession() {
        if (!ready || mediaProjection == null) {
            finishCapture(false, "خدمة التقاط الشاشة غير جاهزة");
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
        } catch (Exception e) {
            finishCapture(false, "تعذر إنشاء لقطة الشاشة");
            return;
        }

        CaptureSession session = new CaptureSession(reader, display, width, height);
        mainHandler.postDelayed(() -> tryAcquire(session), 140L);
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
                if (session.tries++ < 12) {
                    mainHandler.postDelayed(() -> tryAcquire(session), 85L);
                } else {
                    session.close();
                    finishCapture(false, "لم تصل صورة من الشاشة، حاول مرة أخرى");
                }
                return;
            }

            Bitmap bitmap = bitmapFromImage(image, session.width, session.height);
            image.close();
            image = null;
            session.close();
            if (bitmap == null) {
                finishCapture(false, "تعذر قراءة صورة الشاشة");
                return;
            }

            new Thread(() -> {
                boolean ok = saveBitmap(bitmap);
                bitmap.recycle();
                mainHandler.post(() -> finishCapture(ok, ok ? null : "تعذر حفظ لقطة الشاشة"));
            }, "screenshot-save").start();
        } catch (Exception e) {
            if (image != null) image.close();
            session.close();
            finishCapture(false, "حدث خطأ أثناء التقاط الشاشة");
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
            Bitmap cropped;
            if (paddedWidth == width) {
                cropped = full;
            } else {
                cropped = Bitmap.createBitmap(full, 0, 0, width, height);
                full.recycle();
            }
            return cropped;
        } catch (Exception e) {
            return null;
        }
    }

    private boolean saveBitmap(Bitmap bitmap) {
        String name = "Screenshot_" + new SimpleDateFormat("yyyyMMdd_HHmmss_SSS", Locale.US).format(new Date()) + ".png";
        try {
            if (Build.VERSION.SDK_INT >= 29) {
                ContentResolver resolver = getContentResolver();
                ContentValues values = new ContentValues();
                values.put(MediaStore.Images.Media.DISPLAY_NAME, name);
                values.put(MediaStore.Images.Media.MIME_TYPE, "image/png");
                values.put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/Screenshots");
                values.put(MediaStore.Images.Media.IS_PENDING, 1);
                Uri uri = resolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values);
                if (uri == null) return false;
                boolean success = false;
                try (OutputStream out = resolver.openOutputStream(uri)) {
                    if (out != null) success = bitmap.compress(Bitmap.CompressFormat.PNG, 100, out);
                }
                if (success) {
                    ContentValues done = new ContentValues();
                    done.put(MediaStore.Images.Media.IS_PENDING, 0);
                    resolver.update(uri, done, null, null);
                    return true;
                } else {
                    resolver.delete(uri, null, null);
                    return false;
                }
            } else {
                File dir = new File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_PICTURES), "Screenshots");
                if (!dir.exists() && !dir.mkdirs()) return false;
                File file = new File(dir, name);
                try (OutputStream out = new FileOutputStream(file)) {
                    return bitmap.compress(Bitmap.CompressFormat.PNG, 100, out);
                }
            }
        } catch (Exception e) {
            return false;
        }
    }

    private void finishCapture(boolean success, String error) {
        capturing = false;
        mainHandler.postDelayed(() -> setFloatingVisible(true), 170L);
        if (success) {
            Toast.makeText(this, "تم حفظ لقطة الشاشة", Toast.LENGTH_SHORT).show();
        } else if (error != null) {
            Toast.makeText(this, error, Toast.LENGTH_LONG).show();
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
        button.setElevation(dp(7));

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
                        try { windowManager.updateViewLayout(button, floatingParams); } catch (Exception ignored) {}
                        return true;
                    case MotionEvent.ACTION_UP:
                        if (!moved) requestCapture(180L);
                        return true;
                    default:
                        return true;
                }
            }
        });

        floatingButton = button;
        try {
            windowManager.addView(button, floatingParams);
        } catch (Exception e) {
            floatingButton = null;
        }
    }

    private void setFloatingVisible(boolean visible) {
        if (floatingButton != null) {
            floatingButton.setVisibility(visible ? View.VISIBLE : View.INVISIBLE);
        }
    }

    private void removeFloatingButton() {
        if (floatingButton != null) {
            try { windowManager.removeView(floatingButton); } catch (Exception ignored) {}
            floatingButton = null;
        }
    }

    private void releaseProjection() {
        ready = false;
        if (mediaProjection != null) {
            try {
                if (projectionCallback != null) mediaProjection.unregisterCallback(projectionCallback);
            } catch (Exception ignored) {}
            try { mediaProjection.stop(); } catch (Exception ignored) {}
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
                this, 0, open,
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
            try { display.release(); } catch (Exception ignored) {}
            try { reader.close(); } catch (Exception ignored) {}
        }
    }
}
