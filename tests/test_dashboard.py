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


def test_pipeline_route_registered():
    from fastapi.testclient import TestClient

    from career_copilot.main import app

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/dashboard/pipeline")
    assert resp.status_code != 404


def test_nav_contains_pipeline_link():
    from fastapi.testclient import TestClient

    from career_copilot.main import app

    client = TestClient(app)
    response = client.get("/")
    assert '/dashboard/pipeline"' in response.text
