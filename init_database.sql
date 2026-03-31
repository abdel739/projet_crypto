-- Script d'initialisation de la base de données pour le projet de stockage sécurisé
-- À exécuter dans pgAdmin ou psql

-- Création de la base (si nécessaire)
-- CREATE DATABASE crypto_storage;

-- Utilisation de la base
-- \c crypto_storage;

-- Table des utilisateurs
CREATE TABLE IF NOT EXISTS Utilisateur (
    id_user SERIAL PRIMARY KEY,
    login VARCHAR(50) UNIQUE NOT NULL,
    password_hash BYTEA NOT NULL,
    sel BYTEA NOT NULL,
    cle_publique_pem BYTEA NOT NULL,
    cle_privee_pem BYTEA NOT NULL,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des fichiers stockés
CREATE TABLE IF NOT EXISTS Fichier (
    id_fichier SERIAL PRIMARY KEY,
    id_user INTEGER NOT NULL REFERENCES Utilisateur(id_user) ON DELETE CASCADE,
    nom_original VARCHAR(255) NOT NULL,
    nom_stockage VARCHAR(255) NOT NULL UNIQUE,
    taille_octets INTEGER NOT NULL,
    hash_sha256 BYTEA NOT NULL,
    cle_chiffrement_aes BYTEA NOT NULL,
    iv_chiffrement BYTEA NOT NULL,
    date_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des partages de fichiers entre utilisateurs
CREATE TABLE IF NOT EXISTS Partage (
    id_partage SERIAL PRIMARY KEY,
    id_fichier INTEGER NOT NULL REFERENCES Fichier(id_fichier) ON DELETE CASCADE,
    id_proprietaire INTEGER NOT NULL REFERENCES Utilisateur(id_user) ON DELETE CASCADE,
    id_destinataire INTEGER NOT NULL REFERENCES Utilisateur(id_user) ON DELETE CASCADE,
    cle_chiffrement_partage BYTEA NOT NULL, -- Clé AES chiffrée avec la clé publique du destinataire
    date_partage TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(id_fichier, id_destinataire)
);

-- Table des sessions (optionnel, pour gestion avancée)
CREATE TABLE IF NOT EXISTS Session (
    id_session SERIAL PRIMARY KEY,
    id_user INTEGER NOT NULL REFERENCES Utilisateur(id_user) ON DELETE CASCADE,
    token_session VARCHAR(128) UNIQUE NOT NULL,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_expiration TIMESTAMP NOT NULL,
    ip_address INET,
    user_agent TEXT
);

-- Index pour optimiser les performances
CREATE INDEX IF NOT EXISTS idx_fichier_user ON Fichier(id_user);
CREATE INDEX IF NOT EXISTS idx_partage_fichier ON Partage(id_fichier);
CREATE INDEX IF NOT EXISTS idx_partage_destinataire ON Partage(id_destinataire);
CREATE INDEX IF NOT EXISTS idx_session_token ON Session(token_session);
CREATE INDEX IF NOT EXISTS idx_session_user ON Session(id_user);

-- Trigger pour nettoyer les sessions expirées (optionnel)
CREATE OR REPLACE FUNCTION nettoyer_sessions_expirees()
RETURNS void AS $$
BEGIN
    DELETE FROM Session WHERE date_expiration < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Commentaires pour documentation
COMMENT ON TABLE Utilisateur IS 'Table des utilisateurs avec leurs clés RSA';
COMMENT ON TABLE Fichier IS 'Fichiers chiffrés stockés sur le serveur';
COMMENT ON TABLE Partage IS 'Partages sécurisés entre utilisateurs';
COMMENT ON TABLE Session IS 'Sessions utilisateur pour gestion avancée';

COMMENT ON COLUMN Fichier.cle_chiffrement_aes IS 'Clé AES utilisée pour chiffrer le fichier (stockée chiffrée)';
COMMENT ON COLUMN Fichier.iv_chiffrement IS 'Vecteur d''initialisation pour le chiffrement AES';
COMMENT ON COLUMN Partage.cle_chiffrement_partage IS 'Clé AES chiffrée avec la clé publique du destinataire';
