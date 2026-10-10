# Open Food Facts Allergen Scanner Backend (FastAPI)

FastAPI server for detecting allergens from food packaging labels using the [Open Food Facts Ingredient Detection Model](https://huggingface.co/openfoodfacts/ingredient-detection) (`xlm-roberta-large`), combined with Google Cloud Vision OCR and a comprehensive allergen keyword dataset.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
python3 -m pip install -r requirements.txt
```

### 2. Configure Google Cloud Vision (Optional)
If you have a Google Cloud service account key:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-service-account.json"
```
*(If no credentials are provided, the server can use EasyOCR or accept pre-extracted OCR text via `/scan/text`)*.

### 3. Start the FastAPI Server
```bash
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
The server will start at:
* **Interactive API Docs (Swagger):** `http://localhost:8000/docs`
* **Healthcheck:** `http://localhost:8000/health`

---

## 📡 API Endpoints

### 1. `POST /scan/image` (Multipart Form Upload)
Takes an image file (JPEG, PNG, WEBP), performs OCR, isolates the ingredient list using the Open Food Facts AI model, and detects allergens.

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/scan/image" \
  -F "file=@/path/to/label.jpg" \
  -F "user_allergens=[\"Dairy allergy\", \"Wheat allergy\"]"
```

### 2. `POST /scan/text` (JSON Body)
Analyzes pre-extracted packaging text (e.g. from Flutter Google ML Kit on-device OCR):

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/scan/text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Ingredients: Water, Heavy Cream (Milk), Potatoes, Crab Meat, Wheat Flour, Salt, Soy Lecithin.",
    "user_allergens": ["Dairy allergy", "Wheat allergy"]
  }'
```

### 3. `GET /allergens`
Returns the list of all supported allergen categories to populate selection chips in Flutter.

---

## 📱 Flutter App Integration

All ready-to-use Flutter client code is located in `flutter_client/`:

* `flutter_client/models/scan_result.dart`: Strongly-typed Dart models (`ScanResult`, `AllergenDetection`).
* `flutter_client/allergen_scanner_service.dart`: HTTP networking service with background JSON isolate parsing.
* `flutter_client/example_scanner_screen.dart`: Complete camera/gallery scanning UI screen.

### Network URLs for Flutter:
| Target Platform | Base URL |
| :--- | :--- |
| **Android Emulator** | `http://10.0.2.2:8000` *(built into AllergenScannerService)* |
| **iOS Simulator** | `http://127.0.0.1:8000` |
| **Physical Phone (Wi-Fi)** | `http://<YOUR_COMPUTER_LOCAL_IP>:8000` *(e.g. `http://192.168.1.105:8000`)* |
