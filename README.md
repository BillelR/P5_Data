# P5_Data
Présentation projet 5
=======
# 🏥 DataSoluTech – Migration des données médicales vers MongoDB

> **Mission** : Migration d'un dataset de patients (CSV) vers MongoDB, conteneurisée via Docker, avec documentation complète et tests d'intégrité.

---

## 📋 Sommaire

1. [Contexte du projet](#1-contexte-du-projet)
2. [Structure du dépôt](#2-structure-du-dépôt)
3. [Prérequis](#3-prérequis)
4. [Lancement rapide (Docker)](#4-lancement-rapide-docker)
5. [Installation locale (sans Docker)](#5-installation-locale-sans-docker)
6. [Schéma de la base de données](#6-schéma-de-la-base-de-données)
7. [Authentification et rôles utilisateurs](#7-authentification-et-rôles-utilisateurs)
8. [Tests d'intégrité](#8-tests-dintégrité)
9. [Description du script de migration](#9-description-du-script-de-migration)
10. [Déploiement sur AWS](#10-déploiement-sur-aws)

---

## 1. Contexte du projet

**DataSoluTech** propose à son client une solution Big Data scalable pour gérer un dataset de **~55 000 dossiers patients** (fichier `healthcare_dataset.csv`).

Le client rencontrait des problèmes de scalabilité avec son système relationnel traditionnel. La solution retenue repose sur **MongoDB**, une base de données NoSQL orientée documents, idéale pour :

- Les données médicales semi-structurées
- La scalabilité horizontale (sharding)
- La flexibilité du schéma (évolutions futures)
- Les requêtes rapides sur des champs variés (condition médicale, assurance, date)

---

## 2. Structure du dépôt

```
datasolutech-project/
│
├── healthcare_dataset.csv          # Dataset source (55 500 lignes)
├── requirements.txt                # Dépendances Python
├── docker-compose.yml              # Orchestration des conteneurs
│
├── scripts/
│   ├── migrate.py                  # Script principal de migration CSV → MongoDB
│   └── test_migration.py           # Tests unitaires et d'intégrité (unittest + pytest)
│
├── docker/
│   ├── Dockerfile                  # Image du service de migration
│   └── mongo-init.js               # Initialisation MongoDB (users, schéma)
│
└── README.md                       # Ce fichier
```

---

## 3. Prérequis

| Outil | Version recommandée | Vérification |
|---|---|---|
| Ubuntu | 20.04 / 22.04 / 24.04 | `lsb_release -a` |
| Docker | ≥ 24.0 | `docker --version` |
| Docker Compose | ≥ 2.20 | `docker compose version` |
| Python | ≥ 3.11 (optionnel, pour exécution locale) | `python3 --version` |

### Installation de Docker sur Ubuntu

```bash
# Mise à jour des paquets
sudo apt update && sudo apt upgrade -y

# Installation des dépendances
sudo apt install -y ca-certificates curl gnupg

# Ajout de la clé GPG officielle Docker
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Ajout du dépôt Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Installation de Docker Engine + Compose
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Ajouter votre utilisateur au groupe docker (évite sudo)
sudo usermod -aG docker $USER
newgrp docker

# Vérification
docker --version
docker compose version
```

---

## 4. Lancement rapide (Docker)

> ✅ **Méthode recommandée** – aucune installation Python nécessaire.

```bash
# 1. Cloner le dépôt (ou extraire l'archive)
git clone https://github.com/votre-username/datasolutech-project.git
cd datasolutech-project

# 2. Lancer tous les services (MongoDB + migration + Mongo Express)
docker compose up --build

# Le service 'migration' s'exécute automatiquement et s'arrête une fois terminé.
# MongoDB et Mongo Express continuent de tourner.

# 3. Vérifier les logs de la migration
docker compose logs migration

# 4. Accéder à l'interface web Mongo Express
# → http://localhost:8081  (login: admin / admin123)

# 5. Arrêter les services
docker compose down

# 6. Arrêter ET supprimer les volumes (données MongoDB)
docker compose down -v
```

**Pour relancer une migration (re-import) :**
```bash
docker compose run --rm migration python scripts/migrate.py --csv /app/healthcare_dataset.csv --drop
```

---

## 5. Installation locale (sans Docker)

```bash
# 1. Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Démarrer MongoDB localement (via Docker uniquement pour la DB)
docker run -d --name mongodb \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=adminpassword \
  -p 27017:27017 \
  mongo:7.0

# 4. Lancer la migration
python scripts/migrate.py --csv healthcare_dataset.csv

# 5. Re-migrer en vidant la collection
python scripts/migrate.py --csv healthcare_dataset.csv --drop
```

**Variables d'environnement disponibles :**

| Variable | Valeur par défaut | Description |
|---|---|---|
| `MONGO_URI` | `mongodb://admin:adminpassword@localhost:27017/` | URI de connexion |
| `DB_NAME` | `healthcare_db` | Nom de la base |
| `COLL_NAME` | `patients` | Nom de la collection |

---

## 6. Schéma de la base de données

### Base : `healthcare_db`
### Collection : `patients`

Chaque document représente un dossier patient :

```json
{
  "_id":                "ObjectId (auto-généré)",
  "name":               "Bobby Jackson",
  "age":                30,
  "gender":             "Male",
  "blood_type":         "B-",
  "medical_condition":  "Cancer",
  "date_of_admission":  "ISODate(2024-01-31T00:00:00Z)",
  "doctor":             "Matthew Smith",
  "hospital":           "Sons And Miller",
  "insurance_provider": "Blue Cross",
  "billing_amount":     18856.28,
  "room_number":        328,
  "admission_type":     "Urgent",
  "discharge_date":     "ISODate(2024-02-02T00:00:00Z)",
  "medication":         "Paracetamol",
  "test_results":       "Normal"
}
```

### Types des champs

| Champ | Type BSON | Description |
|---|---|---|
| `_id` | ObjectId | Identifiant unique MongoDB |
| `name` | String | Nom normalisé (Titre) |
| `age` | Int32 | Âge en années |
| `gender` | String | `"Male"` ou `"Female"` |
| `blood_type` | String | Groupe sanguin (ex. `"B-"`) |
| `medical_condition` | String | Pathologie principale |
| `date_of_admission` | Date | Date d'admission |
| `doctor` | String | Médecin traitant |
| `hospital` | String | Établissement |
| `insurance_provider` | String | Assurance |
| `billing_amount` | Double | Montant facturé (USD) |
| `room_number` | Int32 | Numéro de chambre |
| `admission_type` | String | `"Urgent"`, `"Emergency"`, `"Elective"` |
| `discharge_date` | Date | Date de sortie |
| `medication` | String | Traitement prescrit |
| `test_results` | String | `"Normal"`, `"Abnormal"`, `"Inconclusive"` |

### Index créés

| Index | Champ | Objectif |
|---|---|---|
| `name_1` | `name` | Recherche par patient |
| `medical_condition_1` | `medical_condition` | Filtrage par pathologie |
| `date_of_admission_1` | `date_of_admission` | Tri / filtrage temporel |
| `insurance_provider_1` | `insurance_provider` | Analyse par assureur |

---

## 7. Authentification et rôles utilisateurs

L'initialisation MongoDB crée automatiquement trois comptes :

| Utilisateur | Mot de passe | Rôle | Usage |
|---|---|---|---|
| `admin` | `adminpassword` | `root` | Administration complète |
| `app_user` | `app_secure_password` | `readWrite` | Script de migration / application |
| `readonly_user` | `readonly_secure_password` | `read` | Analystes / tableaux de bord |

> ⚠️ **En production**, remplacez impérativement ces mots de passe par des secrets gérés via AWS Secrets Manager ou un fichier `.env` non versionné.

---

## 8. Tests d'intégrité

Les tests couvrent trois niveaux :

1. **Tests unitaires** – fonctions de nettoyage et typage (`clean_name`, `parse_date`, `cast_row`)
2. **Tests d'intégrité CSV** – colonnes présentes, types corrects, absence de doublons
3. **Tests post-migration** – structure des documents, appel de `insert_many` (avec mock)

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Lancer tous les tests avec rapport de couverture
pytest scripts/test_migration.py -v --cov=scripts --cov-report=term-missing

# Lancer un test spécifique
pytest scripts/test_migration.py::TestCSVIntegrity -v
```

---

## 9. Description du script de migration

Le script `scripts/migrate.py` effectue les opérations suivantes :

1. **Connexion** à MongoDB via `pymongo` (timeout 5 s, erreur explicite si MongoDB indisponible)
2. **Chargement du CSV** ligne par ligne avec gestion des erreurs (lignes invalides ignorées et tracées)
3. **Transformation** : normalisation des noms, cast des types (`int`, `float`, `datetime`), suppression des espaces parasites
4. **Insertion en masse** via `insert_many` (mode `ordered=False` pour continuer malgré les erreurs)
5. **Création des index** sur les champs les plus interrogés
6. **Rapport final** : nombre de documents insérés et total dans la collection

---

## 10. Déploiement sur AWS

Voir la présentation PowerPoint fournie pour le détail des options AWS recommandées :

- **Amazon DocumentDB** – Service MongoDB-compatible managé (idéal pour la production)
- **Amazon ECS / Fargate** – Déploiement des conteneurs Docker sans gestion de serveurs
- **Amazon S3** – Stockage des fichiers CSV source et sauvegardes
- **Amazon RDS** – Alternative relationnelle si besoin d'un système hybride

---

*Projet réalisé dans le cadre du stage Data Engineer chez DataSoluTech.*
*Auteur : Stagiaire – Mars 2026*
