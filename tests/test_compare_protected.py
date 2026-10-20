import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/compare_protected.py"
spec = importlib.util.spec_from_file_location("compare_protected", SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class ProtectedTests(unittest.TestCase):
    def test_typography_aliases_and_thai_digits(self):
        self.assertFalse(checker.compare("ราคา ๑,๒๐๐.๐๐ บาท ปริมาตร ๓๕๐ มล.", "ราคา ฿1200 ปริมาตร 350 ml")["review_needed"])

    def test_reordered_unchanged_facts(self):
        self.assertFalse(checker.compare("350 ml และ 800 g", "800 กรัม และ 350 มล.")["review_needed"])

    def test_quantity_swap_despite_same_number_totals(self):
        result = checker.compare("350 ml และ 800 g", "800 ml และ 350 g")
        self.assertNotIn("numbers", result["changed"])
        self.assertEqual(result["removed"]["quantities"], {"350 ml": 1, "800 g": 1})
        self.assertEqual(result["added"]["quantities"], {"350 g": 1, "800 ml": 1})

    def test_changed_number_and_missing_unit(self):
        result = checker.compare("9 bar, 93 °C, 20%", "8 bar, 93, 20%")
        self.assertEqual(result["removed"]["numbers"], {"9": 1})
        self.assertIn("93 °C", result["removed"]["quantities"])

    def test_negative_and_fractional_numbers(self):
        self.assertFalse(checker.compare("−๓.๕ °C, +.50 g", "-3.50 °C, 0.5 g")["review_needed"])
        self.assertTrue(checker.compare("-3.5 °C", "3.5 °C")["review_needed"])

    def test_prose_url_punctuation_and_balanced_parenthesis(self):
        url = "https://example.com/a_(b)?id=350"
        self.assertFalse(checker.compare("ดู (" + url + ").", url)["review_needed"])
        self.assertEqual(checker.extract(url)["numbers"], {})
        self.assertTrue(checker.compare(url, url.replace("350", "800"))["review_needed"])

    def test_unicode_hashtags_and_case(self):
        old = "#กาแฟที่บ้าน๒ #Example"
        self.assertEqual(checker.extract(old)["hashtags"], {"#กาแฟที่บ้าน๒": 1, "#Example": 1})
        self.assertTrue(checker.compare(old, "#กาแฟที่บ้าน2 #example")["review_needed"])

    def test_repeated_protected_exact_strings(self):
        result = checker.compare("EXAMPLE EXAMPLE Example", "EXAMPLE Example Example", ["EXAMPLE"])
        self.assertEqual(result["removed"]["explicit"], {"EXAMPLE": 1})
        self.assertEqual(result["changed"]["explicit"], {"before_count": 2, "after_count": 1})

    def test_ordered_markers_are_ignored_but_decimal_data_checked(self):
        self.assertFalse(checker.compare("1. Coffee\n2) Tea", "8. Coffee\n9) Tea")["review_needed"])
        self.assertTrue(checker.compare("1.5 bar", "2.5 bar")["review_needed"])
        self.assertTrue(checker.compare("1. Coffee", "2. Coffee", ["1. Coffee"])["review_needed"])

    def test_explicit_preserves_exact_format_despite_number_normalization(self):
        self.assertTrue(checker.compare("๑,๒๐๐ บาท", "1200 บาท", ["๑,๒๐๐ บาท"])["review_needed"])

    def test_known_limit_same_unit_label_swap(self):
        # Surface multisets cannot infer which model owns each quantity.
        self.assertFalse(checker.compare("A 350 ml; B 800 ml", "A 800 ml; B 350 ml")["review_needed"])

    def test_cli_bom_status_and_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            before, after, protect = [Path(directory) / name for name in ("before.txt", "after.txt", "protect.json")]
            before.write_text("๙ bar EXAMPLE", encoding="utf-8-sig")
            after.write_text("9 bar EXAMPLE", encoding="utf-8-sig")
            protect.write_text('["EXAMPLE", "EXAMPLE"]', encoding="utf-8-sig")
            original = before.read_bytes()
            arguments = ["--before", str(before), "--after", str(after), "--protect", str(protect)]
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(checker.main(arguments), 0)
            self.assertFalse(json.loads(output.getvalue())["review_needed"])
            after.write_text("8 bar EXAMPLE", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(checker.main(arguments), 1)
            self.assertEqual(before.read_bytes(), original)
            for invalid in ('{}', '[""]', '[" "]', '[1]', '[null]', '[[]]', 'not json'):
                protect.write_text(invalid, encoding="utf-8")
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(checker.main(arguments), 2)
                self.assertIn("error", json.loads(output.getvalue()))
            protect.write_bytes(b"\xff")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(checker.main(arguments), 2)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(checker.main(["--before", str(before), "--after", str(after) + ".missing"]), 2)


if __name__ == "__main__":
    unittest.main()
