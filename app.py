from flask import Flask, request, jsonify, session, send_file, render_template
from flask_cors import CORS
import os
import secrets
import io
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

from bd_manager import DatabaseManager
from security_utils import SecurityUtils

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or secrets.token_hex(32)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True, #Empêche le JavaScript malveillant d'accéder au cookie de session. Cela protège contre les attaques XSS (Cross-Site Scripting).
    SESSION_COOKIE_SAMESITE='Lax',#Empêche l'envoi du cookie lors de requêtes venant d'autres sites. Cela protège contre les attaques CSRF (Cross-Site Request Forgery).
    SESSION_COOKIE_SECURE=os.getenv('SESSION_COOKIE_SECURE', '0') == '1'#Si activé (à 1), le cookie ne circule que si la connexion est en HTTPS. En développement local (localhost), on le laisse souvent à 0.
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:5000,http://127.0.0.1:5000'
    ).split(',')
    if origin.strip()
]
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": allowed_origins}})

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'zip'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])#création d'un compte utilisateur avec un login et un mot de passe. 
#Le mot de passe est haché avec un sel avant d'être stocké en base de données.'
# Une paire de clés RSA est également générée pour l'utilisateur.
def register():
    try:
        data = request.get_json(silent=True) or {}
        login = data.get('login')
        password = data.get('password')
        
        if not login or not password:
            return jsonify({'success': False, 'message': 'Login et mot de passe requis'}), 400
        
        db = DatabaseManager()
        secu = SecurityUtils()
        
        # VÃ©rifier si l'utilisateur existe dÃ©jÃ 
        existing_user = db.execute_query("SELECT id_user FROM Utilisateur WHERE login = %s", (login,))
        if existing_user:
            return jsonify({'success': False, 'message': 'Ce login est dÃ©jÃ  utilisÃ©'}), 400
        
        print(f"Début inscription pour {login}")
        
        # Hachage du mot de passe
        pwd_hash, salt = secu.hash_password(password)
        print(f"Mot de passe hashé pour {login}")
        
        # Génération des clés RSA (clé privée + clé publique)
        private_pem, public_pem = secu.generate_rsa_keys()
        print(f"Clés RSA générées pour {login}")
        
        # Vérifier que la colonne cle_privee_pem existe
        check_column_query = """
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'utilisateur' AND column_name = 'cle_privee_pem';
        """
        column_exists = db.execute_query(check_column_query)
        if not column_exists:
            print(f"Colonne cle_privee_pem manquante pour {login}, tentative d'ajout automatique")
            alter_query = "ALTER TABLE Utilisateur ADD COLUMN cle_privee_pem BYTEA;"
            alter_success = db.execute_action(alter_query)
            if alter_success:
                print(f"Colonne ajoutée automatiquement pour {login}")
            else:
                print(f"Échec ajout colonne pour {login}")
                return jsonify({'success': False, 'message': 'Impossible d\'ajouter la colonne cle_privee_pem. Vérifiez les permissions DB.'}), 500
            
            # Re-vérifier
            column_exists = db.execute_query(check_column_query)
            if not column_exists:
                return jsonify({'success': False, 'message': 'Colonne cle_privee_pem toujours manquante après ajout.'}), 500
        
        # Insertion dans la base de données
        query = """
        INSERT INTO Utilisateur (login, password_hash, sel, cle_publique_pem, cle_privee_pem)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id_user;
        """
        
        params = (login, pwd_hash, salt, public_pem, private_pem)
        result = db.execute_query(query, params)
        print(f"Résultat insert pour {login}: {result}")
        
        if result:
            user_id = result[0][0]
            # On conserve uniquement l'etat de session, sans stocker de secret cryptographique cote client
            session['user_id'] = user_id
            session['login'] = login
            
            print(f"Inscription réussie pour {login}, id: {user_id}")
            return jsonify({
                'success': True, 
                'message': 'Inscription réussie',
                'user': {'id': user_id, 'login': login}
            })
        else:
            print(f"Échec insert pour {login}, vérifiez la base de données (colonne cle_privee_pem manquante ?)")
            return jsonify({'success': False, 'message': 'Erreur lors de l\'inscription'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])#connexion d'un utilisateur en vérifiant le login et le mot de passe. Le mot de passe fourni est haché avec le même sel que celui stocké en base, et comparé au hachage stocké. Si la connexion est réussie, l'état de session est mis à jour.
def login():
    try:
        data = request.get_json(silent=True) or {}
        login = data.get('login')
        password = data.get('password')
        
        if not login or not password:
            return jsonify({'success': False, 'message': 'Login et mot de passe requis'}), 400
        
        db = DatabaseManager()
        secu = SecurityUtils()
        
        # RÃ©cupÃ©rer l'utilisateur
        query = "SELECT id_user, password_hash, sel FROM Utilisateur WHERE login = %s"
        result = db.execute_query(query, (login,))
        
        if not result:
            return jsonify({'success': False, 'message': 'Login ou mot de passe incorrect'}), 401
        
        user_id, stored_hash, salt = result[0]
        stored_hash = bytes(stored_hash)
        salt = bytes(salt)
        
        # VÃ©rifier le mot de passe
        pwd_hash, _ = secu.hash_password(password, salt)
        
        if pwd_hash != stored_hash:
            return jsonify({'success': False, 'message': 'Login ou mot de passe incorrect'}), 401
        
        # Connexion rÃ©ussie
        session['user_id'] = user_id
        session['login'] = login
        
        return jsonify({
            'success': True,
            'message': 'Connexion rÃ©ussie',
            'user': {'id': user_id, 'login': login}
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'DÃ©connexion rÃ©ussie'})

@app.route('/api/user', methods=['GET'])
def get_user():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Non connecte'}), 401
    
    return jsonify({
        'success': True,
        'user': {'id': session['user_id'], 'login': session['login']}
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Non connecte'}), 401
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'Aucun fichier fourni'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Nom de fichier vide'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Type de fichier non autorisÃ©'}), 400
        
        # Lire les donnÃ©es du fichier
        file_data = file.read()
        
        # VÃ©rifier la taille
        if len(file_data) > MAX_FILE_SIZE:
            return jsonify({'success': False, 'message': 'Fichier trop volumineux (max 16MB)'}), 400
        
        # SÃ©curitÃ©
        db = DatabaseManager()
        secu = SecurityUtils()
        
        # GÃ©nÃ©rer une clÃ© AES et chiffrer le fichier
        aes_key = secu.generate_aes_key()
        encrypted_data, iv = secu.encrypt_file_aes(file_data, aes_key)
        
        # Calculer le hash
        file_hash = secu.hash_file_sha256(file_data)
        
        # GÃ©nÃ©rer un nom de stockage unique
        storage_name = secrets.token_urlsafe(16)
        
        # Sauvegarder le fichier chiffrÃ© sur le disque
        with open(os.path.join(UPLOAD_FOLDER, storage_name), 'wb') as f:
            f.write(encrypted_data)
        
        # InsÃ©rer dans la base de donnÃ©es
        query = """
        INSERT INTO Fichier (id_user, nom_original, nom_stockage, taille_octets, 
                           hash_sha256, cle_chiffrement_aes, iv_chiffrement)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id_fichier;
        """
        
        params = (
            session['user_id'],
            secure_filename(file.filename),
            storage_name,
            len(file_data),
            file_hash,
            aes_key,  # Dans un vrai projet, cette clÃ© serait chiffrÃ©e avec la clÃ© RSA de l'utilisateur
            iv
        )
        
        result = db.execute_query(query, params)
        
        if result:
            file_id = result[0][0]
            return jsonify({
                'success': True,
                'message': 'Fichier uploadÃ© avec succÃ¨s',
                'file': {
                    'id': file_id,
                    'name': secure_filename(file.filename),
                    'size': len(file_data)
                }
            })
        else:
            # Nettoyer le fichier en cas d'erreur
            os.remove(os.path.join(UPLOAD_FOLDER, storage_name))
            return jsonify({'success': False, 'message': 'Erreur lors de l\'insertion en base'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@app.route('/api/files', methods=['GET'])
def get_files():
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Non connecte'}), 401
        
        db = DatabaseManager()
        
        query = """
        SELECT id_fichier, nom_original, taille_octets, date_upload
        FROM Fichier
        WHERE id_user = %s
        ORDER BY date_upload DESC;
        """
        
        result = db.execute_query(query, (session['user_id'],))
        
        files = []
        for row in result:
            files.append({
                'id': row[0],
                'name': row[1],
                'size': row[2],
                'date': row[3].strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'success': True,
            'files': files
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@app.route('/api/download/<int:file_id>', methods=['GET'])
def download_file(file_id):
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Non connecte'}), 401
        
        db = DatabaseManager()
        secu = SecurityUtils()
        
        # RÃ©cupÃ©rer les infos du fichier
        query = """
        SELECT nom_original, nom_stockage, cle_chiffrement_aes, iv_chiffrement, id_user
        FROM Fichier
        WHERE id_fichier = %s;
        """
        
        result = db.execute_query(query, (file_id,))
        
        if not result:
            return jsonify({'success': False, 'message': 'Fichier non trouvÃ©'}), 404
        
        file_info = result[0]
        
        # VÃ©rifier que l'utilisateur est bien le propriÃ©taire
        if file_info[4] != session['user_id']:
            return jsonify({'success': False, 'message': 'Acces non autorise'}), 403
        
        # Lire le fichier chiffrÃ©
        encrypted_file_path = os.path.join(UPLOAD_FOLDER, file_info[1])
        if not os.path.exists(encrypted_file_path):
            return jsonify({'success': False, 'message': 'Fichier physique non trouve'}), 404
        
        with open(encrypted_file_path, 'rb') as f:
            encrypted_data = f.read()
        
        # DÃ©chiffrer avec AES
        decrypted_data = secu.decrypt_file_aes(encrypted_data, file_info[2], file_info[3])
        
        # Envoyer le fichier dÃ©chiffrÃ©
        return send_file(
            io.BytesIO(decrypted_data),
            as_attachment=True,
            download_name=file_info[0],
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@app.route('/api/share', methods=['POST'])
def share_file():
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Non connecte'}), 401
        
        data = request.get_json(silent=True) or {}
        file_id = data.get('file_id')
        recipient_login = data.get('recipient_login')
        
        if not file_id or not recipient_login:
            return jsonify({'success': False, 'message': 'ParamÃ¨tres manquants'}), 400
        
        db = DatabaseManager()
        secu = SecurityUtils()
        
        # VÃ©rifier que le fichier appartient Ã  l'utilisateur
        file_query = """
        SELECT id_user, cle_chiffrement_aes 
        FROM Fichier 
        WHERE id_fichier = %s;
        """
        file_result = db.execute_query(file_query, (file_id,))
        
        if not file_result:
            return jsonify({'success': False, 'message': 'Fichier non trouvÃ©'}), 404
        
        if file_result[0][0] != session['user_id']:
            return jsonify({'success': False, 'message': 'Acces non autorise'}), 403
        
        # Récupérer l'ID du destinataire
        recipient_query = "SELECT id_user, cle_publique_pem FROM Utilisateur WHERE login = %s;"
        recipient_result = db.execute_query(recipient_query, (recipient_login,))

        if recipient_result and recipient_result[0][0] == session['user_id']:
            return jsonify({'success': False, 'message': 'Impossible de partager un fichier avec soi-même'}), 400
        
        if not recipient_result:
            return jsonify({'success': False, 'message': 'Utilisateur destinataire non trouvÃ©'}), 404
        
        recipient_id, recipient_public_key = recipient_result[0]
        
        # VÃ©rifier que le partage n'existe pas dÃ©jÃ 
        existing_share = db.execute_query(
            "SELECT id_partage FROM Partage WHERE id_fichier = %s AND id_destinataire = %s;",
            (file_id, recipient_id)
        )
        
        if existing_share:
            return jsonify({'success': False, 'message': 'Fichier dÃ©jÃ  partagÃ© avec cet utilisateur'}), 400
        
        # Chiffrer la clÃ© AES avec la clÃ© publique du destinataire
        aes_key = file_result[0][1]  # La clÃ© AES du fichier
        encrypted_aes_key = secu.encrypt_with_rsa_public(aes_key, recipient_public_key)
        
        # CrÃ©er le partage
        share_query = """
        INSERT INTO Partage (id_fichier, id_proprietaire, id_destinataire, cle_chiffrement_partage)
        VALUES (%s, %s, %s, %s)
        RETURNING id_partage;
        """
        
        params = (file_id, session['user_id'], recipient_id, encrypted_aes_key)
        share_result = db.execute_query(share_query, params)
        
        if share_result:
            return jsonify({
                'success': True,
                'message': f'Fichier partagÃ© avec {recipient_login} avec succÃ¨s'
            })
        else:
            return jsonify({'success': False, 'message': 'Erreur lors du partage'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@app.route('/api/shared-files', methods=['GET'])#partage de fichier 
def get_shared_files():
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Non connecte'}), 401
        
        db = DatabaseManager()
        
        query = """
        SELECT f.id_fichier, f.nom_original, f.taille_octets, p.date_partage, u.login as proprietaire
        FROM Partage p
        JOIN Fichier f ON p.id_fichier = f.id_fichier
        JOIN Utilisateur u ON p.id_proprietaire = u.id_user
        WHERE p.id_destinataire = %s
        ORDER BY p.date_partage DESC;
        """
        
        result = db.execute_query(query, (session['user_id'],))
        
        files = []
        for row in result:
            files.append({
                'id': row[0],
                'name': row[1],
                'size': row[2],
                'date': row[3].strftime('%Y-%m-%d %H:%M:%S'),
                'owner': row[4]
            })
        
        return jsonify({
            'success': True,
            'files': files
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

@app.route('/api/download-shared/<int:file_id>', methods=['GET'])
def download_shared_file(file_id):
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Non connecte'}), 401

        db = DatabaseManager()
        secu = SecurityUtils()

        query = """
        SELECT f.nom_original, f.nom_stockage, f.iv_chiffrement, p.cle_chiffrement_partage, u.cle_privee_pem
        FROM Partage p
        JOIN Fichier f ON p.id_fichier = f.id_fichier
        JOIN Utilisateur u ON u.id_user = p.id_destinataire
        WHERE p.id_fichier = %s AND p.id_destinataire = %s;
        """
        result = db.execute_query(query, (file_id, session['user_id']))

        if not result:
            return jsonify({'success': False, 'message': 'Acces non autorise'}), 403

        file_info = result[0]
        encrypted_file_path = os.path.join(UPLOAD_FOLDER, file_info[1])
        if not os.path.exists(encrypted_file_path):
            return jsonify({'success': False, 'message': 'Fichier physique non trouve'}), 404

        with open(encrypted_file_path, 'rb') as f:
            encrypted_data = f.read()

        # Déchiffrement de la clé AES échangée via RSA
        shared_encrypted_aes = file_info[3]
        recipient_private_pem = file_info[4]
        aes_key = secu.decrypt_with_rsa_private(shared_encrypted_aes, recipient_private_pem)

        decrypted_data = secu.decrypt_file_aes(encrypted_data, aes_key, file_info[2])

        return send_file(
            io.BytesIO(decrypted_data),
            as_attachment=True,
            download_name=file_info[0],
            mimetype='application/octet-stream'
        )
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'}), 500

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', '0') == '1'
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))
    app.run(debug=debug_mode, host=host, port=port)



