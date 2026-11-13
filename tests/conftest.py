"""Fixtures comunes para la suite de pruebas de la juguetería.

Cada prueba utiliza una base SQLite en el directorio temporal de pytest.
La base de datos de la aplicación real (app.db) no se modifica.
"""
import pytest
from app import crear_app


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "jugueteria_test.db"


@pytest.fixture
def app(db_path):
    aplicacion = crear_app(str(db_path))
    aplicacion.config.update(TESTING=True)
    return aplicacion


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def usuario():
    return {"username": "alejandro", "password": "clave1234"}


@pytest.fixture
def token(client, usuario):
    respuesta_registro = client.post("/registro", json=usuario)
    assert respuesta_registro.status_code == 201
    respuesta_login = client.post("/login", json=usuario)
    assert respuesta_login.status_code == 200
    return respuesta_login.json["token"]


@pytest.fixture
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def producto_valido():
    return {"nombre": "Coche teledirigido", "precio": 29.95, "stock": 12}


@pytest.fixture
def cliente_valido():
    return {
        "nombre": "Ana García",
        "email": "ana@example.com",
        "telefono": "600123456",
    }


@pytest.fixture
def producto_creado(client, auth_headers, producto_valido):
    respuesta = client.post("/productos", json=producto_valido, headers=auth_headers)
    assert respuesta.status_code == 201
    return respuesta.json


@pytest.fixture
def cliente_creado(client, auth_headers, cliente_valido):
    respuesta = client.post("/clientes", json=cliente_valido, headers=auth_headers)
    assert respuesta.status_code == 201
    return respuesta.json
