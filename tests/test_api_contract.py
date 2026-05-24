from app.main import app


def route_methods_by_path() -> dict[str, set[str]]:
    routes: dict[str, set[str]] = {}

    for route in app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None)

        if not path or not methods:
            continue

        routes[path] = set(methods)

    return routes


def test_system_routes_are_registered():
    routes = route_methods_by_path()

    assert "/healthz" in routes
    assert "GET" in routes["/healthz"]

    assert "/readyz" in routes
    assert "GET" in routes["/readyz"]


def test_auth_routes_are_registered():
    routes = route_methods_by_path()

    expected = {
        "/auth/register": "POST",
        "/auth/login": "POST",
        "/auth/me": "GET",
        "/auth/refresh": "POST",
        "/auth/logout": "POST",
        "/auth/verify/send": "POST",
        "/auth/verify/confirm": "POST",
        "/auth/password/forgot": "POST",
        "/auth/password/reset": "POST",
    }

    for path, method in expected.items():
        assert path in routes
        assert method in routes[path]


def test_admin_routes_are_registered():
    routes = route_methods_by_path()

    expected = {
        "/admin/users": "GET",
        "/admin/users/{uid}": "GET",
        "/admin/users/{uid}/role": "POST",
        "/admin/users/{uid}/lock": "POST",
        "/admin/users/{uid}/unlock": "POST",
        "/admin/auth-events": "GET",
    }

    for path, method in expected.items():
        assert path in routes
        assert method in routes[path]
