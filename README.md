# ONEF Customer Success AI

Backend Python pour automatiser la lecture d'emails Gmail, l'analyse du ton client avec Gemini, la consultation d'un historique Google Sheets et la génération de réponses Gmail dans Gmail.

Le projet suit le cadrage demandé dans `prompt.txt` :

- `src/main.py` : orchestration et API FastAPI
- `src/gmail_api.py` : lecture Gmail, brouillons, marquage lu
- `src/sheets_api.py` : recherche client dans Google Sheets
- `src/logic.py` : analyse, matrice de décision, génération de réponse
- `index.py` : point d'entrée Vercel
- `src/manager_store.py` : file manager persistée localement
- `src/manager_ui.py` : interface manager web

## Fonctionnement

1. Lit les emails non lus de la boîte Gmail.
2. Extrait le contenu texte et l'adresse email du client.
3. Cherche le client dans Google Sheets.
4. Analyse le message avec Gemini ou avec un fallback heuristique si `GEMINI_API_KEY` n'est pas fournie.
5. Applique la matrice de décision centralisée dans `src/logic.py`.
6. Décide si la réponse peut être envoyée automatiquement ou doit rester en brouillon.
7. Envoie ou crée un brouillon Gmail selon le niveau de risque.
8. Marque le message comme lu après traitement.

## Variables d'environnement

Copier `.env.example` vers `.env`, puis renseigner les champs utiles.

Variables principales :

- `GEMINI_API_KEY` : clé API Gemini
- `GEMINI_MODEL` : modèle à utiliser, par défaut `gemini-2.5-flash`
- `GOOGLE_CREDENTIALS_JSON` : JSON OAuth Google complet sur une ligne, ou laisser `credentials.json`
- `GOOGLE_REDIRECT_URI` : callback OAuth exact
- `GOOGLE_TOKEN_JSON` : token OAuth obtenu après consentement
- `GOOGLE_SHEETS_SPREADSHEET_ID` : ID du Google Sheet client
- `GOOGLE_SHEETS_RANGE` : plage, par défaut `Clients!A:Z`
- `MAX_MESSAGES_PER_RUN` : nombre max d'emails traités par exécution
- `APP_BASE_URL` : URL publique du déploiement, par exemple `https://custumer-success-ai.vercel.app`
- `AUTO_SEND_REPLIES` : `true` pour autoriser l'envoi automatique
- `ALLOW_AUTO_SEND_FURIOUS` : `true` seulement si tu acceptes les réponses automatiques à des clients très mécontents
- `COMPANY_NAME` : nom de l'entreprise injecté dans les prompts
- `COMPANY_SIGNATURE` : signature des emails
- `KNOWLEDGE_BASE_TEXT` : règles métier, FAQ ou politique interne injectées à l'IA
- `CRON_SECRET` : secret Bearer pour sécuriser `/api/cron`
- `DECISION_MATRIX_JSON` : surcharge optionnelle de la matrice métier

Exemple de matrice :

```json
[
  {
    "sentiment": "FURIEUX",
    "min_total_achats": 100000,
    "discount_pct": 20,
    "gesture_label": "remise de 20%"
  }
]
```

## Installation locale

```bash
cd /mnt/d/amelie/custumer-success-ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## OAuth Google

Le dépôt contient déjà `credentials.json`, mais il te faut aussi un `token` OAuth avec `refresh_token` pour permettre les exécutions automatiques.

### Option recommandée avec l'API du projet

1. Déploie le projet.
2. Définis :
   - `APP_BASE_URL=https://custumer-success-ai.vercel.app`
   - `GOOGLE_REDIRECT_URI=https://custumer-success-ai.vercel.app/google/oauth/callback`
3. Ouvre :
   - `https://custumer-success-ai.vercel.app/google/oauth/start`
4. Copie l'`authorization_url` dans le navigateur et connecte-toi.
5. Après retour sur `/google/oauth/callback`, récupère `token_json`.
6. Ajoute ce JSON comme variable `GOOGLE_TOKEN_JSON` dans Vercel.

### Important

Ton `credentials.json` actuel contient encore comme `redirect_uris` la racine du site. Pour que le callback fonctionne proprement, il faut enregistrer dans Google Cloud :

- `https://custumer-success-ai.vercel.app/google/oauth/callback`

et si tu veux tester en local :

- `http://localhost:8000/google/oauth/callback`

## Google Sheets

Le code suppose une première ligne d'en-têtes dans la feuille. Les alias suivants sont gérés automatiquement :

- Email : `email`, `mail`, `adresse_email`
- Total achats : `total_achats`, `total achats`, `montant_total`, `lifetime_value`
- Nombre de commandes : `nombre_commandes`, `nb_commandes`, `orders`, `commandes`
- Nom : `nom`, `name`, `client`, `customer_name`

## Lancement local

Exécution ponctuelle en CLI :

```bash
source venv/bin/activate
python -m src.main
```

API locale :

```bash
source venv/bin/activate
uvicorn src.main:app --reload
```

Routes utiles :

- En local via `uvicorn`, les routes sont sans préfixe `/api`.
- Une fois déployées sur Vercel, les routes restent accessibles à la racine.
- `GET /` : statut simple
- `GET /health` : état de configuration
- `GET /manager` : interface manager web
- `GET /manager/api/items` : file manager persistée
- `POST /manager/api/sync` : synchronisation Gmail vers la file manager
- `POST /run` : traite la boîte une fois
- `GET /google/oauth/start` : génère l'URL de consentement
- `GET /google/oauth/callback` : échange le code contre le token
- `GET /cron` : endpoint prévu pour l'automatisation

## Déploiement Vercel

Le projet inclut déjà `vercel.json` avec :

- fonction Python : `index.py`
- cron : une fois par jour sur `/cron` (compatible plan Hobby)

Configurer sur Vercel :

- `GEMINI_API_KEY`
- `GOOGLE_CREDENTIALS_JSON` ou le contenu du fichier `credentials.json`
- `GOOGLE_TOKEN_JSON`
- `GOOGLE_REDIRECT_URI`
- `GOOGLE_SHEETS_SPREADSHEET_ID`
- `GOOGLE_SHEETS_RANGE`
- `APP_BASE_URL`
- `CRON_SECRET`

Si `CRON_SECRET` est activé, l'appel doit inclure :

```text
Authorization: Bearer <CRON_SECRET>
```

## Limites importantes

- Vercel n'exécute pas de daemon Python permanent. L'automatisation se fait donc par appels planifiés (`cron`), ce qui est la bonne adaptation pour ce type d'hébergement.
- La file manager repose actuellement sur SQLite local (`manager_queue.db`). En local c'est persistant, sur Vercel le stockage reste éphémère tant qu'aucune base externe n'est ajoutée.
- Le système peut envoyer automatiquement seulement si `AUTO_SEND_REPLIES=true` et si le mail est jugé assez sûr.
- Les cas risqués comme remboursement, forte colère client ou faible confiance IA restent orientés vers un brouillon.
- Sans `GEMINI_API_KEY`, le projet reste utilisable avec une classification heuristique plus simple, mais moins intelligente.

## Fichiers présents

- [src/main.py](/mnt/d/amelie/custumer-success-ai/src/main.py)
- [src/gmail_api.py](/mnt/d/amelie/custumer-success-ai/src/gmail_api.py)
- [src/sheets_api.py](/mnt/d/amelie/custumer-success-ai/src/sheets_api.py)
- [src/logic.py](/mnt/d/amelie/custumer-success-ai/src/logic.py)
- [src/config.py](/mnt/d/amelie/custumer-success-ai/src/config.py)
- [src/manager_store.py](/mnt/d/amelie/custumer-success-ai/src/manager_store.py)
- [src/manager_ui.py](/mnt/d/amelie/custumer-success-ai/src/manager_ui.py)
- [index.py](/mnt/d/amelie/custumer-success-ai/index.py)
