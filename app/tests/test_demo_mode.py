from app.config import settings
from app.tests import TestClass, client


class TestDemoMode(TestClass):
    def test_demo_pages_say_so_and_publish_nothing(self, monkeypatch):
        assert "demo-banner" not in client.get("/").text
        home = client.get("/").text
        # The three ways in show on every deployment; the demonstration note only on a demo.
        for entry in ('href="/specimens"', 'href="/studies"', 'href="/depositions"', "Explore chemical data",
                      "github.com/dzlatkovic/exherbario", 'action="/specimens"'):
            assert entry in home, entry
        assert "About this demonstration" not in home
        assert "X-Robots-Tag" not in client.get("/").headers
        monkeypatch.setattr(settings, "DEMO_MODE", True)
        home = client.get("/")
        assert "Demonstration instance" in home.text and 'content="noindex, nofollow"' in home.text
        assert home.headers["X-Robots-Tag"] == "noindex, nofollow"
        assert "About this demonstration" in home.text and "synthetic" in home.text and 'href="/sign-in"' in home.text
        monkeypatch.setattr(settings, "DEMO_RESET_HOUR", 3)
        assert "reset every day at 03:00 UTC" in client.get("/").text
        monkeypatch.setattr(settings, "DEMO_RESET_HOUR", -1)
        assert "reset every day" not in client.get("/").text
        assert client.get("/api/specimen").headers["X-Robots-Tag"] == "noindex, nofollow"
        sign_in = client.get("/sign-in").text
        assert "curator@demo.exherbario.org" in sign_in and settings.DEMO_PASSWORD in sign_in
        assert client.get("/api/dwca.zip").status_code == 404
