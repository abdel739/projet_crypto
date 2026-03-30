D´evelopper une application web de stockage de
fichiers s´ecuris´e
1 Introduction
Les services de stockage en ligne permettent aux utilisateurs de sauvegarder
et partager leurs fichiers `a distance. Cependant, ces services posent plusieurs
probl`emes de s´ecurit´e importants : protection des donn´ees stock´ees, contrˆole
des acc`es, et partage s´ecuris´e entre utilisateurs.
Dans ce projet, vous devrez concevoir et impl´ementer une application web de
stockage de fichiers s´ecuris´e, permettant aux utilisateurs de t´el´everser, stocker et
partager des fichiers tout en garantissant la confidentialit´e et le contrˆole d’acc`es.
L’objectif est de comprendre comment s´ecuriser un service web manipulant
des donn´ees sensibles.
2 Objectifs p´edagogiques
A l’issue de ce projet, vous devrez ˆetre capables de : `
• Impl´ementer un syst`eme d’authentification utilisateur
• Stocker des fichiers cˆot´e serveur
• Impl´ementer un m´ecanisme de partage s´ecuris´e de fichiers
• Appliquer des principes de s´ecurit´e informatique (contrˆole d’acc`es, chiffrement, gestion des identit´es)
3 Fonctionnalit´es attendues
Votre application devra impl´ementer au minimum les fonctionnalit´es suivantes
:
• Gestion des utilisateurs : cr´eation, suppression de compte et connexion/d´econnexion des utilisateurs. Le mot de passe ne doit jamais ˆetre
stock´e en clair.
1
• Upload et stockage de fichiers : un utilisateur authentifi´e doit pouvoir voir
la liste des fichiers stock´es sur son compte, envoyer un fichier au serveur
et en t´el´echarger.
• Confidentialit´e des fichiers stock´es : seul le propri´etaire peut acc´eder `a ses
fichiers (chiffrement des fichiers).
• Partage s´ecuris´e des fichiers entre utilisateurs : un utilisateur doit pouvoir
partager ses fichiers avec un autre utilisateur sans rompre la contrainte de
confidentialit´e.
L’interface doit rester simple (HTML/CSS) et pr´esenter une page d’inscript/connexion
et une page de liste de fichiers.
4 Technologies autoris´ees
Vous ˆetes libres de choisir les technologies que vous pr´ef´erez pour r´ealiser ce
projet.
5 Livrable attendu
• Le code source complet
• Un README expliquant comment lancer le projet
• Un court rapport (3 pages max) expliquant ce qui a ´et´e fait et comment
la s´ecurit´e a ´et´e r´ealis´ee dans ce projet.
2