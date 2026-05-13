# Analytics App — API Specification

**Base path:** `/api/v1/analytics/`  
**Auth:** All endpoints require `Authorization: Bearer <access_token>` (JWT).  
**Error format:** All errors follow `{ "success": false, "code": "...", "details": "..." }`.

---

## Role Access Matrix

| Endpoint | ADMIN | PRINCIPAL | TEACHER | STUDENT | PARENT |
|---|:---:|:---:|:---:|:---:|:---:|
| `GET/POST /exams/` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `POST /exams/<id>/upload/` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `GET /exams/<id>/overview/` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `GET /exams/<id>/subjects/<s>/questions/` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `GET /exams/<id>/subjects/<s>/questions/<n>/students/` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `GET /exams/<id>/sections/<sec>/` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `GET /exams/<id>/sections/<sec>/subjects/<s>/questions/` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `GET /exams/<id>/sections/<sec>/subjects/<s>/questions/<n>/students/` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `GET /student/<id>/exams/` | ✅ | ✅ | ✅ own section | ✅ own only | ✅ own child |
| `GET /student/<id>/` | ✅ | ✅ | ✅ own section | ✅ own only | ✅ own child |
| `GET /student/<id>/subject/<s>/` | ✅ | ✅ | ✅ own section | ✅ own only | ✅ own child |
| `GET /template/` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `POST /seed/` (DEBUG only) | ✅ | ✅ | ❌ | ❌ | ❌ |

---

## Common Error Codes

| HTTP | Code | When |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Missing required param |
| 400 | `ANALYTICS_VALIDATION_ERROR` | Analytics not DONE yet, or bad subject name |
| 400 | `CSV_STRUCTURE_ERROR` | CSV missing required columns |
| 401 | `AUTHENTICATION_FAILED` | Missing / expired token |
| 403 | `PERMISSION_DENIED` | Role not allowed, or cross-section/student access |
| 404 | `NOT_FOUND` | Exam / class / section / student not found |
| 404 | `EXAM_NOT_FOUND` | `exam_id` does not exist for this school |
| 404 | `STUDENT_NOT_FOUND` | `student_id` does not exist for this school |

---

## 1. Exam Management

### `GET /api/v1/analytics/exams/` — List Exams

Returns exams dynamically filtered by the authenticated user's role:
- **STUDENT:** Exams they have participated in.
- **TEACHER:** Exams belonging to classes/sections they teach.
- **PRINCIPAL/ADMIN:** All exams for the school.

Response `200`:
```json
{
  "success": true,
  "exams": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "exam_name": "Unit Test 1",
      "exam_date": "2026-04-15",
      "analytics_status": "DONE",
      "type": "CLASS"
    }
  ]
}
```

### `POST /api/v1/analytics/exams/` — Create Exam

**Content-Type:** `application/json`

**Request fields:**

| Field | Type | Required | Description |
|---|---|:---:|---|
| `exam_name` | string | ✅ | Name of the exam |
| `class_id` | UUID | one of | Creates a **class-level** exam — all sections of this class are included |
| `section_id` | UUID | one of | Creates a **section-level** exam — only this section is included |

Provide exactly one of `class_id` or `section_id`.

Request (class exam):
```json
{ "exam_name": "Unit Test 1", "class_id": "aaaa-..." }
```

Request (section exam):
```json
{ "exam_name": "Unit Test 1", "section_id": "bbbb-..." }
```

Response `201`:
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "exam_name": "Unit Test 1",
  "analytics_status": "CREATED",
  "academic_class": { "id": "...", "name": "Class 11" },
  "section": null,
  "created_at": "2026-05-12T10:00:00Z"
}
```

### `POST /api/v1/analytics/exams/{exam_id}/upload/` — Upload File

**Content-Type:** `multipart/form-data`  
Exam must be in `CREATED` status.

| Field | Type | Description |
|---|---|---|
| `csv_file` | File | CSV result file |
| `excel_file` | File | Excel rank-card file |
| `pdf_file` | File | PDF result file |

Response `202`: same as legacy upload response.

### `GET /api/v1/analytics/exams/{exam_id}/overview/` — Exam Overview (Unified)

This endpoint returns different data based on the authenticated user's role:

#### 1. Teacher & Principal View (`role_view: "STAFF"`)
- **Principals** receive details for all sections.
- **Teachers** receive details for *only* the sections assigned to them.

Response `200`:
```json
{
  "exam": {
    "id": "...", "exam_name": "Unit Test 1",
    "exam_date": "2026-04-15", "analytics_status": "DONE",
    "type": "CLASS"
  },
  "role_view": "STAFF",
  "class_avgs": [
    { "subject_id": "...", "subject_name": "MATHS",     "avg": 62.5, "max_marks": 80 }
  ],
  "sections": [
    { "section_id": "...", "section_name": "A", "avg": 64.2 }
  ],
  "top_students": [
    { "student_id": "...", "name": "Aarav Mehta", "student_ref_id": "S001", "total_marks": 148, "rank": 1 }
  ]
}
```

#### 2. Student View (`role_view: "STUDENT"`)
Students receive their personalized results and risk breakdown for the exam instead of class averages.

Response `200`:
```json
{
  "exam": {
    "id": "...", "exam_name": "Unit Test 1",
    "exam_date": "2026-04-15", "analytics_status": "DONE",
    "type": "CLASS"
  },
  "role_view": "STUDENT",
  "student_results": {
    "total_marks": 142,
    "overall_risk": "WATCH",
    "subjects": [
      {
        "subject_id": "...",
        "subject_name": "MATHS",
        "total_marks": 42,
        "max_marks": 80,
        "correct": 14,
        "wrong": 4,
        "unattempted": 2,
        "risk_label": "WATCH"
      }
    ]
  }
}
```

### `GET /api/v1/analytics/exams/{exam_id}/subjects/{subject_id}/questions/` — Class Question Stats

Response `200`:
```json
{
  "exam": { "id": "...", "exam_name": "Unit Test 1" },
  "subject": { "id": "...", "name": "MATHS" },
  "total_questions": 80,
  "questions": [
    { "q_no": 1, "correct_count": 18, "wrong_count": 3, "unattempted_count": 0, "difficulty_tag": "HARD", "difficulty_index": 85.7, "has_key_error": false }
  ]
}
```

### `GET /api/v1/analytics/exams/{exam_id}/subjects/{subject_id}/questions/{q_no}/students/` — Class Question Students

Response `200`:
```json
{
  "exam": { "id": "...", "exam_name": "Unit Test 1" },
  "subject": { "id": "...", "name": "MATHS" },
  "q_no": 1,
  "students": {
    "correct":     [{ "student_id": "...", "student_ref_id": "S001", "name": "Aarav Mehta" }],
    "wrong":       [],
    "unattempted": []
  }
}
```

### `GET /api/v1/analytics/exams/{exam_id}/sections/{section_id}/` — Section Detail

Response `200`:
```json
{
  "exam": { "id": "...", "exam_name": "Unit Test 1" },
  "section": { "id": "...", "name": "A" },
  "subjects": [
    { "subject_id": "...", "subject_name": "MATHS", "section_avg": 74.0, "class_avg": 72.5, "delta": 1.5 }
  ]
}
```

### `GET /api/v1/analytics/exams/{exam_id}/sections/{section_id}/subjects/{subject_id}/questions/` — Section Question Stats

Same shape as class question stats, with added `section` field.

### `GET /api/v1/analytics/exams/{exam_id}/sections/{section_id}/subjects/{subject_id}/questions/{q_no}/students/` — Section Question Students

Same shape as class question students, filtered to the section only.

---

## 2. Upload Exam CSV (Legacy)

```
POST /api/v1/analytics/upload/
```

**Auth:** PRINCIPAL or ADMIN only.  
**Content-Type:** `multipart/form-data`

**Request fields:**

| Field | Type | Required | Description |
|---|---|:---:|---|
| `csv_file` | File | ✅ | CSV with exactly 181+ columns (see CSV Format section) |

**Response `202 Accepted`:**
```json
{
  "success": true,
  "exam_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "exam_name": "CRASH-SR-MPC-EAM-PROG-II",
  "exam_date": "2025-04-15",
  "analytics_status": "PENDING",
  "students_saved": 21,
  "skipped_count": 2,
  "subjects": [
    { "subject_name": "MATHS",     "total_questions": 80 },
    { "subject_name": "PHYSICS",   "total_questions": 40 },
    { "subject_name": "CHEMISTRY", "total_questions": 40 }
  ],
  "skipped": [
    { "row_number": 5, "student_id": "12345", "reason": "Invalid maths_total value: 'abc'" }
  ]
}
```

> Analytics computation runs in a **background thread**. Poll `GET /exams/` or `GET /dashboard/?exam_id=` to check `analytics_status`.  
> Possible statuses: `PENDING` → `RUNNING` → `DONE` | `FAILED`

---

## 2. Download CSV Template

```
GET /api/v1/analytics/template/
```

**Auth:** Any authenticated user.

**Response `200 OK`:**  
`Content-Type: text/csv`  
`Content-Disposition: attachment; filename="analytics_template.csv"`

Returns a CSV with all 181 required column headers plus 3 example data rows.

---

## 3. List Exams

```
GET /api/v1/analytics/exams/
```

**Auth:** PRINCIPAL or ADMIN only.

**Response `200 OK`:**
```json
{
  "success": true,
  "exams": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "exam_name": "CRASH-SR-MPC-EAM-PROG-II",
      "exam_date": "2025-04-15",
      "analytics_status": "DONE"
    }
  ]
}
```

---

## 4. Dashboard — Screen 1 (Class Comparison)

```
GET /api/v1/analytics/dashboard/?exam_id=<uuid>
```

**Auth:** PRINCIPAL or ADMIN only.

**Query params:**

| Param | Required | Description |
|---|:---:|---|
| `exam_id` | ❌ | UUID of the exam. Omit to get exams list only. |

**Response `200 OK` — no `exam_id`:**
```json
{
  "success": true,
  "exams": [ { "id": "...", "exam_name": "...", "exam_date": "...", "analytics_status": "DONE" } ]
}
```

**Response `200 OK` — analytics not ready yet:**
```json
{
  "success": true,
  "exam": { "id": "...", "exam_name": "...", "analytics_status": "RUNNING" },
  "message": "Analytics is processing. Please try again shortly.",
  "exams": [ ... ]
}
```

**Response `200 OK` — analytics DONE:**
```json
{
  "success": true,
  "exam": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "exam_name": "CRASH-SR-MPC-EAM-PROG-II",
    "exam_date": "2025-04-15",
    "analytics_status": "DONE"
  },
  "subject_summary": [
    {
      "subject_name": "CHEMISTRY",
      "total_questions": 40,
      "school_avg": 28.4,
      "top_scorer": {
        "name": "MAHIMA REDDY.G",
        "student_ref_id": "2251863",
        "marks": 38,
        "class_name": "Class 11",
        "section_name": "A"
      }
    }
  ],
  "class_comparison": {
    "labels": ["Class 11", "Class 12"],
    "datasets": [
      { "subject": "CHEMISTRY", "data": [31.5, 38.0] },
      { "subject": "MATHS",     "data": [48.1, 54.2] },
      { "subject": "PHYSICS",   "data": [29.3, 35.1] }
    ]
  },
  "exams": [ ... ]
}
```

> `class_comparison` is ready to drop into Recharts/Chart.js — `labels` are X-axis, `datasets[i].data` are Y values aligned to `labels`.

---

## 5. Class Detail — Screen 2 (Section Breakdown)

```
GET /api/v1/analytics/class/<uuid:class_id>/?exam_id=<uuid>
```

**Auth:** PRINCIPAL or ADMIN only.

**Path params:**

| Param | Type | Description |
|---|---|---|
| `class_id` | UUID | ID of an `AcademicClass` in the school |

**Query params:**

| Param | Required | Description |
|---|:---:|---|
| `exam_id` | ✅ | UUID of a DONE exam |

**Response `200 OK`:**
```json
{
  "success": true,
  "class_name": "Class 11",
  "exam": { "id": "...", "exam_name": "...", "exam_date": "..." },
  "sections": [
    {
      "section_id": "a1b2c3d4-...",
      "section_name": "A",
      "student_count": 21,
      "subjects": [
        {
          "subject_name": "MATHS",
          "avg_marks": 48.1,
          "median_marks": 47.0,
          "std_dev": 12.3,
          "at_risk_count": 4,
          "top_scorer": {
            "name": "ARJUN REDDY",
            "student_ref_id": "2251900",
            "marks": 72
          }
        }
      ]
    }
  ]
}
```

> `sections` are ordered by `section_name`. `subjects` within each section are ordered by `subject_name`.

---

## 6. Section Students — Screen 3 (Student Table)

```
GET /api/v1/analytics/section/<uuid:section_id>/?exam_id=<uuid>
```

**Auth:** PRINCIPAL, ADMIN, or TEACHER (own section only).

**Path params:**

| Param | Type | Description |
|---|---|---|
| `section_id` | UUID | ID of a `Section` in the school |

**Query params:**

| Param | Required | Description |
|---|:---:|---|
| `exam_id` | ✅ | UUID of a DONE exam |

**Response `200 OK`:**
```json
{
  "success": true,
  "class_name": "Class 11",
  "section_name": "A",
  "section_id": "a1b2c3d4-...",
  "exam": { "id": "...", "exam_name": "...", "exam_date": "..." },
  "students": [
    {
      "student_id": "e5f6a7b8-...",
      "student_ref_id": "2251863",
      "name": "MAHIMA REDDY.G",
      "maths_pct": 52.5,
      "physics_pct": 45.0,
      "chem_pct": 37.5,
      "total_pct": 46.9,
      "subject_risk": {
        "MATHS": "WATCH",
        "PHYSICS": "SAFE",
        "CHEMISTRY": "ALERT"
      },
      "overall_risk": "ALERT"
    }
  ]
}
```

> `students` are ordered by `total_pct` descending (highest scorer first).  
> `student_id` is the `AnalyticsStudent` UUID — use it to navigate to Screen 6 & 7.  
> `overall_risk` = worst risk label across all subjects (`ALERT > WATCH > SAFE`).

---

## 7. Question Heatmap — Screen 4

```
GET /api/v1/analytics/section/<uuid:section_id>/subject/<uuid:subject_id>/heatmap/?exam_id=<uuid>
```

**Auth:** PRINCIPAL, ADMIN, or TEACHER (own section only).

**Path params:**

| Param | Type | Description |
|---|---|---|
| `section_id` | UUID | ID of a `Section` |
| `subject_id` | UUID | ID of an `ExamSubject` (obtained from Screen 2 sections response or `GET /exams/`) |

**Query params:**

| Param | Required | Description |
|---|:---:|---|
| `exam_id` | ✅ | UUID of a DONE exam |

**Response `200 OK`:**
```json
{
  "success": true,
  "class_name": "Class 11",
  "section_name": "A",
  "section_id": "a1b2c3d4-...",
  "subject_name": "MATHS",
  "total_questions": 80,
  "exam": { "id": "...", "exam_name": "...", "exam_date": "..." },
  "questions": [
    {
      "q_no": 1,
      "correct_count": 18,
      "wrong_count": 3,
      "skip_count": 0,
      "difficulty_index": 85.7,
      "difficulty_tag": "EASY",
      "has_key_error": false
    },
    {
      "q_no": 2,
      "correct_count": 4,
      "wrong_count": 12,
      "skip_count": 5,
      "difficulty_index": 19.0,
      "difficulty_tag": "HARD",
      "has_key_error": true
    }
  ]
}
```

> `difficulty_tag` values: `EASY` (>70%), `MEDIUM` (30–70%), `HARD` (<30%).  
> `has_key_error`: `true` if `discrimination_index < -0.15` AND `difficulty_index < 70`.  
> Questions are ordered by `q_no` ascending.

---

## 8. Question Detail — Screen 5

```
GET /api/v1/analytics/section/<uuid:section_id>/subject/<uuid:subject_id>/question/<int:q_no>/?exam_id=<uuid>
```

**Auth:** PRINCIPAL, ADMIN, or TEACHER (own section only).

**Path params:**

| Param | Type | Description |
|---|---|---|
| `section_id` | UUID | ID of a `Section` |
| `subject_id` | UUID | ID of an `ExamSubject` |
| `q_no` | integer | Question number (1-indexed) |

**Query params:**

| Param | Required | Description |
|---|:---:|---|
| `exam_id` | ✅ | UUID of a DONE exam |

**Response `200 OK`:**
```json
{
  "success": true,
  "class_name": "Class 11",
  "section_name": "A",
  "section_id": "a1b2c3d4-...",
  "subject_name": "MATHS",
  "q_no": 12,
  "exam": { "id": "...", "exam_name": "...", "exam_date": "..." },
  "question": {
    "q_no": 12,
    "correct_count": 6,
    "wrong_count": 11,
    "skip_count": 4,
    "difficulty_index": 28.6,
    "difficulty_tag": "HARD",
    "discrimination_index": 0.42,
    "has_key_error": false
  }
}
```

> Screen 5 adds `discrimination_index` that Screen 4 heatmap omits.

---

## 9. Student All Exams (Timeline)

```
GET /api/v1/analytics/student/<uuid:student_id>/exams/
```

**Auth:** PRINCIPAL, ADMIN, TEACHER (own section), STUDENT (own), PARENT (own child).

**Path params:**

| Param | Type | Description |
|---|---|---|
| `student_id` | UUID | `AnalyticsStudent.id` |

**Response `200 OK`:**
```json
{
  "success": true,
  "student": {
    "student_id": "...",
    "student_ref_id": "2251863",
    "name": "MAHIMA REDDY.G",
    "class_name": "Class 11",
    "section_name": "A"
  },
  "exams": [
    {
      "id": "...",
      "exam_name": "Unit Test 2",
      "exam_date": "2026-05-10",
      "total_marks": 150,
      "overall_risk": "SAFE",
      "subjects": [
         { "subject_id": "...", "subject_name": "MATHS", "marks": 70, "max_marks": 80, "risk_label": "SAFE" },
         { "subject_id": "...", "subject_name": "PHYSICS", "marks": 35, "max_marks": 40, "risk_label": "SAFE" }
      ]
    },
    {
      "id": "...",
      "exam_name": "Unit Test 1",
      "exam_date": "2026-04-15",
      "total_marks": 85,
      "overall_risk": "ALERT",
      "subjects": [
         { "subject_id": "...", "subject_name": "MATHS", "marks": 40, "max_marks": 80, "risk_label": "WATCH" },
         { "subject_id": "...", "subject_name": "PHYSICS", "marks": 15, "max_marks": 40, "risk_label": "ALERT" }
      ]
    }
  ]
}
```

> Returns a combined list of all exams the student participated in, pre-populated with subject-wise results. `overall_risk` is automatically determined based on the highest risk level across all subjects for each exam.

---

## 10. Student Summary — Screen 6

```
GET /api/v1/analytics/student/<uuid:student_id>/?exam_id=<uuid>
```

**Auth:** PRINCIPAL, ADMIN, TEACHER (own section), STUDENT (own), PARENT (own child).

**Path params:**

| Param | Type | Description |
|---|---|---|
| `student_id` | UUID | `AnalyticsStudent.id` — obtained from Screen 3's `student_id` field |

**Query params:**

| Param | Required | Description |
|---|:---:|---|
| `exam_id` | ✅ | UUID of a DONE exam |

**Response `200 OK`:**
```json
{
  "success": true,
  "student": {
    "student_id": "e5f6a7b8-...",
    "student_ref_id": "2251863",
    "name": "MAHIMA REDDY.G",
    "class_name": "Class 11",
    "section_name": "A"
  },
  "exam": { "id": "...", "exam_name": "...", "exam_date": "..." },
  "exams": [
    { "id": "...", "exam_name": "...", "exam_date": "...", "analytics_status": "DONE" }
  ],
  "subjects": [
    {
      "subject_name": "CHEMISTRY",
      "total_marks": 30,
      "max_marks": 40,
      "percentage": 75.0,
      "exam_rank": 3,
      "correct": 15,
      "wrong": 2,
      "unattempted": 3,
      "risk_label": "SAFE",
      "performance_label": "ABOVE_AVERAGE",
      "z_score": 0.8112
    },
    {
      "subject_name": "MATHS",
      "total_marks": 42,
      "max_marks": 80,
      "percentage": 52.5,
      "exam_rank": 11,
      "correct": 14,
      "wrong": 4,
      "unattempted": 2,
      "risk_label": "WATCH",
      "performance_label": "AVERAGE",
      "z_score": -0.12
    },
    {
      "subject_name": "PHYSICS",
      "total_marks": 18,
      "max_marks": 40,
      "percentage": 45.0,
      "exam_rank": 15,
      "correct": 9,
      "wrong": 6,
      "unattempted": 5,
      "risk_label": "WATCH",
      "performance_label": "BELOW_AVERAGE",
      "z_score": -0.74
    }
  ],
  "overall_risk": "WATCH"
}
```

> `exams` list enables a frontend exam-picker dropdown.  
> `subjects` are ordered by `subject_name` (CHEMISTRY → MATHS → PHYSICS alphabetically).  
> `performance_label` values: `EXCEPTIONAL`, `ABOVE_AVERAGE`, `AVERAGE`, `BELOW_AVERAGE`, `NEEDS_ATTENTION`.

---

## 10. Student Subject Drill-down — Screen 7

```
GET /api/v1/analytics/student/<uuid:student_id>/subject/<uuid:subject_id>/?exam_id=<uuid>
```

**Auth:** PRINCIPAL, ADMIN, TEACHER (own section), STUDENT (own), PARENT (own child).

**Path params:**

| Param | Type | Description |
|---|---|---|
| `student_id` | UUID | `AnalyticsStudent.id` |
| `subject_id` | UUID | `ExamSubject.id` — obtained from Screen 6's subjects list |

**Query params:**

| Param | Required | Description |
|---|:---:|---|
| `exam_id` | ✅ | UUID of a DONE exam |

**Response `200 OK`:**
```json
{
  "success": true,
  "student": {
    "student_id": "e5f6a7b8-...",
    "student_ref_id": "2251863",
    "name": "MAHIMA REDDY.G",
    "class_name": "Class 11",
    "section_name": "A"
  },
  "exam": { "id": "...", "exam_name": "...", "exam_date": "..." },
  "subject_name": "MATHS",
  "result": {
    "total_marks": 42,
    "max_marks": 80,
    "percentage": 52.5,
    "exam_rank": 11,
    "correct": 14,
    "wrong": 4,
    "unattempted": 2,
    "risk_label": "WATCH",
    "performance_label": "AVERAGE",
    "z_score": -0.12
  },
  "questions": [
    { "q_no": 1,  "status": "C" },
    { "q_no": 2,  "status": "W" },
    { "q_no": 3,  "status": "U" },
    { "q_no": 4,  "status": "C" }
  ]
}
```

> `questions` are ordered by `q_no` ascending.  
> `status` values: `C` (Correct), `W` (Wrong), `U` (Unattempted).  
> Only C/W/U status is exposed — no answer keys or correct answers are returned.

---

## 11. Seed Data (DEBUG only)

```
POST /api/v1/analytics/seed/
```

**Auth:** PRINCIPAL or ADMIN only.  
**Restriction:** Returns `403` if `DEBUG=False`.

Inserts 21 synthetic students for exam `CRASH-SR-MPC-EAM-PROG-II` with a realistic performance distribution:
- 3 EXCEPTIONAL, 5 ABOVE_AVERAGE, 8 AVERAGE, 3 BELOW_AVERAGE, 2 NEEDS_ATTENTION

**Response:** Same shape as `POST /upload/` (`202`).

---

## CSV Format

### Required columns (181 total)

**Student info (6):**

| Column | Type | Example |
|---|---|---|
| `student_id` | string | `2251863` |
| `student_name` | string | `MAHIMA REDDY.G` |
| `exam_name` | string | `CRASH-SR-MPC-EAM-PROG-II` |
| `exam_date` | `YYYY-MM-DD` | `2025-04-15` |
| `class` | string | `Class 11` |
| `section` | string | `A` |

**Per-subject summary (15 = 5 × 3 subjects):**

| Columns | Subject |
|---|---|
| `maths_total`, `maths_rank`, `maths_correct`, `maths_wrong`, `maths_unattempted` | MATHS |
| `physics_total`, `physics_rank`, `physics_correct`, `physics_wrong`, `physics_unattempted` | PHYSICS |
| `chem_total`, `chem_rank`, `chem_correct`, `chem_wrong`, `chem_unattempted` | CHEMISTRY |

**Per-question status (160 = 80 + 40 + 40):**

| Pattern | Subject | Count |
|---|---|---|
| `m_q1` … `m_q80` | MATHS | 80 |
| `p_q1` … `p_q40` | PHYSICS | 40 |
| `c_q1` … `c_q40` | CHEMISTRY | 40 |

Question status values: `C` (Correct), `W` (Wrong), `U` (Unattempted).

> All rows in the same CSV must have the same `exam_name` and `exam_date`.  
> Rows with parse errors are skipped and reported in the `skipped` array of the upload response.

---

## Analytics Computation Formulas

### Difficulty Index
```
difficulty_index = (correct_count / total_students) × 100

EASY   if difficulty_index > 70
MEDIUM if 30 ≤ difficulty_index ≤ 70
HARD   if difficulty_index < 30
```

### Discrimination Index
```
top27    = top 27% of students by subject total_marks
bottom27 = bottom 27%
discrimination_index = (correct_in_top27 / n27) − (correct_in_bottom27 / n27)

has_key_error = True if discrimination_index < -0.15 AND difficulty_index < 70
```

### Risk Score (0–100)
```
score_component = 40 × max(0, (batch_avg − marks) / batch_avg)
wrong_component = 30 × (wrong / (correct + wrong))   [0 if no attempts]
skip_component  = 20 × (unattempted / total_questions)
risk_score      = min(100, score_component + wrong_component + skip_component)

SAFE  if risk_score < 30
WATCH if risk_score < 60
ALERT if risk_score ≥ 60
```

### Performance Label (z-score)
```
z_score = (student_marks − mean) / std_dev

z >  1.5 → EXCEPTIONAL
z >  0.5 → ABOVE_AVERAGE
z > −0.5 → AVERAGE
z > −1.5 → BELOW_AVERAGE
else     → NEEDS_ATTENTION
```

---

## URL Summary

| Method | URL | Screen | Auth |
|---|---|---|---|
| `GET` | `/analytics/template/` | — | Any |
| `POST` | `/analytics/upload/` | — | Principal/Admin |
| `GET` | `/analytics/exams/` | — | Principal/Admin |
| `GET` | `/analytics/dashboard/?exam_id=` | Screen 1 | Principal/Admin |
| `GET` | `/analytics/class/<uuid>/?exam_id=` | Screen 2 | Principal/Admin |
| `GET` | `/analytics/section/<uuid>/?exam_id=` | Screen 3 | Principal/Admin/Teacher(own) |
| `GET` | `/analytics/section/<uuid>/subject/<uuid>/heatmap/?exam_id=` | Screen 4 | Principal/Admin/Teacher(own) |
| `GET` | `/analytics/section/<uuid>/subject/<uuid>/question/<n>/?exam_id=` | Screen 5 | Principal/Admin/Teacher(own) |
| `GET` | `/analytics/student/<uuid>/?exam_id=` | Screen 6 | All 4 roles (restricted) |
| `GET` | `/analytics/student/<uuid>/subject/<uuid>/?exam_id=` | Screen 7 | All 4 roles (restricted) |
| `POST` | `/analytics/seed/` | — | Principal/Admin (DEBUG only) |
