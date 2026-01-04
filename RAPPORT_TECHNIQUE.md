# Rapport Technique du Projet Système de Recommandation "Beauty"

## 1. Vue d'Ensemble
Ce projet est une application web e-commerce complète intégrant un système de recommandation de produits de beauté. Il utilise une architecture client-serveur classique avec un backend Python (Flask) et une base de données relationnelle (MySQL), enrichie par un moteur de recommandation hybride alimenté par des algorithmes de filtrage collaboratif (ALS).

## 2. Technologies Utilisées

### Backend & Framework
-   **Flask:** Framework web léger pour gérer les routes HTTP et le rendu des templates.
-   **Flask-SQLAlchemy:** ORM (Object Relational Mapper) pour interagir avec la base de données MySQL.
-   **Flask-Login:** Gestion de l'authentification des utilisateurs (sessions, login, logout).
-   **Flask-Bcrypt:** Sécurisation des mots de passe par hachage.

### Base de Données
-   **MySQL (via PyMySQL):** Base de données principale stockant :
    -   Utilisateurs (`users`)
    -   Produits (`products`)
    -   Interactions (`interactions`) : Vues, likes.
    -   Panier (`cart_items`) & Wishlist (`wishlist_items`)
    -   Avis (`reviews`)
-   **Lazy Loading:** Les produits sont chargés "à la volée" dans la base SQL à partir des métadonnées (Parquet) uniquement lorsqu'un utilisateur les consulte ou les ajoute, optimisant ainsi le stockage.

### Science des Données & Machine Learning
-   **Pandas & NumPy:** Manipulation de données structurées.
-   **SciPy:** Gestion des matrices clairsemées (sparse matrices) pour les interactions utilisateurs-produits.
-   **Implicit (Probable):** Bibliothèque utilisée pour l'algorithme ALS (Alternating Least Squares) optimisé pour les données implicites (les vues et les clics sont des signaux implicites d'intérêt, contrairement aux notes explicites).
-   **Joblib & Pickle:** Sérialisation et chargement des modèles entraînés et des encodeurs.

### Frontend
-   **HTML/Jinja2:** Templates rendus côté serveur.
-   **Bootstrap (Probable):** Structure CSS pour le responsive design (déduit de la structure classique Flask).

## 3. Approche de Recommandation

Le cœur du système (`recommender.py`) implémente une **approche hybride avancée** pour pallier au problème du "Cold Start" (démarrage à froid) :

### A. Filtrage Collaboratif (Utilisateurs Existants)
Pour les utilisateurs ayant un historique :
1.  **Modèle ALS (Alternating Least Squares):** Décompose la matrice d'interactions en facteurs latents (vecteurs) pour les utilisateurs et les produits.
2.  **Score:** Le score de pertinence est le produit scalaire entre le vecteur utilisateur et le vecteur produit.
3.  **Filtrage:** Les produits déjà vus ou aimés sont exclus des résultats.

### B. Approche Hybride "Session-Aware" (Nouveaux Utilisateurs avec Historique Récent)
Si un utilisateur est nouveau (pas dans le modèle entraîné) mais a navigué sur le site dans la session actuelle :
1.  **Item-Item CF:** Le système prend les produits vus récemment (`recent_asins`).
2.  **Similarité:** Il cherche des produits similaires dans l'espace vectoriel du modèle ALS (basé sur la similarité cosinus des facteurs produits). Ceci permet de recommander des articles ressemblant à ce que l'utilisateur regarde *maintenant*, même sans historique long.

### C. Fallback (Secours)
1.  **Par Catégorie:** Si l'approche Item-Item ne donne pas assez de résultats, le système remplit la liste avec des produits populaires de la même catégorie que le dernier article vu.
2.  **Cold Start Pur (Global):** Si l'utilisateur n'a aucune interaction (ni passée, ni récente), le système affiche une liste pré-calculée d'articles populaires/tendance (`recent_items.pkl`).

## 4. Analyse Fichier par Fichier

| Fichier / Dossier | Rôle & Description |
| :--- | :--- |
| **`app.py`** | **Contrôleur Principal.** Configure l'application Flask, la connexion DB, et définit toutes les routes (`/`, `/login`, `/product/<asin>`, etc.). Gère la logique métier comme l'ajout au panier et l'enregistrement des interactions pour le moteur de recommandation. |
| **`recommender.py`** | **Moteur de Recommandation.** Classe `Recommender` qui charge les modèles (`.pkl`, `.npz`). Contient toute la logique algorithmique décrite ci-dessus (recommend(), recommend_from_history(), get_cold_start_items()). |
| **`models.py`** | **Schéma de Données.** Définit les classes Python correspondant aux tables SQL : `User`, `Product`, `Interaction`, `CartItem`, `WishlistItem`, `Review`. |
| **`requirements.txt`** | **Dépendances.** Liste des bibliothèques nécessaires (`flask`, `joblib`, `scipy`, etc.). |
| **`Adaptive_ColdAware_ALS_Recommender_Asmae (1).ipynb`** | **Entraînement.** Notebook Jupyter contenant le pipeline de Data Science : chargement des données brutes, nettoyage, création des matrices d'interaction, entraînement du modèle ALS, et sauvegarde des artefacts. |
| **`artifacts/`** | **Stockage Modèles.** Dossier contenant les fichiers binaires générés par le notebook : matrice d'entraînement, modèles ALS, encodeurs (ID <-> User), et métadonnées produits (Parquet). |
| **`templates/`** | **Vues.** Fichiers HTML (`index.html`, `product.html`, `login.html`) utilisant Jinja2 pour afficher dynamiquement les données envoyées par `app.py`. |
| **`data/`** | **Données Source.** Contient probablement les datasets originaux (CSV/JSON) utilisés pour l'entraînement. |

## 5. Conclusion
Ce projet est une implémentation robuste démontrant une excellente compréhension des contraintes réelles des systèmes de recommandation. Il ne se contente pas d'un modèle académique mais intègre une **stratégie de déploiement réaliste** : gestion des nouveaux utilisateurs, mise à jour en temps réel basée sur la session (Session-based Recs), et persistance des données via une base SQL transactionnelle pour le e-commerce.
