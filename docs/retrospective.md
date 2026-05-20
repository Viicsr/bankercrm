# Retrospective - BankCRM Backend

## What I learned
- Async Python with SQLAlchemy 2.0: how AsyncSession, engine lifecycle,
  and the difference between asyncpg and psycopg2 affect the whole stack
- JWT stateless auth + RBAC: why stateless is powerful and where its
  limits are (no immediate token revocation without Redis)
- Domain exceptions vs HTTPException in services: the transport-agnostic
  principle and why it matters for testability and reuse
- Structured JSON logging with correlation IDs: why request_id in both
  header and error body is a real operational win, not just polish
- Alembic async migrations: how to version schema changes safely
- Docker multi-stage builds: how to keep images small and CI reproducible
- GitHub Actions: how lint → test → build gates protect the main branch
- ADRs: how to document technical decisions so they survive the codebase

## What cost me the most time
- **Async mental model in testing:** understanding why `Task attached to a different loop`
  happened and why the engine must be created inside the fixture, not at module level.
  The syntax (`async def`, `await`) was straightforward — the event loop lifecycle
  in pytest was not.

- **SQLAlchemy async lazy loading:** hitting `MissingGreenlet` / `DetachedInstanceError`
  when accessing relationships outside the session scope. Learning that lazy loading
  does not work in async context and that `selectinload` is required, not optional.

- **pytest-asyncio fixture scopes:** `ScopeMismatch` errors when mixing session-scoped
  and function-scoped async fixtures. Required understanding how `asyncio_mode = auto`
  and scope interact before tests were stable.

## Decisions I would change
- Start with URL versioning strategy documented from day 1 (ADR-014 was late)
- Consider cursor-based pagination from the start if the data model grows
- Add rate limiting to auth endpoints earlier — it's a security concern, not a feature

## Known technical debt
- No refresh token blacklisting: deactivating a user doesn't invalidate
  existing refresh tokens. Requires Redis. Documented in ADR-005.
- SQLite in local tests vs PostgreSQL in CI: type strictness differences
  could produce false positives. Acceptable for Phase 1 speed, not for production.
- No rate limiting on auth endpoints: brute force on /login is possible.
  Deferred to Phase 2 or as a dedicated task.
- /api/v1 prefix has no corresponding /api/v2 mechanism yet — URL versioning
  exists in convention only, not in router configuration.

## Next steps
- Deploy on Railway with public URL
- External API endpoint consuming ECB exchange rates
- Rate limiting (slowapi or a middleware)
- Blacklist refresh tokens with Redis