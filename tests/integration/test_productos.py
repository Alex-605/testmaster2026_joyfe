"""CRUD de productos por HTTP con SQLite temporal real."""
import sqlite3
import pytest


def test_listar_productos_vacio(client, auth_headers):
    respuesta = client.get("/productos", headers=auth_headers)
    assert respuesta.status_code == 200
    assert respuesta.json == []


def test_crear_producto(client, auth_headers, producto_valido):
    respuesta = client.post("/productos", headers=auth_headers, json=producto_valido)
    assert respuesta.status_code == 201
    assert respuesta.json["id"] > 0
    assert {k: respuesta.json[k] for k in producto_valido} == producto_valido


def test_crear_producto_precio_y_stock_cero(client, auth_headers):
    datos = {"nombre": "Regalo", "precio": 0, "stock": 0}
    respuesta = client.post("/productos", headers=auth_headers, json=datos)
    assert respuesta.status_code == 201
    assert respuesta.json["precio"] == 0
    assert respuesta.json["stock"] == 0


def test_listar_varios_productos_en_orden(client, auth_headers):
    for nombre in ("Pelota", "Peluche", "Puzzle"):
        assert client.post("/productos", json={"nombre": nombre, "precio": 10, "stock": 1},
                           headers=auth_headers).status_code == 201
    respuesta = client.get("/productos", headers=auth_headers)
    assert respuesta.status_code == 200
    assert [p["nombre"] for p in respuesta.json] == ["Pelota", "Peluche", "Puzzle"]
    assert [p["id"] for p in respuesta.json] == sorted(p["id"] for p in respuesta.json)


def test_obtener_producto_por_id(client, auth_headers, producto_creado):
    respuesta = client.get(f"/productos/{producto_creado['id']}", headers=auth_headers)
    assert respuesta.status_code == 200
    assert respuesta.json == producto_creado


def test_obtener_producto_inexistente(client, auth_headers):
    respuesta = client.get("/productos/9999", headers=auth_headers)
    assert respuesta.status_code == 404
    assert respuesta.json["error"] == "Producto no encontrado"


def test_actualizar_producto_completo(client, auth_headers, producto_creado):
    nuevo = {"nombre": "Robot", "precio": 45.5, "stock": 3}
    respuesta = client.put(f"/productos/{producto_creado['id']}",
                           json=nuevo, headers=auth_headers)
    assert respuesta.status_code == 200
    assert respuesta.json == {"id": producto_creado["id"], **nuevo}
    consulta = client.get(f"/productos/{producto_creado['id']}", headers=auth_headers)
    assert consulta.json == respuesta.json


def test_actualizar_producto_inexistente(client, auth_headers, producto_valido):
    respuesta = client.put("/productos/9999", headers=auth_headers, json=producto_valido)
    assert respuesta.status_code == 404
    assert respuesta.json["error"] == "Producto no encontrado"


def test_eliminar_producto(client, auth_headers, producto_creado):
    ruta = f"/productos/{producto_creado['id']}"
    borrado = client.delete(ruta, headers=auth_headers)
    assert borrado.status_code == 204
    assert borrado.data == b""
    assert client.get(ruta, headers=auth_headers).status_code == 404


def test_eliminar_producto_inexistente(client, auth_headers):
    respuesta = client.delete("/productos/9999", headers=auth_headers)
    assert respuesta.status_code == 404
    assert respuesta.json["error"] == "Producto no encontrado"


@pytest.mark.parametrize("datos", [
    {}, {"precio": 10, "stock": 1},
    {"nombre": "Peluche", "stock": 1},
    {"nombre": "Peluche", "precio": 10},
    {"nombre": "Peluche", "precio": -1, "stock": 1},
    {"nombre": "Peluche", "precio": True, "stock": 1},
    {"nombre": "Peluche", "precio": "10", "stock": 1},
    {"nombre": "Peluche", "precio": 10, "stock": -1},
    {"nombre": "Peluche", "precio": 10, "stock": 1.5},
    {"nombre": "Peluche", "precio": 10, "stock": False},
    {"nombre": 123, "precio": 10, "stock": 1},
])
def test_crear_producto_con_datos_invalidos(client, auth_headers, datos):
    respuesta = client.post("/productos", headers=auth_headers, json=datos)
    assert respuesta.status_code == 400
    assert "error" in respuesta.json
    assert client.get("/productos", headers=auth_headers).json == []


def test_crear_producto_sin_json(client, auth_headers):
    respuesta = client.post("/productos", headers=auth_headers,
                            data="no json", content_type="text/plain")
    assert respuesta.status_code == 400


@pytest.mark.parametrize("datos", [
    {"nombre": "Robot", "precio": -1, "stock": 2},
    {"nombre": "Robot", "precio": 20, "stock": "2"},
    {"nombre": "", "precio": 20, "stock": 2},
])
def test_actualizacion_invalida_no_modifica_producto(
    client, auth_headers, producto_creado, datos
):
    ruta = f"/productos/{producto_creado['id']}"
    respuesta = client.put(ruta, json=datos, headers=auth_headers)
    assert respuesta.status_code == 400
    assert client.get(ruta, headers=auth_headers).json == producto_creado


def test_datos_producto_se_guardan_en_sqlite(
    client, auth_headers, producto_creado, db_path
):
    with sqlite3.connect(db_path) as db:
        fila = db.execute("SELECT nombre, precio, stock FROM productos WHERE id = ?",
                          (producto_creado["id"],)).fetchone()
    assert fila == (producto_creado["nombre"], producto_creado["precio"], producto_creado["stock"])


def test_borrar_un_producto_no_elimina_los_demas(client, auth_headers, producto_creado):
    segundo = client.post("/productos", json={"nombre": "Puzzle", "precio": 15, "stock": 2},
                          headers=auth_headers).json
    client.delete(f"/productos/{producto_creado['id']}", headers=auth_headers)
    respuesta = client.get("/productos", headers=auth_headers)
    assert respuesta.json == [segundo]
