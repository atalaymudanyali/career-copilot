def test_index_returns_html():
    from fastapi.testclient import TestClient

    from career_copilot.main import app

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Career Copilot" in response.text


def test_index_contains_dashboard_link():
    from fastapi.testclient import TestClient

    from career_copilot.main import app

    client = TestClient(app)
    response = client.get("/")
    assert '/dashboard"' in response.text
