package com.example.flutter_application_1;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.view.animation.AccelerateDecelerateInterpolator;
import android.view.animation.Animation;
import android.view.animation.TranslateAnimation;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.Toast;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;
import androidx.core.content.FileProvider;
import io.flutter.FlutterInjector;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public class ImageCaptureActivity extends AppCompatActivity {
    public static final String EXTRA_IMAGE_PATH = "image_path";

    private Uri tempCameraUri;
    private String tempCameraPath;

    private final ActivityResultLauncher<Uri> takePictureLauncher =
        registerForActivityResult(new ActivityResultContracts.TakePicture(), success -> {
            if (Boolean.TRUE.equals(success) && tempCameraPath != null) {
                returnSuccess(tempCameraPath);
            } else {
                cleanupTempCameraFile();
            }
        });

    private final ActivityResultLauncher<String> pickImageLauncher =
        registerForActivityResult(new ActivityResultContracts.GetContent(), uri -> {
            if (uri != null) {
                copySelectedImageToCache(uri);
            }
        });

    private final ActivityResultLauncher<String> requestCameraPermissionLauncher =
        registerForActivityResult(new ActivityResultContracts.RequestPermission(), isGranted -> {
            if (Boolean.TRUE.equals(isGranted)) {
                launchCamera();
            } else {
                Toast.makeText(this, "Camera permission is required to take photos", Toast.LENGTH_SHORT).show();
            }
        });

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_image_capture);

        // Load the Misbar logo asset directly from Flutter assets
        loadLogoImage();

        // Clear any old temp images from cache
        try {
            File storageDir = new File(getCacheDir(), "images");
            if (storageDir.exists()) {
                File[] files = storageDir.listFiles();
                if (files != null) {
                    for (File f : files) {
                        f.delete();
                    }
                }
            }
        } catch (Exception ignored) {}

        findViewById(R.id.btn_back).setOnClickListener(v -> {
            setResult(RESULT_CANCELED);
            finish();
        });

        findViewById(R.id.btn_capture).setOnClickListener(v -> {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
                launchCamera();
            } else {
                requestCameraPermissionLauncher.launch(Manifest.permission.CAMERA);
            }
        });

        findViewById(R.id.btn_upload_image).setOnClickListener(v -> {
            pickImageLauncher.launch("image/*");
        });

        findViewById(R.id.btn_flash).setOnClickListener(v -> {
            Toast.makeText(this, "Flash toggled", Toast.LENGTH_SHORT).show();
        });
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) {
            startLaserAnimation();
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        startLaserAnimation();
    }

    private void loadLogoImage() {
        ImageView ivLogo = findViewById(R.id.iv_brand_logo);
        TextView tvFallback = findViewById(R.id.tv_brand_logo_fallback);

        Bitmap logoBitmap = null;

        // 1. Try Flutter asset lookup key
        try {
            String assetKey = FlutterInjector.instance()
                .flutterLoader()
                .getLookupKeyForAsset("assets/images/misbar_logo.png");
            try (InputStream is = getAssets().open(assetKey)) {
                logoBitmap = BitmapFactory.decodeStream(is);
            }
        } catch (Exception ignored) {}

        // 2. Direct flutter_assets fallback path
        if (logoBitmap == null) {
            try (InputStream is = getAssets().open("flutter_assets/assets/images/misbar_logo.png")) {
                logoBitmap = BitmapFactory.decodeStream(is);
            } catch (Exception ignored) {}
        }

        if (logoBitmap != null && ivLogo != null) {
            ivLogo.setImageBitmap(logoBitmap);
            ivLogo.setVisibility(View.VISIBLE);
            if (tvFallback != null) tvFallback.setVisibility(View.GONE);
        } else if (tvFallback != null) {
            tvFallback.setVisibility(View.VISIBLE);
        }
    }

    private void startLaserAnimation() {
        View laserLine = findViewById(R.id.view_laser_line);
        if (laserLine != null) {
            laserLine.clearAnimation();
            float distance = 150f * getResources().getDisplayMetrics().density;
            TranslateAnimation animation = new TranslateAnimation(
                Animation.ABSOLUTE, 0f,
                Animation.ABSOLUTE, 0f,
                Animation.ABSOLUTE, 0f,
                Animation.ABSOLUTE, distance
            );
            animation.setDuration(1600);
            animation.setRepeatCount(Animation.INFINITE);
            animation.setRepeatMode(Animation.REVERSE);
            animation.setInterpolator(new AccelerateDecelerateInterpolator());
            laserLine.startAnimation(animation);
        }
    }

    private void launchCamera() {
        try {
            File photoFile = createCacheImageFile();
            tempCameraPath = photoFile.getAbsolutePath();
            tempCameraUri = FileProvider.getUriForFile(
                this,
                getPackageName() + ".fileprovider",
                photoFile
            );
            takePictureLauncher.launch(tempCameraUri);
        } catch (Exception e) {
            Toast.makeText(this, "Failed to initialize camera: " + e.getMessage(), Toast.LENGTH_SHORT).show();
        }
    }

    private void copySelectedImageToCache(Uri sourceUri) {
        try {
            File targetFile = createCacheImageFile();
            try (InputStream in = getContentResolver().openInputStream(sourceUri);
                 FileOutputStream out = new FileOutputStream(targetFile)) {
                if (in != null) {
                    byte[] buffer = new byte[8192];
                    int bytesRead;
                    while ((bytesRead = in.read(buffer)) != -1) {
                        out.write(buffer, 0, bytesRead);
                    }
                }
            }
            returnSuccess(targetFile.getAbsolutePath());
        } catch (Exception e) {
            Toast.makeText(this, "Failed to load selected photo", Toast.LENGTH_SHORT).show();
        }
    }

    private File createCacheImageFile() throws Exception {
        String timeStamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(new Date());
        File storageDir = new File(getCacheDir(), "images");
        if (!storageDir.exists()) {
            storageDir.mkdirs();
        }
        return new File(storageDir, "IMG_" + timeStamp + ".jpg");
    }

    private void cleanupTempCameraFile() {
        if (tempCameraPath != null) {
            try {
                File f = new File(tempCameraPath);
                if (f.exists() && f.length() == 0) {
                    f.delete();
                }
            } catch (Exception ignored) {}
            tempCameraPath = null;
            tempCameraUri = null;
        }
    }

    private void returnSuccess(String imagePath) {
        Intent resultIntent = new Intent();
        resultIntent.putExtra(EXTRA_IMAGE_PATH, imagePath);
        setResult(RESULT_OK, resultIntent);
        finish();
    }

    @Override
    public void onBackPressed() {
        super.onBackPressed();
        setResult(RESULT_CANCELED);
        finish();
    }
}
