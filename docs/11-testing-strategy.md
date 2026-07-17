# Testing Strategy

## Unit Test

- Sinh sample ID.
- Clamp timestamp.
- Tinh duration.
- Random background.
- Schema loader.
- Annotation validator.

## Integration Test

- Mot video -> inventory.
- Mot video -> clips.
- Mot video -> manifest.
- Manifest -> annotation tool.
- Annotation -> export.
- Export -> coverage report.

## Contract Test

- Candidate manifest sample validate.
- Annotation export sample validate.
- Invalid fixture bi reject.
- Schema backward compatibility.

## End-to-end Test

```text
Sample video -> candidate mining -> manifest -> annotation fixture
-> export -> validation -> coverage report
```
