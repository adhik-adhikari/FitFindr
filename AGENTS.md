# FitFindr Development Guidelines

Before implementing features, read:

- `docs/product.md`
- `docs/architecture.md`
- `docs/data-model.md`

These documents define the current product scope, system architecture, and persistence design.

## Development principles

- Build incrementally in small, focused changes.
- Keep changes scoped to the requested feature.
- Avoid unrelated refactors.
- Prefer simple, conventional implementations over unnecessary abstractions.
- Do not add dependencies without a clear product or engineering need.
- Preserve the architecture boundaries defined in the documentation.
- Do not implement deferred roadmap features unless explicitly requested.

## Testing

- Add or update tests for implemented behavior.
- Run the relevant tests after changes.
- Keep deterministic tests separate from live AI-provider evaluation.

## AI behavior

- Treat model output as proposed data, not trusted truth.
- Validate structured AI output before persistence.
- Preserve the user confirmation and correction flow for garment analysis.
- Do not fabricate uncertain garment attributes.
- Keep deterministic business rules separate from probabilistic AI behavior where practical.

## Data and security

- Enforce user ownership on backend operations.
- Do not trust client-supplied ownership identifiers.
- Do not expose privileged credentials or provider secrets to the frontend.
- Keep private garment images protected by the storage and authorization boundaries defined in the architecture.

## Git and scope

- Keep changes logically scoped.
- Do not create commits unless explicitly requested.
- Avoid combining unrelated features in one change.