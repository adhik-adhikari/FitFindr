# FitFindr Architecture

> **Status:** Agreed design for incremental implementation; this document does not claim that the system is already built or deployed.
>
> **Product authority:** [product.md](product.md). This document explains how to implement its requirements. Intentional product changes belong in `product.md` first. Detailed table definitions, constraints, and indexes belong in the planned `data-model.md`.

## 1. Architectural goal

FitFindr helps a user answer **“What should I wear today?”** using clothing they own. Garment analysis supplies reviewed wardrobe data; recommendations are the central experience.

The architecture is a **modular monolith**: one FastAPI application contains the domain logic, organized into clear modules, and a separately deployed Next.js frontend presents the mobile-first web experience. A separate frontend deployment does not imply a microservices backend.

The design prioritizes understandable business rules, private user data, controlled AI outputs, and a practical public deployment for a solo developer. It supports the documented roadmap through small extension points without implementing future features early.

### Scope vocabulary

| Classification | Meaning | Examples |
|---|---|---|
| **MVP** | Required to deliver the current product | Upload/review/save, wardrobe management, recommendations, preferences, confirmed wear history |
| **Foundation** | Engineering support needed now; does not expand user-facing scope | Thin adapters, migrations, CI, ownership-scoped access, structured logging |
| **Deferred** | Add only when a product requirement or observed operational problem justifies it | Queues, learned preferences, saved outfits, search, shopping |

Foundations should remain small and tied to concrete needs. An interface around an external provider is useful; a generic plugin framework is unnecessary.

## 2. System shape and technology choices

```text
Browser: responsive Next.js + TypeScript UI (Vercel)
  ├── sign-in/session operations ───────────────► Supabase Auth
  ├── HTTPS JSON + bearer access token ─────────► FastAPI (Render)
  └── authorized image upload/display ──────────► Supabase private Storage
                                                   ▲
FastAPI modular monolith                           │ signed access
  ├── owned application data ───────────────────► Supabase PostgreSQL
  ├── storage operations ───────────────────────► Supabase private Storage
  ├── garment analysis ─────────────────────────► Multimodal AI provider
  ├── outfit recommendation ────────────────────► Recommendation AI provider
  └── optional weather lookup ──────────────────► Weather provider
```

| Choice | Rationale | Tradeoff |
|---|---|---|
| Next.js + TypeScript | Supports the responsive web UI and typed frontend contracts | A separate Python backend requires deliberate API contract coordination |
| FastAPI | Centralizes domain rules, validation, and Python AI integrations | Two runtimes must be developed and deployed |
| Modular monolith | Modules share a process and database, making transactions and changes manageable | Modules need disciplined boundaries; deployment remains one backend unit |
| PostgreSQL | Garments, ownership, preferences, and wear history are relational data | Schema evolution requires migrations and thoughtful constraints |
| Private object storage | Keeps image bytes outside relational rows and application host disks | Database and storage changes cannot share one atomic transaction |
| Managed auth | Delegates credential and session management to an identity provider | Provider configuration and identity migration remain real responsibilities |
| Managed deployment | Vercel hosts the frontend; Render hosts FastAPI; Supabase supplies Auth, PostgreSQL, and Storage | Several services introduce network dependencies and provider-specific configuration |

This is the selected topology, not a promise about provider pricing or plan limits. Verify operational limits and connection settings when deploying. Select a hosting configuration with acceptable startup behavior before sharing the public demo.

## 3. Frontend and backend responsibilities

**Next.js owns presentation and interaction:** account/session UI through managed auth; photo capture or selection; direct upload; confirmation-first garment review; wardrobe browsing and filters; progressive preference setup; recommendation inputs and cards; and basic wear history. It retains the request while the user changes it or requests another outfit, and shows loading, retry, conflict, compromise, and no-result states.

Location access is contextual and skippable during recommendation use. It is not part of mandatory onboarding. Preferences are also optional and introduced after the core flow.

**FastAPI owns application truth:** verified identity, authorization, lifecycle transitions, canonical garment validation, starter-wardrobe readiness, preference validation, recommendation context construction, external integrations, output validation, and durable wear records.

The browser does not directly query application tables or submit trusted wardrobe, preference, history, or weather data to the recommendation endpoint. It sends the current intent; FastAPI loads the authoritative context. Auth operations and signed storage transfers are the intentional direct-browser exceptions.

Business rules must remain enforceable without the UI. Disabling a button is useful feedback, not authorization or validation.

## 4. Backend modules and integration boundaries

Use routes for HTTP concerns, application services for workflows, domain models/policies for rules, and repositories/adapters for persistence and integrations. These are ordinary modules within one application.

| Module | Responsibility |
|---|---|
| Authentication | Shared authenticated-user dependency and `AuthVerifier` |
| Wardrobe | Garment lifecycle, canonical edits, favorites, availability, deletion, filters, and derived summary |
| Media and analysis | `GarmentStorage`, image validation/normalization, `GarmentAnalysisService`, and `GarmentAnalyzer` |
| Preferences | Validated explicit `PreferenceProfile` |
| Recommendations | `RecommendationService`, context construction, `OutfitRecommender`, and output validation |
| Outfit policy | Role-based composition and centralized `OutfitPolicy` |
| Wear history | `WearEvent` creation, item snapshots, basic history, and recent-wear summaries |
| Weather | `WeatherAdapter` and normalized request-level `WeatherContext` |

Keep adapters limited to operations FitFindr actually uses. Provider SDK objects must not become domain models. Isolating an SDK reduces code coupling; it does not eliminate provider migration work or differences in model quality.

A single repository should contain `frontend/`, `backend/`, project documentation, and a README. Frontend and backend contract changes can then be reviewed together. The exact internal folder layout can evolve during implementation.

## 5. Domain and persistence boundaries

### Garment lifecycle and canonical data

A `Garment` represents one physical owned item, including items that look identical. No automatic deduplication is required.

```text
Create draft → upload → analyze → review/correct → confirm → active
                                  │
                                  └── problems leave the item unconfirmed
```

A draft is not eligible for recommendations. Confirmation establishes known **category, type, and primary color**, then activates the garment. Optional metadata may remain unknown, represented consistently as `null` rather than fabricated values.

Availability is separate from lifecycle: an active garment may be unavailable while remaining visible in the wardrobe. Only active, available, supported garments are recommendation candidates.

Store the latest validated AI proposal separately from canonical garment fields, with useful analysis provenance such as provider/model and schema version. Confirmation writes the user's reviewed values into canonical fields. Later user edits change canonical data without rewriting the stored analysis proposal. Recommendations use canonical values, so user corrections remain authoritative.

Optional known metadata includes secondary colors, pattern, formality, style tags, warmth, broad material, sleeve length, neckline/collar, and broad fit. User-controlled fields include tags, a note, favorite status, and availability. Notes are excluded from recommendation context. Custom organizational tags do not become implicit recommendation constraints.

### PostgreSQL shape

The agreed MVP application schema has four core tables: `garments`, `user_preferences`, `wear_events`, and `wear_event_items`. Managed auth provides owner identity; an application profile table is unnecessary until app-specific profile data is needed.

Use columns for stable, frequently validated or queried garment properties, PostgreSQL arrays for appropriate multi-value attributes, and JSONB for the analysis proposal and controlled nested preference configuration. JSONB is a storage choice, not permission to accept arbitrary rules. Database constraints complement service validation; detailed nullability, relationships, and indexes belong in `data-model.md`.

### Role-based outfit composition

`OutfitComposition` contains items with `role` and `garment_id`, rather than embedding permanent `top_id`, `bottom_id`, and `shoes_id` fields throughout the system.

`OutfitPolicy` enforces the MVP structure:

- exactly one top;
- exactly one bottom;
- exactly one pair of shoes;
- zero or one outerwear item;
- no duplicate garment IDs, and each garment category must match its role.

Use this same policy for model-output validation and wear-event creation. Role-based structure is a foundation for future categories, not support for dresses or accessories today. Those require explicit product changes and new policy rules.

### Durable and temporary data

| Durable | Request-level or frontend session state |
|---|---|
| Garments and canonical metadata | Recommendation context and request interpretation |
| Original image objects and storage keys | Generated recommendations and exclusions for “Try another” |
| Latest analysis proposal/provenance | Weather and temporary location context |
| Explicit preferences | Signed image URLs |
| Confirmed wear events and item snapshots | Recommendation explanations before confirmation |

Do not create recommendation-session or weather tables for MVP.

## 6. Image ingestion and multimodal analysis

1. The frontend checks obvious file problems for immediate feedback.
2. `POST /api/v1/garments` creates an owned draft and returns narrowly scoped, short-lived upload authorization for a server-generated object key.
3. The browser uploads directly to private storage. Image bytes do not pass through the FastAPI upload route.
4. After upload succeeds, `POST /api/v1/garments/{id}/analyze` verifies ownership, draft state, object existence, size, and actual supported/decodable image content.
5. A media boundary normalizes orientation and prepares a model-compatible image, removing unnecessary metadata from the AI-bound copy. The filename extension is not authoritative.
6. The multimodal model assesses usability and proposes attributes. FastAPI validates the structured result and stores the proposal.
7. The user accepts, corrects, or completes the minimum required fields.
8. `POST /api/v1/garments/{id}/confirm` validates reviewed data and transitions the garment to active.

Persist the original image initially. Temporary normalized copies can serve analysis; persistent thumbnails and other derivatives are deferred until useful. Exact formats, decoding limits, and normalization libraries are implementation decisions; do not promise every phone format before support is verified.

The analysis contract distinguishes usable images with uncertain attributes from unusable inputs. Controlled reasons include no garment, multiple garments, unreliable blur/darkness/cropping, and unsupported garment. Busy backgrounds and partial cropping are not automatic rejection: proceed if reliable analysis is possible. Optional uncertainty does not block saving; missing required fields can be completed by the user.

A provider timeout permits retrying the same stored image. An unsuitable photo requires a clearer photo. **Whether that replaces the image on the same draft or creates another draft remains undecided**, consistent with `product.md`. No image-replacement endpoint is required by this architecture.

Store an object key, never a persistent signed URL. After authorizing access, FastAPI returns a short-lived signed read URL for display. Restrict upload grants to the intended object and operation, with size/type restrictions where supported and backend verification regardless.

Garment deletion must remove the live garment and its image while preserving historical item snapshots. PostgreSQL and storage cannot commit atomically: handle partial failure explicitly, retain sufficient cleanup information, and log failures without exposing credentials. Final deletion ordering and recovery mechanics must be settled during implementation. Scheduled orphan/draft cleanup can be added later without introducing a queue platform.

## 7. Hybrid recommendation architecture

**Deterministic code handles facts and invariants. AI handles language interpretation and subjective suitability.** The backend does not implement a second fashion-scoring engine.

```text
Authenticate and validate request
  → verify wardrobe readiness and selected garment
  → load owned eligible garments, preferences, and recent wear
  → optionally obtain normalized weather
  → construct RecommendationContext
  → AI interprets, constructs, ranks, and explains outfits
  → deterministic validation
  → valid response, or one bounded repair attempt
  → controlled failure if still invalid
```

### Before the model call

Count active, available garments to enforce the starter threshold: **3 tops, 2 bottoms, and 2 pairs of shoes**. Outerwear is optional. The derived wardrobe summary provides missing-category guidance; the recommendation service enforces the same rule.

Check that a build-around item exists, belongs to the user, is active, and is available. An unavailable selection is a conflict, not an instruction to silently ignore the selection.

Load all eligible structured garments for an ordinary wardrobe. Do not enumerate every top × bottom × shoes combination or remove candidates based on subjective color/style judgments. Candidate preselection is deferred until measured context-size or quality problems justify it.

### Model input and decision contract

`RecommendationContext` contains occasion, the original free-text request, optional build-around ID, canonical wardrobe metadata, explicit preferences, normalized weather or `null`, recent-wear summaries, favorite signals, and previously shown compositions to exclude.

Do not send wardrobe images, signed URLs, AI extraction proposals, free-form notes, storage paths, auth identity, or tokens. Image understanding happens at ingestion; structured recommendations reduce cost and latency and preserve user corrections.

One recommendation call interprets intent, detects contradictions, constructs and ranks outfits, and explains the decision. A separate intent-parser call is deferred. Preserve the original text rather than forcing all nuance through a rigid parser.

The structured `RecommendationDecision` includes:

- request interpretation: supported hard constraints, soft preferences, and detected conflicts;
- outcome: `good_match`, `compromise`, `no_suitable_outfit`, or internal request-resolution `conflict`;
- zero to three role-based outfit compositions;
- concise reasons, meaningful compromises/warnings, and actual influencing factors;
- a limiting explanation when no suitable outfit exists.

A recommending result contains one primary outfit and at most two meaningful alternatives. Conflict/no-result decisions contain none. Ranking does not imply an arbitrary numerical fashion score.

### Priority and validation

Apply the product priority in order: valid structure and availability; current request and selected garment; strong saved garment-type/attribute preferences; occasion; advisory weather; saved style/color/dressiness preferences; compatibility; then recent wear and favorites.

Saved preferences are strong defaults, not absolute prohibitions. Current requests override them without changing the saved profile. Weather may produce a warning rather than override direct intent. A compromise must explain its limitation; it must not silently violate an explicit constraint or disguise an unsuitable outfit as a good match.

FastAPI checks schema and result consistency, supplied candidate IDs, role/category compatibility, duplicate items, build-around inclusion, supported interpreted hard constraints, duplicate alternative compositions, and the maximum result count. Candidate membership establishes ownership and eligibility for the loaded context. Recheck live eligibility where needed before returning a result if concurrent edits could make it stale; validate again when recording wear.

These checks cannot prove that the model understood every sentence or that an outfit is stylish. Request interpretation, subjective suitability, explanation fidelity, and meaningful variety require representative evaluation examples and manual review. Deterministic validation must not be presented as a guarantee of fashion quality.

Invalid model output gets **one repair attempt**, followed by a controlled retryable failure if still invalid. This is a bounded workflow, not an agent loop. No suitable outfit and request conflicts are legitimate domain outcomes and must not trigger automatic retries.

### Result actions

“Try another” calls the same endpoint with previous exact compositions to exclude. Validate and bound that input; compare compositions independent of item ordering. Exclusions are temporary, not permanent feedback or wear history.

“Change request” retains editable inputs in the frontend. “View item” uses garment detail. Marking an item unavailable uses the garment update route and allows a new recommendation with the retained request.

## 8. Explicit preferences, wear history, and weather

### Preferences

`PreferenceProfile` supports styles, preferred/avoided colors, dressiness, garment-type preferences/avoidances, and controlled garment-attribute preferences/avoidances. **Sleeve length is supported at minimum**; the exhaustive attribute list remains open.

For example, validated JSONB can represent `garment_attributes.sleeve_length.prefer = ["long"]` and `avoid = ["sleeveless"]`. FastAPI/Pydantic defines allowed dimensions and values. Do not build a generic database predicate language.

Return defaults when no profile exists. Replace the complete profile with `PUT`; this avoids ambiguous nested JSON merge semantics. Learned preferences are deferred and should remain distinct from explicit user choices.

### Wear history

Only **Wear this** creates a `WearEvent`; generating, viewing, or retrying an outfit does not. The frontend submits a role-based composition, not a nonexistent persisted recommendation ID.

FastAPI verifies all submitted garments under the authenticated owner, validates active/available state and `OutfitPolicy`, and writes the event plus `WearEventItem` rows and snapshots in one database transaction. Snapshots preserve historical garment descriptions after edits or deletion. A deleted live garment reference can become `null`; its removed image is not promised to remain visible.

Recent item use and combinations are summarized for recommendation context. They are soft diversity signals, never mandatory cooldowns. Exact recency windows and weights remain undecided. History records the user's confirmation, not inferred real-world behavior. History correction APIs are deferred.

### Weather

The browser optionally supplies permitted location coordinates with a recommendation request. `WeatherAdapter` normalizes provider output into a small schema with explicit units for temperature and relevant condition/rain information. Location and weather remain temporary and are not persisted for MVP.

No separate public weather endpoint is needed. Missing permission, unavailable weather, or a timeout causes recommendation to continue without weather, with accurate context disclosure. Weather is advisory and cannot guarantee comfort.

## 9. API surface

All application routes use `/api/v1` and require authentication. `/health` is public and contains no private data. Route examples describe the agreed contract; exact payload schemas and UI copy are finalized during implementation.

| Method and route | Purpose |
|---|---|
| `POST /api/v1/garments` | Create an owned draft and upload authorization |
| `POST /api/v1/garments/{id}/analyze` | Verify stored image and synchronously produce a proposal |
| `POST /api/v1/garments/{id}/confirm` | Validate reviewed fields and activate |
| `GET /api/v1/garments` | List active owned garments; category, color, type, availability filters |
| `GET /api/v1/garments/{id}` | Owned detail, including draft review data when applicable |
| `PATCH /api/v1/garments/{id}` | Edit canonical/user-controlled fields; preserve invariants |
| `DELETE /api/v1/garments/{id}` | Delete live garment and arrange image removal; preserve history |
| `GET /api/v1/wardrobe/summary` | Derived available counts, unlock status, and missing categories |
| `GET /api/v1/preferences` | Current explicit profile or defaults |
| `PUT /api/v1/preferences` | Validate and replace the full explicit profile |
| `POST /api/v1/recommendations` | Current intent plus optional location and excluded compositions |
| `POST /api/v1/wear-events` | Record confirmed composition and snapshots |
| `GET /api/v1/wear-events` | Basic confirmed history, newest first |
| `GET /health` | Lightweight process responsiveness |

Recommendation input includes required occasion, optional original text, build-around ID, location, and previous compositions. FastAPI loads wardrobe, preferences, and history itself. Public responses hydrate validated IDs into display-ready garment data and signed image URLs so the UI need not fetch each outfit item separately.

Use a consistent error envelope containing `code`, `message`, optional `details`, and a request identifier. Keep application codes stable while refining user-facing wording.

| Situation | API behavior |
|---|---|
| Good match, compromise, no suitable outfit | `200`; valid product outcomes |
| Contradictory current instructions | `409 REQUEST_CONFLICT` with actionable explanation |
| Unavailable selected item | `409 GARMENT_UNAVAILABLE` |
| Starter threshold unmet | `409 WARDROBE_NOT_READY` with missing categories |
| Missing/invalid/expired token | `401` |
| Resource absent or owned by someone else | `404` without revealing private existence |
| Invalid payload or unusable image | Controlled client/domain error with specific code |
| Provider timeout or invalid output after repair | Controlled dependency failure with appropriate retry guidance |

Do not allow clients to activate drafts by freely patching lifecycle status. Confirmation is an explicit domain transition. Pagination, individual history-event routes, and history editing are deferred until needed; text search is outside required MVP scope.

## 10. Authentication, authorization, and privacy

Supabase Auth handles account credentials and session issuance/refresh. The frontend obtains an access token and sends it as `Authorization: Bearer ...`. A centralized `AuthVerifier` validates signature, expiry, expected issuer/audience, and subject before deriving the trusted user identity. Verification must use an approved signing configuration, not merely decode claims.

Every repository operation scopes resources by this identity. Never trust a submitted `user_id`. Lists, mutations, analysis, signed image access, preferences, recommendations, and wear events all enforce ownership. Submitted composition IDs are checked as a group so a cross-user item cannot enter history.

FastAPI is the primary application authorization boundary. No custom passwords, refresh-token tables, or server-local login sessions are required. Thin auth isolation helps keep provider details out of domain code, but migrating stored owner identities may still require a real migration.

A full duplicate RLS authorization system is deferred. **This does not permit exposed Supabase data access:** disable unintended browser access to application tables through appropriate grants/API configuration and protective policies where needed. Public auth configuration must not grant access around FastAPI. Private storage remains protected, with signed grants issued only after authorization.

Use HTTPS and environment-specific allowed frontend origins for CORS. CORS is not a substitute for authorization. Keep database credentials, privileged storage credentials, AI keys, and weather keys on the backend. Frontend public configuration may contain the API URL and public auth client configuration, never privileged keys.

External AI receives only task data. Auth tokens and identity details never enter prompts. Weather receives temporary location without user identity. Avoid logging precise coordinates, images, signed URLs, credentials, and full personal request text by default.

## 11. Runtime, deployment, and operations

### Synchronous MVP calls

Garment analysis and recommendations wait for provider results within the HTTP request. “Synchronous” describes the user workflow; outbound I/O should not unnecessarily block the server's event loop. The UI shows progress and controlled failure states.

This avoids jobs, workers, polling, and queue operations while usage is small. The tradeoff is dependence on provider latency and hosting request limits. Set explicit external timeouts and an overall operation budget; bounded retries/repair must fit that budget. Weather should have a shorter noncritical budget so it cannot dominate recommendation latency. Final durations are configuration decisions informed by measurement.

Retry only appropriate transient failures, with bounded attempts. Domain outcomes require user action or honest results, not automatic repetition. Limit image sizes, request sizes, and retry counts, and use available provider/platform abuse protections. Redis-backed distributed rate limiting is deferred.

### Environments and durable state

Start with local development and production using separate data/configuration and provider credentials. Do not test destructive changes against the production wardrobe database. A dedicated staging environment and custom domains are deferred.

Vercel deploys `frontend/`; Render runs `backend/` as a long-lived ASGI service. PostgreSQL connections use a bounded application pool with the selected Supabase connection mode configured at deployment. Images and durable application state belong in storage/PostgreSQL, never a host's local filesystem.

Backend instances remain stateless between requests apart from normal connection pools and integration caches. Horizontal scaling is deferred; before adding instances, assess database pool sizes, provider limits, and any per-process safeguards.

### CI and migrations

Use GitHub Actions for frontend type checking, linting, relevant tests/build validation, and backend linting and tests. Keep dependency definitions and lockfiles reproducible. Validate contracts and important behavior: tenant isolation, lifecycle transitions, outfit policy, preference values, provider failure handling, and wear snapshots. Separate deterministic tests from model-quality evaluation; routine tests should not depend on live paid AI calls.

Version schema changes with Alembic alongside SQLAlchemy persistence. Apply reviewed migrations deliberately; do not run competing migrations from every application startup or make undocumented production dashboard changes. Coordinate migrations and application releases. Prefer additive, backward-compatible changes because frontend and backend deploy independently; destructive changes need a deliberate recovery plan.

Feature branches and reviewed changes lead to `main`, the intended production branch. Managed hosts deploy from the repository after required checks pass. A failed build or migration must not be treated as a successful release.

### Logging and health

Structured logs include request ID, route, method, status, duration, error code, and integration operation/success/failure. Track AI latency, validation/repair failures, and provider errors to guide improvements without storing raw personal data as a shadow database.

`GET /health` confirms that the FastAPI process responds. It does not call AI or weather and does not claim every dependency is healthy. Additional readiness probes can be added if operations justify them.

Add lightweight scrubbed error monitoring near the first public deployment for unexpected frontend/backend exceptions and release context. A metrics/tracing platform is deferred. Confirm the deployed upload → review → recommendation → wear-history flow and private access behavior before presenting the public app.

## 12. Failure behavior

| Failure | Response and recovery |
|---|---|
| Upload interrupted | Keep unconfirmed state; permit a new upload attempt through the chosen UX |
| Image unsuitable | Explain the controlled reason and request a clearer supported photo |
| Attribute uncertain | Leave unknown; user completes only required fields |
| Analysis dependency unavailable | Preserve draft/image for retry |
| Weather unavailable | Continue without weather and disclose actual context used |
| Model invents an ID or violates outfit policy | Reject, repair once, then fail safely |
| Wardrobe cannot satisfy request | Explain compromise or no suitable outfit; do not force three results |
| Conflicting current instructions | Ask the user to change one before presenting an outfit |
| Garment changed since recommendation | Revalidate on action; expose a conflict rather than record stale invalid state |
| Database/storage deletion partly fails | Handle explicitly, preserve cleanup information, and log for recovery |
| Duplicate/retried write | Prevent accidental repeat submissions in UI; define write retry/idempotency behavior during endpoint implementation |

No distributed transactions, event bus, or resilience framework is required. Clear state transitions and bounded recovery are the MVP approach.

## 13. Deferred scope and extension points

| Deferred item | Reason and path to reconsider |
|---|---|
| Microservices | No independent teams or scaling boundaries justify distributed backend operations |
| Redis, queues, Celery/workers | Add jobs behind analysis/recommendation services if measured latency, batches, or buffering requires them |
| Vector database and RAG | Current context is a small owned relational wardrobe; no retrieval requirement justifies embeddings |
| Agents and agent frameworks | The workflow has known steps and a bounded model call/repair, not autonomous tool use |
| Docker | Add if reproducible packaging, system dependencies, or another host creates a concrete need |
| Kubernetes | No current orchestration requirement |
| Separate intent-parser model | Add only if evaluation demonstrates a benefit that outweighs extra latency/cost |
| Persistent recommendation identity and richer feedback | Add when feedback/analytics needs durable recommendation records |
| Saved/favorite outfits | Add separate saved compositions using the existing role-based concept |
| Learned preferences | Add separately from user-authored preferences |
| Dresses, accessories, complex outfits | Extend category/role vocabularies and `OutfitPolicy` after product scope changes |
| Search, collections, seasons, archives | Add query/index or organization structures for documented future needs |
| Calendar/travel planning | Add planning entities without treating current ephemeral recommendations as a planning system |
| Shopping/catalog discovery | Introduce separate `CatalogProduct` and discovery concerns; do not mix retailer inventory into owned `Garment` |
| Persistent image derivatives and scheduled draft cleanup | Add when storage/display or maintenance needs justify them |

Virtual try-on, body analysis, social features, laundry tracking, and shopping suggestions are not part of the current architecture. The documented roadmap describes possible directions, not committed releases.

## 14. Decisions intentionally left open

Implementation and product testing should settle the AI providers/models, weather provider and normalized schema, exact timeouts, supported image formats/limits, upload recovery and image replacement UX, cleanup ordering, final controlled subtype/style/formality vocabularies, and the preference-capable attributes beyond sleeve length.

`product.md` also leaves occasion labels, recent-wear window, recommendation weights, history correction, and final copy open. This architecture must not silently freeze them. Keep configurable engineering values distinct from product decisions that require a document update.

## 15. Interview explanation

> FitFindr uses a Next.js frontend and one modular FastAPI backend. PostgreSQL stores owned wardrobe data and confirmed wear history, while private object storage holds photos. Managed auth establishes identity, and FastAPI authorizes every operation. A multimodal model proposes garment attributes, but the user confirms the canonical data. For outfits, Python loads eligible garments and enforces structure and constraints; AI interprets the request and evaluates subjective suitability. The backend validates the response and permits one repair attempt. Recommendations stay temporary until the user records “Wear this.” Managed deployment, migrations, CI, timeouts, and diagnostic logs provide production foundations without introducing infrastructure the MVP does not need.

The key tradeoff is deliberate: AI supplies flexible judgment, while ordinary software controls identity, data truth, and valid actions. That produces an explainable architecture without claiming the model is infallible or building a separate fashion rules engine.
