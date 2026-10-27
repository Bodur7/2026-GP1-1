import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock

SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from fastapi.testclient import TestClient
from main import app
from app.auth import get_current_user
from app.services.user_allergen_service import (
    UserDocumentNotFoundError,
    DatabaseUnavailableError,
    InvalidAllergyDataError,
    fetch_user_allergens_from_db,
)

client = TestClient(app)

class TestFirestoreAuthoritativeAllergy(unittest.TestCase):
    def setUp(self):
        self.mock_user = {
            "uid": "user_alice_123",
            "email": "alice@misbar.local",
            "name": "Alice",
        }
        app.dependency_overrides[get_current_user] = lambda: self.mock_user

    def tearDown(self):
        app.dependency_overrides.clear()

    @patch("main.fetch_user_allergens_from_db")
    def test_3_and_9_scans_retrieve_from_firestore_not_payload(self, mock_fetch):
        """
        Verify: Every scan (text and image) retrieves allergies directly from Firestore
        using verified UID, and NEVER uses request payloads.
        """
        mock_fetch.return_value = ["Dairy allergy"]

        # Text scan
        resp = client.post("/scan/text", json={"text": "Ingredients: Milk, Sugar"})
        self.assertEqual(resp.status_code, 200)
        mock_fetch.assert_called_with(user_id="user_alice_123")
        data = resp.json()
        self.assertFalse(data["is_safe"])
        user_allergens = [d for d in data["allergens_detected"] if d["is_user_allergen"]]
        self.assertEqual(len(user_allergens), 1)
        self.assertIn("milk", user_allergens[0]["allergen"].lower() + str(user_allergens[0]["matched_ingredients"]).lower())

    @patch("main.fetch_user_allergens_from_db")
    def test_4_forged_user_allergens_field_cannot_affect_text_scan(self, mock_fetch):
        """
        Verify: Supplying a forged 'user_allergens' field in a JSON text scan request
        has ZERO effect. Backend retrieves strictly from Firestore.
        """
        # User in Firestore has 'Dairy allergy'
        mock_fetch.return_value = ["Dairy allergy"]

        # Attacker / client attempts to forge user_allergens: [] to bypass Dairy detection
        resp = client.post("/scan/text", json={
            "text": "Ingredients: Whole milk, Cream",
            "user_allergens": []  # Forged override attempt!
        })

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # Forged list was ignored; Dairy from Firestore was used!
        self.assertFalse(data["is_safe"], "Forged empty user_allergens must NOT bypass Firestore Dairy allergy")
        user_allergens = [d for d in data["allergens_detected"] if d["is_user_allergen"]]
        self.assertGreater(len(user_allergens), 0)

    @patch("main.fetch_user_allergens_from_db")
    @patch("main.perform_ocr")
    @patch("main.extract_ingredients")
    @patch("main.check_image_quality")
    def test_4_and_9_forged_user_allergens_field_cannot_affect_image_scan(
        self, mock_quality, mock_extract, mock_ocr, mock_fetch
    ):
        """
        Verify: Supplying a forged 'user_allergens' in multipart form data to /scan/image
        has ZERO effect. Backend retrieves strictly from Firestore.
        """
        mock_quality.return_value = {"accepted": True}
        mock_ocr.return_value = ("Ingredients: Whole milk, Cream", "mock_vision")
        mock_extract.return_value = "Whole milk, Cream"
        mock_fetch.return_value = ["Dairy allergy"]

        fake_image = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 100

        # Attacker sends forged user_allergens in form-data
        resp = client.post(
            "/scan/image",
            files={"file": ("label.jpg", fake_image, "image/jpeg")},
            data={"user_allergens": json.dumps([])}  # Forged override!
        )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data["is_safe"], "Forged user_allergens in multipart form must be ignored")
        user_allergens = [d for d in data["allergens_detected"] if d["is_user_allergen"]]
        self.assertGreater(len(user_allergens), 0)
        mock_fetch.assert_called_with(user_id="user_alice_123")

    @patch("main.fetch_user_allergens_from_db")
    def test_5_user_isolation_strictly_derives_uid_from_token(self, mock_fetch):
        """
        Verify: User can only access and scan against their own Firestore record.
        """
        mock_fetch.return_value = ["Gluten allergy"]

        # Call endpoint as user_alice_123
        resp = client.post("/scan/text", json={"text": "Ingredients: Wheat flour"})
        self.assertEqual(resp.status_code, 200)
        mock_fetch.assert_called_with(user_id="user_alice_123")

        # Now simulate a different authenticated user Bob
        app.dependency_overrides[get_current_user] = lambda: {
            "uid": "user_bob_456",
            "email": "bob@misbar.local"
        }
        mock_fetch.reset_mock()
        mock_fetch.return_value = ["Peanut allergy"]

        resp2 = client.post("/scan/text", json={"text": "Ingredients: Wheat flour"})
        self.assertEqual(resp2.status_code, 200)
        mock_fetch.assert_called_with(user_id="user_bob_456")
        # For Bob, wheat is safe because Bob only has Peanut allergy
        self.assertTrue(resp2.json()["is_safe"])

    @patch("main.fetch_user_allergens_from_db")
    def test_6_valid_empty_allergy_list_distinguished_from_firestore_failure(self, mock_fetch):
        """
        Verify:
        - Genuinely empty allergy list ([]) succeeds and results in is_safe=True for personal allergies.
        - Missing user document raises 404 NOT FOUND.
        - Database query failure raises 503 SERVICE UNAVAILABLE.
        - Invalid allergy data raises 500 INTERNAL SERVER ERROR.
        """
        # Case A: Valid empty list
        mock_fetch.return_value = []
        resp_empty = client.post("/scan/text", json={"text": "Ingredients: Milk, Peanuts, Wheat"})
        self.assertEqual(resp_empty.status_code, 200)
        self.assertTrue(resp_empty.json()["is_safe"], "User with 0 selected allergies has no personal conflict")
        # Global detections must still list the allergens
        self.assertGreater(len(resp_empty.json()["allergens_detected"]), 0)
        for d in resp_empty.json()["allergens_detected"]:
            self.assertFalse(d["is_user_allergen"])

        # Case B: Missing user document in Firestore -> 404
        mock_fetch.side_effect = UserDocumentNotFoundError("Doc missing")
        resp_missing = client.post("/scan/text", json={"text": "Ingredients: Milk"})
        self.assertEqual(resp_missing.status_code, 404)
        self.assertIn("not found", resp_missing.json()["detail"].lower())

        # Case C: Firestore connection failure -> 503
        mock_fetch.side_effect = DatabaseUnavailableError("Network timeout")
        resp_down = client.post("/scan/text", json={"text": "Ingredients: Milk"})
        self.assertEqual(resp_down.status_code, 503)
        self.assertIn("unavailable", resp_down.json()["detail"].lower())

        # Case D: Corrupted database field -> 500
        mock_fetch.side_effect = InvalidAllergyDataError("Field not a list")
        resp_corrupt = client.post("/scan/text", json={"text": "Ingredients: Milk"})
        self.assertEqual(resp_corrupt.status_code, 500)
        self.assertIn("invalid", resp_corrupt.json()["detail"].lower())

    @patch("main.fetch_user_allergens_from_db")
    def test_8_remaining_allergens_flagged_and_unselected_visible_globally(self, mock_fetch):
        """
        Verify: Remaining selected allergies are flagged as user allergens,
        while unselected allergens remain visible in global detections with is_user_allergen=False.
        """
        # User has only Gluten allergy in Firestore
        mock_fetch.return_value = ["Gluten allergy"]

        resp = client.post("/scan/text", json={"text": "Ingredients: Wheat flour, Milk, Peanuts"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data["is_safe"], "Product contains Gluten which user is allergic to")

        # Gluten must have is_user_allergen=True
        gluten = next((d for d in data["allergens_detected"] if "gluten" in d["allergen"].lower() or "cereals" in d["allergen"].lower()), None)
        self.assertIsNotNone(gluten)
        self.assertTrue(gluten["is_user_allergen"])

        # Milk and Peanuts must be present globally with is_user_allergen=False
        milk = next((d for d in data["allergens_detected"] if "milk" in d["allergen"].lower() or "dairy" in d["allergen"].lower()), None)
        self.assertIsNotNone(milk)
        self.assertFalse(milk["is_user_allergen"])

        peanut = next((d for d in data["allergens_detected"] if "peanut" in d["allergen"].lower()), None)
        self.assertIsNotNone(peanut)
        self.assertFalse(peanut["is_user_allergen"])

if __name__ == "__main__":
    unittest.main()
