# Labeling Guideline

## intrusion_loitering

### Definition

Doi tuong lang vang gan hang rao trong vung theo doi.

### Positive Examples

- Dung/di lai gan hang rao du lau theo rule nghiep vu.

### Negative Examples

- Di ngang qua ngoai ROI.

### Boundary Rule

Bat dau khi doi tuong vao vung theo doi, ket thuc khi roi vung hoac het hanh vi.

## intrusion_approach

### Definition

Doi tuong tiep can hoac cham sat hang rao.

## intrusion_crossing

### Definition

Doi tuong treo, vuot rao hoac vao khu cam.

## camera_cover

### Definition

Camera bi che mot phan hoac toan phan.

## camera_movement

### Definition

Camera rung, xoay hoac lech goc keo dai.

## background

### Definition

Khong co event trong clip.

## ambiguous

Dung khi khong du bang chung de xac nhan hoac reject.

## invalid

Dung khi clip hong, thieu context nghiem trong hoac khong xem duoc.

## Reviewer Notes

- Khong suy doan hanh vi ngoai hinh anh quan sat duoc.
- Dung `needs_review` khi can nguoi thu hai xem lai.
- Reject candidate khi candidate khong co event theo guideline.
