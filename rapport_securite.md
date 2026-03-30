# Rapport de Sécurité - JAHJAH SECURITY

*Application Web de Stockage de Fichiers Sécurisé*

## 1. Introduction

Ce rapport présente les mesures de sécurité implémentées dans l'application JAHJAH SECURITY, une plateforme de stockage de fichiers en ligne développée dans le cadre du projet de cryptographie. L'objectif principal est de garantir la confidentialité, l'intégrité et le contrôle d'accès des données utilisateur.

## 2. Architecture de Sécurité

### 2.1 Authentification et Gestion des Identités

**Hachage des mots de passe**
- Algorithme : SHA-256 avec salage aléatoire
- Fonction de dérivation : PBKDF2 avec 100 000 itérations
- Sel : 16 octets générés aléatoirement pour chaque utilisateur
- Stockage : Mot de passe jamais stocké en clair

```python
def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)  # Sel aléatoire de 16 octets
    
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return pwd_hash, salt
```

**Gestion des clés cryptographiques**
- Génération automatique d'une paire de clés RSA-2048 par utilisateur
- Clé privée : Conservée par l'utilisateur (simulation via session)
- Clé publique : Stockée en base de données au format PEM
- Utilisation : Chiffrement des clés de partage de fichiers

### 2.2 Chiffrement des Données

**Chiffrement des fichiers stockés**
- Algorithme : AES-256 en mode CBC
- Clé : 256 bits générée aléatoirement par fichier
- IV : 128 bits unique pour chaque chiffrement
- Padding : PKCS7 pour alignement sur blocs de 16 octets

```python
def encrypt_file_aes(file_data, key):
    iv = os.urandom(16)  # IV unique
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    # ... chiffrement avec padding PKCS7
```

**Intégrité des données**
- Calcul de hash SHA256 pour chaque fichier
- Vérification lors du déchiffrement
- Détection de corruption ou modification non autorisée

### 2.3 Contrôle d'Accès

**Autorisation basée sur les sessions**
- Token de session : 128 bits aléatoires
- Durée de vie limitée (configurable)
- Vérification systématique des permissions

**Isolation des données utilisateur**
- Séparation stricte des fichiers par utilisateur
- Contrôle d'accès avant chaque opération
- Pas de partage implicite entre utilisateurs

## 3. Mécanisme de Partage Sécurisé

### 3.1 Chiffrement Hybride

Le partage utilise un mécanisme de chiffrement hybride combinant AES et RSA :

1. **Génération** : Clé AES unique pour chaque fichier
2. **Chiffrement fichier** : AES-256-CBC avec clé aléatoire
3. **Chiffrement clé** : RSA-2048 avec clé publique du destinataire
4. **Stockage** : Clé AES chiffrée avec RSA dans la table de partage

### 3.2 Flux de Partage

```
Propriétaire → [Chiffre clé AES avec clé publique destinataire] → Destinataire
     ↓                                                        ↓
[Fichier chiffré avec AES]                            [Déchiffre clé AES avec clé privée]
     ↓                                                        ↓
[Stockage sécurisé]                                   [Accès au fichier]
```

### 3.3 Avantages de cette approche

- **Confidentialité** : Seul le destinataire peut déchiffrer la clé
- **Non-répudiation** : Preuve cryptographique du partage
- **Contrôle** : Le propriétaire contrôle explicitement les accès
- **Scalabilité** : Une clé par partage, pas par utilisateur

## 4. Menaces et Mesures de Protection

### 4.1 Menaces identifiées

**Attaques par force brute**
- **Mesure** : PBKDF2 avec 100 000 itérations
- **Efficacité** : Ralentit considérablement les tentatives

**Injection SQL**
- **Mesure** : Requêtes paramétrées avec psycopg2
- **Protection** : Validation automatique des entrées

**Vol de session**
- **Mesure** : Tokens aléatoires et durée de vie limitée
- **Protection** : HTTPS recommandé en production

**Accès non autorisé aux fichiers**
- **Mesure** : Vérification systématique de l'appartenance
- **Protection** : Isolation complète des données utilisateur

### 4.2 Limitations et Améliorations Possibles

**Limitations actuelles**
- Simulation de stockage des clés privées (session)
- Absence de HTTPS en développement
- Pas de rotation des clés cryptographiques
- Pas d'audit des accès

**Améliorations recommandées**
- Implémentation d'un système de gestion des clés (KMS)
- Ajout de l'authentification multi-facteurs
- Implémentation de logs d'audit
- Rotation périodique des clés

## 5. Conformité et Bonnes Pratiques

### 5.1 Principes de sécurité appliqués

**Principe de moindre privilège**
- Accès strictement nécessaire aux fonctionnalités
- Isolation des données entre utilisateurs

**Défense en profondeur**
- Plusieurs couches de sécurité
- Validation à chaque niveau

**Sécurité par l'obscurité évitée**
- Algorithmes standards et éprouvés
- Implémentations open-source et vérifiables

### 5.2 Bonnes pratiques de développement

- **Validation des entrées** : Contrôle systématique des données utilisateur
- **Gestion d'erreurs** : Messages d'erreur non révélateurs
- **Mise à jour** : Utilisation de bibliothèques cryptographiques maintenues
- **Tests** : Vérification des mécanismes de sécurité

## 6. Performance vs Sécurité

### 6.1 Compromis acceptés

**Performance**
- Chiffrement/déchiffrement synchrone (simplicité vs performance)
- Taille maximale des fichiers limitée à 16MB
- Nombre d'itérations PBKDF2 équilibré

**Sécurité**
- Clés RSA-2048 (bon compromis sécurité/performance)
- AES-256 (standard de référence)
- Pas de compromis sur la robustesse des algorithmes

### 6.2 Optimisations possibles

- Chiffrement asymétrique pour les clés de session
- Cache des clés déchiffrées (avec rotation)
- Compression avant chiffrement
- Parallélisation des opérations cryptographiques

## 7. Conclusion

L'application JAHJAH SECURITY implémente une architecture de sécurité robuste adaptée aux exigences d'un service de stockage de fichiers en ligne. Les mécanismes de chiffrement, d'authentification et de contrôle d'accès garantissent la confidentialité et l'intégrité des données utilisateur.

Le système de partage sécurisé utilise des techniques cryptographiques standards éprouvées, assurant que seuls les utilisateurs autorisés peuvent accéder aux fichiers partagés.

Bien que certaines améliorations soient possibles pour une utilisation en production, l'architecture actuelle fournit une base solide démontrant la compréhension et l'application correcte des principes de sécurité informatique.

---

*Ce rapport présente l'état actuel de l'application au moment de la soumission du projet.*
