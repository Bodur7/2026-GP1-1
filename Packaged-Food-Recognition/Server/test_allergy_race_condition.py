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

client = TestClient(app)

class TestAllergyRaceConditionBackend(unittest.TestCase):
    def setUp(self):
        self.mock_user = {
            "uid": "race_condition_test_user",
            "email": "tester@misbar.local",
            "name": "Race Tester",
        }
        app.dependency_overrides[get_current_user] = lambda: self.mock_user

    def tearDown(self):
        app.dependency_overrides.clear()

    @patch("main.fetch_user_allergens_from_db")
    def test_scenario_1_scan_text_uses_request_payload_over_stale_db(self, mock_fetch_db):
        """
        Scenario 1: User removes 'Dairy allergy' and immediately scans an ingredient label.
        Simulate DB still having the stale allergy ['Dairy allergy', 'Gluten allergy'],
        while the scan request payload supplies the updated list ['Gluten allergy'].
        Verify scan result uses updated payload, NOT flagging milk as user allergy conflict.
        """
        # Stale DB return
        mock_fetch_db.return_value = ["Dairy allergy", "Gluten allergy"]

        text_input = "Ingredients: Milk, Sugar, Salt"
        # Client sends updated allergens in payload (Dairy removed)
        resp = client.post("/scan/text", json={
            "text": text_input,
            "user_allergens": ["Gluten allergy"]
        })

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])

        # Check global detection vs user allergen detection
        # Milk should be detected globally as an allergen
        dairy_detections = [d for d in data["allergens_detected"] if "milk" in d["allergen"].lower() or "dairy" in d["allergen"].lower()]
        self.assertTrue(len(dairy_detections) > 0, "Milk must be detected globally")

        # But it must NOT be flagged as is_user_allergen since Dairy was removed by the user
        for d in dairy_detections:
            self.assertFalse(d["is_user_allergen"], "Removed allergen must NOT be marked is_user_allergen")

        # Since only Milk was in the text and Dairy was removed, is_safe should be True
        self.assertTrue(data["is_safe"], "Product should be safe for user who removed Dairy")

        # Ensure DB was not even queried for user allergens because client provided them directly
        mock_fetch_db.assert_not_called()

    @patch("main.fetch_user_allergens_from_db")
    @patch("main.perform_ocr")
    @patch("main.extract_ingredients")
    @patch("main.check_image_quality")
    def test_scenario_2_scan_image_uses_form_payload_over_stale_db(
        self, mock_quality, mock_extract, mock_ocr, mock_fetch_db
    ):
        """
        Scenario 2: User removes an allergen and immediately scans an image (multipart).
        Simulate DB still retaining 'Dairy allergy', while client multipart payload
        passes user_allergens='["Gluten allergy"]'.
        """
        mock_quality.return_value = {"accepted": True}
        mock_ocr.return_value = ("Ingredients: Whole milk, Cream", "mock_vision")
        mock_extract.return_value = "Whole milk, Cream"
        mock_fetch_db.return_value = ["Dairy allergy"]

        # Fake image file
        fake_image = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 100

        resp = client.post(
            "/scan/image",
            files={"file": ("label.jpg", fake_image, "image/jpeg")},
            data={"user_allergens": json.dumps(["Gluten allergy"])}
        )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])

        # Dairy is detected globally
        self.assertGreater(len(data["allergens_detected"]), 0)
        for d in data["allergens_detected"]:
            self.assertFalse(d["is_user_allergen"], "Dairy should not be flagged as user allergen")

        self.assertTrue(data["is_safe"])
        mock_fetch_db.assert_not_called()

    @patch("main.fetch_user_allergens_from_db")
    def test_scenario_7_remaining_selected_allergens_are_still_detected(self, mock_fetch_db):
        """
        Scenario 7: Verify that allergens that REMAIN selected are still detected correctly.
        User kept 'Gluten allergy' and 'Egg allergy'.
        Text contains Wheat and Eggs.
        """
        resp = client.post("/scan/text", json={
            "text": "Ingredients: Wheat flour, Eggs, Sugar",
            "user_allergens": ["Gluten allergy", "Egg allergy"]
        })

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data["is_safe"], "Product contains user's selected allergens so is_safe must be False")

        user_flags = [d for d in data["allergens_detected"] if d["is_user_allergen"]]
        self.assertGreaterEqual(len(user_flags), 1, "Remaining selected allergens must be flagged as user allergens")

    @patch("main.fetch_user_allergens_from_db")
    def test_scenario_8_global_allergen_detection_intact_for_unselected_allergens(self, mock_fetch_db):
        """
        Scenario 8: Global allergen detection remains intact even when an allergen
        is not selected as a personal allergy.
        User only has 'Gluten allergy'.
        Text contains Peanuts.
        Peanuts must appear in allergens_detected with is_user_allergen=False.
        """
        resp = client.post("/scan/text", json={
            "text": "Ingredients: Roasted Peanuts, Salt",
            "user_allergens": ["Gluten allergy"]
        })

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # Peanuts is present in allergens_detected
        peanut_detections = [d for d in data["allergens_detected"] if "peanut" in d["allergen"].lower()]
        self.assertGreater(len(peanut_detections), 0, "Peanuts must be detected in global list")

        # But not a user allergen
        for d in peanut_detections:
            self.assertFalse(d["is_user_allergen"])

        # And is_safe is True for this user because Gluten was not present
        self.assertTrue(data["is_safe"])

    @patch("main.fetch_user_allergens_from_db")
    def test_empty_user_allergens_does_not_fall_back_to_stale_db(self, mock_fetch_db):
        """
        When user removes ALL allergens (user_allergens=[]), the scan must treat user
        as having 0 personal allergies, rather than falling back to DB.
        """
        mock_fetch_db.return_value = ["Dairy allergy", "Tree Nut allergy"]

        resp = client.post("/scan/text", json={
            "text": "Ingredients: Milk, Cashews, Almonds",
            "user_allergens": []
        })

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        for d in data["allergens_detected"]:
            self.assertFalse(d["is_user_allergen"])
        self.assertTrue(data["is_safe"])
        mock_fetch_db.assert_not_called()

    @patch("main.fetch_user_allergens_from_db")
    def test_legacy_request_without_user_allergens_falls_back_to_db(self, mock_fetch_db):
        """
        Ensures backward compatibility: If a legacy caller omits user_allergens,
        it safely fetches from DB using verified UID.
        """
        mock_fetch_db.return_value = ["Dairy allergy"]

        resp = client.post("/scan/text", json={
            "text": "Ingredients: Milk, Sugar"
        })

        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        mock_fetch_db.assert_called_once_with(user_id="race_condition_test_user")
        user_flags = [d for d in data["allergens_detected"] if d["is_user_allergen"]]
        self.assertGreater(len(user_flags), 0)
        self.assertFalse(data["is_safe"])

if __name__ == "__main__":
    unittest.main()
