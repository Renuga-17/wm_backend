import pytest
from django.conf import settings

@pytest.fixture(scope='session')
def django_db_setup(
    request,
    django_test_environment,
    django_db_blocker,
    django_db_use_migrations,
    django_db_keepdb,
    django_db_createdb,
    django_db_modify_db_settings,
):
    from django.test.utils import setup_databases, teardown_databases

    # Copy original DATABASES settings to preserve all default Django database configuration keys
    db_config = settings.DATABASES['default'].copy()
    db_config['ENGINE'] = 'django.db.backends.sqlite3'
    db_config['NAME'] = ':memory:'
    settings.DATABASES['default'] = db_config

    # Clear cached Django connection instance to force reload with SQLite backend
    from django.db import connections
    if 'default' in connections:
        del connections['default']

    settings.CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }
    settings.ALLOWED_HOSTS = ['*']

    with django_db_blocker.unblock():
        db_cfg = setup_databases(
            verbosity=request.config.option.verbose,
            interactive=False,
            keepdb=django_db_keepdb,
        )

    yield

    with django_db_blocker.unblock():
        teardown_databases(db_cfg, verbosity=request.config.option.verbose)

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass
