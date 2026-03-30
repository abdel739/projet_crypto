import os
import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class SecurityUtils:
    
    @staticmethod
    def hash_password(password, salt=None):
        """Hachage SHA-256 avec Sel (Jalon 1 - Cours 3)"""
        if salt is None:
            salt = os.urandom(16)  # Génère un sel de 16 octets exp b'\x9f\xa1\x87...'
        
        # On utilise PBKDF2 pour rendre le hachage plus lent (protection contre brute force)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return pwd_hash, salt

    @staticmethod
    def generate_rsa_keys():
        """Génération d'une paire de clés RSA 2048 bits (Jalon 2 - Cours 2)"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()

        # On transforme la clé publique en format PEM (texte) pour la stocker en base
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # On retourne la clé privée (objet) et la clé publique (bytes pour la BDD)
        return private_key, public_pem

    @staticmethod
    def generate_aes_key():
        """Génère une clé AES 256 bits"""
        return os.urandom(32)  # 32 octets = 256 bits

    @staticmethod
    def encrypt_file_aes(file_data, key):
        """Chiffre des données avec AES-256-CBC"""
        iv = os.urandom(16)  # IV de 16 octets pour AES-CBC
        
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        
        encryptor = cipher.encryptor()
        
        # Padding PKCS7
        padding_length = 16 - (len(file_data) % 16)
        padded_data = file_data + bytes([padding_length] * padding_length)
        
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        return encrypted_data, iv

    @staticmethod
    def decrypt_file_aes(encrypted_data, key, iv):
        """Déchiffre des données avec AES-256-CBC"""
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
        
        # Retrait du padding PKCS7
        padding_length = padded_data[-1]
        return padded_data[:-padding_length]

    @staticmethod
    def encrypt_with_rsa_public(data, public_key_pem):
        """Chiffre des données avec une clé publique RSA"""
        public_key = serialization.load_pem_public_key(
            public_key_pem,
            backend=default_backend()
        )
        
        encrypted_data = public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return encrypted_data

    @staticmethod
    def decrypt_with_rsa_private(encrypted_data, private_key_pem):
        """Déchiffre des données avec une clé privée RSA"""
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,
            backend=default_backend()
        )
        
        decrypted_data = private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return decrypted_data

    @staticmethod
    def hash_file_sha256(file_data):
        """Calcule le hash SHA256 d'un fichier"""
        return hashlib.sha256(file_data).digest()