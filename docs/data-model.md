# FitFindr Data Model

> **Status:** Agreed persistence design for incremental implementation. These tables are proposed, not a claim that migrations or features already exist.
>
> **Authority:** [product.md](product.md) defines product behavior and scope; [architecture.md](architecture.md) defines system boundaries. This document specifies the MVP domain and PostgreSQL schema within those decisions. Product changes must be reflected in the product document first.

## 1. Purpose and conventions

This document is the basis for implementing SQLAlchemy persistence models, Pydantic contracts, and Alembic migrations next. It describes data, invariants, and transactions rather than implementation code.

The MVP has exactly four application core tables: `garments`, `user_preferences`, `wear_events`, and `wear_event_items`. Supabase-managed identity and storage infrastructure are external to that count.

Schema conventions:

- Names use `snake_case`; domain names use `Garment`, `PreferenceProfile`, `WearEvent`, and `WearEventItem`.
- Entity IDs use PostgreSQL `UUID`. FastAPI generates UUIDs before insertion; no database UUID-generation extension is required. IDs are opaque identifiers, not authorization credentials.
- Owner IDs use `UUID` matching the selected Supabase Auth identity.
- Timestamps use `TIMESTAMPTZ`; store instants consistently and format them for display separately.
- `created_at` defaults to database `now()`. `updated_at` initially defaults to `now()` and is explicitly updated by application writes. A default alone does not maintain it on updates; no timestamp trigger is required.
- Unknown optional scalar attributes use SQL `NULL`, not the strings `Unknown`, `null`, or an invented value. The UI may display “Unknown.”
- Multi-value garment attributes use non-null `TEXT[]` with an empty-array default. Empty means no known values recorded; it does not assert certainty that no accent color or style exists.
- Controlled scalar values use `TEXT`, with application validation and selected database checks. No PostgreSQL enum types are required.
- Column defaults apply when values are omitted; explicit `NULL` must still obey nullability.

## 2. Domain overview and relationships

A garment is one physical owned item. Identical-looking items remain separate garments. A preference profile records explicit user choices. A wear event records a user-confirmed outfit, with one item row per role and a historical description per item.

```text
Managed identity: auth.users (Supabase-owned; not an application profile)
  id UUID PK
    |
    +-- 1 : many --> garments
    |                 id UUID PK
    |                 user_id UUID FK
    |                 status: draft | active
    |                 is_available: boolean
    |
    +-- 1 : 0..1 --> user_preferences
    |                 user_id UUID PK / FK
    |                 preferences JSONB
    |
    +-- 1 : many --> wear_events
                      id UUID PK
                      user_id UUID FK
                      worn_at TIMESTAMPTZ
                        |
                        +-- 1 : 3..4 --> wear_event_items
                                          id UUID PK
                                          wear_event_id UUID FK
                                          role TEXT
                                          garment_id UUID nullable FK
                                          garment_snapshot JSONB
                                               |
                             garments 1 : many-+ (live reference)
                             garment deletion => garment_id NULL

3..4 item cardinality is enforced by OutfitPolicy at creation,
not by a simple PostgreSQL foreign key or CHECK constraint.
```

There is no durable `Outfit` or `Recommendation` entity in MVP. `OutfitComposition` is a reusable value object shared by recommendations and wear recording.

## 3. Ownership and managed authentication identity

For the selected topology, `garments.user_id`, `user_preferences.user_id`, and `wear_events.user_id` reference `auth.users(id)` in the same Supabase PostgreSQL database. The initial FK policy is `ON DELETE CASCADE` for these owned records. An auth account deletion therefore removes its application rows, including wear events and their items. This is an ownership cleanup rule, not an additional account-management UI requirement.

Do not create, alter, or manage the provider's `auth.users` table with application migrations. Alembic manages application tables and their cross-schema FKs; its migration environment must have the necessary privileges. Local migration testing must provide the managed-auth dependency or a clearly isolated test fixture matching its key, rather than pretending an application-owned users table is production identity.

FastAPI verifies the access token and derives a trusted owner ID from its subject. Clients cannot set or transfer `user_id`. Every read, update, deletion, signed-image operation, and composition lookup is scoped to that owner. FKs ensure identity existence; they do not establish request authorization.

`wear_event_items` inherits ownership through its parent event. It has no redundant `user_id`. Its garment FK alone cannot prevent a cross-user reference: the service must verify that all selected garments belong to the event owner before insertion.

No app profile table is needed: there are no current app-specific profile fields requiring one. Do not store credentials, refresh tokens, sessions, email copies, or auth-provider metadata in wardrobe tables. Backend authorization remains the primary boundary; application-table grants/API exposure must prevent browser access around FastAPI as described in the architecture.

If auth later moves outside this database, direct FKs may no longer be possible. Introduce an intentional identity mapping/migration then; do not add a speculative identity abstraction table now. Account deletion also needs object-storage cleanup, which database cascades cannot perform.

## 4. `garments`

### Proposed columns

| Column | PostgreSQL type | Nullable | Default / source | Meaning |
|---|---|---|---|---|
| `id` | `UUID` | No | Application-generated | Physical item identity |
| `user_id` | `UUID` | No | Verified owner | FK to managed identity |
| `status` | `TEXT` | No | `'draft'` | Lifecycle only |
| `image_key` | `TEXT` | Yes | None | Server-generated private object key |
| `category` | `TEXT` | Yes | None | `top`, `bottom`, `shoes`, `outerwear` |
| `garment_type` | `TEXT` | Yes | None | Controlled subtype valid for category |
| `primary_color` | `TEXT` | Yes | None | Controlled primary color |
| `secondary_colors` | `TEXT[]` | No | Empty array | Known accent/secondary colors |
| `pattern` | `TEXT` | Yes | None | Broad controlled pattern |
| `formality` | `TEXT` | Yes | None | Broad editable formality |
| `style_tags` | `TEXT[]` | No | Empty array | Controlled subjective style tags |
| `warmth` | `TEXT` | Yes | None | Broad warmth description |
| `material` | `TEXT` | Yes | None | Broad material/fabric; not exact composition |
| `sleeve_length` | `TEXT` | Yes | None | Applicable to tops/outerwear |
| `neckline` | `TEXT` | Yes | None | Broad neckline/collar when applicable |
| `fit` | `TEXT` | Yes | None | Broad fit/silhouette |
| `custom_tags` | `TEXT[]` | No | Empty array | User organizational labels |
| `note` | `TEXT` | Yes | None | User note; excluded from recommendations |
| `is_favorite` | `BOOLEAN` | No | `false` | Soft recommendation signal |
| `is_available` | `BOOLEAN` | No | `true` | Current eligibility flag, separate from status |
| `analysis_proposal` | `JSONB` | Yes | None | Latest validated normalized analysis result |
| `analysis_provider` | `TEXT` | Yes | None | Provider that produced stored proposal |
| `analysis_model` | `TEXT` | Yes | None | Model identifier used for stored proposal |
| `analysis_schema_version` | `INTEGER` | Yes | None | Application proposal-contract version |
| `analyzed_at` | `TIMESTAMPTZ` | Yes | None | Time stored analysis completed |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Draft creation |
| `updated_at` | `TIMESTAMPTZ` | No | `now()` initially | Latest successful row mutation |

### Keys and database constraints

- Primary key: `id`; owner FK as specified above.
- `status` must be one of `draft`, `active`.
- `category` must be `NULL` or one of `top`, `bottom`, `shoes`, `outerwear`. Store singular application codes even when UI labels are plural.
- If `status = 'active'`, `image_key`, `category`, `garment_type`, and `primary_color` must all be non-null; textual required values must also be nonblank after trimming.
- Any non-null `image_key`, `garment_type`, or `primary_color` must be nonblank. Optional scalar text is normalized to a value or `NULL` by the service.
- An analysis proposal is either absent with all four provenance fields absent, or present as a JSON object with all provenance fields present. Provider/model identifiers must be nonblank and `analysis_schema_version` positive.

Express the active-row CHECK with explicit `IS NOT NULL` predicates. PostgreSQL CHECK constraints also accept an unknown/null result; a comparison-only check can accidentally permit missing required data.

A database image-key check establishes that a reference exists, not that a valid uploaded image exists. FastAPI must verify the stored image before confirmation. Category and lifecycle checks apply to drafts too; draft nullability permits incomplete information without permitting arbitrary unsupported category codes.

### Application taxonomy and validation

`garment_type` is validated against a centralized category-to-subtype taxonomy in application code, not a database enum or lookup table. For example, `hoodie` belongs to `top`; `jeans` belongs to `bottom`. Examples do not freeze the full taxonomy. A category change must revalidate the subtype and category-specific optional fields.

Pydantic/domain validation controls color, pattern, formality, warmth, style, material, sleeve length, neckline, and fit vocabularies and their applicability. Normalize and deduplicate array entries, reject null/blank elements, and bound lengths/counts in API contracts. Custom tags permit user labels rather than requiring the style taxonomy; they do not become hidden recommendation rules.

For attributes not applicable to a category, use `NULL` rather than forcing a value. Do not infer exact fabric percentages. Unknown required values may exist in a draft but cannot survive confirmation or an edit to an active garment.

The complete subtype and optional-attribute vocabularies remain implementation/content decisions. Keep their source centralized and shared by review, confirmation, edits, AI normalization, and preference validation.

### Lifecycle and availability

```text
draft (incomplete, excluded from wardrobe candidates)
  -> server assigns image key / browser uploads
  -> verified image analysis produces proposal
  -> user reviews, corrects, completes required values
  -> explicit confirm transaction writes canonical fields + status active

active + available   -> eligible candidate
active + unavailable -> visible wardrobe item, excluded from candidates
```

A draft may have a reserved key before an object exists. `image_key` is nullable to model incomplete state, but the normal creation flow assigns the server-generated key before returning upload authorization. An active garment must have a verified uploaded image and valid canonical metadata. Availability can change independently; it never activates a draft. Clients cannot bypass confirmation by freely patching `status`.

There is no `archived`, `deleted`, `clean`, `dirty`, or asynchronous analysis-job status in MVP. Physical deletion is separate from lifecycle. Failed analysis leaves the garment draft; optional unknown attributes do not block activation. Whether recovery replaces an image on the same draft or creates a new draft remains open.

Starter readiness is derived from active, available counts: at least three tops, two bottoms, and two pairs of shoes. Outerwear is optional. Do not persist onboarding progress or a readiness boolean that can become stale.

## 5. Canonical fields and latest analysis proposal

Canonical garment columns are the reviewed values used for display, filtering, and recommendations. The proposal preserves what the analyzer suggested; it is never an automatic override of later user corrections.

The JSONB value is an application-normalized result, not an unbounded provider response. Its conceptual shape is:

```json
{
  "image_assessment": { "usable": true, "issue": null },
  "garment": {
    "category": "top",
    "garment_type": "hoodie",
    "primary_color": "navy",
    "secondary_colors": [],
    "pattern": "solid",
    "formality": "casual",
    "style_tags": ["casual"],
    "warmth": "warm",
    "material": "fleece",
    "sleeve_length": "long",
    "neckline": null,
    "fit": "regular"
  }
}
```

This example illustrates structure, not a final exhaustive vocabulary. An unusable-image result can contain `image_assessment.usable = false`, a controlled issue, and `garment = null`. A usable proposal may still have missing required attributes for the user to complete.

Store a valid domain analysis outcome and its provenance together atomically. A new successful validated analysis replaces the previous proposal and provenance; there is no immutable analysis-run history. A timeout, malformed provider response, or other technical failure must not replace a valid proposal with fabricated data. User confirmation and subsequent edits change canonical fields without rewriting the stored proposal.

Analysis metadata identifies the provider/model, application contract version, and completion time; it does not promise reproducibility or per-field correction auditing. Do not store provider reasoning traces, credentials, image bytes, signed URLs, or raw SDK objects. If image replacement is implemented, clear/invalidate the old proposal with the image change so it cannot be presented as analysis of the new photo.

## 6. `user_preferences`

| Column | PostgreSQL type | Nullable | Default / source | Meaning |
|---|---|---|---|---|
| `user_id` | `UUID` | No | Verified owner | Primary key and FK to managed identity |
| `preferences` | `JSONB` | No | No SQL default; validated application value | Complete explicit preference profile |
| `schema_version` | `INTEGER` | No | `1` | Profile-contract version |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | First saved profile |
| `updated_at` | `TIMESTAMPTZ` | No | `now()` initially | Last complete replacement |

Constraints: primary key on `user_id` gives at most one row per user; `preferences` must be a JSON object; `schema_version > 0`. Detailed nested validation belongs to Pydantic and the preference service.

No row is required at account creation. GET returns the normalized default profile when absent. PUT validates and replaces the entire profile, inserting on first save. This avoids ambiguous nested JSON merge behavior and supports optional preference setup.

Proposed version-1 normalized shape:

```json
{
  "preferred_styles": [],
  "preferred_colors": [],
  "avoided_colors": [],
  "dressiness": null,
  "garment_types": {
    "prefer": [],
    "avoid": []
  },
  "garment_attributes": {
    "sleeve_length": {
      "prefer": ["long"],
      "avoid": ["sleeveless"]
    }
  }
}
```

The default shape uses empty sleeve-length arrays too. Garment-type entries use the centralized subtype codes; preference attribute values use the same controlled attribute vocabulary as garments. `dressiness` is a nullable controlled text value on the casual-to-dressed-up dimension; its exact labels remain open, and it is not an arbitrary numeric fashion score.

Only explicitly supported dimensions are accepted. Sleeve length is confirmed for MVP; do not accept arbitrary keys, executable predicates, or rules against every column. Validate array elements, normalize duplicates, and reject the same value appearing in both prefer and avoid for a dimension. This is input consistency, not a change in recommendation priority.

These values are strong defaults or ranking signals. A current request can override them without modifying the saved profile. Unknown garment attributes are not automatically evidence of a preference match or avoidance violation. Absence of preferences must remain useful behavior. Learned preference signals are separate future data, never silently merged into user-authored settings.

## 7. `wear_events` and `wear_event_items`

### `wear_events` columns

| Column | PostgreSQL type | Nullable | Default / source | Meaning |
|---|---|---|---|---|
| `id` | `UUID` | No | Application-generated | Confirmation identity |
| `user_id` | `UUID` | No | Verified owner | FK to managed identity |
| `worn_at` | `TIMESTAMPTZ` | No | `now()` | Instant of “Wear this” confirmation |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Persistence timestamp |

Primary key: `id`. There is no recommendation FK, scheduled date, occasion-history requirement, weather payload, score, or stored explanation. `worn_at` records the confirmation instant in MVP, not proof of actual physical wear. Historical date correction/backdating APIs are deferred; no client timezone or editable date is required now.

### `wear_event_items` columns

| Column | PostgreSQL type | Nullable | Default / source | Meaning |
|---|---|---|---|---|
| `id` | `UUID` | No | Application-generated | Historical item-row identity |
| `wear_event_id` | `UUID` | No | Parent event | FK to `wear_events(id)` |
| `role` | `TEXT` | No | Validated composition | `top`, `bottom`, `shoes`, `outerwear` |
| `garment_id` | `UUID` | Yes | Live garment at creation | FK to `garments(id)` |
| `garment_snapshot` | `JSONB` | No | Server-generated canonical snapshot | Description at confirmation |

Database constraints:

- Primary key on `id`.
- Event FK uses `ON DELETE CASCADE`; deleting an event removes its item rows.
- Garment FK uses `ON DELETE SET NULL`; deleting a garment retains the item row and snapshot.
- `role` CHECK permits only the four MVP roles.
- Unique `(wear_event_id, role)` prevents multiple items in the same role.
- Unique `(wear_event_id, garment_id)` prevents repeating a live garment within an event. Ordinary PostgreSQL uniqueness permits multiple null references after deletion.
- `garment_snapshot` must be a JSON object.

The nullable garment FK supports deletion history; new item rows must contain a valid live garment ID. A database CHECK requiring the FK to remain non-null would defeat `ON DELETE SET NULL`.

### Composition and write transaction

A composition consists of role/garment-ID pairs:

```json
{
  "items": [
    { "role": "top", "garment_id": "<owned UUID>" },
    { "role": "bottom", "garment_id": "<owned UUID>" },
    { "role": "shoes", "garment_id": "<owned UUID>" }
  ]
}
```

`OutfitPolicy` requires exactly one top, bottom, and shoes item, with zero or one outerwear item. No duplicate garments are allowed, and each category must match its role. Role-based rows allow future structural changes without spreading permanent `top_id`/`bottom_id` columns through services; they do not enable future categories in MVP.

Only “Wear this” writes history. FastAPI loads all submitted IDs scoped to the authenticated user, validates current active/available state and composition policy, creates snapshots from canonical data, and inserts the event and all items in one database transaction. Never accept client-authored snapshots or trust a previously displayed recommendation to remain eligible.

Use a transaction/concurrency strategy that keeps loaded garments stable through validation and snapshot insertion, such as locking the selected garment rows until commit. Ownership, role/category agreement, minimum item counts, and current eligibility are service invariants, not properties a simple FK or per-row CHECK can enforce. Failed validation rolls back the entire event; no partial history is permitted.

Generating, viewing, changing, or retrying a recommendation creates no wear event. Repeated legitimate confirmations of the same combination are allowed. Do not add uniqueness on user/date or composition. Duplicate submission and HTTP retry/idempotency behavior must be resolved during endpoint implementation; do not silently assume repeated requests represent distinct wear.

### Historical snapshot contract

A snapshot has `schema_version: 1` and captures `category`, `garment_type`, `primary_color`, `secondary_colors`, `pattern`, `formality`, `style_tags`, `warmth`, `material`, `sleeve_length`, `neckline`, and `fit` from canonical fields at confirmation. Preserve optional nulls and empty arrays. The item row already contains its historical role.

Exclude notes, custom organizational tags, favorite/availability flags, AI proposals, owner/auth data, storage keys, signed URLs, and image bytes. These do not belong in the historical garment description. JSON shape/version validation is performed by the application.

Snapshots are not refreshed when garments are edited. Historical descriptions should render from snapshots; live `garment_id` enables navigation and recent-use aggregation while the garment exists. Deleted garments cannot be navigated to or selected again. Their removed images are not promised to remain visible; use a placeholder and snapshot description. No duplicated historical image storage is required.

Recent-wear summaries derive from events and live garment references/compositions. They remain soft diversity signals; no persisted cooldown, wear counter, last-worn column, or ranking weight is needed.

## 8. Deletion and history semantics

Garment deletion is a hard deletion of the live row. PostgreSQL sets its historical item references to null and retains snapshots. Editing a garment affects future recommendations and confirmations, not historical descriptions. Deleting a draft follows the same live-row/storage cleanup principle, without requiring history.

The application must also arrange removal of the original private object. Database deletion and storage deletion are not atomic. Final ordering, retry handling, and where cleanup information is retained remain implementation decisions; preserve the key needed for recovery before losing the row. Do not add a queue, outbox, or deletion-jobs table without a demonstrated need. A failed partial deletion must be handled explicitly, not reported as complete cleanup.

Auth-account cascades remove preferences, garments, and wear history; they do not retain anonymized snapshots or remove storage objects automatically. If account deletion becomes an exposed workflow, coordinate storage cleanup deliberately. Retention/compliance policy and draft-cleanup windows are not frozen here.

History editing/deletion endpoints are deferred. The event-to-item cascade defines database integrity for maintenance/account deletion without implying a new user-facing history feature.

## 9. Indexes and query patterns

| Index | Definition / purpose | MVP decision |
|---|---|---|
| Entity primary keys | UUID lookup; preference owner lookup | Required |
| `ix_garments_user_status_category` | `(user_id, status, category)` for owned lists, including unavailable active garments | Required |
| `ix_garments_active_available_user_category` | `(user_id, category)` WHERE `status = 'active' AND is_available = true` | Required for candidates and starter counts |
| `ix_wear_events_user_worn_at` | `(user_id, worn_at DESC, id DESC)` | Required for owned newest-first history and recent-use loading |
| Unique event/role | `(wear_event_id, role)` | Required integrity; also supports loading event items |
| Unique event/garment | `(wear_event_id, garment_id)` | Required integrity for live items |
| `ix_wear_event_items_garment_id` | `(garment_id)` | Required for garment-use lookup and FK deletion work |
| Unique image key | `(image_key)` WHERE `image_key IS NOT NULL` | Optional defensive index if keys identify one object in the configured original-image namespace |

The image-key uniqueness option protects accidental object sharing, not duplicate-looking clothing; two physical garments can have identical metadata. Resolve its namespace assumption before the initial migration if choosing to enable it.

PostgreSQL does not automatically index referencing FK columns. The listed owner/event indexes cover those access paths; the separate garment-ID index is needed because event-leading indexes do not serve garment-leading lookup efficiently.

Category, primary-color, type, and availability filtering can initially run within the owner's small wardrobe. Add targeted composite indexes only when observed query plans justify them. Do not add speculative GIN indexes to arrays/JSONB, full-text indexes, embeddings, or indexes on every attribute. Preferences and proposals are loaded with their owner/garment, not searched as arbitrary JSON documents.

## 10. Durable entities and temporary value objects

| Concept | Persistence | Boundary |
|---|---|---|
| `Garment` | `garments` plus private original object | Owned physical wardrobe item |
| `PreferenceProfile` | Optional `user_preferences` row | Explicit saved choices |
| `WearEvent` / `WearEventItem` | Event and snapshot rows | Confirmed history |
| `OutfitComposition` | Value object; item rows only when worn | Role-based selection and validation |
| `RecommendationContext` | Request memory | Canonical candidates, occasion, original request, build-around ID, preferences, weather, recent wear, prior exclusions |
| `RecommendationResult` / internal `RecommendationDecision` | Request response / frontend state | Outcomes, compositions, explanations, warnings, interpretation |
| `WeatherContext` | Request memory | Normalized conditions with explicit units |
| Location coordinates | Request memory | Optional permitted weather lookup |
| Signed image URLs | Short-lived response values | Authorized display/upload access |

Recommendation context excludes auth identities/tokens, storage paths, images, AI proposals, notes, and implicit custom-tag rules. Temporary “Try another” exclusions are bounded compositions in request/session state, not permanent dislikes. A conflict or no-suitable-outfit outcome creates no durable record.

## 11. SQLAlchemy, Pydantic, and provider schema separation

SQLAlchemy models describe persistence: columns, keys, nullability, relationships, and database constraints. Configure relationship deletion behavior to preserve the database's `ON DELETE SET NULL` history rule; deleting a garment must never cascade-delete wear items through the ORM.

Pydantic request/response models describe API contracts and validated domain values. Draft, confirmation, edit, preference, composition, snapshot, and analysis contracts have different requirements. Do not expose a single unrestricted ORM-shaped payload that allows clients to set ownership, timestamps, provenance, or lifecycle state.

Provider schemas describe external model input/output and remain behind adapters. Normalize provider names and values into controlled FitFindr schemas, validate them, then persist a proposal or validate a recommendation. SDK responses are not database entities. Provider restrictions may require a different wire shape; that must not dictate canonical column names or overwrite user truth.

Domain policy owns lifecycle transitions, attribute applicability, preference semantics, and outfit structure. Database checks backstop stable row invariants. Service transactions enforce relationships and current state. Keep these responsibilities explicit without duplicating subjective fashion scoring in SQL.

## 12. Migration principles

1. Create only the four core application tables and their documented keys/checks/indexes. Reference managed auth; do not migrate its internals or introduce a profile table.
2. Use explicit, consistently named constraints so Alembic changes and errors are understandable. Review generated migrations, especially checks, partial indexes, arrays, JSONB, and cross-schema FKs.
3. Match PostgreSQL nullability and server defaults to this design; Python defaults alone do not protect other database writers. Ensure update timestamps are maintained by application writes.
4. Use TEXT/check category and role codes. Adding categories later requires intentional product/policy updates and check migrations; avoiding PostgreSQL enums reduces enum-specific migration friction, not all migration work.
5. Prefer additive changes: add nullable columns or new versioned JSON keys, deploy compatible readers/writers, backfill if needed, and only then tighten constraints. Existing snapshots keep their historical schema version.
6. Keep JSONB contracts versioned. Validate older stored shapes through deliberate compatibility or migration logic; changing a Pydantic class does not migrate stored documents automatically.
7. Apply migrations deliberately with suitable auth-schema privileges and environment isolation. Do not run competing migrations at each application startup or make undocumented production dashboard changes.
8. Before destructive migrations, plan backup/recovery and assess data loss; coordinate releases because frontend and backend deploy separately.

Implementation verification should cover active-row checks, tenant isolation, preference validation, valid event composition, atomic snapshot writes, edits preserving history, garment deletion retaining snapshots, and event/account cascades. These are substantive domain/integrity checks; no live paid model calls are needed to verify the schema.

## 13. Main choices and tradeoffs

| Choice | Reason | Cost / limit |
|---|---|---|
| Relational canonical columns | Clear invariants and common wardrobe filters | New stable attributes may need migrations |
| Arrays for colors and tags | Simple bounded multi-value attributes on one garment | Poor fit for future rich tag entities or complex cross-user analytics |
| JSONB proposals | Preserves normalized nested analysis without provider-specific tables | Requires contract validation/versioning; not an audit history |
| JSONB controlled preferences | Small nested configuration can grow additively | Database object checks cannot validate full semantics |
| Nullable draft attributes with active check | One garment identity spans upload and review | Confirmation and edits must enforce stronger active rules |
| Separate availability boolean | Temporary exclusion does not remove wardrobe identity | It is not laundry tracking or archive lifecycle |
| Role-based wear items | Reuses composition policy and supports additive structure later | Complete composition and ownership require transactional service checks |
| Nullable FK plus snapshot | Retains truthful history after edits/deletion | Deleted images disappear; snapshots duplicate selected metadata intentionally |
| Direct managed-auth FK | Referential integrity without duplicating profiles | Couples stored identities and migrations to selected auth topology |
| Ephemeral recommendations/weather | Avoids collecting data the MVP does not need | No durable recommendation analytics, replay, or richer feedback yet |

## 14. Future additive entities and explicitly deferred tables

Future entities require product approval and their own schema design; names below describe extension points, not tables to create now.

- **Saved outfits:** possible `saved_outfits` and role-based item rows for user-saved combinations. Keep them distinct from factual wear events and decide their deletion/reference behavior when the feature is specified.
- **Catalog products:** a separate `CatalogProduct` domain for retailer inventory, price, links, stock, and sizing. A purchasable item is not an owned `Garment`; do not mix catalog IDs into current wear-item FKs.
- **Collections:** possible owned collections and membership rows if organization requirements justify them. Current custom tags do not require collection tables.
- **Learned preference signals:** separate records from explicit preferences, with provenance and evaluation appropriate to future learning. Do not reinterpret “Try another” as a persisted dislike today.

Also deferred:

| Tables / data | Why deferred |
|---|---|
| App users/profiles, passwords, sessions, refresh tokens | Managed auth supplies identity; no app profile fields needed |
| Recommendation runs, sessions, results, permanent exclusions | Current results are ephemeral; richer feedback/analytics is outside MVP |
| Analysis runs or per-field edit audit | Only latest proposal/provenance is agreed |
| Weather, locations, permission-history records | Location/weather are temporary; weather is optional |
| Taxonomy lookup tables and normalized tag/color joins | Central application vocabularies and arrays meet current needs |
| Image assets/variants table | One original image key suffices; derivatives are deferred |
| Jobs, queues, outbox, cleanup task tables | Synchronous workflows and bounded application recovery first |
| Planning/calendar/travel records | Future planning has no current persistence requirement |
| Laundry, seasons, archives, purchase/price/receipt records | Outside current product scope |
| Embeddings/vector retrieval, fashion-score tables | No current retrieval requirement or justified objective fashion score |

## 15. Decisions intentionally left open

The schema above fixes the core persistence shape. It intentionally does not freeze:

- Full garment subtype, color, style, formality, warmth, material, neckline, fit, and sleeve-length vocabularies; subtype/category and attribute validation must be centralized before those contracts ship.
- Preference-capable attributes beyond sleeve length and final dressiness labels.
- Final occasion labels, recent-wear windows/weights, or recommendation ranking weights; these are not database columns here.
- AI provider/model, final provider wire schemas, weather provider/normalization details, timeout values, supported image formats, and media limits.
- Same-draft image replacement versus another draft, persistent derivatives, cleanup ordering/recovery, abandoned-draft retention, and optional image-key uniqueness.
- Wear-confirmation write retry/idempotency details; resolve before the endpoint permits retryable writes.
- Future history corrections, richer account/profile needs, and account-deletion retention/UX policies.

Resolve implementation blockers explicitly when implementing their boundary. Do not turn an open product choice into a hidden migration assumption.

## 16. Interview explanation

> PostgreSQL stores owned garments, optional explicit preferences, and confirmed wear history. A garment can be an incomplete draft, but an active garment must have a verified image and reviewed category, type, and primary color. Availability is separate so users can exclude clothing without deleting it. AI suggestions stay in a latest-proposal JSON document; recommendations use the user's canonical values. “Wear this” validates a role-based composition and records snapshots in one transaction. If a garment is later edited or deleted, the historical description stays intact. Managed auth supplies identity, and FastAPI enforces ownership. Recommendations and weather stay temporary because the MVP does not need durable records for them yet.
