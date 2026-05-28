# Retrospective — BankCRM Backend (Phase 1)

## What I learned

- **Async Python with SQLAlchemy 2.0:** how AsyncSession, engine lifecycle,
  and the difference between asyncpg and psycopg2 affect the whole stack
- **JWT stateless auth + RBAC:** why stateless is powerful and where its
  limits are (no immediate token revocation without Redis)
- **Domain exceptions vs HTTPException in services:** the transport-agnostic
  principle and why it matters for testability and reuse
- **Structured JSON logging with correlation IDs:** why request_id in both
  header and error body is a real operational win, not just polish
- **Alembic async migrations:** how to version schema changes safely
- **Docker multi-stage builds:** how to keep images small and CI reproducible
- **GitHub Actions:** how lint → test → build gates protect the main branch
- **ADRs:** how to document technical decisions so they survive the codebase
- **Railway CD:** how Continuous Deployment complements CI — Railway listens
  to `main`, detects the Dockerfile, and deploys automatically on each push
- **Async HTTP clients (httpx):** why `requests` blocks the event loop and why
  `httpx.AsyncClient` is required in an async FastAPI stack
- **External API integration (SDMX-JSON):** how to consume the ECB public API,
  parse a domain-specific financial format, and expose it as clean REST
- **Heterogeneous source aggregation:** combining internal PostgreSQL data with
  real-time external API data in a single endpoint — the aggregator pattern
- **502 vs 500:** the correct HTTP semantics when an external dependency fails,
  and how a custom exception hierarchy makes this automatic across the codebase

---

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

- **ALLOWED_ORIGINS in Railway:** Railway does not support JSON arrays in
  environment variables. The `field_validator(mode="before")` pattern to parse
  a comma-separated string into `list[str]` was a small but non-obvious fix.

---

## Decisions I would change

- Start with URL versioning strategy documented from day 1 (ADR-014 was late)
- Consider cursor-based pagination from the start if the data model grows
- Add rate limiting to auth endpoints earlier — it's a security concern, not a feature
- Cache ECB rates from day one the BCE updates once daily, so hitting the external 
 API on every request is wasteful; a Redis cache with a date-based key would have been the right default

---

## Known technical debt

- **No refresh token blacklisting:** deactivating a user doesn't invalidate
  existing refresh tokens. Requires Redis. Documented in ADR-005.
- **SQLite in local tests vs PostgreSQL in CI:** type strictness differences
  could produce false positives. Acceptable for Phase 1 speed, not for production.
- **No rate limiting on auth endpoints:** brute force on `/login` is possible.
  Deferred to Phase 2 or as a dedicated task.
- **ECB rates not cached:** same data fetched N times per day across requests.
  Fix: Redis cache with `(currencies, date)` as key, TTL until end of trading day.
- **No circuit breaker on ECB integration:** if the ECB API goes down, every
  request waits for the full `timeout=10s` before returning 502. A circuit
  breaker would fail fast after N consecutive errors.
- **`/api/v1` prefix has no `/api/v2` mechanism yet:** URL versioning exists
  in convention only, not in router configuration.

---

## Completed milestones

| Week | Milestone |
|------|-----------|
| 3 | JWT Auth + RBAC (admin, analyst, read_only) |
| 5 | pytest coverage ≥80% + GitHub Actions CI/CD |
| 6 | Dockerfile + docker-compose (FastAPI + PostgreSQL) |
| 7 | OpenAPI/Swagger complete + README with architecture diagram |
| 8 | Railway deploy with public URL + ECB real-time integration |

---

## Next steps (Phase 2)

- Rate limiting on auth endpoints (slowapi or custom middleware)
- Refresh token blacklist with Redis
- Cache ECB rates in Redis (date-based key, no TTL needed)
- Circuit breaker for external API calls
- Frontend (React or Next.js) consuming the API