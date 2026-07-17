# Tasks

## P0-001 - Initialize repository skeleton

Status: DONE

Priority: Critical

Dependencies: None

Files:

- `.git/`
- `.gitignore`
- top-level Markdown files
- app/data/output/docs folders

Acceptance:

- `git status` chay thanh cong.
- Cac thu muc trong plan ton tai.
- Khong commit video va output sinh tu dong.

Validation:

```bash
git status
make lint
make test
```

Evidence:

- Git repository initialized.
- Skeleton and docs created.

## P1-001 - Define data contracts

Status: DONE

Priority: Critical

Dependencies: P0-001

Files:

- `shared/schemas/*.schema.json`
- `data/samples/*.json`
- `tests/fixtures/invalid/*.json`
- `scripts/validate_json.py`

Acceptance:

- Schema co version.
- Sample JSON hop le.
- Invalid fixtures bi reject.
- Timestamp dung integer millisecond.

Validation:

```bash
make validate-schemas
make validate-samples
make test
```

Evidence:

- Validation script and tests added.

## P2-001 - Candidate mining POC

Status: DONE

Priority: High

Dependencies: P1-001

Files:

- `apps/candidate-mining/src/candidate_mining/`
- `apps/candidate-mining/README.md`

Acceptance:

- Co CLI nhan video va candidate events.
- Sinh inventory, clips, manifest va report.
- Random background dung seed.

Validation:

```bash
make test
```

Evidence:

- Unit tests cover boundary normalization, sample_id and background sampling.
- `make candidate-mining RUN_ID=local-dev` generated inventory, clips and manifest.
- Generated manifest validated with clip existence checks.

## P3-001 - Annotation API and UI POC

Status: DONE

Priority: High

Dependencies: P1-001

Files:

- `apps/annotation-tool/backend/src/annotation_api/`
- `apps/annotation-tool/frontend/`

Acceptance:

- Backend load/validate manifest.
- UI hien thi clip metadata va form gan nhan.
- Export annotation dung schema.

Validation:

```bash
make test
```

Evidence:

- Annotation export tests added.
- FastAPI TestClient integration tests cover health/config/manifest/export success and validation failure.
- React build passes with Vite 8.1.5.

## P4-001 - Validation and coverage reporting

Status: DONE

Priority: High

Dependencies: P1-001

Files:

- `scripts/validate_dataset.py`
- `scripts/coverage_report.py`
- `tests/test_reporting_release.py`

Acceptance:

- Dataset validator checks manifest and annotation relationship.
- Coverage report validates against schema.
- Tests cover coverage report generation.

Validation:

```bash
make validate-dataset
make coverage-report
make test
```

Evidence:

- `make validate-dataset` passed.
- `make coverage-report` wrote `outputs/reports/coverage-report.json`.
- `make test` passed 14 tests.

## P5-001 - Local release package

Status: DONE

Priority: Medium

Dependencies: P4-001

Files:

- `scripts/release.py`
- `outputs/releases/v0.1.0/`

Acceptance:

- Release package includes manifest, annotation export, coverage report, dataset card, checklist, checksums and release notes.

Validation:

```bash
make release
```

Evidence:

- `make release` wrote `outputs/releases/v0.1.0/`.
- Release script is covered by unit test using a temporary output directory.

## SEC-001 - Frontend dependency audit

Status: DONE

Priority: High

Dependencies: P3-001

Files:

- `apps/annotation-tool/frontend/package.json`
- `apps/annotation-tool/frontend/package-lock.json`

Acceptance:

- `npm audit` reports zero vulnerabilities.
- React production build still passes.

Validation:

```bash
npm audit --json
npm run build
```

Evidence:

- Upgraded Vite to 8.1.5 and `@vitejs/plugin-react` to 6.0.3.
- `npm audit --json` reports total vulnerabilities = 0.
- `npm run build` passes.
