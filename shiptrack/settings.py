"""Django settings for shiptrack.

Hardened per OWASP ASVS L1/L2 + Top 10 (2021).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# pytest-django imports settings via a hook that runs *before* conftest.py, so
# env vars set in conftest can't be relied on. Detect a pytest invocation here
# instead and use it as the testing-mode signal.
_RUNNING_TESTS = (
    "pytest" in os.path.basename(sys.argv[0]).lower()
    or any(a == "test" or a.startswith("test_") for a in sys.argv[1:2])
    or "PYTEST_CURRENT_TEST" in os.environ
    or "PYTEST_VERSION" in os.environ
)

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_TESTING=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    DJANGO_CSRF_TRUSTED_ORIGINS=(list, ["http://localhost:8080"]),
    DJANGO_SECURE_SSL_REDIRECT=(bool, False),
    DJANGO_SESSION_COOKIE_SECURE=(bool, False),
    DJANGO_CSRF_COOKIE_SECURE=(bool, False),
    DJANGO_SECURE_HSTS_SECONDS=(int, 0),
    AXES_FAILURE_LIMIT=(int, 5),
    AXES_COOLOFF_TIME=(int, 1),
    USE_POSTGRES=(bool, True),
    OAUTH_GOOGLE_ENABLED=(bool, False),
    OAUTH_MICROSOFT_ENABLED=(bool, False),
)

env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

DEBUG = env("DJANGO_DEBUG")
TESTING = env("DJANGO_TESTING") or _RUNNING_TESTS

# A safe dev fallback is allowed only when DEBUG=True or TESTING=True.
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default=("insecure-dev-key" if (DEBUG or TESTING) else None),
)
if not SECRET_KEY:
    raise RuntimeError(
        "DJANGO_SECRET_KEY is required in production. Generate one with "
        "`python -c 'from django.core.management.utils import get_random_secret_key as g; print(g())'`."
    )

ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env("DJANGO_CSRF_TRUSTED_ORIGINS")

# ---------------------------------------------------------------------------
# Apps
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # Third-party
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "axes",
    "csp",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    # Local
    "accounts",
    "incidents",
]

# Optional social providers — only loaded when explicitly enabled, so that
# `pyjwt`/`cryptography` aren't a hard dependency for installs that don't use SSO.
if env("OAUTH_GOOGLE_ENABLED"):
    INSTALLED_APPS.append("allauth.socialaccount.providers.google")
if env("OAUTH_MICROSOFT_ENABLED"):
    INSTALLED_APPS.append("allauth.socialaccount.providers.microsoft")

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_permissions_policy.PermissionsPolicyMiddleware",
    "csp.middleware.CSPMiddleware",
    # Axes must be the LAST middleware so it sees the resolved request.user.
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "shiptrack.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "incidents.context_processors.user_role",
            ],
        },
    },
]

WSGI_APPLICATION = "shiptrack.wsgi.application"
ASGI_APPLICATION = "shiptrack.asgi.application"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
if env("USE_POSTGRES") and not TESTING:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_DB", default="shiptrack"),
            "USER": env("POSTGRES_USER", default="shiptrack"),
            "PASSWORD": env("POSTGRES_PASSWORD", default=""),
            "HOST": env("POSTGRES_HOST", default="db"),
            "PORT": env("POSTGRES_PORT", default="5432"),
            "CONN_MAX_AGE": 60,
            "OPTIONS": {"sslmode": env("POSTGRES_SSLMODE", default="prefer")},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = "incidents:list"
LOGOUT_REDIRECT_URL = "account_login"

ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_USERNAME_MIN_LENGTH = 3
ACCOUNT_RATE_LIMITS = {
    "login_failed": "5/5m",
    "signup": "20/d",
}
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    },
    "microsoft": {
        "TENANT": env("MICROSOFT_TENANT", default="common"),
    },
}

AXES_FAILURE_LIMIT = env("AXES_FAILURE_LIMIT")
AXES_COOLOFF_TIME = env("AXES_COOLOFF_TIME")
AXES_LOCKOUT_PARAMETERS = ["username", "ip_address"]
AXES_RESET_ON_SUCCESS = True

# ---------------------------------------------------------------------------
# DRF
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "user": "1000/hour",
        "anon": "60/hour",
    },
}

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------
REDIS_URL = env("REDIS_URL", default="redis://redis:6379/0")
CACHES: dict[str, dict] = (
    {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    if (DEBUG or TESTING)
    else {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        }
    }
)

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static / media
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
_STATIC_BACKEND = (
    "django.contrib.staticfiles.storage.StaticFilesStorage"
    if (DEBUG or TESTING)
    else "whitenoise.storage.CompressedManifestStaticFilesStorage"
)
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": _STATIC_BACKEND},
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DATA_UPLOAD_MAX_MEMORY_SIZE = 25 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 25 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 2000

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Security headers (OWASP)
# ---------------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env("DJANGO_SECURE_SSL_REDIRECT")
SESSION_COOKIE_SECURE = env("DJANGO_SESSION_COOKIE_SECURE")
CSRF_COOKIE_SECURE = env("DJANGO_CSRF_COOKIE_SECURE")
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # readable by JS for fetch()
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 60 * 60 * 8

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

SECURE_HSTS_SECONDS = env("DJANGO_SECURE_HSTS_SECONDS")
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:")
CSP_FONT_SRC = ("'self'",)
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)
CSP_OBJECT_SRC = ("'none'",)
CSP_INCLUDE_NONCE_IN = ("script-src",)

PERMISSIONS_POLICY: dict[str, list[str]] = {
    "accelerometer": [],
    "camera": [],
    "geolocation": [],
    "gyroscope": [],
    "magnetometer": [],
    "microphone": [],
    "payment": [],
    "usb": [],
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.security": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "axes": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "incidents": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
