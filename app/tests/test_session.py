"""Browser sessions: cookie sign-in, CSRF on writes, safe redirects and sign-out."""

from fastapi.testclient import TestClient

from app.main import app
from app.tests import TestClass
from app.users.services import UserServices, signJWT
from app.users.session import CSRF_COOKIE, SESSION_COOKIE


def browser():
    """A separate client, so its cookies never reach other tests."""
    return TestClient(app)


def sign_in(web, email="lab@example.org", password="password", next_page="/researcher"):
    return web.post("/sign-in", data={"email": email, "password": password, "next": next_page}, follow_redirects=False)


class TestSession(TestClass):
    def setup_method(self):
        super().setup_method()
        self.user = UserServices.create_user("Lab", "Owner", "lab@example.org", "password")

    def test_sign_in_sets_cookies_and_returns_to_the_page(self):
        web = browser()
        assert web.get("/researcher", follow_redirects=False).headers["location"] == "/sign-in?next=%2Fresearcher"
        response = sign_in(web, next_page="/researcher?tab=studies")
        assert response.status_code == 303 and response.headers["location"] == "/researcher?tab=studies"
        cookies = response.headers.get_list("set-cookie")
        session = next(cookie for cookie in cookies if cookie.startswith(SESSION_COOKIE + "="))
        csrf = next(cookie for cookie in cookies if cookie.startswith(CSRF_COOKIE + "="))
        assert "HttpOnly" in session and "SameSite=lax" in session and "HttpOnly" not in csrf
        page = web.get("/researcher")
        assert page.status_code == 200 and "My work" in page.text and "Lab Owner" in page.text
        assert "Studies" in page.text and "Depositions" in page.text and "New deposition" in page.text
        assert "Register a voucher" not in page.text  # curators only
        assert web.get("/api/users/me").json() == {"id": self.user.user_id, "name": "Lab", "surname": "Owner",
                                                   "email": "lab@example.org", "role": "researcher"}
        assert web.get("/sign-in", follow_redirects=False).headers["location"] == "/researcher"

    def test_cookie_writes_need_the_csrf_token(self):
        web = browser()
        sign_in(web)
        assert web.post("/api/chemistry/studies", json={"title": "No token"}).status_code == 403
        assert web.post("/api/chemistry/studies", json={"title": "Wrong"}, headers={"X-CSRF-Token": "x"}).status_code == 403
        token = web.cookies[CSRF_COOKIE]
        created = web.post("/api/chemistry/studies", json={"title": "With token"}, headers={"X-CSRF-Token": token})
        assert created.status_code == 201, created.text
        bearer = {"Authorization": "Bearer " + signJWT(self.user.user_id, "classic_user")["access_token"]}
        assert browser().post("/api/chemistry/studies", json={"title": "API client"}, headers=bearer).status_code == 201

    def test_rejected_sign_ins_and_unsafe_redirects(self):
        web = browser()
        wrong = sign_in(web, password="nope")
        assert wrong.status_code == 401 and "not correct" in wrong.text and SESSION_COOKIE not in web.cookies
        assert sign_in(web, email="nobody@example.org").status_code == 401
        for target in ("//evil.example/x", "https://evil.example/", "/\\evil.example", "javascript:alert(1)"):
            assert sign_in(browser(), next_page=target).headers["location"] == "/researcher", target
        forged = browser().post("/sign-in", data={"email": "lab@example.org", "password": "password"},
                                headers={"Origin": "https://evil.example"}, follow_redirects=False)
        assert forged.status_code == 403 and SESSION_COOKIE not in forged.headers.get("set-cookie", "")

    def test_sign_out_and_deactivated_accounts(self):
        web = browser()
        sign_in(web)
        assert web.post("/sign-out", data={"csrf_token": "forged"}, follow_redirects=False).status_code == 303
        assert web.get("/api/users/me").status_code == 200  # a forged sign-out changes nothing
        out = web.post("/sign-out", data={"csrf_token": web.cookies[CSRF_COOKIE]}, follow_redirects=False)
        assert out.headers["location"] == "/sign-in"
        assert web.get("/api/users/me").status_code == 403
        assert web.get("/researcher", follow_redirects=False).status_code == 303

        again = browser()
        sign_in(again)
        UserServices.update_user_is_active(self.user.user_id, False)
        assert again.get("/api/users/me").status_code == 403
        assert again.get("/researcher", follow_redirects=False).status_code == 303
