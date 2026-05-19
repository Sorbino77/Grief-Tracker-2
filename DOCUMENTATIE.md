# ShipTrack — handleiding

Goed. Voor we beginnen: dit is geen marketing-pamflet, geen feature-tour
voor managers, geen LinkedIn-post. Dit is de documentatie voor wie dit ding
moet draaien, gebruiken, deployen, en aanvallen wanneer hij stuk is. Lees ze
in de volgorde die ge wilt — er zit een inhoudsopgave bovenaan en de
hoofdstukken staan los van elkaar.

Bondig waar het kan, lang waar het moet.

Inhoud:

1. [Wat is dit eigenlijk](#1-wat-is-dit-eigenlijk)
2. [Snelstart (echt 30 seconden)](#2-snelstart-echt-30-seconden)
3. [Installatie van nul](#3-installatie-van-nul)
4. [Hoe ziet het project er uit](#4-hoe-ziet-het-project-er-uit)
5. [De UI uitgelegd](#5-de-ui-uitgelegd)
6. [Importeren van Excel/CSV](#6-importeren-van-excelcsv)
7. [REST API](#7-rest-api)
8. [Gebruikers en rollen](#8-gebruikers-en-rollen)
9. [Beveiliging — OWASP-stijl](#9-beveiliging--owasp-stijl)
10. [Tests en linters](#10-tests-en-linters)
11. [Deployen](#11-deployen)
12. [GitHub: CI/CD](#12-github-cicd)
13. [Lokale Postgres in 5 stappen](#13-lokale-postgres-in-5-stappen)
14. [Troubleshooting (lees dit eerst voor ge een issue opent)](#14-troubleshooting)
15. [FAQ](#15-faq)

---

## 1. Wat is dit eigenlijk

ShipTrack is een Django-app om **shipment incidents** bij te houden. Schade,
ontbrekende labels, verkeerd gerouteerde leveringen, alles wat fout kan
gaan tussen vertrek en aankomst. Origineel was dat een Excel ("Grief
003.xlsm") met één tab vol rijen en een tab met draaitabellen voor analyse.

Excel werkt prima zolang er één persoon mee werkt. Eens er drie mensen
tegelijk in willen werken is het einde verhaal: bestanden die elkaar
overschrijven, formules die ineens stuk zijn, kolommen die iemand
"per ongeluk" verplaatst heeft. Vandaar deze app.

Wat ze doet:

- **Incidents bijhouden**: primary ref, ship ID, transport order ref,
  leverancier, land, locatie, carrier, type issue, datum, status, schuld,
  notitie. Plus audit-velden (wie maakte wat, wanneer).
- **Importeren** uit `.xlsx`, `.xlsm`, `.csv`. Herkent de oude K+N-kolommen
  (`K&N REF`, `KN REF`, `Kuehne ref`) **én** de nieuwe neutrale namen.
  De bestaande Excel-bestanden moeten dus niet aangepast worden, ze gaan er
  zo in.
- **Filteren en zoeken** op alle velden die je verwacht.
- **Analytics** met interactieve draaitabellen (rij × kolom + heatmap-shading
  + grand total).
- **REST API** voor wie scripts wil schrijven of een ander frontend wil
  bouwen.
- **Multi-user** met rollen: Admin, Editor, Viewer.
- **OWASP-hardened**. Niet om mee te pochen op een congres — gewoon omdat
  een tracker zonder fatsoenlijke beveiliging in een multi-user context een
  open beerput is.

Wat ze **niet** is: blockchain, AI-tussenlaag, "intelligent platform". Het is
een formulier-gedreven app met een database eronder. Punt.

---

## 2. Snelstart (echt 30 seconden)

Alles al geïnstalleerd? (uv aanwezig, Postgres draait, `.env` ingevuld?)

**Windows**: dubbelklik **`start.bat`** in de project-root. Ge moet niks
typen. De browser opent zelf op http://127.0.0.1:8000 zodra de server
antwoordt op `/healthz/`.

**Mac/Linux**:

```bash
make up
```

Doet exact hetzelfde via `scripts/launch.sh`.

Inloggen met `admin` / `Ac6smuaf1991.` (of wat ge in `.env` zet als
`DJANGO_SUPERUSER_PASSWORD`).

> Werkt het niet? Geen paniek, het is altijd één van drie dingen: Postgres
> draait niet, het wachtwoord is verkeerd, of `.env` staat fout. Spring naar
> [§14](#14-troubleshooting).

---

## 3. Installatie van nul

### 3.1 Wat ge nodig hebt

| Wat | Versie | Waarom |
|---|---|---|
| **uv** | ≥ 0.8 | Python package manager. Snel, deterministisch, geen pip-tools-shenanigans |
| **Python** | 3.11 of 3.12 | uv haalt die zelf binnen als ze niet aanwezig is |
| **PostgreSQL** | 16 of 17 | Productie-DB. Voor tests gebruiken we SQLite |
| **Git** | recent | Voor pushen naar GitHub |
| **Docker** | optioneel | Alleen als ge via `docker compose` wil draaien |

Geen Node, geen npm, geen webpack, geen Vite, geen 47 frontend tools. Bewuste
keuze. (Frontend is server-rendered HTML met Bootstrap. Daarover later
meer.)

### 3.2 uv installeren

Windows in PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Mac/Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Terminal herstarten zodat `uv` op uw `PATH` staat. Test met
`uv --version`. Indien dat een errorke geeft staat ze niet op de PATH —
fix dat eerst.

### 3.3 Project klonen en deps binnenhalen

```bash
git clone <repo-url>
cd "Grief Tracker 2"
uv sync
```

`uv sync` leest `pyproject.toml` + `uv.lock`, maakt `.venv/` aan, installeert
**bit-perfect** dezelfde versies als wat de CI heeft. Het beruchte "het werkt
op mijn machine" is hiermee opgelost. (Niet helemaal: er zijn nog Python-
en OS-specifieke binaries, maar voor 99% van de gevallen is dit genoeg.)

### 3.4 `.env` aanmaken

```bash
cp .env.example .env
```

Open `.env` en pas aan:

- **`DJANGO_SECRET_KEY`** — niet die placeholder van het voorbeeld, ge maakt
  een echte:
  ```bash
  uv run python -c "import secrets; print(secrets.token_urlsafe(64))"
  ```
- **`POSTGRES_PASSWORD`** — uw eigen sterk wachtwoord
- **`DJANGO_SUPERUSER_*`** — username, email, password voor de eerste admin

De Postgres-credentials vullen we in zodra de database draait. Zie
[§13](#13-lokale-postgres-in-5-stappen).

### 3.5 Database aanmaken en migreren

Postgres draait? (Of `USE_POSTGRES=False` voor SQLite-modus?)

```bash
uv run python manage.py migrate
uv run python manage.py seed_demo
```

`migrate` zet de tabellen op. `seed_demo` maakt de drie standaard groepen
(Admin/Editor/Viewer) aan en — als de `DJANGO_SUPERUSER_*` env vars gezet
zijn — meteen ook de eerste superuser. Wachtwoord wordt netjes Argon2-hashed,
nooit als plaintext op disk.

### 3.6 Server starten

```bash
uv run python manage.py runserver
```

Of dubbelklik `start.bat`. Open http://127.0.0.1:8000 en ge zit binnen.

---

## 4. Hoe ziet het project er uit

Een tree die op één scherm past:

```
.
├── shiptrack/              ← Django project (settings, top-level URLs, niet zelf een app met modellen)
│   ├── settings.py         ← Alle config. Hier zit de OWASP-hardening
│   ├── urls.py             ← /healthz/, /admin/, /accounts/, /incidents/, /api/
│   ├── wsgi.py / asgi.py
│   └── formhelpers.py      ← BootstrapFormMixin (auto form-control op widgets)
│
├── accounts/               ← Custom User + RBAC
│   ├── models.py           ← User met `role` veld
│   ├── permissions.py      ← @role_required + DRF permissions
│   ├── views.py            ← profile, user_list, user_create, change_role
│   ├── forms.py            ← UserCreateForm met password-validators
│   ├── admin.py            ← CustomUserAdmin (blokkeert self-demote)
│   └── signals.py          ← Post-migrate hook: groups aanmaken
│
├── incidents/              ← De hoofd-app
│   ├── models.py           ← Incident, Carrier, IssueType, Location
│   ├── views.py            ← list/detail/create/edit/delete/resolve/import/analytics
│   ├── forms.py            ← IncidentForm, ImportUploadForm
│   ├── filters.py          ← django-filter set
│   ├── importers.py        ← Spreadsheet parser. Idempotent. Forgiving op headers
│   ├── pivot.py            ← Draaitabel-bouwer
│   ├── api.py / api_urls.py← DRF viewsets
│   ├── serializers.py
│   └── management/commands/
│       ├── import_incidents.py
│       └── seed_demo.py
│
├── templates/              ← Server-rendered HTML (Bootstrap 5.3)
│   ├── base.html           ← Navbar + theme toggle + alerts + footer
│   ├── accounts/
│   └── incidents/
│
├── static/
│   ├── css/styles.css      ← Eigen design op Bootstrap. Heatmap, status pills
│   ├── js/theme.js         ← Light/dark/auto toggle (CSP-veilig)
│   └── vendor/bootstrap/   ← Bootstrap 5.3.3 lokaal (geen CDN, want CSP)
│
├── tests/                  ← pytest suite (56+ tests)
│
├── scripts/
│   ├── launch.ps1 / launch.sh         ← Easy launcher
│   └── reset_pg_and_provision.ps1     ← Postgres password reset (admin only)
│
├── .github/                ← CI/CD workflows + Dependabot config
├── Dockerfile              ← Multi-stage build met uv
├── docker-compose.yml      ← Web + Postgres + Redis + nginx
├── render.yaml             ← Render.com one-click
├── fly.toml                ← Fly.io blueprint
├── start.bat               ← Windows double-click launcher
├── Makefile                ← `make help` voor alle taken
├── pyproject.toml          ← Deps + ruff + mypy + bandit + pytest config
└── uv.lock                 ← Bevroren versies
```

**Drie Django apps**:

- `shiptrack` is het project (settings + top-level URLs, geen eigen modellen).
- `accounts` doet users + rollen + permission helpers.
- `incidents` is waar de business value zit.

Templates en static bestanden staan op project-niveau, niet per-app, omdat
ze cross-app dingen tonen (de navbar staat in `templates/base.html` en die
wordt door beide apps gebruikt — dus heeft het geen zin om ze per-app te
splitsen).

---

## 5. De UI uitgelegd

### 5.1 Inloggen

Ga naar `/`. Niet ingelogd? Ge wordt naar `/accounts/login/` gestuurd. Username
+ wachtwoord. Klaar.

Vergeten wachtwoord werkt via allauth (`/accounts/password/reset/`), maar
**alleen als ge SMTP geconfigureerd hebt**. Voor lokale dev werkt dat niet
out-of-the-box — gewoon een nieuw wachtwoord zetten via:

```bash
uv run python manage.py changepassword <user>
```

### 5.2 De Incidents-lijst (`/incidents/`)

Wat ge ziet:

- **Filterbalk** bovenaan: search-veld, status, causing party, carrier,
  issue type, datum-range. Submit met **Apply**, reset met **Reset**.
- **Tabel** met paginatie (50 per pagina).
- **Per rij**: primary ref (klikbaar), ship ID, supplier, carrier, issue
  type, datum, status (gekleurd pill: amber = ongoing, groen = resolved).
- **Acties**: View / Edit (Edit alleen voor editor of admin).
- **Pager** onderaan: ‹ Previous / Next ›.

Filters worden in de URL bewaard (`?status=ONGOING&carrier=12`). Bookmarken
mag, doorsturen mag — gewoon URL kopiëren en plakken.

### 5.3 Een incident bekijken (`/incidents/<pk>/`)

Alle velden netjes in een card. Onderaan de actie-knoppen, afhankelijk van
uw rol:

- **Editor of admin**: **Edit** + **Mark resolved** (verschijnt enkel als de
  status nog ongoing is — anders nutteloos).
- **Admin**: **Delete** met JS-confirm. Eens weg is het echt weg, dus geen
  per-ongeluk-clicks.
- **Viewer**: ge moogt kijken en that's it.

### 5.4 Een nieuw incident toevoegen

Klik **+ New incident** rechtsboven op de lijst (niet zichtbaar voor
viewers). Vul in. Validatie pakt op:

- **Primary reference**: alleen letters, cijfers, spaties, `_`, `-`, `.`, `/`.
  Dus geen `<script>`-grappen — die regex blokkeert dat.
- **Country**: ISO-2 code (BE, NL, GB...). Kleine letters worden naar caps
  gepushed.
- **Issue date**: niet in de toekomst.
- **Resolve date**: niet vóór issue date.

Bij invalid form blijft ge op de pagina, met rode foutmeldingen onder de
betreffende velden.

### 5.5 Analytics (`/incidents/analytics/`)

Hier zit het zware werk.

#### Pivot table (draaitabel)

Bovenaan kiest ge **rows** en **columns** uit een dropdown — de draaitabel
herrekent en toont een 2D grid met telling per kruising. Plus rij-totalen,
kolom-totalen, en grand total rechtsonder.

Beschikbare dimensies: Carrier, Issue type, Causing party, Status, Country,
Location, Year, Month. Voor de kolom-as is er extra `(none)` — dan krijgt ge
een 1D-tabel.

Slim:

- **Heatmap-shading**: cellen met meer incidents kleuren intenser indigo.
  De cel met het hoogste aantal krijgt een ringetje rond zich (de "hotspot").
- **Sticky eerste kolom**: bij brede pivots (carrier × maand bv.) blijft de
  carrier-naam zichtbaar als ge horizontaal scrollt.
- **Filters tellen mee**: alle filters bovenaan worden toegepast vóór de
  pivot.
- **Werkt in dark mode**: kleurschaal past zich aan, anders zou de heatmap
  onleesbaar zijn op donkere achtergrond.
- **(unknown)-bucket**: incidents zonder carrier of met leeg veld vallen
  niet stilletjes weg, ze komen in een eigen rij `(unknown)`. Goed om te
  zien hoeveel "rommel" er nog in de data zit.

#### At-a-glance breakdowns

Onder de pivot vijf simpele "by X" tabellen (per carrier, per issue type,
per causing party, per status, per jaar). Geen instellingen, gewoon
read-only overzichten. Voor wie geen zin heeft om met dimensies te spelen.

### 5.6 Import (`/incidents/import/`)

Editor of admin upload een spreadsheet, klaar. Volledige uitleg in
[§6](#6-importeren-van-excelcsv).

### 5.7 Users (`/u/users/`)

Alleen admins zien deze pagina. Lijst met alle users + rol-aanpasser per rij.
Plus een **+ New user** knop om iemand uit te nodigen zonder via Django
admin te moeten.

Belangrijk: **ge kunt uw eigen rol niet veranderen** als admin. Ook niet als
ge "even per ongeluk" op viewer klikt. Ook niet via een tampered request
in DevTools. Drie verdedigingslagen, zie [§9.4](#94-self-demote-bescherming).

### 5.8 Profile (`/u/profile/`)

Eigen account. Wachtwoord wijzigen via "Change password" — gaat via
allauth's flow met dezelfde validators als bij user creation (12 char min,
common-password blocklist, niet te similar aan username).

### 5.9 Theme toggle

Rechtsboven in de navbar. Drie opties:

- **☀ Light**
- **🌙 Dark**
- **◐ Auto** (volgt uw OS)

Keuze wordt onthouden via `localStorage` (per browser, per profiel). Werkt
zonder pagina-refresh: Auto luistert mee naar `prefers-color-scheme:
change` en flipt mee als ge midden in de sessie uw OS van licht naar donker
zet.

---

## 6. Importeren van Excel/CSV

### 6.1 Via de UI

`/incidents/import/`. Bestand kiezen, eventueel sheet name + header row
aanpassen, vinkje **dry-run** aanzetten als ge eerst wilt zien of het zonder
fouten gaat. Click Import.

Onderaan komt een rapport: hoeveel created, updated, skipped, errors. Plus
de eerste 50 errors met rij-nummer + bericht.

### 6.2 Via de CLI

```bash
uv run python manage.py import_incidents \
    "Grief 003.xlsm" --sheet=Grief --header-row=10
```

Zonder `--sheet` defaultet hij naar `Incidents`. Zonder `--header-row`
naar `1`. Voor het oude K+N-bestand is `--sheet=Grief --header-row=10`
correct (er staan 9 dashboard-rijen boven de echte header-rij).

`--dry-run` doet alles in een transaction die op het einde wordt
teruggedraaid. Handig om eerst te valideren zonder de DB te raken.

### 6.3 Welke kolomnamen worden herkend

De importer is **bewust forgiving**. Zowel modern als legacy:

| Veld in DB | Headers (case-insensitive) |
|---|---|
| `primary_ref` | `Primary Ref`, `Primary Reference`, `REF`, `REF1`, `REF2`, `REF3`, **`K&N REF`**, **`KN REF`**, **`Kuehne ref`** |
| `ship_id` | `Ship ID`, `ShipID`, `Shipment ID` |
| `transport_order_ref` | `TO Ref`, `Transport order ref`, `Transport order reference` |
| `supplier_name` | `Supplier Name`, `Supplier` |
| `country` | `Ctry`, `Country` |
| `location` | `Loc`, `Location` |
| `carrier` | `Carrier` |
| `issue_type` | `Issue type`, `IssueType` |
| `issue_date` | `Date`, `Issue date` |
| `image_available` | `Image` |
| `causing_party` | `Causing party` |
| `resolve_date` | `Resolve Date`, `ResolveDate` |
| `status` | `Status` |
| `note` | `Note`, `Notes`, `Comment` |

Het oude K+N-bestand werkt dus zonder enige aanpassing. Niet uit
sentimentaliteit — gewoon omdat het herschrijven van Excel-bestanden door
gebruikers oneindig saai is en bovendien een hoop typo's introduceert.

### 6.4 Hoe deduplicatie werkt

Op DB-niveau zit er een uniqueness constraint op `(primary_ref, issue_type)`.
Twee rijen met diezelfde combinatie = update, geen duplicate. Re-importeren
van hetzelfde bestand voegt dus niks toe; alleen veld-veranderingen worden
doorgevoerd.

In de praktijk: bij de 2932-rij workbook geeft een tweede import
`created=0, updated=2926`. De 6 "ontbrekende" zijn duplicaten in de
**bron-Excel zelf** (zelfde primary_ref + issue_type tweemaal ingevoerd —
een gebruiker die gewoon een Ctrl+D heeft gedaan in plaats van een echte
nieuwe rij).

### 6.5 Wat als een rij faalt

Per-row errors worden gerapporteerd, niet de hele import. Eén corrupte rij
blokkeert dus geen 2900 andere. Voorbeelden:

- **Onleesbare datum**: alle gangbare formaten worden geprobeerd
  (`%Y-%m-%d`, `%d/%m/%Y`, `%m/%d/%Y`, `%d-%m-%Y`, `%Y/%m/%d`), maar als
  iemand "29-feb-2023" typt is dat sowieso geen geldige datum.
- **Lege primary_ref**: wordt skipped (niet als error gerapporteerd).
- **Sub-veld validatie**: bv. country langer dan 2 tekens — wordt
  afgekapt op 2 chars in plaats van te falen.

### 6.6 Limieten

- Max **25 MB** upload (gehard in zowel form als settings)
- Max **200.000 rijen** per import (zip-bomb defense — hoewel openpyxl met
  `data_only=True` toch al geen formules executeert)
- Rate limit: **10 imports/minuut** per user (django-ratelimit)
- Alleen `.xlsx`, `.xlsm`, `.csv` toegestaan (extensie-check + size-check
  vóór de file de DB raakt)

---

## 7. REST API

Voor wie de UI moet bypassen, of een ander frontend wil bouwen.

### 7.1 Endpoints

```
GET    /api/v1/incidents/                  → lijst (gepagineerd, 50/pagina)
POST   /api/v1/incidents/                  → nieuw
GET    /api/v1/incidents/<pk>/             → detail
PATCH  /api/v1/incidents/<pk>/             → partial update
PUT    /api/v1/incidents/<pk>/             → full update
DELETE /api/v1/incidents/<pk>/             → verwijderen

GET    /api/v1/carriers/                   → carriers
GET    /api/v1/issue-types/                → issue types
GET    /api/v1/locations/                  → locations
```

Plus dezelfde write-endpoints op carriers / issue-types / locations.

### 7.2 Authenticatie

Twee opties:

**Session auth** (handig in browser): log in via `/accounts/login/`, gebruik
dezelfde sessiecookie. De browsable API op `/api/v1/auth/login/` is ook
beschikbaar voor wie de DRF-UI wil.

**Token auth** (handig voor scripts):

```bash
DJANGO_SETTINGS_MODULE=shiptrack.settings uv run python -c "
import django; django.setup()
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
u = get_user_model().objects.get(username='admin')
tok, _ = Token.objects.get_or_create(user=u)
print(tok.key)
"
```

Stuur die mee:

```bash
curl -H "Authorization: Token 74f8035e..." http://127.0.0.1:8000/api/v1/incidents/
```

### 7.3 Filters, search, ordering

```
?status=ONGOING
?carrier=12
?issue_type=5
?issue_date_from=2025-01-01&issue_date_to=2025-06-30
?search=damage           ← zoekt in primary_ref, ship_id, supplier, note
?ordering=-issue_date    ← sorteren (- = desc)
?page=2                  ← paginatie
```

Alle filter-parameters van de HTML-lijst werken ook op de API. Kwestie van
één en dezelfde `IncidentFilter`-class voor beide.

### 7.4 Throttling

- Authenticated user: **1000 requests/uur**
- Anonymous: **60/uur** (en ge krijgt sowieso 403 op alles behalve
  `/healthz/`, dus die 60 zal ge nooit halen)

### 7.5 Voorbeeld: een incident POSTen

```bash
curl -X POST http://127.0.0.1:8000/api/v1/incidents/ \
  -H "Authorization: Token 74f8035e..." \
  -H "Content-Type: application/json" \
  -d '{
    "primary_ref": "TEST-001",
    "issue_date": "2025-06-15",
    "status": "ONGOING",
    "image_available": "NA",
    "causing_party": "SUPPLIER",
    "carrier": 19,
    "issue_type": 21,
    "supplier_name": "Acme Corp"
  }'
```

Antwoord:

- `201` + JSON met de aangemaakte resource bij succes
- `403` als ge viewer zijt (dus mag enkel GET'en)
- `400` als de payload faalt op validatie (response zegt welke velden)

---

## 8. Gebruikers en rollen

### 8.1 Drie rollen, geen meer

| Rol | Mag... |
|---|---|
| **Viewer** | Lijst zien, detail zien, analytics zien, API GET'en |
| **Editor** | Bovenstaande + nieuw aanmaken, bewerken, importeren, mark resolved |
| **Admin** | Bovenstaande + verwijderen, gebruikers aanmaken, rollen veranderen, Django admin |

Geen "super-editor", geen "junior-admin", geen "external-viewer". Drie
niveaus, gedaan. Als ge meer fijnmazigheid nodig hebt (specifieke locations
afschermen bv.), dan moet ge dat in een aparte permission-laag bouwen — en
dat is een gesprek over scope, niet iets wat ge tussendoor doet.

### 8.2 Een gebruiker aanmaken

Twee manieren:

**In de app**: log in als admin → Users → **+ New user** → vul in. Wachtwoord
moet door de validators (zie [§9.2](#92-wachtwoord-policy)).

**Via CLI** (handig voor de eerste admin op een nieuwe install):

```bash
uv run python manage.py createsuperuser
```

### 8.3 Rol veranderen

Op `/u/users/` als admin: dropdown per user → andere rol kiezen → Save.
Klaar. Niet-admins zien deze pagina niet eens — `@role_required(Role.ADMIN)`
op de view. Ze krijgen een 403 als ze de URL toch typen.

### 8.4 `is_staff` versus `is_superuser`

Aparte vlaggen op het Django User model — niet vergissen:

- **`is_staff`**: mag in Django admin (`/admin/`). Onze `UserCreateForm`
  zet die op True voor nieuwe Admins, False voor Editors/Viewers.
- **`is_superuser`**: mag alles, omzeilt **alle** permission checks. Alleen
  via `createsuperuser` of via de `seed_demo` env vars. **De in-app form zet
  die nooit op True**. Bewust. Superuser is voor bootstrap en disaster
  recovery, niet voor dagelijks gebruik.

Dus: als ge "Admin via de UI" klikt, krijgt die persoon `is_staff=True` maar
**niet** `is_superuser=True`. Dat is goed — superuser is een gevaarlijk
recht en moet alleen aan een handvol mensen toegekend worden, niet automatisch
aan iedereen die admin is.

---

## 9. Beveiliging — OWASP-stijl

Niet omdat security-talk cool staat in een README, maar omdat een tracker
zonder fatsoenlijke beveiliging in een multi-user setting gewoon een open
doos is. Wij dekken alle Top-10-categorieën van 2021 af.

### 9.1 OWASP Top-10 cheat sheet

| Risk | Waar het zit |
|---|---|
| **A01 Broken Access Control** | `@role_required` op elke HTML-view, `IsEditor`/`IsAdmin` op DRF, login-required overal behalve `/healthz/` |
| **A02 Cryptographic Failures** | Argon2 hashing, HSTS, secure+httponly cookies, secrets via env (nooit gecommit) |
| **A03 Injection** | Pure Django ORM (geen raw SQL), parameterized search via `__icontains`, autoescape in templates |
| **A04 Insecure Design** | Deny-by-default permissions, atomic importer met dry-run, file-size + content-type guards |
| **A05 Security Misconfiguration** | DEBUG=False default, geen secret-key default in productie, CSP, Permissions-Policy, X-Frame-Options DENY, non-root container, internal-only DB network |
| **A06 Vulnerable Components** | Pinned deps in `pyproject.toml` + `uv.lock`, weekly Dependabot PRs |
| **A07 Identification & Auth** | django-axes lockout, 12-char password validator, allauth rate limits |
| **A08 Data Integrity Failures** | CSRF middleware, signed sessions, idempotent importer (uniqueness constraint) |
| **A09 Logging & Monitoring** | Structured stdout logging, axes logt lockouts |
| **A10 SSRF** | Geen user-supplied outbound URLs |

### 9.2 Wachtwoord-policy

In `settings.py`:

```python
AUTH_PASSWORD_VALIDATORS = [
    UserAttributeSimilarityValidator,
    MinimumLengthValidator (min_length=12),
    CommonPasswordValidator,
    NumericPasswordValidator,
]
```

Dus:

- **Minimum 12 tekens**. (`12345678` was lang genoeg in 2010, niet meer
  in 2026.)
- **Niet enkel cijfers**.
- **Niet in de Django common-password blocklist** (~20.000 stuks: `password`,
  `qwerty123`, en hun ergere familie).
- **Niet te similar aan uw username/email**. Iemand met username `kjanssens`
  die als wachtwoord `Kjanssens2025!` neemt: niet voorbij de validator.

Hashing: **Argon2** (winnaar van de Password Hashing Competition). PBKDF2 +
BCrypt + PBKDF2-SHA1 staan ook in de hashers-lijst voor backwards compat
(als ge vanuit een ander Django-project oude users importeert, blijven die
eerst werken en worden ze bij eerste login geüpgrade naar Argon2).

### 9.3 Brute-force lockout

`django-axes` zit in de auth-backend. Default: na **5 mislukte pogingen**
binnen **1 uur** wordt het IP+username 1 uur geblokkeerd. Aanpasbaar via
`AXES_FAILURE_LIMIT` en `AXES_COOLOFF_TIME` in `.env`.

`AXES_RESET_ON_SUCCESS = True`: na een geslaagde login wordt de counter
gewist. Dus als ge gewoon uw wachtwoord ff vergeten zijt en het op de derde
poging hebt, zit ge niet meteen vast.

### 9.4 Self-demote bescherming

Een admin **kan zichzelf niet downgraden** tot editor of viewer. Drie lagen
verdediging — defense in depth, zoals dat heet:

1. **In de view** (`change_role`): als `request.user.pk == target.pk` en
   `new_role != ADMIN`, return 302 met een nette error message. DB wordt
   niet aangeraakt.
2. **In de Django admin** (`CustomUserAdmin`): het `role` veld wordt
   readonly gerenderd wanneer een admin zichzelf bewerkt. En als laatste
   vangnet: `save_model` rolt elke poging tot self-demotion terug, ook als
   iemand het readonly-attribuut via DevTools heeft uitgezet.
3. **In de UI** (`user_list.html`): voor uw eigen rij wordt de dropdown
   helemaal niet getoond — er staat "— locked —" in plaats van. Probleem
   is onzichtbaar voor de gebruiker.

Waarom drie lagen? Omdat één laag wegvallen (een DevTools-truc, een bug in
een refactor, etc.) niet meteen uw hele organisatie zonder admin moet laten
zitten. En omdat een gecompromitteerde admin-sessie een prachtig vehikel is
om zichzelf naar viewer te zetten en de échte admin te verwijderen — niet
gaan gebeuren.

### 9.5 CSRF, CSP, HSTS, en de rest van de afkortingen

- **CSRF**: standaard Django middleware. Elke state-changing request heeft
  een token nodig. Test `test_admin_csrf_required` bewijst dat zelfs een
  admin een 403 krijgt als hij geen token meestuurt.
- **CSP**: `default-src 'self'` met enkele uitzonderingen:
  `'unsafe-inline'` in style-src wegens Bootstrap utility classes (geen
  manier om dat zonder runtime-overhead op te lossen), nonces in script-src
  voor inline scripts. Bootstrap zelf wordt **lokaal** geserveerd uit
  `static/vendor/bootstrap/` — niet via CDN, want dat zou de CSP juist
  weer breken.
- **HSTS**: aan in productie (`DJANGO_SECURE_HSTS_SECONDS=31536000`,
  includeSubDomains, preload). Uit in dev (anders gaat uw browser blijven
  redirecten naar HTTPS op localhost).
- **Cookies**: `SESSION_COOKIE_HTTPONLY=True` (geen JS-toegang),
  `SESSION_COOKIE_SAMESITE=Lax` (geen cross-site sneaking),
  `SESSION_COOKIE_SECURE=True` in prod.
- **X-Frame-Options**: `DENY`. Geen iframe-embedding. Anti-clickjacking.
- **Referrer-Policy**: `same-origin`. Geen URL-parameters lekken naar
  externe sites.
- **Permissions-Policy**: alle gevoelige browser-API's (camera, microfoon,
  geolocation, USB, etc.) uitgeschakeld.

### 9.6 Wat we niet hebben (en waarom dat oké is)

- **Geen 2FA**. Zou kunnen toegevoegd worden via `django-otp` of
  `django-allauth`'s 2FA-extensie, maar voor de huidige scope (intern
  tracking-tooltje) is een sterk wachtwoord + axes lockout afdoende. Als ge
  dit aan het publieke internet gaat hangen voor 100+ users: dan wel 2FA.
- **Geen audit-log van leeszoekopdrachten**. Wie heeft wat ingekeken? Niet
  bijgehouden. Wie heeft wat gewijzigd: wel, via `created_by`/`updated_by`
  + timestamps.
- **Geen field-level permissions**. Alle editors zien alle velden. Als ge
  bv. wilt dat editors van locatie A geen incidents van locatie B mogen
  zien, moet ge een aparte permission-laag bouwen.

---

## 10. Tests en linters

```bash
make test
# of:
uv run pytest -q
```

Tests draaien tegen een **SQLite in-memory** database, dus geen Postgres
nodig. Pytest detecteert zichzelf, zet testing-mode aan, schakelt naar
SQLite, en gebruikt simple static files storage (geen manifest-hash gedoe).

### 10.1 Wat is er getest

56 tests, gegroepeerd:

- **`test_models.py`**: model-gedrag (`mark_resolved`, uniqueness, role
  helpers).
- **`test_views.py`**: RBAC op alle HTML-views, validatie, healthz, filter
  by status.
- **`test_api.py`**: DRF endpoints met auth, viewer-only, editor-can-post.
- **`test_importer.py`**: xlsx + csv import, idempotency, dry-run, bad
  dates, **legacy K+N headers**.
- **`test_security.py`**: security headers aanwezig, CSRF required, password
  validators, axes config, **self-demote bescherming op alle drie lagen**.
- **`test_user_create.py`**: admin-only flow, password hashing, duplicate
  prevention, weak password rejection.
- **`test_pivot.py`**: pivot helper math, view rendering, invalid input
  handling.

### 10.2 Coverage

```bash
uv run pytest --cov --cov-report=html
```

Open `htmlcov/index.html`. Mikken op > 85% op de business-logica
(views, importers, pivot).

### 10.3 Linters — vier verschillende

```bash
make lint
# draait achter elkaar:
uv run ruff check .          ← style + bugbear + security + django + simplify
uv run ruff format --check . ← formatter
uv run bandit -r accounts incidents shiptrack -c pyproject.toml
uv run mypy accounts incidents shiptrack manage.py
```

**Allemaal moeten clean zijn**. CI faalt als één van de vier rood staat. Voor
auto-fix:

```bash
make format    # ruff format + ruff check --fix
```

---

## 11. Deployen

Vier opties, kies wat past:

### 11.1 docker-compose (op uw eigen server)

```bash
git clone <repo>
cd <repo>
cp .env.example .env
# .env aanpassen: secret key, postgres password, allowed hosts
docker compose up --build -d
```

Vier services in een private docker network:

- **db** — Postgres 16 alpine. Niet exposed naar buiten.
- **redis** — Redis 7 alpine. Cache + axes. Idem niet exposed.
- **web** — Django met gunicorn op port 8000.
- **nginx** — reverse proxy. Exposed op port **8080**.

Voor productie: zet TLS vóór nginx (Caddy, Traefik, of certbot), zet de
`DJANGO_SECURE_*` env vars op `True`, pas `DJANGO_ALLOWED_HOSTS` aan naar
uw echte domein.

### 11.2 Render.com (one-click)

Push naar GitHub, klik de "Deploy to Render" badge in de README. Render
leest `render.yaml`, zet managed Postgres + Redis + de web-service op in
één private network. Secret key wordt automatisch gegenereerd. Gij vult
alleen de `DJANGO_SUPERUSER_*` in via het dashboard.

Free tier werkt voor proeverijen. Voor productie: upgrade — de free tier
slaapt na inactiviteit en de eerste request na een slaap duurt ~30s.

### 11.3 Fly.io

```bash
flyctl launch --copy-config --name <YOUR_APP_NAME>
flyctl postgres create --name <YOUR_APP_NAME>-db
flyctl postgres attach <YOUR_APP_NAME>-db
flyctl secrets set \
    DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')" \
    DJANGO_SUPERUSER_USERNAME=admin \
    DJANGO_SUPERUSER_EMAIL=admin@example.com \
    DJANGO_SUPERUSER_PASSWORD='<sterk wachtwoord>'
flyctl deploy
```

`fly.toml` ligt al klaar (Amsterdam region, auto-stop machines, HTTPS forced,
healthcheck op `/healthz/`).

### 11.4 Eigen Docker host (image van GHCR)

Na elke push naar `main` bouwt de release-workflow een multi-arch image
(amd64 + arm64) en pusht naar `ghcr.io/<owner>/<repo>:latest`. Op uw eigen
host:

```bash
docker run -d --name shiptrack \
  -p 8000:8000 \
  -e DJANGO_SECRET_KEY=$(python -c "import secrets;print(secrets.token_urlsafe(64))") \
  -e DJANGO_DEBUG=False \
  -e DJANGO_ALLOWED_HOSTS=your.domain.com \
  -e USE_POSTGRES=True \
  -e POSTGRES_HOST=db.example.com \
  -e POSTGRES_DB=shiptrack \
  -e POSTGRES_USER=shiptrack \
  -e POSTGRES_PASSWORD=*** \
  ghcr.io/<owner>/<repo>:latest
```

---

## 12. GitHub: CI/CD

Twee workflows in `.github/workflows/`:

### 12.1 `ci.yml` — bij elke push en PR

Drie parallelle jobs:

1. **lint-and-test**: ruff + ruff format check + bandit + mypy + pytest met
   coverage. **Allemaal moeten groen**, anders is uw PR niet mergeable.
2. **django-deploy-check**: simuleert een productie-omgeving (HTTPS-only
   flags aan) en draait `manage.py check --deploy`.
3. **docker-build**: bouwt de Docker image en doet een smoke-test (`docker
   run` + curl naar `/healthz/`). Als de image niet kan starten, fail.

Concurrency: nieuwe pushes naar dezelfde branch annuleren oudere runs.
Geen verspilling van runner-minuten op uitdated commits.

### 12.2 `release.yml` — bij push naar main + bij `v*.*.*` tags

- **Multi-arch build** (amd64 + arm64) via QEMU + buildx.
- **Push naar GHCR** met tags: `latest`, semver (`1.2.3`, `1.2`),
  `sha-abc1234`, `branch-main`.
- **SBOM en provenance attestations** — supply-chain transparency. Bij elke
  release weet ge precies wat er in zit.
- Gebruikt `secrets.GITHUB_TOKEN` automatisch — geen extra config nodig.

### 12.3 Dependabot (`.github/dependabot.yml`)

Wekelijks PRs voor:

- **Python deps** (Django + DRF + security tools gegroepeerd, om PR-spam te
  voorkomen)
- **GitHub Actions** versies
- **Docker base image**

Niet routinematig negeren — security patches lopen via deze flow. Lees de
release notes, draai CI, merge als groen.

---

## 13. Lokale Postgres in 5 stappen

Voor wie geen Docker wil voor lokale dev maar wel een echte Postgres
draait.

### 13.1 Postgres installeren

- **Windows**: download installer van https://www.postgresql.org/download/windows/.
  Onthoud het wachtwoord van de `postgres` superuser dat ge tijdens de
  install zet. (Verlies dat wachtwoord en ge zit met een sub-handelingstaak
  van een uur om het te resetten.)
- **Mac**: `brew install postgresql@17 && brew services start postgresql@17`.
- **Linux**: `apt install postgresql-16` of `pacman -S postgresql`.

### 13.2 Database + user aanmaken (met script)

We hebben hier een script voor:
**`scripts/reset_pg_and_provision.ps1`** (Windows, vereist **elevated**
PowerShell). Wat het doet:

1. Backupt `pg_hba.conf` (timestamped).
2. Stopt de Postgres-service.
3. Schrijft een tijdelijke trust-mode `pg_hba.conf`.
4. Start de service.
5. Reset het `postgres` superuser wachtwoord.
6. Maakt de `shiptrack` user + database aan.
7. Stopt de service.
8. Restored de **originele** `pg_hba.conf` (in een `try/finally`, dus ook
   als er ergens iets fout gaat — ge gaat nooit met een open trust-mode
   server eindigen).
9. Start opnieuw met de echte auth.
10. Verifieert dat zowel `postgres` als `shiptrack` correct kunnen inloggen.

```powershell
# In een ELEVATED PowerShell:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\scripts\reset_pg_and_provision.ps1
```

Antwoord op de prompts (wachtwoord wordt verborgen ingegeven, niet
zichtbaar in shell history).

### 13.3 Manueel (als ge het script niet vertrouwt)

```sql
-- als postgres superuser:
CREATE USER shiptrack WITH PASSWORD '<sterk wachtwoord>';
CREATE DATABASE shiptrack OWNER shiptrack;
GRANT ALL PRIVILEGES ON DATABASE shiptrack TO shiptrack;
\c shiptrack
GRANT ALL ON SCHEMA public TO shiptrack;
```

Daarna in `.env`:

```env
USE_POSTGRES=True
POSTGRES_DB=shiptrack
POSTGRES_USER=shiptrack
POSTGRES_PASSWORD=<dat sterke wachtwoord>
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_SSLMODE=disable
```

---

## 14. Troubleshooting

Voor ge een issue opent: kijk hier eerst. 90% van wat er fout gaat staat
hieronder.

### "Postgres on localhost:5432 not reachable"

Drie oorzaken, op volgorde van waarschijnlijkheid:

1. **Postgres draait niet**. Start de service (Windows: `Get-Service
   postgresql-x64-17 | Start-Service`. Mac: `brew services start
   postgresql@17`. Linux: `systemctl start postgresql`).
2. **Postgres draait op een andere port**. Pas `POSTGRES_PORT` in `.env`
   aan.
3. **Ge wilt geen Postgres**. Zet `USE_POSTGRES=False` in `.env`. Django
   schakelt dan naar SQLite. Goed voor experimenteren, ongeschikt voor
   productie.

### "DJANGO_SECRET_KEY is required in production"

Twee oplossingen:

1. **Genereer een echte**:
   ```bash
   uv run python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```
   Zet de output in `.env` als `DJANGO_SECRET_KEY=...`.
2. **Lokale dev**: zet `DJANGO_DEBUG=True` in `.env`. Dan accepteert
   settings.py een fallback. **Niet** doen in productie. (De fallback heet
   ook letterlijk `insecure-dev-key`. Als ge dat in een productie-instance
   ziet draaien: meteen draaien aan rotaten, en de logs nakijken op wat er
   ondertussen gebeurd kan zijn.)

### "Browser laat oude design zien na een wijziging"

Browser cache. **Ctrl+Shift+R** (hard refresh). Of DevTools open → Network
tab → "Disable cache" aanvinken (werkt zolang DevTools open is).

Als dat niet werkt: cache helemaal leegmaken (DevTools → Application →
Storage → Clear site data) en opnieuw laden.

### "Theme toggle werkt niet, kies wordt niet onthouden"

`localStorage` is geblokkeerd of vol:

- **Private/incognito mode**: localStorage werkt vaak wel maar wordt gewist
  bij sluiten. Niks aan te doen, dat is by design.
- **Browser-instelling**: sommige browsers (Brave bv.) blokkeren
  localStorage by default voor third-party scripts. Onze theme.js is
  same-origin dus zou moeten werken — als het niet werkt, check de
  privacy-instellingen.
- **Volle storage** (zeldzaam): `localStorage.clear()` in DevTools console
  maakt plaats. Onze code slikt de error stilletjes (geen crash), maar de
  keuze wordt dan niet bewaard.

### "Bootstrap CSS laadt niet — pagina is naakt"

Twee dingen om te checken:

1. **`collectstatic` gedraaid?** In productie wel nodig: `make collectstatic`.
   In dev (`DEBUG=True`) gebruikt Django de `staticfiles` finder direct, dus
   geen collectstatic nodig.
2. **CSP blokkeert iets?** DevTools console open. Als ge rode "Refused to
   load the stylesheet" ziet, is er een CSP issue. Check dat ge geen CDN
   probeert te laden — alles moet uit `/static/` komen. (Onze Bootstrap
   wordt **lokaal** geserveerd uit `static/vendor/bootstrap/`. Per ongeluk
   een CDN-link in `base.html` zetten = alles wit.)

### "Tests falen met 'Dependency on app with no migrations'"

Migraties zijn niet gegenereerd. Oplossing:

```bash
uv run python manage.py makemigrations accounts incidents
```

### "Import faalt met 'Could not locate a Primary Ref column'"

De header-row staat niet waar de importer hem zoekt. Voor het oude
K+N-bestand zit hij op rij **10** (er staan 9 dashboard-rijen boven).
Pas `--header-row=10` aan, of pas in de UI het veld aan voor ge submit.

Voor een eigen CSV: header op rij 1, en gebruik herkenbare kolomnamen (zie
de tabel in [§6.3](#63-welke-kolomnamen-worden-herkend)).

### "axes.exceptions.AxesBackendRequestParameterRequired"

Ge gebruikt `client.login()` in een test in plaats van
`client.force_login()`. django-axes wil een `request` zien in
`authenticate()`. Use `force_login(user)` of `user.check_password(...)` om
wachtwoorden te verifiëren in tests — niet `login()`.

### "Outline rond max-cell wordt afgesneden in de pivot"

Was een bug. Sticky thead binnen een `overflow-x: auto` container = hoofdpijn
verzekerd. Inmiddels gefixed door:

1. `box-shadow: inset` ipv `outline` voor de max-cell ring (rendert *binnen*
   de cel, geen clipping).
2. Sticky thead helemaal weggehaald op de pivot — werkt niet betrouwbaar in
   `.table-responsive`.

Sticky **eerste kolom** is wel behouden (werkt prima voor horizontale scroll).

### "Filters resetten niet"

Click **Reset** (= link naar de pagina zonder query string). Of typ de URL
manueel zonder `?...`. De filters zitten in de URL, dus simpelweg refreshen
behoudt ze. Dat is een feature (URL kan gedeeld worden), geen bug.

### "Server start maar `/incidents/` geeft 500"

Check `make migrate` is gedaan en de DB-tabellen bestaan. Of de Postgres
user heeft geen `GRANT` op het schema. Of de migrations zijn maar voor de
helft gedraaid (zeldzaam, gebeurt soms na een gefaalde upgrade).

```bash
uv run python manage.py showmigrations
uv run python manage.py migrate --plan
```

Toont wat klaar is en wat nog niet.

---

## 15. FAQ

### Waarom Postgres en niet SQLite voor productie?

- **Concurrent writes**: SQLite locked de hele database voor write
  transacties. Met 5 mensen tegelijk = wachtrijen.
- **Connection pooling** (`CONN_MAX_AGE=60`).
- **Backups**: `pg_dump` is een industry standard.
- **Toekomstige features**: full-text search, JSONB queries, etc.

SQLite is prima voor tests en heel kleine single-user setups, maar zodra ge
meer dan 2 mensen hebt is het einde verhaal.

### Waarom uv en niet pip?

- **Snelheid**. uv is 10-100× sneller dan pip voor sync operations.
- **Lockfile uit de doos**. Geen `pip-tools` ernaast nodig.
- **Eén tool voor Python install + venv + deps**. Geen pyenv + virtualenv +
  pip-tools triplet meer.
- **Reproducible builds**. Lockfile bevat hashes, dus supply-chain
  tampering wordt opgevangen.

Niks tegen pip persoonlijk, maar uv is gewoon sneller en simpeler.

### Waarom geen TypeScript / React / Vue / Svelte?

Omdat het een formulier-gedreven app is, geen interactive widget-tuin.
Server-rendered HTML met Bootstrap is sneller te schrijven, sneller te
laden, en heeft geen build-step. De analytics-pivot doet de aggregatie
server-side — geen reden om die in JavaScript te dupliceren.

Als er ooit echt rich client-interactie nodig is (live charts,
drag-and-drop, real-time updates) kan ge een React-eiland in een specifieke
pagina inbouwen zonder de hele stack om te gooien. Niet vooruit-engineeren
voor noden die er nog niet zijn.

### Kan ik Django admin gebruiken in plaats van de UI?

Ja, op `/admin/` voor users met `is_staff=True`. Daar krijgt ge standaard
Django admin met alle modellen. Handig voor handmatig prutsen aan reference
data (carriers, locations, issue types). Niet bedoeld voor dagelijks
gebruik.

### Waarom heeft de codebase nog "K+N" of "Grief" referenties?

De **importer** herkent legacy kolomheaders (`K&N REF`, `KN REF`,
`Kuehne ref`) zodat oude Excels gewoon nog werken — bewuste keuze, geen
vergetelheid. Verder zou er nergens nog `grief` of `K+N` als naam moeten
staan in de code (wel als comment of in tests die de import-aliassen
testen).

### Hoe maak ik back-ups van de database?

Met docker-compose op uw eigen server:

```bash
docker compose exec -T db pg_dump -U shiptrack shiptrack > backup-$(date +%F).sql
```

Cronjob 'm op een dagelijks tijdstip dat geen impact heeft. Restore:

```bash
docker compose exec -T db psql -U shiptrack shiptrack < backup-2025-06-15.sql
```

Op Render: zij doen automatic daily backups voor managed Postgres. Op
Fly.io: ook (`fly postgres backup list`).

### Kan ik andere kolommen toevoegen aan het Incident model?

Ja:

1. Voeg het veld toe in `incidents/models.py`.
2. `uv run python manage.py makemigrations incidents`
3. `uv run python manage.py migrate`
4. Voeg het veld toe aan `IncidentForm.Meta.fields` als ge het editeerbaar
   wilt maken.
5. Voeg het toe aan `IncidentSerializer.Meta.fields` voor de API.
6. Update de templates die het tonen (`incident_detail.html`,
   `incident_list.html` als ge het in de tabel wilt).
7. Eventueel een filter toevoegen in `incidents/filters.py`.
8. Eventueel als pivot-dimensie toevoegen in `incidents/pivot.py`.
9. **Tests schrijven**, anders breekt iemand het volgende week.

Klink veel maar het zijn meestal 1-3 regels per file.

### Waar is mijn `.env`?

`.gitignore`'d. **Nooit committen.** Als ge hem kwijt zijt, bouw hem opnieuw
op uit `.env.example`. Als ge ooit per ongeluk hebt gecommit: rotate alle
secrets meteen (`DJANGO_SECRET_KEY`, postgres password, eventueel ook
admin password) en force-push of `git filter-repo` om hem uit de history te
halen.

### Kan ik dit deployen achter mijn bestaande nginx/Apache?

Ja. De web-container draait gunicorn op port 8000, ge zet uw eigen
reverse proxy ervoor. Vergeet niet de `X-Forwarded-Proto` header te zetten
— Django leest die dankzij `SECURE_PROXY_SSL_HEADER` om te weten dat de
binnenkomende request via HTTPS kwam. Anders krijgt ge een redirect-loop.

### Hoe krijg ik foutmeldingen via email als productie crasht?

Niet ingebouwd. Twee opties:

1. **Sentry**: gebruik `sentry-sdk[django]`, voeg de DSN als env var toe,
   importeer en init in `settings.py`. ~5 regels code.
2. **Django ADMINS + email backend**: configureer SMTP in `EMAIL_*`
   settings + zet de `ADMINS` setting. Django stuurt dan automatisch een
   email bij elke 500.

Sentry is comfortabeler (groepeert errors, geeft context). De
ADMINS-aanpak is gratis en simpel.

---

## Slot

Als iets onduidelijk is of er ontbreekt iets: update deze file. Documentatie
die niet meegroeit met de code is documentatie zonder waarde — erger nog,
verkeerde documentatie misleidt nieuwe mensen actief.

Voor security issues: zie `SECURITY.md`. **Niet** via een public issue
(daar mailt ge er over of ge gebruikt GitHub's private vulnerability
reporting).

Voor PR's: zie de PR-template in `.github/pull_request_template.md`. Korte
summary + test plan, that's it.
