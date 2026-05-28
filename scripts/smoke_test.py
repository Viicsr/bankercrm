"""
Smoke test para verificar que el deploy de producción funciona correctamente.
"""

import sys

import httpx


def run_smoke_tests(base_url: str):
    print(f"Running smoke tests against {base_url}\n")

    with httpx.Client(base_url=base_url, timeout=15.0, follow_redirects=True) as client:
        # 1. Health check
        r = client.get("/health")
        assert r.status_code == 200, f"Health check failed: {r.status_code}"
        assert r.json()["status"] == "ok"
        print(
            f"Health check: {r.json()['environment']} | DB: {r.json()['dependencies']['database']['status']}"
        )

        # 2. Auth sin token → 401
        r = client.get("/api/v1/clients")
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        print("Protected endpoints require auth")

        # 3. Registro
        r = client.post(
            "/api/v1/auth/register",
            json={"email": "smoketest@bankercrm.com", "password": "Smoke1234!", "role": "admin"},
        )
        # 201 si es la primera vez, 409 si el smoke user ya existe
        assert r.status_code in (201, 409), f"Register failed: {r.status_code}"
        print("Register endpoint working")

        # 4. Login
        r = client.post(
            "/api/v1/auth/login",
            data={"username": "smoketest@bankercrm.com", "password": "Smoke1234!"},
        )
        assert r.status_code == 200, f"Login failed: {r.status_code}"
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Login + JWT working")

        # 5. FX rates
        r = client.get("/api/v1/fx/rates?currencies=USD&currencies=GBP", headers=headers)
        assert r.status_code == 200, f"FX rates failed: {r.status_code}"
        rates = r.json()["rates"]
        assert len(rates) > 0
        print(
            f"FX rates: EUR/USD = {next(rate['rate'] for rate in rates if rate['currency'] == 'USD')}"
        )

    print(f"\n all smoke tests passed for {base_url}")


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    run_smoke_tests(url)
