# MODVIIRS

Monorepo con dos aplicaciones independientes: una API Flask y un frontend React con TypeScript y Vite.

```text
backend/
  src/modviirs/
    __init__.py       # Fábrica y configuración de la aplicación
    api/              # Blueprints y endpoints HTTP
  tests/              # Pruebas de contrato de la API
  pyproject.toml      # Paquete Python y herramientas
frontend/
  src/
    features/hello/   # Interfaz de la funcionalidad de bienvenida
    lib/api.ts        # Acceso HTTP y validación de la respuesta
    App.tsx           # Composición de la pantalla
  package-lock.json
docs/architecture.md # Decisiones y guía para crecer
.github/workflows/    # Verificaciones automáticas
```

## Desarrollo local

Requisitos: Python 3.12 o superior, Node.js 24 LTS y npm. Ejecutar los comandos desde la raíz salvo donde se indique. No es necesario configurar variables para empezar.

Primera terminal, backend:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements-dev.lock
backend/.venv/bin/python -m pip install --no-deps -e backend
backend/.venv/bin/flask --app modviirs:create_app run --debug --port 5000
```

Segunda terminal, frontend:

```bash
cd frontend
npm ci
npm run dev
```

Abrir http://localhost:5173. Vite reenvía `/api` hacia `http://127.0.0.1:5000`, manteniendo las llamadas del navegador en el mismo origen.

## API

| Método | Ruta | Respuesta 200 |
| --- | --- | --- |
| GET | `/api/v1/hello` | `{"message":"Hello World"}` |
| GET | `/api/v1/health` | `{"status":"ok"}` |

```bash
curl http://127.0.0.1:5000/api/v1/hello
```

Los errores HTTP usan JSON con `error` y `message`. Health confirma que el proceso responde; no comprueba servicios externos.

## Verificación

```bash
backend/.venv/bin/pytest backend/tests
backend/.venv/bin/ruff check backend
backend/.venv/bin/ruff format --check backend
cd frontend
npm run lint
npm run build
```

CI ejecuta estas verificaciones en cada push y pull request. `npm run build` comprueba TypeScript y genera `frontend/dist`.

## Configuración y despliegue

Flask lee variables con prefijo `MODVIIRS_` mediante `from_prefixed_env`. React permite cambiar la base de la API con `VITE_API_BASE_URL` durante la compilación; ver `frontend/.env.example`. Las variables `VITE_*` son públicas. Los archivos `.env` locales quedan excluidos de Git; Flask no los carga automáticamente en esta base.

Para servir la API en Linux con un servidor WSGI:

```bash
backend/.venv/bin/gunicorn --bind 127.0.0.1:5000 'modviirs:create_app()'
```

Publicar `frontend/dist` con un servidor de archivos estáticos y configurar un reverse proxy que envíe `/api/*` al backend sin quitar ese prefijo. El proxy de Vite es exclusivo de desarrollo. Para rutas futuras del frontend, configurar fallback a `index.html`, manteniendo `/api` fuera del fallback. Terminar HTTPS en el proxy y desactivar el modo debug. Si se usan dominios distintos, configurar CORS explícitamente en el backend; esta base usa un mismo origen.

Las dependencias npm están fijadas en `package-lock.json`; Python, en `backend/requirements-dev.lock` para desarrollo/CI y `backend/requirements.lock` para ejecución. Para actualizar Python, usar un entorno limpio, instalar `-e './backend[dev]'`, ejecutar los controles y regenerar ambos locks. Revisar y probar las actualizaciones antes de incorporarlas.

Ver [decisiones de arquitectura](docs/architecture.md).
