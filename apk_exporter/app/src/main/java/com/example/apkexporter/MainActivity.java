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
    private AppAdapter adapter;
    private TextView countText;
    private AppItem pendingSave;
    private PackageManager packageManager;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        packageManager = getPackageManager();

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1) {
            getWindow().getDecorView().setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
        }

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(16), dp(18), dp(16), dp(12));
        root.setBackgroundColor(Color.rgb(248, 249, 250));
        root.setLayoutParams(new ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT));

        TextView title = new TextView(this);
        title.setText("حافظ التطبيقات");
        title.setTextSize(24);
        title.setTextColor(Color.rgb(25, 25, 25));
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        title.setGravity(Gravity.RIGHT);
        root.addView(title, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        TextView subtitle = new TextView(this);
        subtitle.setText("اختر أي تطبيق مثبت واحفظ نسخة منه داخل مجلد التنزيلات / AppsBackup");
        subtitle.setTextSize(14);
        subtitle.setTextColor(Color.rgb(90, 90, 90));
        subtitle.setGravity(Gravity.RIGHT);
        LinearLayout.LayoutParams subParams = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        subParams.topMargin = dp(5);
        root.addView(subtitle, subParams);

        EditText search = new EditText(this);
        search.setHint("ابحث باسم التطبيق...");
        search.setSingleLine(true);
        search.setTextSize(16);
        search.setGravity(Gravity.RIGHT | Gravity.CENTER_VERTICAL);
        search.setPadding(dp(12), dp(8), dp(12), dp(8));
        LinearLayout.LayoutParams searchParams = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(52));
        searchParams.topMargin = dp(14);
        root.addView(search, searchParams);

        countText = new TextView(this);
        countText.setTextSize(13);
        countText.setTextColor(Color.rgb(100, 100, 100));
        countText.setGravity(Gravity.RIGHT);
        LinearLayout.LayoutParams countParams = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        countParams.topMargin = dp(8);
        countParams.bottomMargin = dp(6);
        root.addView(countText, countParams);

        ListView listView = new ListView(this);
        listView.setDividerHeight(1);
        listView.setCacheColorHint(Color.TRANSPARENT);
        adapter = new AppAdapter();
        listView.setAdapter(adapter);
        root.addView(listView, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        setContentView(root);

        search.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) { }
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
                filterApps(s == null ? "" : s.toString());
            }
            @Override public void afterTextChanged(Editable s) { }
        });

        loadApps();
    }

    private void loadApps() {
        allApps.clear();
        List<ApplicationInfo> installed = packageManager.getInstalledApplications(0);
        for (ApplicationInfo info : installed) {
            if (info.packageName.equals(getPackageName())) continue;
            boolean system = (info.flags & ApplicationInfo.FLAG_SYSTEM) != 0;
            boolean updatedSystem = (info.flags & ApplicationInfo.FLAG_UPDATED_SYSTEM_APP) != 0;
            if (system && !updatedSystem) continue;
            if (info.sourceDir == null) continue;

            CharSequence labelCs = packageManager.getApplicationLabel(info);
            String label = labelCs == null ? info.packageName : labelCs.toString();
            allApps.add(new AppItem(info, label, info.packageName));
        }

        final Collator collator = Collator.getInstance(new Locale("ar"));
        Collections.sort(allApps, new Comparator<AppItem>() {
            @Override
            public int compare(AppItem a, AppItem b) {
                return collator.compare(a.label, b.label);
            }
        });
        filterApps("");
    }

    private void filterApps(String query) {
        String q = query.trim().toLowerCase(Locale.ROOT);
        visibleApps.clear();
        for (AppItem item : allApps) {
            if (q.isEmpty()
                    || item.label.toLowerCase(Locale.ROOT).contains(q)
                    || item.packageName.toLowerCase(Locale.ROOT).contains(q)) {
                visibleApps.add(item);
            }
        }
        countText.setText("التطبيقات: " + visibleApps.size());
        adapter.notifyDataSetChanged();
    }

    private void requestSave(AppItem item) {
        if (Build.VERSION.SDK_INT <= Build.VERSION_CODES.P
                && checkSelfPermission(Manifest.permission.WRITE_EXTERNAL_STORAGE)
                != PackageManager.PERMISSION_GRANTED) {
            pendingSave = item;
            requestPermissions(new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE}, REQ_STORAGE);
            return;
        }
        saveAppAsync(item);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQ_STORAGE) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                if (pendingSave != null) saveAppAsync(pendingSave);
            } else {
                toast("يلزم السماح بالوصول للتخزين حتى يتم حفظ التطبيق");
            }
            pendingSave = null;
        }
    }

    private void saveAppAsync(final AppItem item) {
        toast("جاري حفظ " + item.label + "...");
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    List<String> sources = new ArrayList<>();
                    sources.add(item.info.sourceDir);
                    if (item.info.splitSourceDirs != null) {
                        Collections.addAll(sources, item.info.splitSourceDirs);
                    }

                    boolean split = sources.size() > 1;
                    String extension = split ? ".zip" : ".apk";
                    String fileName = safeName(item.label) + "_" + safeName(item.packageName) + extension;

                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                        saveWithMediaStore(fileName, sources, split);
                    } else {
                        saveLegacy(fileName, sources, split);
                    }

                    final String done = split
                            ? "تم الحفظ في Downloads/AppsBackup كملف ZIP لأنه تطبيق مقسم"
                            : "تم الحفظ في Downloads/AppsBackup كملف APK";
                    runOnUiThread(new Runnable() {
                        @Override public void run() { toast(done); }
                    });
                } catch (final Exception e) {
                    runOnUiThread(new Runnable() {
                        @Override public void run() {
                            toast("تعذر الحفظ: " + (e.getMessage() == null ? "خطأ غير معروف" : e.getMessage()));
                        }
                    });
                }
            }
        }).start();
    }

    private void saveLegacy(String fileName, List<String> sources, boolean split) throws IOException {
        File downloads = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS);
        File dir = new File(downloads, "AppsBackup");
        if (!dir.exists() && !dir.mkdirs()) {
            throw new IOException("لم أستطع إنشاء مجلد AppsBackup");
        }
        File outFile = uniqueFile(dir, fileName);
        if (split) {
            try (OutputStream out = new BufferedOutputStream(new FileOutputStream(outFile))) {
                writeZip(out, sources);
            }
        } else {
            try (InputStream in = new BufferedInputStream(new FileInputStream(sources.get(0)));
                 OutputStream out = new BufferedOutputStream(new FileOutputStream(outFile))) {
                copy(in, out);
            }
        }
    }

    private void saveWithMediaStore(String fileName, List<String> sources, boolean split) throws IOException {
        ContentResolver resolver = getContentResolver();
        ContentValues values = new ContentValues();
        values.put(MediaStore.Downloads.DISPLAY_NAME, fileName);
        values.put(MediaStore.Downloads.MIME_TYPE,
                split ? "application/zip" : "application/vnd.android.package-archive");
        values.put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/AppsBackup");
        values.put(MediaStore.Downloads.IS_PENDING, 1);

        Uri uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
        if (uri == null) throw new IOException("تعذر إنشاء الملف في التنزيلات");

        boolean success = false;
        try {
            OutputStream raw = resolver.openOutputStream(uri);
            if (raw == null) throw new IOException("تعذر فتح ملف الحفظ");
            try (OutputStream out = new BufferedOutputStream(raw)) {
                if (split) {
                    writeZip(out, sources);
                } else {
                    try (InputStream in = new BufferedInputStream(new FileInputStream(sources.get(0)))) {
                        copy(in, out);
                    }
                }
            }
            success = true;
        } finally {
            if (success) {
                ContentValues done = new ContentValues();
                done.put(MediaStore.Downloads.IS_PENDING, 0);
                resolver.update(uri, done, null, null);
            } else {
                resolver.delete(uri, null, null);
            }
        }
    }

    private void writeZip(OutputStream outputStream, List<String> sources) throws IOException {
        try (ZipOutputStream zip = new ZipOutputStream(outputStream)) {
            for (int i = 0; i < sources.size(); i++) {
                File source = new File(sources.get(i));
                String entryName;
                if (i == 0) {
                    entryName = "base.apk";
                } else {
                    String original = source.getName();
                    entryName = original.endsWith(".apk") ? original : "split_" + i + ".apk";
                }
                zip.putNextEntry(new ZipEntry(entryName));
                try (InputStream in = new BufferedInputStream(new FileInputStream(source))) {
                    copy(in, zip);
                }
                zip.closeEntry();
            }
            zip.finish();
        }
    }

    private void copy(InputStream in, OutputStream out) throws IOException {
        byte[] buffer = new byte[64 * 1024];
        int read;
        while ((read = in.read(buffer)) != -1) {
            out.write(buffer, 0, read);
        }
        out.flush();
    }

    private File uniqueFile(File dir, String fileName) {
        File candidate = new File(dir, fileName);
        if (!candidate.exists()) return candidate;
        int dot = fileName.lastIndexOf('.');
        String base = dot > 0 ? fileName.substring(0, dot) : fileName;
        String ext = dot > 0 ? fileName.substring(dot) : "";
        int n = 2;
        while (candidate.exists()) {
            candidate = new File(dir, base + " (" + n + ")" + ext);
            n++;
        }
        return candidate;
    }

    private String safeName(String text) {
        String s = text.replaceAll("[\\\\/:*?\"<>|]", "_").trim();
        if (s.length() > 80) s = s.substring(0, 80);
        return s.isEmpty() ? "app" : s;
    }

    private void toast(String text) {
        Toast.makeText(this, text, Toast.LENGTH_LONG).show();
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private static class AppItem {
        final ApplicationInfo info;
        final String label;
        final String packageName;

        AppItem(ApplicationInfo info, String label, String packageName) {
            this.info = info;
            this.label = label;
            this.packageName = packageName;
        }
    }

    private class AppAdapter extends BaseAdapter {
        @Override public int getCount() { return visibleApps.size(); }
        @Override public AppItem getItem(int position) { return visibleApps.get(position); }
        @Override public long getItemId(int position) { return position; }

        @Override
        public View getView(int position, View convertView, ViewGroup parent) {
            Holder holder;
            if (convertView == null) {
                LinearLayout row = new LinearLayout(MainActivity.this);
                row.setOrientation(LinearLayout.HORIZONTAL);
                row.setGravity(Gravity.CENTER_VERTICAL);
                row.setPadding(dp(8), dp(8), dp(8), dp(8));
                row.setMinimumHeight(dp(72));
                row.setBackgroundColor(Color.WHITE);
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1) {
                    row.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
                }

                ImageView icon = new ImageView(MainActivity.this);
                LinearLayout.LayoutParams iconParams = new LinearLayout.LayoutParams(dp(48), dp(48));
                iconParams.setMargins(dp(6), 0, dp(6), 0);
                row.addView(icon, iconParams);

                LinearLayout texts = new LinearLayout(MainActivity.this);
                texts.setOrientation(LinearLayout.VERTICAL);
                texts.setGravity(Gravity.CENTER_VERTICAL | Gravity.RIGHT);

                TextView name = new TextView(MainActivity.this);
                name.setTextSize(16);
                name.setTextColor(Color.rgb(30, 30, 30));
                name.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
                name.setGravity(Gravity.RIGHT);
                texts.addView(name, new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

                TextView pkg = new TextView(MainActivity.this);
                pkg.setTextSize(11);
                pkg.setTextColor(Color.rgb(115, 115, 115));
                pkg.setGravity(Gravity.RIGHT);
                texts.addView(pkg, new LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

                row.addView(texts, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

                Button save = new Button(MainActivity.this);
                save.setText("حفظ");
                save.setAllCaps(false);
                save.setTextSize(13);
                LinearLayout.LayoutParams buttonParams = new LinearLayout.LayoutParams(dp(76), dp(46));
                buttonParams.setMargins(dp(6), 0, dp(6), 0);
                row.addView(save, buttonParams);

                holder = new Holder(icon, name, pkg, save);
                row.setTag(holder);
                convertView = row;
            } else {
                holder = (Holder) convertView.getTag();
            }

            final AppItem item = getItem(position);
            holder.name.setText(item.label);
            holder.pkg.setText(item.packageName);
            try {
                Drawable drawable = packageManager.getApplicationIcon(item.info);
                holder.icon.setImageDrawable(drawable);
            } catch (Exception e) {
                holder.icon.setImageDrawable(null);
            }
            holder.save.setOnClickListener(new View.OnClickListener() {
                @Override public void onClick(View v) { requestSave(item); }
            });
            return convertView;
        }
    }

    private static class Holder {
        final ImageView icon;
        final TextView name;
        final TextView pkg;
        final Button save;

        Holder(ImageView icon, TextView name, TextView pkg, Button save) {
            this.icon = icon;
            this.name = name;
            this.pkg = pkg;
            this.save = save;
        }
    }
}
