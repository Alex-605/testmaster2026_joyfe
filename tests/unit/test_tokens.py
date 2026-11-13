"""Generación segura de identificadores de sesión."""
import re
from unittest.mock import patch
from app import generar_token


def test_token_es_hexadecimal_de_32_caracteres():
    token = generar_token()
    assert isinstance(token, str)
    assert re.fullmatch(r"[0-9a-f]{32}", token) is not None


def test_tokens_generados_son_diferentes():
    tokens = {generar_token() for _ in range(100)}
    assert len(tokens) == 100


def test_generar_token_utiliza_secrets():
    with patch("app.secrets.token_hex", return_value="a" * 32) as mock:
        assert generar_token() == "a" * 32
        mock.assert_called_once_with(16)
