import pytest
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Setup test database with performance data"""
    with django_db_blocker.unblock():
        # Run seed script
        from tests.performance.seed_data import seed_clinicians, seed_users
        seed_clinicians(10)
        seed_users(100)  # Smaller dataset for CI/CD

@pytest.fixture
def clinician_user(db):
    """Create a clinician user for testing"""
    return User.objects.create_user(
        username="test_clinician",
        password="testpass123",
        role="CLINICIAN",
        first_name="Test",
        last_name="Clinician"
    )

@pytest.fixture
def admin_user(db):
    """Create an admin user for testing"""
    return User.objects.create_user(
        username="test_admin",
        password="testpass123",
        role="ADMIN",
        is_staff=True
    )

@pytest.fixture(scope="session", autouse=True)
def force_celery_eager():
    """Force Celery to run synchronously during pytest (no RabbitMQ)."""
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    yield