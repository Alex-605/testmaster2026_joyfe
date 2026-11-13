"""Tests unitarios para las reglas de validación. No utilizan HTTP ni SQLite."""
import pytest
from app import validar_cliente, validar_producto, validar_registro


class TestValidarRegistro:
    @pytest.mark.parametrize("datos", [
        {"username": "ana", "password": "1234"},
        {"username": "pedro", "password": "contrasena_segura"},
        {"username": "a", "password": "abcd"},
    ])
    def test_datos_validos(self, datos):
        assert validar_registro(datos) is None

    @pytest.mark.parametrize("datos", [None, [], "texto", 123])
    def test_cuerpo_invalido(self, datos):
        assert validar_registro(datos) == "Cuerpo de la peticion invalido"

    @pytest.mark.parametrize("datos", [
        {"password": "1234"},
        {"username": "", "password": "1234"},
        {"username": 44, "password": "1234"},
        {"username": None, "password": "1234"},
    ])
    def test_username_obligatorio(self, datos):
        assert validar_registro(datos) == "El campo username es obligatorio"

    @pytest.mark.parametrize("password", [None, "", "1", "123", 1234, True, []])
    def test_password_invalida(self, password):
        assert validar_registro({"username": "ana", "password": password}) == (
            "El campo password debe tener al menos 4 caracteres"
        )

    def test_password_justo_cuatro_caracteres(self):
        assert validar_registro({"username": "ana", "password": "1234"}) is None


class TestValidarProducto:
    @pytest.mark.parametrize("datos", [
        {"nombre": "Pelota", "precio": 5, "stock": 1},
        {"nombre": "Muñeca", "precio": 14.99, "stock": 0},
        {"nombre": "Gratis", "precio": 0, "stock": 0},
    ])
    def test_producto_valido(self, datos):
        assert validar_producto(datos) is None

    @pytest.mark.parametrize("datos", [None, [], "producto", 3.5])
    def test_cuerpo_invalido(self, datos):
        assert validar_producto(datos) == "Cuerpo de la peticion invalido"

    @pytest.mark.parametrize("nombre", [None, "", 123, True, []])
    def test_nombre_invalido(self, nombre):
        assert validar_producto({"nombre": nombre, "precio": 10, "stock": 1}) == (
            "El campo nombre es obligatorio"
        )

    @pytest.mark.parametrize("precio", [None, "10", -0.01, -100, True, False, [], {}])
    def test_precio_invalido(self, precio):
        assert validar_producto({"nombre": "Peluche", "precio": precio, "stock": 1}) == (
            "El campo precio debe ser un numero >= 0"
        )

    @pytest.mark.parametrize("stock", [None, "5", -1, 1.5, True, False, [], {}])
    def test_stock_invalido(self, stock):
        assert validar_producto({"nombre": "Peluche", "precio": 10, "stock": stock}) == (
            "El campo stock debe ser un entero >= 0"
        )

    def test_campos_ausentes(self):
        assert validar_producto({"precio": 2, "stock": 3}) == "El campo nombre es obligatorio"
        assert validar_producto({"nombre": "Puzzle", "stock": 3}) == (
            "El campo precio debe ser un numero >= 0"
        )
        assert validar_producto({"nombre": "Puzzle", "precio": 2}) == (
            "El campo stock debe ser un entero >= 0"
        )


class TestValidarCliente:
    @pytest.mark.parametrize("datos", [
        {"nombre": "Ana", "email": "ana@example.com"},
        {"nombre": "Lucas", "email": "lucas@example.es", "telefono": "611223344"},
    ])
    def test_cliente_valido(self, datos):
        assert validar_cliente(datos) is None

    @pytest.mark.parametrize("datos", [None, [], "cliente", 99])
    def test_cuerpo_invalido(self, datos):
        assert validar_cliente(datos) == "Cuerpo de la peticion invalido"

    @pytest.mark.parametrize("nombre", [None, "", 0, False, []])
    def test_nombre_invalido(self, nombre):
        assert validar_cliente({"nombre": nombre, "email": "ana@example.com"}) == (
            "El campo nombre es obligatorio"
        )

    @pytest.mark.parametrize("email", [
        None, "", "no-es-un-email", "usuario@", "@dominio.es", "usuario@dominio",
        "a b@dominio.es", 123, True,
    ])
    def test_email_invalido(self, email):
        assert validar_cliente({"nombre": "Ana", "email": email}) == (
            "El campo email no es valido"
        )

    def test_telefono_opcional(self):
        assert validar_cliente({"nombre": "Ana", "email": "a@b.es"}) is None
