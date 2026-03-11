# Cinnamon

Cinnamon è una web app basata su Django per la gestione di ricette, profili utente e community.

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

3. **Installa le dipendenze**

Con pip:
```bash
pip install -r requirements.txt
```

Oppure con pipenv:
```bash
pipenv install
```

4. **Applica le migrazioni**

```bash
python config/manage.py migrate
```

5. **Crea un superuser (opzionale, per accedere all'admin)**

```bash
python config/manage.py createsuperuser
```

6. **Avvia il server di sviluppo**

```bash
python config/manage.py runserver
```

## Utilizzo

- Accedi a `http://127.0.0.1:8000/` per usare l'applicazione.
- L'admin è disponibile su `http://127.0.0.1:8000/admin/`.
- Le immagini caricate sono salvate in `config/media/`.

## Struttura Principale del Progetto

- `config/` - Configurazione Django, database, media, apps
  - `users/` - Gestione utenti, profili, amicizie
  - `recipes/` - Gestione ricette
- `requirements.txt` / `Pipfile` - Dipendenze

## Test automatici

Il progetto include una suite di test automatici per verificare la correttezza di alcune parti fondamentali dell'applicazione, seguendo le direttive richieste:

- **Unit test su codice applicativo**: vengono testate in profondità le funzionalità dei modelli FriendRequest, Friendship e UserProfile. I test coprono:
  - Creazione e unicità delle richieste di amicizia
  - Accettazione/rifiuto richieste e creazione amicizie
  - Edge case (es. non si può essere amici di se stessi, unicità delle relazioni, richieste inverse)
  - Visualizzazione delle specialità utente
  - Consistenza e coerenza dei dati tra i modelli

- **Test di una vista utente tramite test client Django**: viene testata la view del profilo pubblico (`public_profile`), verificando:
  - Accesso a un profilo pubblico (risposta HTTP 200, presenza del nome utente nella pagina)
  - Accesso a un profilo privato da utente non autorizzato (redirect, messaggio di privacy)
  - Accesso a un profilo privato da parte di un amico autenticato (risposta HTTP 200, contenuto corretto)

Questi test sono implementati in `config/users/tests.py` e possono essere eseguiti con:

```bash
python config/manage.py test users
```

I test coprono sia input validi che non validi, edge case e garantiscono la consistenza architetturale delle funzionalità selezionate.



