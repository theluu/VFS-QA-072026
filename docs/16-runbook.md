# Runbook

## Setup

```bash
make setup
```

Muc dich: cai Python va frontend dependencies.

## Lint

```bash
make lint
```

Muc dich: compile Python va check Markdown links.

## Test

```bash
make test
```

Muc dich: chay unit va contract tests.

## Validate Schemas

```bash
make validate-schemas
```

Muc dich: kiem tra JSON Schema files co field bat buoc.

## Validate Samples

```bash
make validate-samples
```

Muc dich: validate sample JSON va invalid fixtures.

## Candidate Mining

```bash
make candidate-mining INPUT=data/raw/sample.mp4 EVENTS=data/samples/candidate-events.sample.json
```

Output: `outputs/runs/{RUN_ID}/`.

## Annotation Tool

```bash
make annotation-api
make annotation-tool
```

Backend chay port 8000, frontend chay port 5173.

Neu port mac dinh dang ban:

```bash
make annotation-api API_PORT=8020
make annotation-tool API_PORT=8020 API_BASE=http://127.0.0.1:8020 FRONTEND_PORT=5175
```

Backend URL: `http://127.0.0.1:{API_PORT}`.

Frontend URL: `http://127.0.0.1:{FRONTEND_PORT}`.

## Frontend Security Audit

```bash
npm audit --prefix apps/annotation-tool/frontend
```

Muc dich: kiem tra vulnerabilities cua React/Vite dependencies.

## Coverage Report

```bash
make coverage-report
```

Output: `outputs/reports/coverage-report.json`.

## Release

```bash
make release
```

Output: `outputs/releases/v0.1.0/`.
