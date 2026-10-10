package com.example.misbar

import android.app.Activity
import android.content.Intent
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    private val channelName = "com.example.misbar/image_capture"
    private val requestImageCapture = 1001
    private var pendingResult: MethodChannel.Result? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, channelName).setMethodCallHandler { call, result ->
            when (call.method) {
                "openImageCapture" -> {
                    pendingResult = result
                    val intent = Intent(this, ImageCaptureActivity::class.java)
                    startActivityForResult(intent, requestImageCapture)
                }
                else -> result.notImplemented()
            }
        }
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == requestImageCapture) {
            if (resultCode == Activity.RESULT_OK && data != null) {
                val imagePath = data.getStringExtra(ImageCaptureActivity.EXTRA_IMAGE_PATH)
                    ?: data.data?.toString()
                pendingResult?.success(imagePath)
            } else {
                pendingResult?.success(null)
            }
            pendingResult = null
        }
    }
}
