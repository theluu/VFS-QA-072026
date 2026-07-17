# Business Requirements

## Problem

Can tao quy trinh tai lap de chuan bi du lieu test AI Camera an ninh vanh dai.

## Users

- B tao candidate queue tu video.
- C review va gan nhan.
- A/B dung annotation export de danh gia coverage va artifact.

## B -> C

Input: raw video, candidate event JSON, config.

Output: inventory, proxy clips, candidate manifest.

## C -> A/B

Input: candidate manifest va proxy clips.

Output: annotation export co `sample_id`, label, boundary, status, reviewer va comment.

## KPI Business

Precision, recall va false alarm chi duoc tinh khi co predicted alert va ground truth tuong ung. Neu chua co predicted alert, chi bao cao coverage va annotation completion.

## Human Intervention

Con nguoi bat buoc can thi khi:

- Candidate mieu ta hanh vi khong ro.
- Clip thieu context.
- Event boundary tranh cai.
- Label chua co trong taxonomy.
- Candidate co du lieu nhay cam can xu ly.

## Open Questions

- Candidate events se den tu detector, log alert hay file timestamp thu cong?
- Definition cu the cho cap 2 va cap 3 la gi?
- Cooldown/trung alert duoc tinh nhu the nao?
