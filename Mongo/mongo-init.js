// mongo-init.js
// Exécuté automatiquement au premier démarrage du conteneur MongoDB
// Crée la base healthcare_db avec les rôles utilisateurs appropriés

// ── Connexion à la base cible ─────────────────────────────────────────────
db = db.getSiblingDB("healthcare_db");

// ── Création des utilisateurs ─────────────────────────────────────────────

// 1. Utilisateur applicatif (lecture + écriture) – utilisé par le script de migration
db.createUser({
  user: "app_user",
  pwd: "app_secure_password",
  roles: [
    { role: "readWrite", db: "healthcare_db" }
  ]
});

// 2. Utilisateur en lecture seule – pour les analystes / rapports
db.createUser({
  user: "readonly_user",
  pwd: "readonly_secure_password",
  roles: [
    { role: "read", db: "healthcare_db" }
  ]
});

// ── Création de la collection avec schéma de validation JSON ─────────────
db.createCollection("patients", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: [
        "name", "age", "gender", "blood_type", "medical_condition",
        "date_of_admission", "billing_amount"
      ],
      properties: {
        name:               { bsonType: "string",   description: "Nom complet du patient" },
        age:                { bsonType: "int",       minimum: 0, maximum: 150 },
        gender:             { bsonType: "string",   enum: ["Male", "Female"] },
        blood_type:         { bsonType: "string" },
        medical_condition:  { bsonType: "string" },
        date_of_admission:  { bsonType: "date" },
        doctor:             { bsonType: "string" },
        hospital:           { bsonType: "string" },
        insurance_provider: { bsonType: "string" },
        billing_amount:     { bsonType: "double",   minimum: 0 },
        room_number:        { bsonType: "int",      minimum: 1 },
        admission_type:     { bsonType: "string",
                              enum: ["Urgent", "Emergency", "Elective"] },
        discharge_date:     { bsonType: "date" },
        medication:         { bsonType: "string" },
        test_results:       { bsonType: "string",
                              enum: ["Normal", "Abnormal", "Inconclusive"] }
      }
    }
  },
  validationLevel: "moderate",   // warn uniquement – n'empêche pas l'import
  validationAction: "warn"
});

print("✓ Base 'healthcare_db' initialisée avec utilisateurs et schéma de validation.");
