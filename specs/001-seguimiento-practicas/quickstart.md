# Quickstart: correr el backend desde cero

Guía corta (unos 5 minutos) para levantar y verificar el entorno. La sección completa con requisitos y detalles vive en el [README](../../README.md). Probada en Linux con Python 3.14.

## 1. Requisitos

- Python 3.12 o superior.
- Git.

## 2. Clonar e instalar (una vez)

```bash
git clone <url-del-repositorio>
cd sistema-practicas-preprofesionales-unl
make install
```

Crea el venv `.venv` e instala `backend/requirements.txt`.

## 3. Arrancar (un solo comando)

```bash
make run
```

El servidor queda escuchando en `http://127.0.0.1:8000`. Para detenerlo, `Ctrl+C`.

## 4. Verificar

```bash
curl http://127.0.0.1:8000/health/
```

Salida esperada:

```json
{"status": "ok"}
```

## 5. Tests

```bash
make test
```

Esperado: `Ran 2 tests ... OK`.

## Registro de la prueba cruzada

Cuando una persona distinta del autor sigue esta guía de punta a punta, registra el resultado acá y la captura en `evidencias/`.

| Fecha | Persona | Resultado | Evidencia |
| --- | --- | --- | --- |
| 12/10/2026 | Ivett Zaragocín (`ivecanahi`) | Superada en Linux con Python 3.12.3 desde un clon limpio (commit `72abca2`): `make install` sin errores, `make run` levanta el servidor, `GET /health/` → `{"status": "ok"}` y `make test` → 2 tests OK. | [`evidencias/prueba-cruzada.png`](../../evidencias/prueba-cruzada.png) |