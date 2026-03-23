"""
migrate.py
----------
Script de migration du dataset médical (CSV) vers MongoDB.
Usage :
    python migrate.py --csv ../healthcare_dataset.csv
"""

import argparse
import csv
import os
import sys
from datetime import datetime

from pymongo import MongoClient, ASCENDING
from pymongo.errors import BulkWriteError, ConnectionFailure


# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:adminpassword@localhost:27017/")
DB_NAME   = os.getenv("DB_NAME",   "healthcare_db")
COLL_NAME = os.getenv("COLL_NAME", "patients")


# ──────────────────────────────────────────────
# Helpers : nettoyage / typage des données
# ──────────────────────────────────────────────
def clean_name(value: str) -> str:
    """Normalise les noms en Titre (Bobby Jackson)."""
    return value.strip().title()


def parse_date(value: str):
    """Convertit une chaîne YYYY-MM-DD en objet datetime."""
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d")
    except ValueError:
        return None


def cast_row(row: dict) -> dict:
    """
    Transforme une ligne CSV brute en document MongoDB typé.

    Champs produits :
        name, age (int), gender, blood_type, medical_condition,
        date_of_admission (datetime), doctor, hospital,
        insurance_provider, billing_amount (float), room_number (int),
        admission_type, discharge_date (datetime), medication, test_results
    """
    return {
        "name":               clean_name(row["Name"]),
        "age":                int(row["Age"]),
        "gender":             row["Gender"].strip(),
        "blood_type":         row["Blood Type"].strip(),
        "medical_condition":  row["Medical Condition"].strip(),
        "date_of_admission":  parse_date(row["Date of Admission"]),
        "doctor":             clean_name(row["Doctor"]),
        "hospital":           row["Hospital"].strip(),
        "insurance_provider": row["Insurance Provider"].strip(),
        "billing_amount":     float(row["Billing Amount"]),
        "room_number":        int(row["Room Number"]),
        "admission_type":     row["Admission Type"].strip(),
        "discharge_date":     parse_date(row["Discharge Date"]),
        "medication":         row["Medication"].strip(),
        "test_results":       row["Test Results"].strip(),
    }


# ──────────────────────────────────────────────
# Chargement CSV → liste de documents
# ──────────────────────────────────────────────
def load_csv(filepath: str) -> list[dict]:
    documents = []
    errors    = []

    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):          # ligne 1 = header
            try:
                documents.append(cast_row(row))
            except (ValueError, KeyError) as e:
                errors.append(f"  Ligne {i} ignorée – {e}")

    if errors:
        print(f"⚠  {len(errors)} ligne(s) ignorée(s) :")
        for err in errors[:10]:
            print(err)
        if len(errors) > 10:
            print(f"  … et {len(errors) - 10} autres.")

    return documents


# ──────────────────────────────────────────────
# Insertion dans MongoDB
# ──────────────────────────────────────────────
def insert_documents(documents: list[dict], collection) -> int:
    if not documents:
        print("Aucun document à insérer.")
        return 0

    try:
        result = collection.insert_many(documents, ordered=False)
        return len(result.inserted_ids)
    except BulkWriteError as bwe:
        inserted = bwe.details.get("nInserted", 0)
        print(f"⚠  BulkWriteError : {inserted} insérés, "
              f"{len(bwe.details.get('writeErrors', []))} erreur(s).")
        return inserted


# ──────────────────────────────────────────────
# Création des index
# ──────────────────────────────────────────────
def create_indexes(collection) -> None:
    collection.create_index([("name", ASCENDING)])
    collection.create_index([("medical_condition", ASCENDING)])
    collection.create_index([("date_of_admission", ASCENDING)])
    collection.create_index([("insurance_provider", ASCENDING)])
    print("✓  Index créés : name, medical_condition, date_of_admission, insurance_provider")


# ──────────────────────────────────────────────
# Point d'entrée
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Migration CSV → MongoDB")
    parser.add_argument("--csv",   default="../healthcare_dataset.csv",
                        help="Chemin vers le fichier CSV source")
    parser.add_argument("--drop",  action="store_true",
                        help="Vider la collection avant l'import (re-migration)")
    args = parser.parse_args()

    # ── Connexion ────────────────────────────
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print(f"✓  Connecté à MongoDB : {MONGO_URI}")
    except ConnectionFailure as e:
        print(f"✗  Impossible de se connecter à MongoDB : {e}")
        sys.exit(1)

    db         = client[DB_NAME]
    collection = db[COLL_NAME]

    # ── Optionnel : vider la collection ──────
    if args.drop:
        deleted = collection.delete_many({}).deleted_count
        print(f"✓  Collection vidée ({deleted} document(s) supprimés)")

    # ── Chargement CSV ────────────────────────
    print(f"\nChargement de : {args.csv}")
    documents = load_csv(args.csv)
    print(f"✓  {len(documents)} ligne(s) valide(s) chargée(s)")

    # ── Insertion ────────────────────────────
    inserted = insert_documents(documents, collection)
    print(f"✓  {inserted} document(s) insérés dans '{DB_NAME}.{COLL_NAME}'")

    # ── Index ─────────────────────────────────
    create_indexes(collection)

    # ── Vérification rapide ───────────────────
    total = collection.count_documents({})
    print(f"\n📊  Total documents dans la collection : {total}")

    client.close()
    print("\n✅  Migration terminée avec succès !")


if __name__ == "__main__":
    main()
