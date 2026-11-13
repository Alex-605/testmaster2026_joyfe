"""Tests directos del esquema SQLite, sin peticiones HTTP."""
import sqlite3
import pytest
from app import init_db


def test_init_db_crea_las_cuatro_tablas(db_path):
    init_db(str(db_path))
    with sqlite3.connect(db_path) as db:
        tablas = {fila[0] for fila in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
    assert {"usuarios", "tokens", "productos", "clientes"}.issubset(tablas)


def test_init_db_es_idempotente_y_no_borra_datos(db_path):
    init_db(str(db_path))
    with sqlite3.connect(db_path) as db:
        db.execute("INSERT INTO productos (nombre, precio, stock) VALUES (?, ?, ?)",
                   ("Oso", 10.0, 3))
        db.commit()
    init_db(str(db_path))
    with sqlite3.connect(db_path) as db:
        filas = db.execute("SELECT nombre, precio, stock FROM productos").fetchall()
    assert filas == [("Oso", 10.0, 3)]


def test_username_no_se_puede_duplicar_en_sqlite(db_path):
    init_db(str(db_path))
    with sqlite3.connect(db_path) as db:
        db.execute("INSERT INTO usuarios (username, password_hash) VALUES (?, ?)",
                   ("ana", "hash1"))
        db.commit()
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO usuarios (username, password_hash) VALUES (?, ?)",
                       ("ana", "hash2"))


def test_ids_de_productos_son_incrementales(db_path):
    init_db(str(db_path))
    with sqlite3.connect(db_path) as db:
        primero = db.execute("INSERT INTO productos (nombre, precio, stock) VALUES (?, ?, ?)",
                             ("Peluche", 10, 1)).lastrowid
        segundo = db.execute("INSERT INTO productos (nombre, precio, stock) VALUES (?, ?, ?)",
                             ("Puzzle", 20, 2)).lastrowid
    assert segundo > primero


def test_base_sqlite_se_crea_en_la_ruta_indicada(db_path):
    assert not db_path.exists()
    init_db(str(db_path))
    assert db_path.exists()
