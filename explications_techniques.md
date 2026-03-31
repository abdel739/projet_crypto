# Explications Techniques (Version a jour)

Ce document decrit l'etat reel du projet apres les dernieres modifications.

## 1. Architecture du projet

Structure principale:

```text
Tp crypto V1/
|-- app.py
|-- bd_manager.py
|-- security_utils.py
|-- init_database.sql
|-- requirements.txt
|-- .env.example
|-- templates/
|   `-- index.html
`-- static/
    |-- script.js
    `-- style.css
```

Roles:

- `app.py`: API Flask, gestion session, upload/download, partage.
- `bd_manager.py`: acces PostgreSQL via requetes parametrees.
- `security_utils.py`: hash password, RSA, AES, SHA256.
- `init_database.sql`: schema SQL (Utilisateur, Fichier, Partage, Session).
- `static/script.js`: logique frontend.

## 2. Configuration via environnement

Le projet utilise maintenant `.env` (charge avec `python-dotenv`).

Variables principales:

- `FLASK_SECRET_KEY`
- `FLASK_DEBUG`
- `FLASK_HOST`
- `FLASK_PORT`
- `SESSION_COOKIE_SECURE`
- `CORS_ALLOWED_ORIGINS`
- `DB_HOST`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_PORT`

Exemple fourni dans `.env.example`.

## 3. Backend Flask (app.py)

### 3.1 Securite session et CORS

- Secret key chargee depuis env (fallback random).
- Cookies session:
  - `HTTPOnly=True`
  - `SameSite='Lax'`
  - `Secure` pilotable par `SESSION_COOKIE_SECURE`
- CORS restreint aux origines definies dans `CORS_ALLOWED_ORIGINS`.

### 3.2 Endpoints disponibles

- `GET /` page principale
- `POST /api/register`
- `POST /api/login`
- `POST /api/logout`
- `GET /api/user`
- `POST /api/upload`
- `GET /api/files`
- `GET /api/download/<file_id>`
- `POST /api/share`
- `GET /api/shared-files`
- `GET /api/download-shared/<file_id>`

### 3.3 Correctif important applique

Bug corrige sur la connexion:

- PostgreSQL retourne les `BYTEA` en `memoryview`.
- Au login, `stored_hash` et `salt` sont convertis en `bytes`.
- Sans cette conversion, la comparaison hash mot de passe echouait meme avec le bon mot de passe.

## 4. Base de donnees (PostgreSQL)

Nom actuel de base: `crypto_final` (via `DB_NAME`).

Tables:

- `Utilisateur`
- `Fichier`
- `Partage`
- `Session` (table optionnelle, non utilisee par Flask session cookie)

Correctif SQL applique:

- Commentaire de colonne corrige dans `init_database.sql`:
  - `Fichier.iv_chiffrement` (et non `iv_chiffrement_aes`).

## 5. Cryptographie (security_utils.py)

### 5.1 Authentification

- Hash mot de passe: `PBKDF2-HMAC-SHA256`
- Sel aleatoire: 16 octets
- Iterations: 100000

### 5.2 Fichiers

- Cle AES 256 bits par fichier
- Chiffrement AES-CBC + padding PKCS7
- Hash SHA256 du contenu original

### 5.3 Partage

- Paire RSA 2048 creee a l'inscription
- Cle AES chiffree avec cle publique du destinataire pour le partage
- Limite actuelle: au telechargement partage (`/api/download-shared/<id>`), le backend reutilise encore `Fichier.cle_chiffrement_aes` au lieu d'exploiter `Partage.cle_chiffrement_partage` + dechiffrement RSA cote destinataire.

## 6. Frontend (static/script.js)

Points importants:

- API base: `window.location.origin + '/api'`
- Helper `apiFetch()` avec `credentials: 'include'` pour conserver la session.
- Flux supportes:
  - inscription/connexion/deconnexion
  - upload
  - listing fichiers perso et partages
  - download perso
  - download partage (`/api/download-shared/<id>`)

## 7. Dependances

`requirements.txt`:

- `flask==2.3.3`
- `flask-cors==4.0.0`
- `psycopg2-binary==2.9.11`
- `cryptography==41.0.4`
- `werkzeug==2.3.7`
- `python-dotenv==1.0.1`

## 8. Commandes utiles

Installer:

```bash
pip install -r requirements.txt
```

Initialiser la DB:

```bash
psql -d crypto_final -f init_database.sql
```

Lancer:

```bash
py app.py
```

## 9. Limites actuelles a connaitre

- La cle AES de fichier est encore stockee en base.
- Le mode AES utilise CBC (pas AEAD type GCM).
- Les messages d'erreur API peuvent encore etre ameliorees pour eviter des details internes.

Ces points sont des pistes de durcissement pour une prochaine version.

## 10. Tests effectues

Tests verifies pendant les corrections:

- inscription utilisateur (`/api/register`) OK
- connexion utilisateur (`/api/login`) OK
- correction bug login PostgreSQL (`memoryview` vers `bytes`) validee
- upload fichier (`/api/upload`) OK
- liste fichiers proprietaire (`/api/files`) OK
- telechargement proprietaire (`/api/download/<id>`) OK
- partage fichier (`/api/share`) OK
- liste partages recus (`/api/shared-files`) OK
- telechargement partage (`/api/download-shared/<id>`) OK
- verification connexion DB et presence des tables `utilisateur`, `fichier`, `partage`, `session` OK
