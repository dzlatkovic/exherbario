"""The accounts of a demonstration instance (DEMO_MODE), shown on its sign-in page and created by app.demo."""

from app.config import settings

DEMO_ACCOUNTS = (
    {"email": "curator@demo.exherbario.org", "name": "Demo", "surname": "Curator", "role": "Curator"},
    {"email": "researcher@demo.exherbario.org", "name": "Demo", "surname": "Researcher", "role": "Researcher"},
)


def demo_accounts():
    """For the sign-in page: the accounts and their shared password, on a demo instance only."""
    if not settings.DEMO_MODE:
        return []
    return [{**account, "password": settings.DEMO_PASSWORD} for account in DEMO_ACCOUNTS]
