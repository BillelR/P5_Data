"""
test_migration.py
-----------------
Tests d'intégrité des données avant et après la migration.
Utilise unittest + pytest (les deux frameworks sont supportés).

Usage :
    pytest scripts/test_migration.py -v
    # ou
    python -m unittest scripts/test_migration.py
"""

import os
import csv
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

# ─── Rend migrate importable même sans MongoDB installé ───────────────────────
import sys
sys.path.insert(0, os.path.dirname(__file__))

from migrate import cast_row, clean_name, parse_date, load_csv

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "healthcare_dataset.csv")


# ══════════════════════════════════════════════════════════════════════════════
# 1. Tests unitaires – fonctions de transformation
# ══════════════════════════════════════════════════════════════════════════════

class TestCleanName(unittest.TestCase):

    def test_uppercase_normalized(self):
        self.assertEqual(clean_name("BOBBY JACKSON"), "Bobby Jackson")

    def test_mixed_case_normalized(self):
        self.assertEqual(clean_name("bObBy jAcKsOn"), "Bobby Jackson")

    def test_leading_trailing_spaces(self):
        self.assertEqual(clean_name("  alice  "), "Alice")


class TestParseDate(unittest.TestCase):

    def test_valid_date(self):
        result = parse_date("2024-01-31")
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 31)

    def test_invalid_date_returns_none(self):
        self.assertIsNone(parse_date("not-a-date"))

    def test_empty_string_returns_none(self):
        self.assertIsNone(parse_date(""))


class TestCastRow(unittest.TestCase):

    SAMPLE_ROW = {
        "Name": "Bobby JacksOn",
        "Age": "30",
        "Gender": "Male",
        "Blood Type": "B-",
        "Medical Condition": "Cancer",
        "Date of Admission": "2024-01-31",
        "Doctor": "Matthew Smith",
        "Hospital": "Sons and Miller",
        "Insurance Provider": "Blue Cross",
        "Billing Amount": "18856.28",
        "Room Number": "328",
        "Admission Type": "Urgent",
        "Discharge Date": "2024-02-02",
        "Medication": "Paracetamol",
        "Test Results": "Normal",
    }

    def setUp(self):
        self.doc = cast_row(self.SAMPLE_ROW)

    def test_all_expected_fields_present(self):
        expected_fields = [
            "name", "age", "gender", "blood_type", "medical_condition",
            "date_of_admission", "doctor", "hospital", "insurance_provider",
            "billing_amount", "room_number", "admission_type",
            "discharge_date", "medication", "test_results",
        ]
        for field in expected_fields:
            with self.subTest(field=field):
                self.assertIn(field, self.doc)

    def test_age_is_int(self):
        self.assertIsInstance(self.doc["age"], int)
        self.assertEqual(self.doc["age"], 30)

    def test_billing_amount_is_float(self):
        self.assertIsInstance(self.doc["billing_amount"], float)

    def test_room_number_is_int(self):
        self.assertIsInstance(self.doc["room_number"], int)

    def test_dates_are_datetime(self):
        self.assertIsInstance(self.doc["date_of_admission"], datetime)
        self.assertIsInstance(self.doc["discharge_date"], datetime)

    def test_name_normalized(self):
        self.assertEqual(self.doc["name"], "Bobby Jackson")

    def test_invalid_age_raises(self):
        bad_row = dict(self.SAMPLE_ROW, Age="abc")
        with self.assertRaises(ValueError):
            cast_row(bad_row)


# ══════════════════════════════════════════════════════════════════════════════
# 2. Tests d'intégrité du fichier CSV source
# ══════════════════════════════════════════════════════════════════════════════

class TestCSVIntegrity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Charge le CSV une seule fois pour tous les tests de la classe."""
        cls.csv_exists = os.path.isfile(CSV_PATH)
        if cls.csv_exists:
            with open(CSV_PATH, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                cls.rows = list(reader)
                cls.headers = reader.fieldnames or []
        else:
            cls.rows = []
            cls.headers = []

    def _skip_if_no_csv(self):
        if not self.csv_exists:
            self.skipTest(f"CSV introuvable : {CSV_PATH}")

    def test_csv_file_exists(self):
        self.assertTrue(self.csv_exists, f"Le fichier CSV est introuvable : {CSV_PATH}")

    def test_expected_columns_present(self):
        self._skip_if_no_csv()
        expected = [
            "Name", "Age", "Gender", "Blood Type", "Medical Condition",
            "Date of Admission", "Doctor", "Hospital", "Insurance Provider",
            "Billing Amount", "Room Number", "Admission Type",
            "Discharge Date", "Medication", "Test Results",
        ]
        for col in expected:
            with self.subTest(column=col):
                self.assertIn(col, self.headers)

    def test_no_completely_empty_rows(self):
        self._skip_if_no_csv()
        empty_rows = [i + 2 for i, r in enumerate(self.rows)
                      if all(v.strip() == "" for v in r.values())]
        self.assertEqual(empty_rows, [],
                         f"Lignes entièrement vides trouvées : {empty_rows[:5]}")

    def test_age_column_numeric(self):
        self._skip_if_no_csv()
        bad = []
        for i, row in enumerate(self.rows, start=2):
            try:
                int(row["Age"])
            except ValueError:
                bad.append(i)
        self.assertEqual(bad, [], f"Valeurs non-numériques dans 'Age' aux lignes : {bad[:5]}")

    def test_billing_amount_numeric(self):
        self._skip_if_no_csv()
        bad = []
        for i, row in enumerate(self.rows, start=2):
            try:
                float(row["Billing Amount"])
            except ValueError:
                bad.append(i)
        self.assertEqual(bad, [], f"'Billing Amount' non-numérique aux lignes : {bad[:5]}")

    def test_gender_values(self):
        self._skip_if_no_csv()
        allowed = {"Male", "Female"}
        unexpected = {row["Gender"].strip() for row in self.rows
                      if row["Gender"].strip() not in allowed}
        self.assertEqual(unexpected, set(),
                         f"Valeurs inattendues dans 'Gender' : {unexpected}")

    def test_no_duplicate_rows(self):
        self._skip_if_no_csv()
        # Doublons détectés sur (Name, Date of Admission, Billing Amount)
        keys = [(r["Name"], r["Date of Admission"], r["Billing Amount"]) for r in self.rows]
        duplicates = len(keys) - len(set(keys))
        self.assertEqual(duplicates, 0,
                         f"{duplicates} ligne(s) dupliquée(s) détectée(s).")


# ══════════════════════════════════════════════════════════════════════════════
# 3. Tests post-migration (avec mock MongoDB)
# ══════════════════════════════════════════════════════════════════════════════

class TestPostMigration(unittest.TestCase):
    """
    Simule une collection MongoDB pour vérifier que la migration
    produit le bon nombre de documents et les bons types de champs.
    """

    def test_load_csv_returns_list_of_dicts(self):
        if not os.path.isfile(CSV_PATH):
            self.skipTest("CSV introuvable")
        docs = load_csv(CSV_PATH)
        self.assertIsInstance(docs, list)
        self.assertGreater(len(docs), 0)
        self.assertIsInstance(docs[0], dict)

    def test_all_documents_have_required_keys(self):
        if not os.path.isfile(CSV_PATH):
            self.skipTest("CSV introuvable")
        required = {"name", "age", "gender", "billing_amount",
                    "date_of_admission", "medical_condition"}
        docs = load_csv(CSV_PATH)
        for doc in docs:
            missing = required - doc.keys()
            self.assertEqual(missing, set(),
                             f"Clés manquantes dans : {doc.get('name', '?')} → {missing}")

    @patch("migrate.MongoClient")
    def test_insert_many_called_once(self, mock_client_class):
        """Vérifie que insert_many est bien appelé lors de la migration."""
        from migrate import insert_documents

        mock_collection = MagicMock()
        mock_collection.insert_many.return_value.inserted_ids = ["id1", "id2"]

        docs = [{"name": "Test Patient", "age": 40}]
        count = insert_documents(docs, mock_collection)

        mock_collection.insert_many.assert_called_once_with(docs, ordered=False)
        self.assertEqual(count, 2)


# ══════════════════════════════════════════════════════════════════════════════
# Lancement direct
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)
