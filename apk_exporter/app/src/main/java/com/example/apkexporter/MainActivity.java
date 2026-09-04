package com.example.apkexporter;

import android.Manifest;
import android.app.Activity;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.Drawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.text.Collator;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

public class MainActivity extends Activity {
    private static final int REQ_STORAGE = 2001;
    private final List<AppItem> allApps = new ArrayList<>();
    private final List<AppItem> visibleApps = new ArrayList<>();
    private PackageManager pm;
    private AppAdapter adapter;
    private TextView countText;
    private AppItem pendingSave;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        pm = getPackageManager();
        if (Build.VERSION.SDK_INT >= 17) {
            getWindow().getDecorView().setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
        }

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(14), dp(16), dp(14), dp(10));
        root.setBackgroundColor(Color.rgb(248, 249, 250));

        TextView title = new TextView(this);
        title.setText("حافظ التطبيقات");
        title.setTextSize(24);
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        title.setTextColor(Color.rgb(25,25,25));
        title.setGravity(Gravity.RIGHT);
        root.addView(title);

        TextView note = new TextView(this);
        note.setText("يحفظ التطبيق باسمه الحقيقي داخل Downloads/AppsBackup");
        note.setTextSize(14);
        note.setTextColor(Color.rgb(90,90,90));
        note.setGravity(Gravity.RIGHT);
        LinearLayout.LayoutParams noteLp = new LinearLayout.LayoutParams(-1, -2);
        noteLp.topMargin = dp(5);
        root.addView(note, noteLp);

        EditText search = new EditText(this);
        search.setHint("ابحث باسم التطبيق...");
        search.setSingleLine(true);
        search.setGravity(Gravity.RIGHT | Gravity.CENTER_VERTICAL);
        LinearLayout.LayoutParams searchLp = new LinearLayout.LayoutParams(-1, dp(52));
        searchLp.topMargin = dp(12);
        root.addView(search, searchLp);

        countText = new TextView(this);
        countText.setTextSize(13);
        countText.setTextColor(Color.rgb(100,100,100));
        countText.setGravity(Gravity.RIGHT);
        LinearLayout.LayoutParams countLp = new LinearLayout.LayoutParams(-1, -2);
        countLp.topMargin = dp(7);
        countLp.bottomMargin = dp(6);
        root.addView(countText, countLp);

        ListView list = new ListView(this);
        list.setDividerHeight(1);
        adapter = new AppAdapter();
        list.setAdapter(adapter);
        root.addView(list, new LinearLayout.LayoutParams(-1, 0, 1f));
        setContentView(root);

        search.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
                filter(s == null ? "" : s.toString());
            }
            @Override public void afterTextChanged(Editable s) {}
        });
        loadApps();
    }

    private void loadApps() {
        allApps.clear();
        for (ApplicationInfo info : pm.getInstalledApplications(0)) {
            if (getPackageName().equals(info.packageName) || info.sourceDir == null) continue;
            boolean system = (info.flags & ApplicationInfo.FLAG_SYSTEM) != 0;
            boolean updatedSystem = (info.flags & ApplicationInfo.FLAG_UPDATED_SYSTEM_APP) != 0;
            if (system && !updatedSystem) continue;
            CharSequence cs = pm.getApplicationLabel(info);
            String label = cs == null ? info.packageName : cs.toString().trim();
            if (label.isEmpty()) label = info.packageName;
            allApps.add(new AppItem(info, label, info.packageName));
        }
        final Collator collator = Collator.getInstance(new Locale("ar"));
        Collections.sort(allApps, new Comparator<AppItem>() {
            @Override public int compare(AppItem a, AppItem b) {
                return collator.compare(a.label, b.label);
            }
        });
        filter("");
    }

    private void filter(String query) {
        String q = query.trim().toLowerCase(Locale.ROOT);
        visibleApps.clear();
        for (AppItem item : allApps) {
            if (q.isEmpty() || item.label.toLowerCase(Locale.ROOT).contains(q)
                    || item.packageName.toLowerCase(Locale.ROOT).contains(q)) {
                visibleApps.add(item);
            }
        }
        countText.setText("التطبيقات: " + visibleApps.size());
        adapter.notifyDataSetChanged();
    }

    private void requestSave(AppItem item) {
        if (Build.VERSION.SDK_INT <= 28
                && checkSelfPermission(Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) {
            pendingSave = item;
            requestPermissions(new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE}, REQ_STORAGE);
            return;
        }
        saveAsync(item);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQ_STORAGE) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED && pendingSave != null) {
                saveAsync(pendingSave);
            } else {
                toast("يلزم السماح بالتخزين لحفظ التطبيق");
            }
            pendingSave = null;
        }
    }

    private void saveAsync(final AppItem item) {
        toast("جاري حفظ " + item.label + "...");
        new Thread(new Runnable() {
            @Override public void run() {
                try {
                    List<String> sources = new ArrayList<>();
                    sources.add(item.info.sourceDir);
                    if (item.info.splitSourceDirs != null) Collections.addAll(sources, item.info.splitSourceDirs);
                    boolean split = sources.size() > 1;
                    String fileName = safeName(item.label) + (split ? ".zip" : ".apk");
                    if (Build.VERSION.SDK_INT >= 29) saveMediaStore(fileName, sources, split);
                    else saveLegacy(fileName, sources, split);
                    final String msg = split
                            ? "تم الحفظ باسم " + fileName + " (ZIP لأن التطبيق مقسم)"
                            : "تم الحفظ باسم " + fileName;
                    runOnUiThread(new Runnable() { @Override public void run() { toast(msg); } });
                } catch (final Exception e) {
                    runOnUiThread(new Runnable() { @Override public void run() {
                        toast("تعذر الحفظ: " + (e.getMessage() == null ? "خطأ غير معروف" : e.getMessage()));
                    }});
                }
            }
        }).start();
    }

    private void saveLegacy(String fileName, List<String> sources, boolean split) throws IOException {
        File dir = new File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS), "AppsBackup");
        if (!dir.exists() && !dir.mkdirs()) throw new IOException("تعذر إنشاء مجلد AppsBackup");
        File outFile = uniqueFile(dir, fileName);
        if (split) {
            try (OutputStream out = new BufferedOutputStream(new FileOutputStream(outFile))) { writeZip(out, sources); }
        } else {
            try (InputStream in = new BufferedInputStream(new FileInputStream(sources.get(0)));
                 OutputStream out = new BufferedOutputStream(new FileOutputStream(outFile))) { copy(in, out); }
        }
    }

    private void saveMediaStore(String fileName, List<String> sources, boolean split) throws IOException {
        ContentResolver resolver = getContentResolver();
        ContentValues values = new ContentValues();
        values.put(MediaStore.Downloads.DISPLAY_NAME, fileName);
        values.put(MediaStore.Downloads.MIME_TYPE, split ? "application/zip" : "application/vnd.android.package-archive");
        values.put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/AppsBackup");
        values.put(MediaStore.Downloads.IS_PENDING, 1);
        Uri uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
        if (uri == null) throw new IOException("تعذر إنشاء ملف الحفظ");
        boolean ok = false;
        try {
            OutputStream raw = resolver.openOutputStream(uri);
            if (raw == null) throw new IOException("تعذر فتح ملف الحفظ");
            try (OutputStream out = new BufferedOutputStream(raw)) {
                if (split) writeZip(out, sources);
                else try (InputStream in = new BufferedInputStream(new FileInputStream(sources.get(0)))) { copy(in, out); }
            }
            ok = true;
        } finally {
            if (ok) {
                ContentValues done = new ContentValues();
                done.put(MediaStore.Downloads.IS_PENDING, 0);
                resolver.update(uri, done, null, null);
            } else resolver.delete(uri, null, null);
        }
    }

    private void writeZip(OutputStream out, List<String> sources) throws IOException {
        try (ZipOutputStream zip = new ZipOutputStream(out)) {
            for (int i = 0; i < sources.size(); i++) {
                File source = new File(sources.get(i));
                String name = i == 0 ? "base.apk" : source.getName();
                if (!name.endsWith(".apk")) name = "split_" + i + ".apk";
                zip.putNextEntry(new ZipEntry(name));
                try (InputStream in = new BufferedInputStream(new FileInputStream(source))) { copy(in, zip); }
                zip.closeEntry();
            }
            zip.finish();
        }
    }

    private void copy(InputStream in, OutputStream out) throws IOException {
        byte[] buffer = new byte[65536];
        int n;
        while ((n = in.read(buffer)) != -1) out.write(buffer, 0, n);
        out.flush();
    }

    private File uniqueFile(File dir, String fileName) {
        File f = new File(dir, fileName);
        if (!f.exists()) return f;
        int dot = fileName.lastIndexOf('.');
        String base = dot > 0 ? fileName.substring(0, dot) : fileName;
        String ext = dot > 0 ? fileName.substring(dot) : "";
        int i = 2;
        while (f.exists()) f = new File(dir, base + " (" + i++ + ")" + ext);
        return f;
    }

    private String safeName(String text) {
        String s = text.replaceAll("[\\\\/:*?\"<>|]", "_").trim();
        if (s.length() > 90) s = s.substring(0, 90);
        return s.isEmpty() ? "app" : s;
    }

    private int dp(int v) { return Math.round(v * getResources().getDisplayMetrics().density); }
    private void toast(String s) { Toast.makeText(this, s, Toast.LENGTH_LONG).show(); }

    private static class AppItem {
        final ApplicationInfo info;
        final String label;
        final String packageName;
        AppItem(ApplicationInfo info, String label, String packageName) {
            this.info = info; this.label = label; this.packageName = packageName;
        }
    }

    private class AppAdapter extends BaseAdapter {
        @Override public int getCount() { return visibleApps.size(); }
        @Override public AppItem getItem(int position) { return visibleApps.get(position); }
        @Override public long getItemId(int position) { return position; }

        @Override public View getView(int position, View convertView, ViewGroup parent) {
            Holder h;
            if (convertView == null) {
                LinearLayout row = new LinearLayout(MainActivity.this);
                row.setOrientation(LinearLayout.HORIZONTAL);
                row.setGravity(Gravity.CENTER_VERTICAL);
                row.setPadding(dp(8), dp(8), dp(8), dp(8));
                row.setMinimumHeight(dp(72));
                row.setBackgroundColor(Color.WHITE);
                if (Build.VERSION.SDK_INT >= 17) row.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);

                ImageView icon = new ImageView(MainActivity.this);
                LinearLayout.LayoutParams iconLp = new LinearLayout.LayoutParams(dp(48), dp(48));
                iconLp.setMargins(dp(6), 0, dp(6), 0);
                row.addView(icon, iconLp);

                LinearLayout texts = new LinearLayout(MainActivity.this);
                texts.setOrientation(LinearLayout.VERTICAL);
                texts.setGravity(Gravity.CENTER_VERTICAL | Gravity.RIGHT);
                TextView name = new TextView(MainActivity.this);
                name.setTextSize(16); name.setTypeface(Typeface.DEFAULT, Typeface.BOLD); name.setGravity(Gravity.RIGHT);
                TextView pkg = new TextView(MainActivity.this);
                pkg.setTextSize(11); pkg.setTextColor(Color.rgb(115,115,115)); pkg.setGravity(Gravity.RIGHT);
                texts.addView(name, new LinearLayout.LayoutParams(-1, -2));
                texts.addView(pkg, new LinearLayout.LayoutParams(-1, -2));
                row.addView(texts, new LinearLayout.LayoutParams(0, -2, 1f));

                Button save = new Button(MainActivity.this);
                save.setText("حفظ"); save.setAllCaps(false);
                row.addView(save, new LinearLayout.LayoutParams(dp(76), dp(46)));
                h = new Holder(icon, name, pkg, save);
                row.setTag(h);
                convertView = row;
            } else h = (Holder) convertView.getTag();

            final AppItem item = getItem(position);
            h.name.setText(item.label);
            h.pkg.setText(item.packageName);
            try { Drawable d = pm.getApplicationIcon(item.info); h.icon.setImageDrawable(d); }
            catch (Exception e) { h.icon.setImageDrawable(null); }
            h.save.setOnClickListener(new View.OnClickListener() { @Override public void onClick(View v) { requestSave(item); } });
            return convertView;
        }
    }

    private static class Holder {
        final ImageView icon; final TextView name; final TextView pkg; final Button save;
        Holder(ImageView icon, TextView name, TextView pkg, Button save) {
            this.icon = icon; this.name = name; this.pkg = pkg; this.save = save;
        }
    }
}
