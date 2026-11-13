"""Persistencia real de los registros y aislamiento de bases de datos."""
import sqlite3
from app import crear_app


def test_producto_sobrevive_reinicio_de_app(db_path):
    primera = crear_app(str(db_path)).test_client()
    datos = {"username": "ana", "password": "1234"}
    primera.post("/registro", json=datos)
    token = primera.post("/login", json=datos).json["token"]
    headers = {"Authorization": f"Bearer {token}"}
    creado = primera.post("/productos", json={"nombre": "Puzzle", "precio": 10, "stock": 5},
                          headers=headers).json
    segunda = crear_app(str(db_path)).test_client()
    respuesta = segunda.get(f"/productos/{creado['id']}", headers=headers)
    assert respuesta.status_code == 200
    assert respuesta.json == creado


def test_cliente_sobrevive_reinicio_de_app(db_path):
    primera = crear_app(str(db_path)).test_client()
    credenciales = {"username": "ana", "password": "1234"}
    primera.post("/registro", json=credenciales)
    token = primera.post("/login", json=credenciales).json["token"]
    headers = {"Authorization": f"Bearer {token}"}
    creado = primera.post("/clientes", json={"nombre": "Ana", "email": "ana@test.es"},
                          headers=headers).json
    segunda = crear_app(str(db_path)).test_client()
    respuesta = segunda.get(f"/clientes/{creado['id']}", headers=headers)
    assert respuesta.status_code == 200
    assert respuesta.json == creado


def test_registro_y_token_sobreviven_reinicio_de_app(db_path):
    client = crear_app(str(db_path)).test_client()
    credenciales = {"username": "ana", "password": "1234"}
    assert client.post("/registro", json=credenciales).status_code == 201
    token = client.post("/login", json=credenciales).json["token"]
    client_nuevo = crear_app(str(db_path)).test_client()
    assert client_nuevo.get("/clientes", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    assert client_nuevo.post("/login", json=credenciales).status_code == 200


def test_eliminacion_permanece_tras_reinicio(client, auth_headers, producto_creado, db_path):
    client.delete(f"/productos/{producto_creado['id']}", headers=auth_headers)
    cliente_reiniciado = crear_app(str(db_path)).test_client()
    respuesta = cliente_reiniciado.get(f"/productos/{producto_creado['id']}", headers=auth_headers)
    assert respuesta.status_code == 404
    with sqlite3.connect(db_path) as db:
        restantes = db.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
    assert restantes == 0


def test_dos_bases_de_datos_estan_aisladas(tmp_path):
    uno = crear_app(str(tmp_path / "primera.db")).test_client()
    dos = crear_app(str(tmp_path / "segunda.db")).test_client()
    credenciales = {"username": "ana", "password": "1234"}
    uno.post("/registro", json=credenciales)
    token_uno = uno.post("/login", json=credenciales).json["token"]
    assert uno.post("/productos", json={"nombre": "Tren", "precio": 18, "stock": 1},
                    headers={"Authorization": f"Bearer {token_uno}"}).status_code == 201
    # La segunda BD no conoce ni el usuario ni el token de la primera.
    assert dos.post("/login", json=credenciales).status_code == 401
    assert dos.get("/productos", headers={"Authorization": f"Bearer {token_uno}"}).status_code == 401
    assert dos.post("/registro", json=credenciales).status_code == 201
    token_dos = dos.post("/login", json=credenciales).json["token"]
    assert dos.get("/productos", headers={"Authorization": f"Bearer {token_dos}"}).json == []
