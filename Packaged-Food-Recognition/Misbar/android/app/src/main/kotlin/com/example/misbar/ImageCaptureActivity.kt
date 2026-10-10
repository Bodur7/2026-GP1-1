package com.example.misbar

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Bundle
import android.view.View
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.Toast
import androidx.activity.addCallback
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.button.MaterialButton
import java.io.File
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class ImageCaptureActivity : AppCompatActivity() {

    companion object {
        const val EXTRA_IMAGE_PATH = "image_path"
        const val EXTRA_IMAGE_URI = "image_uri"
    }

    private lateinit var toolbar: MaterialToolbar
    private lateinit var layoutPlaceholder: LinearLayout
    private lateinit var ivPreview: ImageView
    private lateinit var layoutInitialActions: LinearLayout
    private lateinit var layoutPreviewActions: LinearLayout
    private lateinit var btnTakePhoto: MaterialButton
    private lateinit var btnPickGallery: MaterialButton
    private lateinit var btnRetake: MaterialButton
    private lateinit var btnConfirm: MaterialButton

    private var currentPhotoUri: Uri? = null
    private var currentPhotoPath: String? = null
    private var tempCameraUri: Uri? = null
    private var tempCameraPath: String? = null

    private val takePictureLauncher = registerForActivityResult(ActivityResultContracts.TakePicture()) { success ->
        if (success && tempCameraUri != null && tempCameraPath != null) {
            currentPhotoUri = tempCameraUri
            currentPhotoPath = tempCameraPath
            showPreview(currentPhotoPath)
        } else {
            // Clean up unused temp file
            tempCameraPath?.let { path ->
                val file = File(path)
                if (file.exists() && file.length() == 0L) {
                    file.delete()
                }
            }
            tempCameraUri = null
            tempCameraPath = null
        }
    }

    private val pickImageLauncher = registerForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        if (uri != null) {
            copySelectedImageToCache(uri)
        }
    }

    private val requestCameraPermissionLauncher = registerForActivityResult(ActivityResultContracts.RequestPermission()) { isGranted ->
        if (isGranted) {
            launchCamera()
        } else {
            Toast.makeText(this, R.string.camera_permission_required, Toast.LENGTH_SHORT).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_image_capture)

        // Ensure zero old temporary images linger in cache
        try {
            File(cacheDir, "images").listFiles()?.forEach { file ->
                if (file.isFile) file.delete()
            }
        } catch (_: Exception) {}

        initViews()
        setupListeners()
    }

    private fun initViews() {
        toolbar = findViewById(R.id.toolbar)
        layoutPlaceholder = findViewById(R.id.layout_placeholder)
        ivPreview = findViewById(R.id.iv_preview)
        layoutInitialActions = findViewById(R.id.layout_initial_actions)
        layoutPreviewActions = findViewById(R.id.layout_preview_actions)
        btnTakePhoto = findViewById(R.id.btn_take_photo)
        btnPickGallery = findViewById(R.id.btn_pick_gallery)
        btnRetake = findViewById(R.id.btn_retake)
        btnConfirm = findViewById(R.id.btn_confirm)
    }

    private fun setupListeners() {
        toolbar.setNavigationOnClickListener {
            cancelAndFinish()
        }

        onBackPressedDispatcher.addCallback(this) {
            cancelAndFinish()
        }

        btnTakePhoto.setOnClickListener {
            checkCameraPermissionAndLaunch()
        }

        btnPickGallery.setOnClickListener {
            pickImageLauncher.launch("image/*")
        }

        btnRetake.setOnClickListener {
            resetToInitialState()
        }

        btnConfirm.setOnClickListener {
            confirmSelection()
        }
    }

    private fun checkCameraPermissionAndLaunch() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
            launchCamera()
        } else {
            requestCameraPermissionLauncher.launch(Manifest.permission.CAMERA)
        }
    }

    private fun launchCamera() {
        try {
            val (file, uri) = createCacheImageFile()
            tempCameraPath = file.absolutePath
            tempCameraUri = uri
            takePictureLauncher.launch(uri)
        } catch (e: Exception) {
            Toast.makeText(this, R.string.failed_to_capture_image, Toast.LENGTH_SHORT).show()
        }
    }

    private fun copySelectedImageToCache(sourceUri: Uri) {
        cleanupCurrentFile()
        try {
            val (file, targetUri) = createCacheImageFile()
            contentResolver.openInputStream(sourceUri)?.use { input ->
                FileOutputStream(file).use { output ->
                    input.copyTo(output)
                }
            }
            currentPhotoPath = file.absolutePath
            currentPhotoUri = targetUri
            showPreview(currentPhotoPath)
        } catch (e: Exception) {
            Toast.makeText(this, R.string.failed_to_load_image, Toast.LENGTH_SHORT).show()
        }
    }

    private fun createCacheImageFile(): Pair<File, Uri> {
        val timeStamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
        val storageDir = File(cacheDir, "images").apply {
            if (!exists()) mkdirs()
        }
        val file = File(storageDir, "IMG_${timeStamp}.jpg")
        val uri = FileProvider.getUriForFile(
            this,
            "${applicationContext.packageName}.fileprovider",
            file
        )
        return Pair(file, uri)
    }

    private fun showPreview(path: String?) {
        if (path == null) return
        val bitmap = BitmapFactory.decodeFile(path)
        ivPreview.setImageBitmap(bitmap)

        layoutPlaceholder.visibility = View.GONE
        ivPreview.visibility = View.VISIBLE

        layoutInitialActions.visibility = View.GONE
        layoutPreviewActions.visibility = View.VISIBLE
    }

    private fun cleanupCurrentFile() {
        currentPhotoPath?.let { path ->
            try {
                val file = File(path)
                if (file.exists()) {
                    file.delete()
                }
            } catch (_: Exception) {}
        }
        currentPhotoUri = null
        currentPhotoPath = null
    }

    private fun resetToInitialState() {
        cleanupCurrentFile()
        ivPreview.setImageDrawable(null)

        ivPreview.visibility = View.GONE
        layoutPlaceholder.visibility = View.VISIBLE

        layoutPreviewActions.visibility = View.GONE
        layoutInitialActions.visibility = View.VISIBLE
    }

    private fun confirmSelection() {
        val uri = currentPhotoUri
        val path = currentPhotoPath
        if (uri != null && path != null) {
            val resultIntent = Intent().apply {
                data = uri
                putExtra(EXTRA_IMAGE_PATH, path)
                putExtra(EXTRA_IMAGE_URI, uri.toString())
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            setResult(RESULT_OK, resultIntent)
            finish()
        }
    }

    private fun cancelAndFinish() {
        cleanupCurrentFile()
        setResult(RESULT_CANCELED)
        finish()
    }
}
