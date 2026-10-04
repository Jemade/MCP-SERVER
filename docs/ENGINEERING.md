# Engineering notes: MCP-SERVER

## Purpose and scope

Local task management, read-only SQLite analytics and weather tools. This repository is an independently inspectable project; customer adoption, production scale and commercial readiness are not claimed without evidence.

## Request and data flow

MCP client → tool validation → SQLite task/analytics access or bounded weather request → structured tool response.

## Implementation map

Primary implementation and review locations: `src/personal_mcp/server.py`, `src/personal_mcp/database.py`, `src/personal_mcp/weather.py`. Dependency manifests and `.github/workflows/` specify installation and automated checks. Read the source for exact contracts and data models.

## Local verification

From `.` in a configured virtual environment:

```sh
pip install -e ".[dev]"
ruff check .
ruff format --check .
pytest -q
```

From the repository root, run `python scripts/repository_check.py` for documentation and tracked-file checks. CI evidence is available in [GitHub Actions](https://github.com/Jemade/MCP-SERVER/actions). Green hygiene checks alone do not mean application tests passed.

## Decisions and boundaries

Local stdio service, not a hosted multi-tenant API. Database paths and client permissions must be controlled by the operator; weather requires network access.

Use the README's current run instructions and configuration examples. Keep provider credentials outside Git. Test changes against controlled fixtures before enabling external services. Health checks indicate process/service state, not end-to-end correctness.

## Review and operational evidence

[Review checklist](REVIEW_CHECKLIST.md) distinguishes repository evidence from outstanding human and deployment validation. Report measured workload, environment and method with any performance claim. Document incident fixes through reproducible issues and regression tests; do not invent user counts or peer reviews.

## Reuse and licensing

The root LICENSE describes the repository license. Third-party dependencies and assets retain their respective licenses.
