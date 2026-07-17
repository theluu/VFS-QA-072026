# AGENTS.md

## Project mission

Xay dung POC phuc vu quy trinh:

1. Nhan video dau vao.
2. Khai pha candidate clips.
3. Sinh candidate manifest theo JSON Schema.
4. Cho phep con nguoi xem va gan nhan.
5. Export annotation co the kiem tra va tai lap.
6. Sinh coverage report va dataset card.

## Required reading order

Truoc khi sua code, phai doc:

1. PROJECT.md
2. docs/00-current-state.md
3. docs/01-business-requirements.md
4. docs/02-scope-and-non-goals.md
5. docs/05-data-contracts.md
6. ACCEPTANCE_CRITERIA.md
7. PLANS.md
8. TASKS.md
9. AGENTS.md gan nhat trong thu muc dang sua

## Source of truth

- JSON Schema la nguon chuan cho format du lieu.
- PROJECT.md la nguon chuan cho muc tieu du an.
- ACCEPTANCE_CRITERIA.md la nguon chuan de xac dinh hoan thanh.
- DECISIONS.md la nguon chuan cho cac quyet dinh ky thuat da chot.
- TASKS.md la nguon chuan cho trang thai cong viec hien tai.

## Non-negotiable rules

- Khong thay doi schema ma khong cap nhat schema version.
- Khong thay doi schema ma khong cap nhat sample JSON va test.
- sample_id phai duy nhat, on dinh va co the tai tao.
- Khong dung ten file ngau nhien lam sample_id.
- Khong ghi de video goc trong data/raw.
- Khong commit video that hoac du lieu nhay cam vao Git.
- Tat ca duong dan luu trong manifest phai la duong dan tuong doi.
- Timestamp phai dung integer millisecond.
- start_ms phai nho hon end_ms.
- end_ms khong duoc vuot qua duration_ms cua video nguon.
- Moi qua trinh random sampling phai nhan random_seed.
- Khong hard-code event label trong giao dien.
- Event label phai duoc doc tu config.
- Khong tu them service ngoai pham vi POC.
- Khong refactor ngoai pham vi task hien tai.
- Khong danh dau task hoan thanh neu chua chay validation va test.
- Khong bo qua loi bang try/except rong.
- Khong tao du lieu gia ma khong danh dau ro la sample hoac fixture.

## Implementation workflow

Voi moi task:

1. Doc tai lieu lien quan.
2. Kiem tra dependency cua task.
3. Ghi ke hoach ngan vao TASKS.md.
4. Thuc hien thay doi nho nhat dap ung yeu cau.
5. Them hoac cap nhat test.
6. Chay lint, unit test va schema validation.
7. Kiem tra output thuc te.
8. Cap nhat TASKS.md.
9. Cap nhat CHANGELOG.md.
10. Cap nhat DECISIONS.md neu co quyet dinh kien truc.

## Required quality checks

Sau khi bootstrap hoan thanh, phai chay:

```bash
make lint
make test
make validate-schemas
make validate-samples
```

## Definition of done

Mot task chi duoc hoan thanh khi:

- Code chay duoc.
- Co test cho logic chinh.
- Khong pha schema hien tai.
- Sample JSON validate thanh cong.
- Tai lieu lien quan da duoc cap nhat.
- Co command tai hien ket qua.
- Khong con placeholder hoac TODO khong duoc ghi nhan.
- Output duoc ghi dung thu muc outputs/.
- TASKS.md co evidence ve test da chay.

## Forbidden actions

- Khong xoa du lieu trong data/raw.
- Khong sua video nguon.
- Khong thay doi sample_id da phat hanh.
- Khong doi ten field schema tuy y.
- Khong tao output ben ngoai outputs/.
- Khong commit secrets, token hoac duong dan may ca nhan.
- Khong danh dau PASS khi command kiem thu chua duoc chay.
