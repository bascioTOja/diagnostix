# Diagnostix

System stacji kontroli pojazdów – aplikacja webowa do obsługi klientów, pojazdów, rezerwacji terminów badań technicznych oraz zapisu wyników przeglądów.

## Najważniejsze funkcje
- Rejestracja i logowanie użytkowników (email jako login)
- Role: **administrator**, **diagnosta**, **klient**
- Pojazdy klienta + historia badań
- Rezerwacje wizyt na badania techniczne
- Diagnosta: harmonogram + zapis wyniku badania
- Administrator: podgląd statystyk
- Dwa interfejsy: widoki HTML + REST API (DRF)

## Moduły
`users`, `vehicles`, `appointments`, `inspections`, `notifications`, `analytics`, `core`.

## Wymagania
- Python **3.13+**
- (zalecane) **uv** albo pip do zarządzania zależnościami

## Szybki start (Windows / CMD)

### Opcja A: instalacja i uruchomienie przez `uv` (zalecane)

**Instalacja zależności**

```cmd
cd diagnostix
uv sync
```

**Konfiguracja `.env`**

```cmd
copy .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Wygenerowaną wartość wklej do `.env` jako `DJANGO_SECRET_KEY`.

**Migracje**

```cmd
uv run python manage.py migrate
```

**(Opcjonalnie) dane demo**

```cmd
uv run python manage.py loaddata core/fixtures/demo_video_seed.json
```

Konta testowe po załadowaniu fixture: `core/fixtures/readme.md`.

**Start serwera**

```cmd
uv run python manage.py runserver
```

Domyślnie: `http://127.0.0.1:8000/`.

### Opcja B: instalacja i uruchomienie przez `pip` (venv)

**(Zalecane) wirtualne środowisko + zależności**

```cmd
cd diagnostix
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
```

**Konfiguracja `.env`**

```cmd
copy .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

**Migracje**

```cmd
python manage.py migrate
```

**(Opcjonalnie) dane demo**

```cmd
python manage.py loaddata core/fixtures/demo_video_seed.json
```

**Start serwera**

```cmd
python manage.py runserver
```

## API
Endpointy są dostępne pod `/api/...` oraz alternatywnie `/api/v1/...`.

## Celery (opcjonalnie)
W dev działa domyślnie na `memory://` (bez Redisa). Jeśli chcesz uruchomić z brokerem (np. Redis), ustaw w `.env` `CELERY_BROKER_URL` i `CELERY_RESULT_BACKEND`, a następnie:

### Uruchomienie przez `uv`

```cmd
uv run celery -A diagnostix worker -l info
uv run celery -A diagnostix beat -l info
```

### Uruchomienie przez `pip` (w aktywnym venv)

```cmd
celery -A diagnostix worker -l info
celery -A diagnostix beat -l info
```

## Testy

### Testy przez `uv`

```cmd
uv run python manage.py test
```

### Testy przez `pip` (w aktywnym venv)

```cmd
python manage.py test
```
