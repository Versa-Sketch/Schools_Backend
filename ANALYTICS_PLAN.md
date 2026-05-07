# School Analytics Platform — Backend Build Plan

## Context

The existing Django 5.2 + DRF backend has a stub analytics endpoint at
`/api/v1/principal/analytics/` that returns empty arrays. The project uses
Clean Architecture (View → Interactor → Storage → Presenter) with SQLite3,
JWT auth, and four roles: PRINCIPAL, TEACHER, STUDENT, PARENT.

This plan implements the full analytics feature as a new `analytics` Django app
inside the existing project, following all established patterns. No frontend
is in scope. Background tasks use Python threading (no Celery). Database
stays SQLite3 — percentiles computed in Python via `statistics` module.

---

## Decisions Locked

| Decision | Choice |
|---|---|
| Database | SQLite3 (existing) |
| Background tasks | `threading.Thread`, daemon=True |
| Answer data (Screen 7) | Show C/W/U status only — no student_ans / correct_ans |
| Frontend | Out of scope |
| New app location | `Schools_Backend/analytics/` |

---

## Build Order

1. Django app scaffold + models + migration  ← DONE
2. CSV parser service
3. Analytics engine service
4. Upload interactor + presenter + view + URL
5. Dashboard interactors + presenter + views + URLs (Screens 1–7)
6. Seed data endpoint
7. Role-based access guards
8. Settings + root URL wiring

---

## Phase 1 — Django App + Models ✅

### App scaffold

```
Schools_Backend/analytics/
  __init__.py
  apps.py
  admin.py
  constants.py
  exceptions.py
  models.py
  migrations/__init__.py
  services/__init__.py  (csv_parser.py, analytics_engine.py)
  interactors/__init__.py  (base.py, upload.py, dashboard.py)
  storages/__init__.py  (analytics_storage.py)
  presenters/__init__.py  (upload_presenter.py, analytics_presenter.py)
  views.py
  urls.py
```

### Models

| Model | Purpose |
|---|---|
| AnalyticsExam | One per CSV upload (exam_name, exam_date, school, status) |
| AnalyticsStudent | Student from CSV; FK to Section (nullable) + text fallback |
| ExamSubject | MATHS / PHYSICS / CHEMISTRY per exam (3 rows per exam) |
| ExamResult | One per student × subject × exam (marks, rank, C/W/U counts) |
| QuestionResult | One per student × question (status: C/W/U) |
| QuestionAnalytics | Pre-computed per exam × subject × q_no (difficulty, discrimination) |
| SectionAnalytics | Pre-computed per exam × section × subject (avg, median, std_dev) |
| StudentRisk | Pre-computed per exam × student × subject (risk_score, labels) |

### Key FK design

- `AnalyticsExam` → FK to `core.School` only (CSV can span multiple sections)
- `AnalyticsStudent` → FK to `core.Section` (nullable=True), text fallbacks for class_name + section_name
- `SectionAnalytics` → FK to `core.Section` (non-nullable — only computed when section matched)
- `StudentRisk` → FK to `AnalyticsStudent`

---

## Phase 2 — CSV Parser (`analytics/services/csv_parser.py`)

### Required columns (181 total)

Student info (6): student_id, student_name, exam_name, exam_date, class, section

Per subject (5 × 3 = 15):
  maths_total, maths_rank, maths_correct, maths_wrong, maths_unattempted
  physics_total, physics_rank, physics_correct, physics_wrong, physics_unattempted
  chem_total, chem_rank, chem_correct, chem_wrong, chem_unattempted

Question statuses (160): m_q1…m_q80, p_q1…p_q40, c_q1…c_q40

### Validation logic

1. `validate_structure(df)` — raise immediately if any column missing
2. `parse_row(row, school)` — validate types/values, return (ParsedRow | None, error)
3. `parse_file(file_obj, school)` → ParseResult with success_count, skipped list

### CSV template download

`GET /api/v1/analytics/template/` — 181 headers + 3 example rows

---

## Phase 3 — Analytics Engine (`analytics/services/analytics_engine.py`)

### Formulas

**Difficulty Index**
```
difficulty_index = (correct_count / total_students) × 100
EASY   if > 70%
MEDIUM if 30–70%
HARD   if < 30%
```

**Discrimination Index**
```
top27   = top 27% of students by subject total_marks
bottom27 = bottom 27%
discrimination = (correct in top27 / n27) − (correct in bottom27 / n27)
has_key_error = True if discrimination < 0
```

**Risk Score (0–100)**
```
score_component  = 40 × max(0, (batch_avg − marks) / batch_avg)
wrong_component  = 30 × (wrong / (correct + wrong))   [0 if no attempts]
skip_component   = 20 × (unattempted / total_questions)
risk_score       = min(100, sum of above)

SAFE  if risk_score < 30
WATCH if risk_score < 60
ALERT if risk_score ≥ 60
```

**Performance Label (from z-score)**
```
z > 1.5  → EXCEPTIONAL
z > 0.5  → ABOVE_AVERAGE
z > −0.5 → AVERAGE
z > −1.5 → BELOW_AVERAGE
else     → NEEDS_ATTENTION
```

---

## Phase 4 — Upload API

`POST /api/v1/analytics/upload/` (Principal only)

Flow:
1. Validate structure → return error immediately if wrong
2. Parse all rows, collect successes + skipped
3. @transaction.atomic: create Exam, ExamSubjects, Students, Results, QuestionResults
4. Thread(target=run_analytics, daemon=True).start()
5. Return immediately with upload summary

---

## Phase 5 — Dashboard APIs (Screens 1–7)

### URL map

```
POST /api/v1/analytics/upload/                                     → CSV upload
GET  /api/v1/analytics/template/                                   → template download
POST /api/v1/analytics/seed/                                       → insert 21 sample students
GET  /api/v1/analytics/dashboard/?exam_id=                         → Screen 1 (Principal)
GET  /api/v1/analytics/class/<str:class_name>/?exam_id=            → Screen 2 (Principal)
GET  /api/v1/analytics/section/<str:class_name>/<str:section_name>/?exam_id=
                                                                   → Screen 3 (P+T)
GET  /api/v1/analytics/section/<str:class_name>/<str:section_name>/
     subject/<str:subject>/heatmap/                                → Screen 4 (P+T)
GET  /api/v1/analytics/section/<str:class_name>/<str:section_name>/
     subject/<str:subject>/question/<int:q_no>/                    → Screen 5 (P+T)
GET  /api/v1/analytics/student/<str:student_ref_id>/               → Screen 6 (P+T+S+Parent)
GET  /api/v1/analytics/student/<str:student_ref_id>/subject/<str:subject>/
                                                                   → Screen 7 (P+T+S+Parent)
```

### Chart data format (ready for Recharts/Chart.js — no frontend transform needed)

Screen 1 class_comparison:
```json
{
  "labels": ["Class 11", "Class 12"],
  "datasets": [
    {"subject": "MATHS",   "data": [48.1, 54.2]},
    {"subject": "PHYSICS", "data": [31.5, 38.0]}
  ]
}
```

Screen 3 student table row:
```json
{"student_ref_id": "2251863", "name": "MAHIMA REDDY.G",
 "maths_pct": 52.5, "physics_pct": 45.0, "chem_pct": 37.5,
 "total_pct": 46.9, "risk_label": "WATCH"}
```

Screen 4 heatmap question:
```json
{"q_no": 1, "correct_count": 18, "wrong_count": 3, "skip_count": 0,
 "difficulty_tag": "EASY", "difficulty_index": 85.7, "has_key_error": false}
```

---

## Phase 6 — Seed Data

`POST /api/v1/analytics/seed/` — inserts 21 students for CRASH-SR-MPC-EAM-PROG-II
with realistic performance distribution (3 EXCEPTIONAL, 5 ABOVE_AVG, 8 AVG,
3 BELOW_AVG, 2 NEEDS_ATTENTION). Triggers analytics in background.

---

## Phase 7 — Role-Based Access

| Endpoint | Principal | Teacher | Student | Parent |
|---|---|---|---|---|
| /upload/ | ✓ | — | — | — |
| /dashboard/ | ✓ | — | — | — |
| /class/<id>/ | ✓ | — | — | — |
| /section/<id>/ | ✓ | own section only | — | — |
| /heatmap/ | ✓ | own section only | — | — |
| /question/<n>/ | ✓ | own section only | — | — |
| /student/<id>/ | ✓ | own section only | own only | own child only |
| /student/<id>/subject/ | ✓ | own section only | own only | own child only |

---

## Files to Modify in Existing Code

| File | Change |
|---|---|
| `schools_backend/settings.py` | Add `'analytics'` to INSTALLED_APPS |
| `schools_backend/urls.py` | Add `path('api/v1/analytics/', include('analytics.urls'))` |
| `principal/views.py` | Remove/redirect the stub analytics_view |
| `principal/urls.py` | Remove stub `analytics/` route |

---

## Utilities to Reuse from Core

| Utility | Location |
|---|---|
| `_ensure_principal(user)` | `principal/interactors/base.py` |
| `AppException`, `PermissionDeniedException`, `ValidationException` | `core/exceptions.py` |
| `custom_exception_handler` | `core/exceptions.py` (already wired in DRF) |
| `IsAuthenticated`, `IsPrincipal`, `IsTeacher` | existing permission classes |
| `TimeStampedModel` | `core/models.py` |
| `@transaction.atomic()` | `django.db.transaction` |

---

## Verification Steps

1. `python manage.py makemigrations analytics && python manage.py migrate`
2. `GET /api/v1/analytics/template/` → download CSV with 181 headers
3. Fill template + `POST /api/v1/analytics/upload/` as Principal → `students_saved: N`
4. Wait 2s, check exam analytics_status → DONE
5. `POST /api/v1/analytics/seed/` → 21 students, analytics computed
6. Walk through each screen endpoint, verify data
7. As Teacher: access another section → 403
8. As Student: own data → 200, other student → 403
