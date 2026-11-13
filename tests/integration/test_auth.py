"""Tests de integración HTTP + autenticación + base de datos real."""
import re
import sqlite3
import pytest
from werkzeug.security import check_password_hash


def test_endpoint_raiz_funciona_sin_login(client):
    respuesta = client.get("/")
    assert respuesta.status_code == 200
    assert "mensaje" in respuesta.json


def test_registro_crea_un_usuario(client, usuario):
    respuesta = client.post("/registro", json=usuario)
    assert respuesta.status_code == 201
    assert respuesta.json == {"mensaje": "Usuario creado correctamente"}


def test_password_se_almacena_como_hash(client, usuario, db_path):
    client.post("/registro", json=usuario)
    with sqlite3.connect(db_path) as db:
        fila = db.execute("SELECT password_hash FROM usuarios WHERE username = ?",
                          (usuario["username"],)).fetchone()
    assert fila is not None
    assert fila[0] != usuario["password"]
    assert check_password_hash(fila[0], usuario["password"])


def test_registro_duplicado_devuelve_409(client, usuario):
    assert client.post("/registro", json=usuario).status_code == 201
    respuesta = client.post("/registro", json=usuario)
    assert respuesta.status_code == 409
    assert respuesta.json["error"] == "Ese usuario ya existe"


@pytest.mark.parametrize("datos", [
    {}, {"username": "ana"}, {"password": "1234"},
    {"username": "ana", "password": "123"},
    {"username": 123, "password": "1234"},
])
def test_registro_valida_datos(client, datos):
    respuesta = client.post("/registro", json=datos)
    assert respuesta.status_code == 400
    assert "error" in respuesta.json


def test_registro_sin_json_devuelve_400(client):
    respuesta = client.post("/registro", data="texto", content_type="text/plain")
    assert respuesta.status_code == 400


def test_login_correcto_devuelve_token_y_lo_guarda(client, usuario, db_path):
    client.post("/registro", json=usuario)
    respuesta = client.post("/login", json=usuario)
    assert respuesta.status_code == 200
    token = respuesta.json["token"]
    assert re.fullmatch(r"[0-9a-f]{32}", token)
    with sqlite3.connect(db_path) as db:
        fila = db.execute("SELECT username FROM tokens WHERE token = ?", (token,)).fetchone()
    assert fila == (usuario["username"],)


@pytest.mark.parametrize("datos", [
    {"username": "inexistente", "password": "clave1234"},
    {"username": "alejandro", "password": "incorrecta"},
    {"username": "alejandro"},
    {},
])
def test_login_credenciales_invalidas(client, usuario, datos):
    client.post("/registro", json=usuario)
    respuesta = client.post("/login", json=datos)
    assert respuesta.status_code == 401
    assert respuesta.json["error"] == "Usuario o contrasena incorrectos"


def test_login_sin_json_devuelve_401(client):
    respuesta = client.post("/login", data="texto", content_type="text/plain")
    assert respuesta.status_code == 401


def test_dos_logins_generan_tokens_diferentes(client, usuario):
    client.post("/registro", json=usuario)
    primero = client.post("/login", json=usuario).json["token"]
    segundo = client.post("/login", json=usuario).json["token"]
    assert primero != segundo


@pytest.mark.parametrize("ruta,metodo", [
    ("/productos", "GET"), ("/productos", "POST"),
    ("/productos/1", "GET"), ("/productos/1", "PUT"), ("/productos/1", "DELETE"),
    ("/clientes", "GET"), ("/clientes", "POST"),
    ("/clientes/1", "GET"), ("/clientes/1", "PUT"), ("/clientes/1", "DELETE"),
])
def test_todas_las_rutas_privadas_exigen_token(client, ruta, metodo):
    respuesta = client.open(ruta, method=metodo)
    assert respuesta.status_code == 401
    assert respuesta.json["error"] == "Falta el token de autenticacion"


@pytest.mark.parametrize("cabecera,esperado", [
    ("Bearer token-inventado", "Token invalido o caducado"),
    ("Bearer ", "Token invalido o caducado"),
    ("Basic usuario:clave", "Falta el token de autenticacion"),
    ("bearer minúsculas", "Falta el token de autenticacion"),
])
def test_formato_o_token_invalido(client, cabecera, esperado):
    respuesta = client.get("/productos", headers={"Authorization": cabecera})
    assert respuesta.status_code == 401
    assert respuesta.json["error"] == esperado


def test_token_valido_permita_consultar_ambos_recursos(client, auth_headers):
    assert client.get("/productos", headers=auth_headers).status_code == 200
    assert client.get("/clientes", headers=auth_headers).status_code == 200


def test_token_se_puede_usar_en_peticion_posterior(client, usuario):
    client.post("/registro", json=usuario)
    token = client.post("/login", json=usuario).json["token"]
    respuesta = client.get("/productos", headers={"Authorization": f"Bearer {token}"})
    assert respuesta.status_code == 200
