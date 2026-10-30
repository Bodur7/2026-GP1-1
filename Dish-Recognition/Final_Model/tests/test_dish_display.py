"""Presentation contract checks using synthetic images and offline service doubles."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from dish_identifier.claude_client import StageError
from dish_identifier.dish_display import DishDisplayNames
from dish_identifier.image_quality import evaluate_response
from dish_identifier.pipeline import Pipeline, runtime_signature


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "names.json"

    def load(self, rows, classes=("cup_cakes",)):
        self.path.write_text(json.dumps(rows))
        return DishDisplayNames(self.path, classes)

    def test_all_121_model_classes_have_exact_english_names(self):
        config = json.loads((ROOT / "configs/pipeline.json").read_text())
        classes = json.loads((ROOT / config["dish_class_mapping_file"]).read_text())["classes"]
        names = DishDisplayNames(ROOT / "misbar_dish_name_mapping.json", classes)
        self.assertEqual(set(names.names), set(classes))
        self.assertEqual(len(names.names), 121)
        self.assertEqual(names.english("cup_cakes"), "Cupcakes")
        self.assertEqual(names.english("apple_pie"), "Apple Pie")
        self.assertEqual(names.english("baba-ghanoush"), "Baba Ghanoush")
        self.assertEqual(names.english("Mandi"), "Mandi")
        self.assertEqual(names.english("dajaj-mashwi"), "Grilled Chicken")

    def test_arabic_is_never_used_as_english_fallback(self):
        row = {"current_name": "cup_cakes", "display_name_en": "Cupcakes", "display_name_ar": "كب كيك"}
        self.assertEqual(self.load([row]).english("cup_cakes"), "Cupcakes")
        del row["display_name_en"]
        with self.assertRaises(StageError):
            self.load([row])

    def test_duplicate_missing_extra_or_blank_entries_fail(self):
        row = {"current_name": "cup_cakes", "display_name_en": "Cupcakes"}
        cases = [[], {}, [None], [row, row], [{**row, "current_name": "Cup_cakes"}],
                 [{**row, "display_name_en": " "}], [{**row, "display_name_en": " Cupcakes"}],
                 [row, {"current_name": "invented", "display_name_en": "Invented"}]]
        for rows in cases:
            with self.subTest(rows=rows), self.assertRaises(StageError):
                self.load(rows)
        with self.assertRaises(StageError):
            self.load([row], classes=("cup_cakes", "pizza"))

    def test_missing_or_invalid_file_fails_clearly(self):
        with self.assertRaises(StageError):
            DishDisplayNames(self.path, ["cup_cakes"])
        self.path.write_text("invalid json")
        with self.assertRaises(StageError):
            DishDisplayNames(self.path, ["cup_cakes"])

    def test_unknown_identifiers_are_never_prettified_or_casefolded(self):
        names = self.load([{"current_name": "cup_cakes", "display_name_en": "Cupcakes"}])
        for key in ("Cup_cakes", "Cupcakes", "missing_dish"):
            with self.subTest(key=key), self.assertRaises(StageError):
                names.english(key)

    def test_mapping_edit_changes_signature_even_if_config_does_not_change(self):
        project = Path(self.temp.name)
        (project / "configs").mkdir()
        (project / "configs/pipeline.json").write_text(json.dumps({"dish_display_mapping_file": self.path.name}))
        self.path.write_text('[]')
        before = runtime_signature(project)
        self.path.write_text('[{}]')
        after = runtime_signature(project)
        self.assertEqual(before["config_sha256"], after["config_sha256"])
        self.assertNotEqual(before["dish_display_mapping_sha256"], after["dish_display_mapping_sha256"])


class PipelineDisplayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.image = Path(self.temp.name) / "synthetic.png"
        Image.new("RGB", (32, 24), (50, 100, 150)).save(self.image)
        self.image_bytes = self.image.read_bytes()
        self.quality = Mock()
        self.quality.check.return_value = evaluate_response({"status": "success", "quality": {"score": .9}})
        self.raw_classification = {"predicted_dish": "cup_cakes", "class_count": 121,
            "top1": {"rank": 1, "dish": "cup_cakes", "confidence": .8}}
        self.runtime = Mock()
        self.runtime.classify.return_value = (copy.deepcopy(self.raw_classification), "unchanged-features")
        self.runtime.supportedness.return_value = {"accepted": True, "score": .8,
            "threshold": .18922570362206778, "LR_score": .7, "OE_score": .8}
        self.extraction = {"dinov2_predicted_dish": "cup_cakes", "ingredients": [
            {"name": "egg", "confidence": 12, "allergens": ["Egg"]}]}
        self.claude = Mock()
        self.claude.analyze.side_effect = [
            ({"image_type": "SINGLE_DISH", "reason": "Synthetic evidence."}, {}),
            (copy.deepcopy(self.extraction), {})]
        def normalize(prompt, schema, max_tokens, audit):
            records = json.loads(prompt.split("Ingredients:\n", 1)[1])
            return {"groups": [{"canonical_name": r["name"], "member_ids": [r["id"]],
                                "reason": "Synthetic grouping."} for r in records]}, {}
        self.claude.analyze_text.side_effect = normalize
        self.pipeline = Pipeline(ROOT, quality=self.quality, claude=self.claude, runtime=self.runtime)
        self.pipeline.recipe_data.retrieve = Mock(wraps=self.pipeline.recipe_data.retrieve)

    def test_english_display_does_not_change_model_lookup_claude_or_human_reference(self):
        snapshots = []
        result = self.pipeline.run(self.image, progress=lambda r: snapshots.append(copy.deepcopy(r)))
        self.assertEqual(result["decision"], "accepted")
        self.assertEqual(result["final_dish"], "cup_cakes")
        self.assertEqual(result["final_dish_display_name_en"], "Cupcakes")
        self.assertEqual(result["stages"][3]["data"], self.raw_classification | {"display_name_en": "Cupcakes"})
        self.assertEqual(self.runtime.classify.return_value[0], self.raw_classification)
        self.runtime.supportedness.assert_called_once_with("unchanged-features")
        self.pipeline.recipe_data.retrieve.assert_called_once_with("cup_cakes")
        self.assertEqual(result["stages"][5]["data"]["dish"], "cup_cakes")
        self.assertEqual(result["stages"][6]["data"], self.extraction)
        extract_call = self.claude.analyze.call_args_list[1]
        self.assertIn("FIXED DINOv2 Top-1 dish name: cup_cakes", extract_call.args[2])
        self.assertEqual(extract_call.args[3]["properties"]["dinov2_predicted_dish"]["enum"], ["cup_cakes"])
        self.assertNotIn("Cupcakes", extract_call.args[2])
        self.assertIn("cup_cakes", self.claude.analyze_text.call_args.args[0])
        self.assertNotIn("Cupcakes", self.claude.analyze_text.call_args.args[0])
        self.assertIsNone(result["reviewed_label"])
        self.assertEqual(result["image_sha256"], hashlib.sha256(self.image_bytes).hexdigest())
        self.assertEqual(self.image.read_bytes(), self.image_bytes)
        self.assertNotIn("display_name_ar", json.dumps(result))
        self.assertEqual(result["protocol"]["dish_display_mapping"]["source_field"], "display_name_en")
        self.assertEqual(result["protocol"]["runtime_signature"], runtime_signature(ROOT))
        # No final name is published while supportedness is pending.
        waiting = next(r for r in snapshots if r["stages"][4]["status"] == "running")
        self.assertIsNone(waiting["final_dish_display_name_en"])

    def test_ood_rejection_keeps_raw_prediction_but_no_final_display_name(self):
        self.runtime.supportedness.return_value["accepted"] = False
        result = self.pipeline.run(self.image)
        self.assertEqual((result["decision"], result["stopped_at"]), ("rejected", "ood"))
        self.assertIsNone(result["final_dish"])
        self.assertIsNone(result["final_dish_display_name_en"])
        self.assertEqual(result["stages"][3]["data"]["top1"], self.raw_classification["top1"])
        self.pipeline.recipe_data.retrieve.assert_not_called()
        self.assertEqual(self.claude.analyze.call_count, 1)
        self.claude.analyze_text.assert_not_called()

    def test_grilled_chicken_uses_english_display_and_original_recipe_key(self):
        self.runtime.classify.return_value = ({"predicted_dish": "dajaj-mashwi", "class_count": 121,
            "top1": {"rank": 1, "dish": "dajaj-mashwi", "confidence": .8}}, "unchanged-features")
        self.claude.analyze.side_effect = [
            ({"image_type": "SINGLE_DISH", "reason": "Synthetic evidence."}, {}),
            ({"dinov2_predicted_dish": "dajaj-mashwi", "ingredients": [
                {"name": "chicken", "confidence": 95, "allergens": []}]}, {})]
        result = self.pipeline.run(self.image)
        self.assertEqual(result["decision"], "accepted")
        self.assertEqual(result["final_dish"], "dajaj-mashwi")
        self.assertEqual(result["final_dish_display_name_en"], "Grilled Chicken")
        self.assertEqual(result["stages"][3]["data"]["display_name_en"], "Grilled Chicken")
        self.pipeline.recipe_data.retrieve.assert_called_once_with("dajaj-mashwi")
        self.assertEqual(result["stages"][5]["data"]["recipe_metadata"]["dishName"], "dajaj-mashwi")
        self.assertIn("FIXED DINOv2 Top-1 dish name: dajaj-mashwi", self.claude.analyze.call_args_list[1].args[2])

    def test_unknown_prediction_fails_before_lookup_and_extraction(self):
        self.runtime.classify.return_value = ({"predicted_dish": "invented_dish"}, "features")
        result = self.pipeline.run(self.image)
        self.assertEqual((result["decision"], result["stopped_at"]), ("error", "classification"))
        self.assertEqual(result["stages"][3]["data"]["error_code"], "missing_dish_display_name")
        self.assertIsNone(result["final_dish_display_name_en"])
        self.pipeline.recipe_data.retrieve.assert_not_called()
        self.runtime.supportedness.assert_not_called()

    def test_no_normalization_mode_still_returns_english_name(self):
        self.pipeline.config["normalization_enabled"] = False
        result = self.pipeline.run(self.image)
        self.assertEqual(result["decision"], "accepted")
        self.assertEqual(result["final_dish_display_name_en"], "Cupcakes")
        self.assertFalse(result["semantic_normalization_performed"])
        self.claude.analyze_text.assert_not_called()


if __name__ == "__main__":
    unittest.main()
