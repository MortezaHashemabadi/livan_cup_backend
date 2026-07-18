import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()

import pytest


@pytest.fixture(scope="session")
def django_db_setup(django_db_blocker):
    from django.conf import settings
    settings.DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "ATOMIC_REQUESTS": False,
        "AUTOCOMMIT": True,
        "CONN_MAX_AGE": 0,
        "CONN_HEALTH_CHECKS": False,
        "OPTIONS": {},
        "TIME_ZONE": None,
        "TEST": {"NAME": None, "MIRROR": None},
    }

    from django.test.utils import setup_databases
    with django_db_blocker.unblock():
        setup_databases(verbosity=1, interactive=False)