from app.config import settings
from app.site_lock import SITE_COOKIE
from app.tests import TestClass, client
from app.users.services import UserServices, signJWT


class TestSiteLock(TestClass):
    def setup_method(self):
        super().setup_method()
        client.cookies.clear()

    def teardown_method(self):
        client.cookies.clear()
        super().teardown_method()

    def test_open_without_a_password(self):
        assert client.get("/", follow_redirects=False).status_code == 200
        assert client.get("/site-password", follow_redirects=False).headers["location"] == "/"

    def test_the_password_opens_the_site(self, monkeypatch):
        monkeypatch.setattr(settings, "SITE_PASSWORD", "alpha-2026")
        locked = client.get("/depositions?page=2", follow_redirects=False)
        assert locked.status_code == 303
        assert locked.headers["location"] == "/site-password?next=%2Fdepositions%3Fpage%3D2"
        assert client.get("/api/depositions/public").status_code == 401
        assert client.get("/assets/herbar/herbar.css").status_code == 200
        assert "not public yet" in client.get("/site-password").text

        wrong = client.post("/site-password", data={"password": "nope", "next": "/"}, follow_redirects=False)
        assert wrong.status_code == 401 and SITE_COOKIE not in client.cookies
        right = client.post("/site-password", data={"password": "alpha-2026", "next": "https://evil.example/"},
                            follow_redirects=False)
        assert right.status_code == 303 and right.headers["location"] == "/"
        assert client.get("/", follow_redirects=False).status_code == 200

        # A new password locks every browser again.
        monkeypatch.setattr(settings, "SITE_PASSWORD", "beta-2027")
        assert client.get("/", follow_redirects=False).status_code == 303

    def test_api_clients_with_a_token_pass(self, monkeypatch):
        monkeypatch.setattr(settings, "SITE_PASSWORD", "alpha-2026")
        user = UserServices.create_user("Api", "Client", "api@example.org", "password-123")
        token = signJWT(user.user_id, "classic_user")["access_token"]
        assert client.get("/api/depositions/public", headers={"Authorization": f"Bearer {token}"}).status_code == 200
        assert client.get("/api/depositions/public", headers={"Authorization": "Bearer forged"}).status_code == 401
