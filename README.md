# Cinnamon

Cinnamon è una web app basata su Django per la gestione di ricette, profili utente, community tematiche e messaggistica privata.

## Librerie e Software Utilizzati

- **Python 3.10**
- **Django 5.2.7**: framework principale per lo sviluppo web.
- **django-crispy-forms 1.14.0**: per una migliore gestione e visualizzazione dei form.
- **Pillow**: per la gestione delle immagini (es. foto profilo, immagini ricette).

## Installazione

1. **Crea un ambiente virtuale (opzionale ma consigliato)**

```bash
python -m venv venv
source venv/bin/activate  # Su Windows: venv\Scripts\activate
```

2. **Installa le dipendenze**

Con pip:
```bash
pip install -r requirements.txt
```

Oppure con pipenv:
```bash
pipenv install
```

3. **Applica le migrazioni**

```bash
python config/manage.py migrate
```

4. **Crea un superuser (opzionale, per accedere all'admin)**

```bash
python config/manage.py createsuperuser
```

5. **Avvia il server di sviluppo**

```bash
python config/manage.py runserver
```

## Utilizzo

- Accedi a `http://127.0.0.1:8000/` per usare l'applicazione.
- L'admin è disponibile su `http://127.0.0.1:8000/admin/`.
- Le immagini caricate sono salvate in `config/media/`.

## Struttura Principale del Progetto

- `config/` - Configurazione Django, database, media, apps
  - `users/` - Gestione utenti, profili, amicizie, notifiche
  - `recipes/` - Gestione ricette, like/dislike, commenti
  - `community/` - Community tematiche, post, votazione, moderazione, inviti
  - `user_messages/` - Messaggistica privata tra utenti
- `requirements.txt` / `Pipfile` - Dipendenze

## Test automatici

Il progetto include una suite di test automatici suddivisi per app, per verificare la correttezza delle funzionalità principali:

- **App users** (`config/users/tests.py`): test esaustivi sui modelli FriendRequest, Friendship e UserProfile (creazione, unicità, accettazione/rifiuto, edge case) e test di integrazione sulla vista del profilo pubblico (accesso pubblico/privato, permessi amicizia, redirect).

- **App recipes** (`config/recipes/tests.py`): test sulla home page (visibilità ricette per utenti anonimi/autenticati/amici, statistiche utente) e sull'endpoint toggle_like (comportamento toggle, autenticazione, risposta JSON).

- **App community** (`config/community/tests.py`): test sulla vista CommunityDetailView (accesso a community pubbliche/private, permessi membro/moderatore) e test di join/leave (iscrizione, abbandono, idempotenza, blocco su community privata).

Per eseguire tutti i test:

```bash
python config/manage.py test users recipes community
```

Oppure per una singola app:

```bash
python config/manage.py test users
python config/manage.py test recipes
python config/manage.py test community
```

I test coprono sia input validi che non validi, edge case e garantiscono la consistenza architetturale delle funzionalità selezionate.
