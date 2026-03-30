# Guide Complet - Comment Fonctionne l'Application

*Explication détaillée pour comprendre chaque partie du projet*

## 🎯 Objectif de ce guide

Ce document explique point par point comment l'application JAHJAH SECURITY fonctionne, pour que tu puisses comprendre chaque mécanisme technique et cryptographique implémenté.

---

## 📁 Structure Générale du Projet

```
tp-crypto/
├── app.py              # Le "cerveau" : serveur web qui gère tout
├── index.html          # L'interface : ce que l'utilisateur voit
├── script.js           # La logique côté client : interactions utilisateur
├── style.css           # Le design : couleurs, mise en page
├── bd_manager.py       # Le gardien : communication avec la base de données
├── security_utils.py   # L'arsenal : toutes les fonctions de cryptographie
├── init_database.sql   # Le plan : structure de la base de données
└── requirements.txt    # La liste : tous les paquets Python nécessaires
```

---

## 🔐 1. L'Authentification - Comment ça marche ?

### Le problème à résoudre
Quand un utilisateur s'inscrit, on doit stocker son mot de passe MAIS JAMAIS en clair. Si quelqu'un vole la base de données, il ne doit pas pouvoir retrouver les mots de passe.

### La solution technique

#### Étape 1 : Hachage avec sel
```python
# Dans security_utils.py
def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)  # Sel aléatoire de 16 octets
    
    # PBKDF2 = Password-Based Key Derivation Function 2
    # 100000 itérations = rend le hachage très lent (protection contre force brute)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return pwd_hash, salt
```

**Pourquoi c'est sécurisé ?**
- **Sel aléatoire** : Même si deux utilisateurs ont le même mot de passe "123456", les hashs seront différents
- **PBKDF2** : Rend le calcul du hash très lent (100000 itérations)
- **SHA-256** : Algorithme de hachage cryptographique standard

#### Étape 2 : Génération des clés RSA
```python
# Chaque utilisateur reçoit une paire de clés RSA-2048
def generate_rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()
    
    # La clé publique est stockée en base (format PEM)
    # La clé privée est gardée par l'utilisateur (simulation via session)
```

**À quoi servent ces clés ?**
- **Clé publique** : Pour chiffrer des données destinées à cet utilisateur
- **Clé privée** : Pour déchiffrer les données chiffrées avec sa clé publique

---

## 🔒 2. Le Chiffrement des Fichiers - Comment ça marche ?

### Le problème à résoudre
Les fichiers sont stockés sur le serveur. Si quelqu'un accède au serveur, il ne doit pas pouvoir lire les fichiers.

### La solution technique : Chiffrement AES-256

#### Étape 1 : Quand l'utilisateur upload un fichier
```python
# 1. Générer une clé AES unique pour ce fichier
aes_key = secu.generate_aes_key()  # 256 bits = 32 octets

# 2. Chiffrer le fichier avec cette clé
encrypted_data, iv = secu.encrypt_file_aes(file_data, aes_key)

# 3. Stocker le fichier chiffré sur le disque
with open(storage_name, 'wb') as f:
    f.write(encrypted_data)

# 4. Stocker la clé AES en base (chiffrée avec la clé RSA de l'utilisateur)
```

#### Étape 2 : Le mécanisme de chiffrement AES
```python
def encrypt_file_aes(file_data, key):
    # IV = Initialisation Vector (16 octets aléatoires)
    iv = os.urandom(16)
    
    # Configuration du chiffrement AES-256-CBC
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    
    # Padding PKCS7 : les données doivent faire un multiple de 16 octets
    padding_length = 16 - (len(file_data) % 16)
    padded_data = file_data + bytes([padding_length] * padding_length)
    
    # Chiffrement
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    return encrypted_data, iv
```

**Pourquoi AES-256-CBC ?**
- **AES-256** : Algorithme de chiffrement symétrique très sécurisé
- **CBC** : Mode d'opération qui utilise un IV pour éviter les répétitions
- **Padding PKCS7** : Standard pour compléter les blocs

---

## 🔗 3. Le Partage Sécurisé - Comment ça marche ?

### Le problème à résoudre
Alice veut partager un fichier avec Bob. Bob doit pouvoir lire le fichier, mais personne d'autre.

### La solution technique : Chiffrement Hybride

#### Étape 1 : Alice partage son fichier
```python
# 1. Récupérer la clé publique RSA de Bob
bob_public_key = get_public_key("bob")

# 2. Chiffrer la clé AES du fichier avec la clé publique de Bob
encrypted_aes_key = secu.encrypt_with_rsa_public(aes_key, bob_public_key)

# 3. Stocker cette information dans la table Partage
INSERT INTO Partage (id_fichier, id_proprietaire, id_destinataire, cle_chiffrement_partage)
VALUES (fichier_id, alice_id, bob_id, encrypted_aes_key)
```

#### Étape 2 : Bob télécharge le fichier partagé
```python
# 1. Récupérer la clé AES chiffrée
encrypted_aes_key = get_encrypted_key_from_database()

# 2. Déchiffrer avec sa clé privée RSA
aes_key = secu.decrypt_with_rsa_private(encrypted_aes_key, bob_private_key)

# 3. Utiliser cette clé AES pour déchiffrer le fichier
file_data = secu.decrypt_file_aes(encrypted_file, aes_key, iv)
```

**Pourquoi cette approche ?**
- **Efficacité** : RSA est lent, AES est rapide → On chiffre une petite clé avec RSA, le gros fichier avec AES
- **Sécurité** : Seul Bob peut déchiffrer la clé AES avec sa clé privée
- **Contrôle** : Alice contrôle exactement qui peut accéder au fichier

---

## 🌐 4. L'Architecture Web - Comment ça s'articule ?

### Le flux complet d'une action

#### Quand l'utilisateur clique sur "S'inscrire"
```
1. Frontend (script.js) → Envoie les données au serveur
2. Backend (app.py) → Reçoit la requête POST /api/register
3. Backend → Appelle security_utils.hash_password()
4. Backend → Appelle security_utils.generate_rsa_keys()
5. Backend → Appelle bd_manager.execute_query() pour stocker l'utilisateur
6. Backend → Répond "succès" au frontend
7. Frontend → Affiche le tableau de bord
```

#### Quand l'utilisateur upload un fichier
```
1. Frontend → Crée FormData avec le fichier
2. Frontend → Envoie POST /api/upload avec le fichier
3. Backend → Reçoit le fichier, le lit en mémoire
4. Backend → Génère clé AES, chiffre le fichier
5. Backend → Sauvegarde le fichier chiffré sur le disque
6. Backend → Stocke les métadonnées en base
7. Backend → Répond "succès"
8. Frontend → Met à jour la liste des fichiers
```

---

## 🗄️ 5. La Base de Données - Comment c'est organisé ?

### Structure des tables

#### Table Utilisateur
```sql
CREATE TABLE Utilisateur (
    id_user SERIAL PRIMARY KEY,           -- ID unique
    login VARCHAR(50) UNIQUE NOT NULL,   -- Nom d'utilisateur
    password_hash BYTEA NOT NULL,         -- Mot de passe haché
    sel BYTEA NOT NULL,                   -- Sel pour le hachage
    cle_publique_pem BYTEA NOT NULL,      -- Clé publique RSA
    date_creation TIMESTAMP DEFAULT NOW() -- Date d'inscription
);
```

#### Table Fichier
```sql
CREATE TABLE Fichier (
    id_fichier SERIAL PRIMARY KEY,
    id_user INTEGER REFERENCES Utilisateur, -- Propriétaire
    nom_original VARCHAR(255),              -- Nom original du fichier
    nom_stockage VARCHAR(255) UNIQUE,        -- Nom sur le serveur (aléatoire)
    taille_octets INTEGER,                   -- Taille en octets
    hash_sha256 BYTEA,                       -- Hash pour vérifier l'intégrité
    cle_chiffrement_aes BYTEA,              -- Clé AES (chiffrée avec RSA)
    iv_chiffrement BYTEA,                   -- Vecteur d'initialisation
    date_upload TIMESTAMP DEFAULT NOW()
);
```

#### Table Partage
```sql
CREATE TABLE Partage (
    id_partage SERIAL PRIMARY KEY,
    id_fichier INTEGER REFERENCES Fichier,      -- Fichier partagé
    id_proprietaire INTEGER REFERENCES Utilisateur, -- Qui partage
    id_destinataire INTEGER REFERENCES Utilisateur, -- Qui reçoit
    cle_chiffrement_partage BYTEA,              -- Clé AES chiffrée avec RSA
    date_partage TIMESTAMP DEFAULT NOW(),
    UNIQUE(id_fichier, id_destinataire)         -- Pas de doublons
);
```

---

## 🔧 6. Les Fichiers Clés - Leur rôle exact

### app.py - Le serveur web
**Rôle** : C'est le chef d'orchestre
- Reçoit toutes les requêtes HTTP
- Vérifie que l'utilisateur est authentifié
- Coordonne les autres modules
- Envoie les réponses JSON au frontend

**Endpoints principaux** :
- `POST /api/register` - Inscription
- `POST /api/login` - Connexion
- `POST /api/upload` - Upload de fichier
- `GET /api/files` - Liste des fichiers
- `POST /api/share` - Partage de fichier

### bd_manager.py - Le gardien de la base
**Rôle** : Protège la base de données
- Évite les injections SQL avec des requêtes paramétrées
- Gère les connexions automatiquement
- Simplifie les opérations CRUD

### security_utils.py - L'arsenal cryptographique
**Rôle** : Contient toutes les fonctions de sécurité
- Hachage de mots de passe
- Génération de clés RSA
- Chiffrement/déchiffrement AES
- Chiffrement RSA

---

## 🚀 7. Comment Lancer et Tester le Projet

### Étape par étape

#### 1. Préparation de l'environnement
```bash
# Installer Python 3.8+
# Installer PostgreSQL 12+

# Installer les dépendances
pip install -r requirements.txt
```

#### 2. Configuration de la base
```sql
-- Dans pgAdmin ou psql
CREATE DATABASE crypto_storage;

-- Exécuter le script
\i init_database.sql
```

#### 3. Configuration de la connexion
```python
# Dans bd_manager.py, modifier si nécessaire
self.config = {
    'host': 'localhost',
    'database': 'crypto_storage',
    'user': 'postgres',           # Ton utilisateur PostgreSQL
    'password': 'ton_mot_de_passe', # Ton mot de passe
    'port': '5432'
}
```

#### 4. Démarrage
```bash
python app.py
```

#### 5. Test de l'application
1. Ouvre `http://localhost:5000`
2. Crée deux comptes : "alice" et "bob"
3. Connecte-toi avec "alice"
4. Upload un fichier
5. Partage ce fichier avec "bob"
6. Déconnecte-toi, connecte-toi avec "bob"
7. Vérifie que tu peux télécharger le fichier partagé

---

## 🎓 8. Concepts Cryptographiques Utilisés

### Hachage vs Chiffrement
- **Hachage** : One-way function (mot de passe → hash, mais hash → ?)
- **Chiffrement** : Two-way function (données ↔ chiffrées avec clé)

### Symétrique vs Asymétrique
- **Symétrique (AES)** : Une seule clé pour chiffrer et déchiffrer (rapide)
- **Asymétrique (RSA)** : Clé publique pour chiffrer, clé privée pour déchiffrer (sécurisé)

### Chiffrement Hybride
- Combine les avantages des deux approches
- RSA pour les petites données (clés)
- AES pour les grosses données (fichiers)

---

## 🐛 9. Problèmes Courants et Solutions

### "Erreur de connexion à la base de données"
**Causes possibles** :
- PostgreSQL n'est pas démarré
- Mauvais identifiants dans `bd_manager.py`
- La base de données n'existe pas

**Solution** :
```bash
# Vérifier que PostgreSQL tourne
pg_ctl status

# Créer la base si nécessaire
createdb crypto_storage

# Exécuter le script d'initialisation
psql -d crypto_storage -f init_database.sql
```

### "Le serveur ne démarre pas"
**Causes possibles** :
- Port 5000 déjà utilisé
- Dépendances manquantes

**Solutions** :
```bash
# Changer de port dans app.py
app.run(debug=True, host='0.0.0.0', port=8080)

# Réinstaller les dépendances
pip install -r requirements.txt --force-reinstall
```

---

## 📈 10. Pour Aller Plus Loin

### Améliorations possibles
1. **HTTPS** : Ajouter SSL/TLS pour la communication
2. **2FA** : Authentification à deux facteurs
3. **Audit** : Logs de toutes les actions
4. **Rotation des clés** : Renouveler périodiquement les clés
5. **Compression** : Compresser avant de chiffrer

### Tests de sécurité
1. **Tests d'injection SQL** : Vérifier que les requêtes paramétrées fonctionnent
2. **Tests de force brute** : Essayer de cracker des mots de passe
3. **Tests d'accès non autorisé** : Tenter d'accéder aux fichiers des autres

---

## 💡 Conclusion

Cette application démontre l'application pratique des concepts de cryptographie dans un contexte web réel. Chaque mécanisme de sécurité a été implémenté en suivant les meilleures pratiques actuelles.

Le code est modulaire, bien documenté et utilise des bibliothèques cryptographiques standards et éprouvées. C'est une excellente base pour comprendre comment la sécurité est implémentée dans les applications modernes.

---

*Ce guide est évolutif ! N'hésite pas à poser des questions sur les parties que tu ne comprends pas.*
