from app.main import app


def test_app_imports_and_registers_routes():
    assert app.title == "ProPlus API"
    assert len(app.routes) > 0
