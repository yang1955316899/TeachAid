# Repository Guidelines

## Project Structure & Module Organization
- Backend: `app/` (FastAPI), config in `app/core/`, models in `app/models/`, services in `app/services/`.
- Frontend: `src/` (Vue 3 + Vite), static in `public/`, alias `@` -> `src`.
- Tooling: `package.json`, `pyproject.toml`, `alembic.ini`, `docker-compose.yml`, `Dockerfile`.
- Assets & data: `uploads/`, `logs/`, docs in `docs/` (see `docs/database_naming_standards.md`).
- Entry points: backend `run.py` or `npm run backend`; frontend `npm run dev`.

## Build, Test, and Development Commands
- Install backend deps: `pip install -r requirements.txt` (or `uv pip sync uv.lock`).
- Run backend (dev): `python run.py` or `npm run backend` (Uvicorn at `:50002`).
- DB bootstrap: `python manage_db.py init` (create tables + seed). Other: `create_tables`, `seed`, `status`, `reset`.
- Frontend (dev): `npm run dev` (Vite at `:50001`).
- Build frontend: `npm run build`; preview: `npm run preview`.
- Lint/format (FE): `npm run lint`, `npm run format`.
- Docker infra: `docker-compose up -d` (MySQL, Redis, backend).

## Coding Style & Naming Conventions
- Python: Black (line length 88), Isort (profile black); prefer type hints and Pydantic models; snake_case for modules/functions, PascalCase for classes.
- Vue/JS: Prettier (2 spaces, single quotes, no semicolons), ESLint (`eslint:recommended`, `plugin:vue/vue3-essential`).
- Components in `src/components` and `src/views` use PascalCase (e.g., `QuestionEditor.vue`).
- API modules under `src/api` use lowerCamelCase functions (e.g., `getQuestionList`).

## Testing Guidelines
- Python: Pytest with asyncio (`pytest-asyncio`). Place tests in `tests/` named `test_*.py`.
- Run tests: `pytest -q` (add `-k name` for subsets). No hard coverage target yet; add meaningful async unit tests.
- Frontend: no test runner configured; propose Vitest when adding FE tests.

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat:`, `fix:`, `refactor:`, `chore:` (matches current history).
- Keep PRs focused; include description, linked issues, and testing notes. Add screenshots/GIFs for UI changes.
- Update docs (`README.md`, `docs/`) when adding features or breaking changes.

## Security & Configuration Tips
- Never commit secrets. Copy `.env.example` to `.env` and set DB/Redis/JWT/LLM keys (`OPENAI_API_KEY`, etc.).
- Local dev defaults: frontend `:50001` proxies `/api` to backend `:50002` (see `vite.config.js`).
- DB migrations: Alembic configured via `alembic.ini`; prefer `manage_db.py` for table init/seed.
