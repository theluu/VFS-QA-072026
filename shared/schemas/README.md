# Schemas

## Current Version

`1.0.0`

## Files

| Schema | Producer | Consumer |
|---|---|---|
| `candidate-manifest.schema.json` | candidate-mining | annotation-tool, validator |
| `annotation-export.schema.json` | annotation-tool | validator, A/B downstream |
| `coverage-report.schema.json` | reporting script | project team |

## Compatibility Rules

- Breaking change tang major version.
- Them field optional tang minor version.
- Sua description khong doi version.
- Sample JSON va tests phai cap nhat cung schema.

## Validate

```bash
make validate-schemas
make validate-samples
```
