# Tóm tắt kế hoạch 3 tuần — Test Data & Ground Truth cho AI Camera an ninh vành đai

> Bản rút gọn của `ke-hoach-3-tuan-kiem-thu-ai-camera.md`, dùng để trao đổi nhanh với mentor/stakeholder và onboard người mới.

---

## 1. Mục tiêu sau 3 tuần

Nhóm 3 người xây dựng được **quy trình** và **bộ dữ liệu test v1** cho AI Camera an ninh vành đai:

```text
Raw video → Kiểm kê → Candidate mining → Lấy mẫu → Human review
→ Ground truth → Tính KPI → Golden set → Bàn giao
```

Kết quả không chỉ là clip đã gán nhãn, mà là **quy trình tái sử dụng được** khi có camera mới hoặc model phiên bản mới.

---

## 2. Phạm vi kiểm thử

Ba nhóm bài toán chính:

### Trèo rào / xâm nhập

| ROI | Hành vi | Cấp độ |
|---|---|---|
| Xanh | Lảng vảng gần hàng rào | Cấp 4 |
| Vàng | Tiếp cận / chạm sát hàng rào | Cấp 2–3 |
| Đỏ | Trèo, vượt rào hoặc vào khu cấm | Cấp 1 |

### Che camera

- Che một phần hoặc toàn phần.
- Phải phân biệt được với: mưa lớn, sương/nước, chói đèn xe, thiếu sáng, mất hình, video freeze.

### Rung lắc / xoay camera

- Rung ngắn do môi trường (không phải event).
- Camera bị lệch/xoay hướng kéo dài (là event).
- ROI bị lệch khỏi khu vực thực tế.

> **ROI đã được cấu hình sẵn.** Team không vẽ hoặc sửa ROI, chỉ lưu `roi_config_id` / phiên bản / snapshot làm bằng chứng.

---

## 3. KPI

Áp dụng **riêng cho từng nhóm**: trèo rào, xoay camera, che camera.

| KPI | Ngưỡng |
|---|---:|
| Recall | ≥ 90% |
| Precision | ≥ 90% |
| Tỷ lệ báo động giả | ≤ 10% |

### Khái niệm

| Ký hiệu | Nghĩa |
|---|---|
| TP | Có sự kiện và hệ thống báo đúng |
| FP | Hệ thống báo nhưng thực tế không có sự kiện, hoặc báo sai loại |
| FN | Có sự kiện nhưng hệ thống không báo |
| TN | Không có sự kiện và hệ thống không báo |

### Công thức

```text
Precision          = TP / (TP + FP)
Recall             = TP / (TP + FN)
Tỷ lệ báo động giả = FP / (TP + FP)
```

> **Lưu ý:** chỉ số "tỷ lệ báo động giả" được giao có **cùng mẫu số với Precision**, nên về bản chất là `1 - Precision`. Cần hỏi lại mentor cách gọi/báo cáo để tránh nhầm với false-positive rate chuẩn `FP/(FP+TN)`.

---

## 4. Phân công nhân sự

| Người | Vai trò chính |
|---|---|
| **A** | QA Lead / Test Design — làm rõ yêu cầu, use case, KPI, pass/fail, coverage, rủi ro, báo cáo và bàn giao |
| **B** | Data & Automation — kiểm kê video, kiểm tra lỗi/trùng/lệch dữ liệu, candidate mining, proxy clip, manifest, versioning |
| **C** | Annotation & Data Quality — guideline nhãn, review video, gán nhãn, agreement, xử lý nhãn mâu thuẫn, ground truth / golden set |

A và B cũng tham gia gán nhãn một phần để có **review chéo**; C chịu trách nhiệm cuối về chất lượng nhãn.

---

## 5. Câu hỏi phải chốt trong Tuần 1

Phần lớn câu hỏi phải hỏi ngay Tuần 1, **trước khi xử lý dữ liệu lớn**.

**Về đối tượng và severity**
- Chỉ phát hiện người hay gồm xe, động vật, nhân viên?
- Cấp 2 khác Cấp 3 thế nào?

**Về event boundary**
- Khi nào một event bắt đầu / kết thúc?
- Người trèo lên rào rồi quay xuống có tính Cấp 1 không?
- Xanh → Vàng → Đỏ là một incident hay nhiều alert?
- Có cooldown / chống alert trùng không?

**Về che camera và rung lắc**
- Che bao nhiêu phần trăm, trong bao lâu thì phải alert?
- Mưa, chói đèn xe, mất hình, video freeze là tamper hay camera-health?
- Rung / xoay camera đến ngưỡng nào mới tính là event?

**Về KPI và dữ liệu**
- Cách tính TP/FP/FN khi alert sai loại hoặc alert trùng?
- AI team có danh sách data đã train để kiểm tra leakage không?
- Ai phê duyệt pass/fail và xử lý case nhãn mâu thuẫn?

> Nếu chưa có câu trả lời: ghi là **assumption** hoặc **blocker**, không tự hiểu theo ý nhóm.

---

## 6. Nội dung từng tuần

### Tuần 1 — Chốt nghiệp vụ và chuẩn bị

- Họp kickoff, hỏi mentor/stakeholder.
- Chốt use case, severity, event boundary, KPI / pass-fail.
- Kiểm tra quyền truy cập video/log/tool/ROI evidence.
- Thiết kế metadata, labeling guideline nháp, pipeline và manifest.
- Chạy dry-run tối thiểu 1 case intrusion, 1 cover, 1 movement.

**Điều kiện qua Tuần 2:** rule đủ rõ để gán nhãn và lấy được evidence từ hệ thống.

### Tuần 2 — Từ raw video thành annotation queue

- B kiểm kê video: FPS, resolution, codec, timestamp, file hỏng, duplicate.
- Kiểm tra data leakage với tập train nếu AI team cung cấp.
- Dùng tool tìm candidate event và cắt proxy clip.
- Lấy mẫu từ 3 nguồn:

| Luồng | Tỷ lệ |
|---|---:|
| Tool-selected candidate | 70% |
| Random background | 20% |
| Risk-based (đêm, mưa, glare, rung, che một phần…) | 10% |

- C review nhanh candidate; A kiểm tra coverage.

> **Lưu ý:** output của tool chỉ là *candidate*, không phải ground truth.

### Tuần 3 — Annotation, ground truth, KPI, bàn giao

- A/B/C cùng calibration trên tập clip nhỏ.
- Gán nhãn chính thức: A 25%, B 25%, C 50%.
- 10–20% clip được hai người gán độc lập để đo agreement.
- Xử lý disagreement, khóa ground truth.
- Tạo benchmark set, production-distribution set, golden set.
- Tính TP/FP/FN/TN và KPI cho từng nhóm.
- Hoàn thiện dataset card, guideline, manifest, coverage report và biên bản bàn giao.

---

## 7. Nguyên tắc chất lượng

- Không dùng video/candidate từ tool làm nhãn cuối tự động.
- Không để video gần trùng hoặc cùng nguồn xuất hiện lẫn giữa các tập độc lập.
- Không đưa clip `ambiguous` hoặc `invalid` vào golden set / KPI chính thức.
- Luôn lưu evidence: video, timestamp, camera ID, ROI version, alert/log, expected/actual result.
- Nếu thiếu data hoặc chưa xác minh leakage → kết luận **"Chưa kết luận"**, không phải **"Đạt"**.
- Golden set phải **nhỏ nhưng nhãn chất lượng cao**, review kỹ, không dùng để train.
