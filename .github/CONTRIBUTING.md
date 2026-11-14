# Contributing to MODVIIRS

Read the [complete contribution policy](../docs/CONTRIBUTING.md), [project context](../docs/README.md), and [agent instructions](../AGENTS.md) before making changes.

## Decisions and evidence

Discuss feature decisions with the project owner before implementing dependent changes. Critically assess alternatives and verify NASA-related claims using official NASA sources. Record evidence, limitations, and approved decisions in the project documentation. The contextual PDF is reference material, not implementation authorization.

## Commit convention

All commit descriptions must be written in **English**, preferably using an imperative verb.

```text
type: :gitmoji: description
```

Examples:

```text
docs: :memo: document NASA context and project guidelines
feat: :sparkles: add fire activity calendar
fix: :bug: correct acquisition time conversion
```

Use Conventional Commit types and literal gitmoji shortcodes. Breaking changes may use `type!: :gitmoji: description` with a `BREAKING CHANGE` explanation in the body.

When a feature is ready or a push is requested with pending changes, ask whether the owner wants a commit and present the proposed message and scope. Wait for approval unless that specific commit has already been explicitly authorized. A push request alone does not authorize creating a pending commit. Push only when explicitly requested or approved; do not rewrite history without specific authorization.

## Version history

The root [VERSION](../VERSION) file is the canonical project version in `X.Y.Z` format:

- X: major/heavy releases, including breaking changes; reset Y and Z.
- Y: new features; reset Z.
- Z: bug fixes and compatible corrections.

Confirm version changes with the owner. Documentation-only changes do not automatically increase the version. Record pending work and releases in [CHANGELOG.md](../CHANGELOG.md). Tags and releases require explicit authorization.
