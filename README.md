# JAHJAH SECURITY - Application de Stockage de Fichiers Sécurisé

Une application web de stockage de fichiers sécurisée développée dans le cadre du projet de cryptographie.

## 🚀 Fonctionnalités

- **Authentification sécurisée** : Inscription et connexion avec hachage SHA-256 + sel
- **Chiffrement des fichiers** : AES-256 pour le stockage des fichiers
- **Contrôle d'accès** : Seul le propriétaire peut accéder à ses fichiers
- **Partage sécurisé** : Partage de fichiers entre utilisateurs avec chiffrement RSA
- **Interface moderne** : Design responsive avec HTML/CSS/JavaScript

## 📋 Prérequis

- Python 3.8+
- PostgreSQL 12+
- Navigateur web moderne

## 🛠️ Installation

### 1. Cloner le projet
```bash
git clone <repository-url>
cd tp-crypto
```

### 2. Installer les dépendances Python
```bash
pip install flask flask-cors psycopg2-binary cryptography
```

### 3. Configurer la base de données PostgreSQL

#### Créer la base de données
```sql
CREATE DATABASE crypto_storage;
```

#### Exécuter le script d'initialisation
```bash
psql -d crypto_storage -f init_database.sql
```

#### Modifier la configuration
Éditez le fichier `bd_manager.py` et modifiez les paramètres de connexion :
```python
self.config = {
    'host': 'localhost',
    'database': 'crypto_storage',  # Modifier si nécessaire
    'user': 'postgres',           # Modifier avec votre utilisateur
    'password': 'votre_mot_de_passe',  # Modifier avec votre mot de passe
    'port': '5432'
}
```

## 🏃‍♂️ Lancement de l'application

### 1. Démarrer le serveur Flask
```bash
python app.py
```

Le serveur démarrera sur `http://localhost:5000`

### 2. Accéder à l'application
Ouvrez votre navigateur et allez sur `http://localhost:5000`

## 📁 Structure du projet

```
tp-crypto/
├── app.py                 # Serveur web Flask
├── bd_manager.py          # Gestion de la base de données
├── security_utils.py       # Fonctions de cryptographie
├── index.html            # Interface utilisateur
├── script.js             # Logique frontend
├── style.css             # Styles CSS
├── init_database.sql     # Script d'initialisation BDD
├── uploads/              # Dossier de stockage des fichiers (créé automatiquement)
└── README.md             # Ce fichier
```

## 🔐 Sécurité implémentée

### Authentification
- **Hachage des mots de passe** : SHA-256 avec sel aléatoire
- **PBKDF2** : 100 000 itérations pour ralentir les attaques par force brute
- **Session sécurisée** : Token aléatoire de 128 bits

### Stockage des fichiers
- **Chiffrement AES-256-CBC** : Chaque fichier est chiffré avec une clé unique
- **IV aléatoire** : Vecteur d'initialisation unique pour chaque fichier
- **Hash SHA256** : Vérification de l'intégrité des fichiers

### Partage sécurisé
- **Chiffrement RSA-2048** : Clés publiques/privées pour le partage
- **Chiffrement hybride** : La clé AES est chiffrée avec RSA
- **Contrôle d'accès** : Vérification stricte des permissions

## 📝 Utilisation

### 1. Créer un compte
- Cliquez sur "Inscription"
- Choisissez un login et un mot de passe robuste
- Votre paire de clés RSA est générée automatiquement

### 2. Se connecter
- Utilisez vos identifiants pour vous connecter
- Une session sécurisée est créée

### 3. Uploader un fichier
- Cliquez sur "Choisir un fichier"
- Sélectionnez un fichier (max 16MB)
- Le fichier est chiffré localement puis envoyé au serveur

### 4. Partager un fichier
- Cliquez sur "Partager" à côté d'un fichier
- Entrez le login de l'utilisateur destinataire
- Le fichier devient accessible pour cet utilisateur

### 5. Télécharger
- Vos fichiers : liste "Mes fichiers sécurisés"
- Fichiers partagés : liste "Fichiers partagés avec moi"

## 🐛 Dépannage

### Problèmes courants

**Erreur de connexion à la base de données**
- Vérifiez que PostgreSQL est en cours d'exécution
- Vérifiez les identifiants dans `bd_manager.py`
- Assurez-vous que la base de données `crypto_storage` existe

**Le serveur ne démarre pas**
- Vérifiez que toutes les dépendances sont installées
- Vérifiez que le port 5000 n'est pas utilisé par une autre application

**Les fichiers ne s'uploadent pas**
- Vérifiez que le dossier `uploads/` a les droits d'écriture
- Vérifiez la taille du fichier (max 16MB)
- Vérifiez le type de fichier (formats autorisés)

## 🔧 Configuration avancée

### Modifier la taille maximale des fichiers
Dans `app.py`, modifiez la constante :
```python
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB par défaut
```

### Ajouter des types de fichiers autorisés
Dans `app.py`, modifiez l'ensemble :
```python
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'zip'}
```

### Changer le port du serveur
Dans `app.py`, modifiez la dernière ligne :
```python
app.run(debug=True, host='0.0.0.0', port=8080)  # Port 8080 au lieu de 5000
```

## 👥 Auteurs

Projet réalisé dans le cadre du cours de cryptographie.
Application développée avec Python Flask, PostgreSQL et des bibliothèques de cryptographie standards.

## 📄 Licence

Ce projet est à usage éducatif dans le cadre du projet de cryptographie.
