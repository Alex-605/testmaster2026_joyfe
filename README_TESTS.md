# Suite de pruebas — API Juguetería

**Proyecto:** API Flask y SQLite del repositorio `andriufit/testmaster2026_joyfe`.

**Objetivo:** validar por separado las reglas de negocio y, de forma integrada, las rutas HTTP, la autenticación y la persistencia en SQLite. No modifica el archivo `app.py` original.

## Estructura

```text
app.py                      # Código original del profesor (en la raíz)
requirements.txt            # Código original
requirements-dev.txt        # Código original
pytest.ini                  # Código original
.gitignore                  # Versión corregida (tests ya no se excluye)
.github/workflows/tests.yml # GitHub Actions
README_TESTS.md
 tests/
   conftest.py
   unit/
      test_validaciones.py
      test_tokens.py
      test_db.py
   integration/
      test_auth.py
      test_productos.py
      test_clientes.py
      test_persistencia.py
```

## Requisitos y ejecución

Desde la carpeta raíz del repositorio, con Python 3.10+:

```bash
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS / Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
pip install pytest-cov
python -m pytest -v
```

Para ejecutar las categorías separadas:

```bash
python -m pytest tests/unit -v
python -m pytest tests/integration -v
```

Para medir la cobertura de `app.py`:

```bash
python -m pytest --cov=app --cov-report=term-missing
```

## Áreas cubiertas

| Categoría | Casos principales |
|---|---|
| Unitarios | Validación de registro, productos y clientes; tokens; creación e idempotencia de tablas SQLite |
| Autenticación | Altas, duplicados, contraseñas con hash, login correcto/incorrecto y protección Bearer |
| Productos | CRUD completo, validación de entradas, errores 400/404, orden de listado y comprobación en SQLite |
| Clientes | CRUD completo, email válido, teléfono opcional, errores 400/404 y comprobación en SQLite |
| Persistencia | Reinicio de la aplicación, conservación de datos y tokens, borrado persistente y aislamiento de BBDD |

## Cómo están aisladas las pruebas

`tests/conftest.py` utiliza `tmp_path`, que proporciona un directorio temporal nuevo a cada test. A partir de ahí, `crear_app(str(db_path))` crea una base SQLite de prueba independiente. Por eso no se usa ni se modifica la `app.db` de la aplicación original y cada test comienza desde un estado limpio.

## Integración continua

Cada push y pull request activa automáticamente el workflow `.github/workflows/tests.yml` de GitHub Actions, que instala las dependencias y ejecuta pytest mostrando la cobertura en el registro de ejecución.

## Nota

Los tests comprueban el comportamiento implementado en el código original. La API está creada para enseñanza y no debe desplegarse como servicio de producción sin reforzar su seguridad.
