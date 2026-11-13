"""CRUD de clientes por HTTP con SQLite temporal real."""
import sqlite3
import pytest


def test_listar_clientes_vacio(client, auth_headers):
    respuesta = client.get("/clientes", headers=auth_headers)
    assert respuesta.status_code == 200
    assert respuesta.json == []


def test_crear_cliente(client, auth_headers, cliente_valido):
    respuesta = client.post("/clientes", json=cliente_valido, headers=auth_headers)
    assert respuesta.status_code == 201
    assert respuesta.json["id"] > 0
    assert {k: respuesta.json[k] for k in cliente_valido} == cliente_valido


def test_crear_cliente_sin_telefono(client, auth_headers):
    respuesta = client.post("/clientes", json={"nombre": "Luis", "email": "luis@test.es"},
                            headers=auth_headers)
    assert respuesta.status_code == 201
    assert respuesta.json["telefono"] == ""


def test_listar_varios_clientes_en_orden(client, auth_headers):
    for nombre in ("Ana", "Luis", "Eva"):
        assert client.post("/clientes", json={"nombre": nombre, "email": f"{nombre}@test.es"},
                           headers=auth_headers).status_code == 201
    respuesta = client.get("/clientes", headers=auth_headers)
    assert respuesta.status_code == 200
    assert [c["nombre"] for c in respuesta.json] == ["Ana", "Luis", "Eva"]
    assert [c["id"] for c in respuesta.json] == sorted(c["id"] for c in respuesta.json)


def test_obtener_cliente_por_id(client, auth_headers, cliente_creado):
    respuesta = client.get(f"/clientes/{cliente_creado['id']}", headers=auth_headers)
    assert respuesta.status_code == 200
    assert respuesta.json == cliente_creado


def test_obtener_cliente_inexistente(client, auth_headers):
    respuesta = client.get("/clientes/9999", headers=auth_headers)
    assert respuesta.status_code == 404
    assert respuesta.json["error"] == "Cliente no encontrado"


def test_actualizar_cliente(client, auth_headers, cliente_creado):
    nuevos_datos = {"nombre": "María", "email": "maria@test.es", "telefono": "699998877"}
    ruta = f"/clientes/{cliente_creado['id']}"
    respuesta = client.put(ruta, json=nuevos_datos, headers=auth_headers)
    assert respuesta.status_code == 200
    assert respuesta.json == {"id": cliente_creado["id"], **nuevos_datos}
    assert client.get(ruta, headers=auth_headers).json == respuesta.json


def test_actualizar_cliente_sin_telefono_lo_vacia(client, auth_headers, cliente_creado):
    ruta = f"/clientes/{cliente_creado['id']}"
    respuesta = client.put(ruta, json={"nombre": "Luis", "email": "luis@test.es"},
                           headers=auth_headers)
    assert respuesta.status_code == 200
    assert respuesta.json["telefono"] == ""


def test_actualizar_cliente_inexistente(client, auth_headers, cliente_valido):
    respuesta = client.put("/clientes/9999", json=cliente_valido, headers=auth_headers)
    assert respuesta.status_code == 404
    assert respuesta.json["error"] == "Cliente no encontrado"


def test_eliminar_cliente(client, auth_headers, cliente_creado):
    ruta = f"/clientes/{cliente_creado['id']}"
    respuesta = client.delete(ruta, headers=auth_headers)
    assert respuesta.status_code == 204
    assert respuesta.data == b""
    assert client.get(ruta, headers=auth_headers).status_code == 404


def test_eliminar_cliente_inexistente(client, auth_headers):
    respuesta = client.delete("/clientes/9999", headers=auth_headers)
    assert respuesta.status_code == 404
    assert respuesta.json["error"] == "Cliente no encontrado"


@pytest.mark.parametrize("datos", [
    {}, {"nombre": "Ana"}, {"email": "ana@test.es"},
    {"nombre": "Ana", "email": "sin-arroba"},
    {"nombre": "Ana", "email": "ana@"},
    {"nombre": "Ana", "email": "ana@dominio"},
    {"nombre": 123, "email": "ana@test.es"},
    {"nombre": "Ana", "email": 12},
])
def test_crear_cliente_con_datos_invalidos(client, auth_headers, datos):
    respuesta = client.post("/clientes", json=datos, headers=auth_headers)
    assert respuesta.status_code == 400
    assert "error" in respuesta.json
    assert client.get("/clientes", headers=auth_headers).json == []


def test_crear_cliente_sin_json(client, auth_headers):
    respuesta = client.post("/clientes", headers=auth_headers,
                            data="no json", content_type="text/plain")
    assert respuesta.status_code == 400


@pytest.mark.parametrize("datos", [
    {"nombre": "", "email": "ana@test.es"},
    {"nombre": "Ana", "email": "no-es-correo"},
])
def test_actualizacion_invalida_no_modifica_cliente(
    client, auth_headers, cliente_creado, datos
):
    ruta = f"/clientes/{cliente_creado['id']}"
    respuesta = client.put(ruta, json=datos, headers=auth_headers)
    assert respuesta.status_code == 400
    assert client.get(ruta, headers=auth_headers).json == cliente_creado


def test_datos_cliente_se_guardan_en_sqlite(client, auth_headers, cliente_creado, db_path):
    with sqlite3.connect(db_path) as db:
        fila = db.execute("SELECT nombre, email, telefono FROM clientes WHERE id = ?",
                          (cliente_creado["id"],)).fetchone()
    assert fila == (cliente_creado["nombre"], cliente_creado["email"], cliente_creado["telefono"])


def test_borrar_un_cliente_no_elimina_los_demas(client, auth_headers, cliente_creado):
    segundo = client.post("/clientes", json={"nombre": "Luis", "email": "luis@test.es"},
                          headers=auth_headers).json
    client.delete(f"/clientes/{cliente_creado['id']}", headers=auth_headers)
    assert client.get("/clientes", headers=auth_headers).json == [segundo]
