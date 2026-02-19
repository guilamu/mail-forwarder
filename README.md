# 📬 Mail Forwarder — Messagerie Académique → Gmail

Script Python qui transfère automatiquement les mails non lus de votre **messagerie académique** (webmail Convergence / `ac-*.fr`) vers votre **boîte Gmail**, en conservant le corps, les pièces jointes et l'expéditeur d'origine dans le champ `Reply-To`.

Chaque mail transféré est préfixé par le tag **`[MAILPRO]`** dans le sujet pour faciliter le filtrage côté Gmail.

---

## ✅ Prérequis

- **Python 3.6+**
- Un **mot de passe d'application** pour la messagerie académique (voir ci-dessous)
- Un **mot de passe d'application Gmail** (voir ci-dessous)

## 🔑 Créer les mots de passe d'application

### Messagerie académique (Convergence)

1. Connectez-vous à votre messagerie académique : [https://messagerie.education.gouv.fr](https://messagerie.education.gouv.fr)
2. Allez dans **Préférences** → **Mots de passe sécurisés**
3. Cliquez sur le bouton **« Connexion »** pour créer un mot de passe d'application sécurisé
4. Suivez les étapes indiquées à l'écran
5. **Copiez le mot de passe généré** — il ne sera plus affiché ensuite

> [!NOTE]
> Ce mot de passe d'application est différent de votre mot de passe personnel. Il est lié à un équipement et peut être révoqué à tout moment sans modifier votre mot de passe principal.

### Gmail

1. Activez la **validation en deux étapes** sur votre compte Google : [https://myaccount.google.com/signinoptions/two-step-verification](https://myaccount.google.com/signinoptions/two-step-verification)
2. Rendez-vous sur la page **Mots de passe des applications** : [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Donnez un nom (ex : `Mail Forwarder`) et cliquez sur **Créer**
4. **Copiez le mot de passe de 16 caractères** généré

---

## ⚙️ Comment ça marche

1. Le script se connecte en **IMAP SSL** à `imap.education.gouv.fr` (port 993)
2. Il recherche tous les mails **sans** le flag `FORWARDED`
3. Pour chaque mail trouvé :
   - Il reconstruit un nouveau message avec le corps (texte + HTML) et les pièces jointes
   - Il ajoute le tag `[MAILPRO]` au sujet
   - Il place l'expéditeur original dans le champ `Reply-To`
   - Il envoie le mail via **SMTP Gmail** (port 587, STARTTLS)
   - Il marque le mail original comme `FORWARDED` sur le serveur IMAP
4. Les mails déjà transférés ne seront jamais retransférés

---

# 🚀 Déploiement

Deux options s'offrent à vous :

| | GitHub Actions | Serveur dédié |
|---|---|---|
| **Coût** | Gratuit | Coût du serveur |
| **Serveur requis** | Non | Oui (VPS, Raspberry Pi…) |
| **Fréquence** | Toutes les 5 min (avec délais possibles) | Toutes les X minutes (fiable) |
| **Maintenance** | Réactivation après 60 jours d'inactivité | Aucune |

---

## Option 1 — GitHub Actions (sans serveur)

Le script tourne directement sur GitHub, sans aucun serveur. Les identifiants sont stockés de manière sécurisée dans les **Secrets** du dépôt.

### 1.1 Créer le dépôt sur GitHub

1. Rendez-vous sur [github.com/new](https://github.com/new)
2. **Repository name** : `mail-forwarder`
3. **Description** : `Transfert automatique des mails de la messagerie académique vers Gmail`
4. Visibilité : **Public** (ou Private si vous préférez)
5. **Ne cochez aucune option** (pas de README, pas de .gitignore — tout est déjà prêt)
6. Cliquez sur **Create repository**

### 1.2 Pousser les fichiers

```bash
cd /chemin/vers/mail-forwarder
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/VOTRE_UTILISATEUR/mail-forwarder.git
git branch -M main
git push -u origin main
```

> [!CAUTION]
> Vérifiez que le fichier `.env` n'apparaît **PAS** dans `git status` avant de pousser. Le `.gitignore` l'exclut automatiquement.

### 1.3 Configurer les Secrets GitHub

1. Sur votre dépôt GitHub, allez dans **Settings** → **Secrets and variables** → **Actions**
2. Cliquez sur **New repository secret** et ajoutez ces 4 secrets :

| Nom du secret | Valeur |
|---|---|
| `IMAP_USER` | `prenom.nom@ac-academie.fr` |
| `IMAP_PASS` | Votre mot de passe d'application académique |
| `GMAIL_USER` | `votre-adresse@gmail.com` |
| `GMAIL_PASS` | Votre mot de passe d'application Gmail |

### 1.4 Première exécution

1. Sur votre dépôt, allez dans l'onglet **Actions**
2. Sélectionnez le workflow **Mail Forwarder**
3. Cliquez sur **Run workflow** → cochez **Initialiser les flags** → **Run workflow**
4. Cette première exécution marque tous les mails existants comme déjà transférés

Le workflow s'exécutera ensuite automatiquement **toutes les 5 minutes**.

> [!WARNING]
> GitHub **désactive** les workflows planifiés sur les dépôts **sans activité pendant 60 jours**. Un simple commit (ou une exécution manuelle) suffit à les réactiver.

---

## Option 2 — Serveur dédié

### 2.1 Installation

```bash
git clone https://github.com/VOTRE_UTILISATEUR/mail-forwarder.git
cd mail-forwarder

# Créer le fichier de configuration
cp .env.example .env
nano .env
```

Remplissez le fichier `.env` avec vos identifiants :

```env
IMAP_USER=prenom.nom@ac-academie.fr
IMAP_PASS=votre-mot-de-passe-application
GMAIL_USER=votre-adresse@gmail.com
GMAIL_PASS=votre-mot-de-passe-application-gmail
```

### 2.2 Première exécution

Marquez tous les mails existants pour éviter de transférer l'intégralité de votre boîte :

```bash
python3 forwarder.py --init
```

### 2.3 Automatisation avec cron

```bash
crontab -e
```

Ajoutez la ligne suivante pour vérifier toutes les 5 minutes :

```cron
*/5 * * * * cd /chemin/vers/mail-forwarder && python3 forwarder.py >> /var/log/mail-forwarder.log 2>&1
```

> [!TIP]
> Adaptez `/chemin/vers/mail-forwarder` au chemin réel d'installation sur votre serveur.

---

## 🗂️ Structure du projet

```
mail-forwarder/
├── .github/
│   └── workflows/
│       └── forward.yml     # GitHub Actions (option 1)
├── forwarder.py            # Script principal
├── .env                    # Vos identifiants (non versionné)
├── .env.example            # Template de configuration
├── .gitignore              # Fichiers exclus de Git
├── requirements.txt        # Dépendances (aucune)
├── LICENSE                 # Licence MIT
└── README.md               # Ce fichier
```
