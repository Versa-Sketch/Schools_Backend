# Plan: Exam Analytics Restructure — Exam-Centric Flow

## Context

The current analytics system treats file upload as the entry point — the exam is created on upload. The new requirement changes this: the principal first creates an exam (tied to a specific class or section), then uploads the result file. Additionally, the analytics drill-down is restructured around the exam (not separate dashboard/class/section screens), and the student-side exam endpoints (currently 501 stubs) must be implemented.

One class can only have one exam — no shared exams across classes.

---

## Screen Flow

```
Principal:
  Exam List
    → Create Exam (name + class/section)
    → Upload file to exam
    → Exam Overview: class avg + section-wise avg + subject-wise avg + top 5 students
        → Click subject (class level) → Questions with C/W/U stats
            → Click question → Student list with status (class-wide)
        → Click section → Section detail: subject-wise avg + Δ from class avg
            → Click subject (section level) → Questions with C/W/U stats
                → Click question → Student list with status (section-only)

Student:
  Exam list → Subject list → Question results (correct/wrong/unattempted)
```

---

## 1. Model Changes

**File:** `analytics/models.py`

### `AnalyticsExam` — add fields:
```python
academic_class = models.ForeignKey(
    'core.AcademicClass', on_delete=models.PROTECT, null=True, blank=True
)
section = models.ForeignKey(
    'core.Section', on_delete=models.PROTECT, null=True, blank=True
)
```
- `analytics_status` choices: add `'CREATED'` as the initial state (before upload)
- `exam_date` → nullable (`null=True, blank=True`) since it comes from the uploaded file
- `uploaded_by` → nullable since it's not known at creation time

### Migration
New migration in `analytics/migrations/` to add `academic_class`, `section` FKs and allow null `exam_date`/`uploaded_by`.

---

## 2. New API Endpoints (Full URL Map)

All under `/api/v1/analytics/` — principal/admin only unless noted.

| Method | URL | Description |
|--------|-----|-------------|
| `POST` | `exams/` | Create exam (name + class or section) |
| `GET` | `exams/` | List exams for school |
| `POST` | `exams/{exam_id}/upload/` | Upload CSV/Excel/PDF to existing exam |
| `GET` | `exams/{exam_id}/overview/` | Class avg + sections + subjects + top 5 |
| `GET` | `exams/{exam_id}/subjects/{subject_id}/questions/` | Class-wide question stats |
| `GET` | `exams/{exam_id}/subjects/{subject_id}/questions/{q_no}/students/` | Class-wide student list for question |
| `GET` | `exams/{exam_id}/sections/{section_id}/` | Section detail (subject avgs + class avg diff) |
| `GET` | `exams/{exam_id}/sections/{section_id}/subjects/{subject_id}/questions/` | Section question stats |
| `GET` | `exams/{exam_id}/sections/{section_id}/subjects/{subject_id}/questions/{q_no}/students/` | Section student list for question |
| `GET` | `template/` | Download CSV template (keep existing) |

**Student side** (replace 501 stubs in `student/urls.py`):

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `student/exams/` | List exams the student participated in |
| `GET` | `student/exams/{exam_id}/subjects/` | Subjects for that exam |
| `GET` | `student/exams/{exam_id}/subjects/{subject_id}/questions/` | Per-question result (C/W/U) |

---

## 3. Storage Changes

**File:** `analytics/storages/analytics_storage.py`

### New / Modified Methods

**`create_exam_record(school, exam_name, academic_class_id, section_id)`**
- Creates `AnalyticsExam` with status=`CREATED`, no `exam_date` or `uploaded_by` yet
- Validates: either `academic_class_id` or `section_id` must be set (not both, not neither)

**`update_exam_on_upload(exam_id, exam_date, uploaded_by)`**
- Called inside upload pipeline; sets `exam_date`, `uploaded_by`, transitions status to `PENDING`

**`get_exam_overview(exam_id, school_id)`**
Returns:
- Class-level avg marks per subject (from `SectionAnalytics` aggregated across sections)
- Per-section averages (from `SectionAnalytics`)
- Top 5 students by total marks (from `ExamResult` aggregated by student)

**`get_top_students(exam_id, n=5)`**
- Aggregates `ExamResult.total_marks` by `student`, orders descending, returns top n with name

**`get_section_subject_detail(exam_id, section_id, school_id)`**
- Returns subject-wise avg for the section (from `SectionAnalytics`)
- Returns class-level avg per subject for delta calculation

**`get_class_question_students(exam_id, subject_id, q_no, school_id)`**
- Returns `QuestionResult` for ALL students in the exam's class for a given question
- (Existing `get_question_results_for_section_question` is section-scoped — need class-scoped variant)

**Reuse existing (unchanged):**
- `get_question_analytics_for_subject(exam_id, subject_id)` → question stats for class/section subject screen
- `get_question_results_for_section_question(exam_id, section_id, subject_id, q_no)` → section question students
- `get_exam_results_for_student(exam_id, student_id, school_id)` → student subject list
- `get_question_results_by_student_id(exam_id, student_id, subject_id)` → student question list
- `get_exams_for_school(school_id)` → list exams
- `run_analytics(exam_id)` → background computation (unchanged)

**Student exam list:**

**`get_exams_for_student(student_ref_id, school_id)`**
- Queries `ExamResult` joined to `AnalyticsExam` where student matches, returns distinct exams

**`get_subjects_for_student_exam(exam_id, student_id)`**
- Returns `ExamSubject` records where student has `ExamResult`

---

## 4. Upload Pipeline Change

**File:** `analytics/interactors/upload.py` — `UploadExamCSVInteractor`

**Current flow:** Upload → create AnalyticsExam → parse → persist → run_analytics

**New flow:**
- Accept `exam_id` in request
- Validate exam exists, belongs to school, status is `CREATED`
- Parse file (unchanged — parsers are unaffected)
- Call `update_exam_on_upload()` instead of `create_exam()`
- Persist results and run analytics (unchanged)

---

## 5. Interactor Changes

### New: `analytics/interactors/exams.py`
- `CreateExamInteractor.create(user, data)` — validates, calls storage, returns exam
- `ExamOverviewInteractor.overview(user, exam_id)` — returns class avg, sections, subjects, top 5
- `ClassSubjectQuestionsInteractor.get(user, exam_id, subject_id)` — class-wide question stats
- `ClassQuestionStudentsInteractor.get(user, exam_id, subject_id, q_no)` — class-wide student list

### Refactor: `analytics/interactors/section.py`
- `SectionDetailInteractor.get(user, exam_id, section_id)` — subject avgs + class avg diff
- `SectionSubjectQuestionsInteractor.get(user, exam_id, section_id, subject_id)` — section questions
- `SectionQuestionStudentsInteractor.get(user, exam_id, section_id, subject_id, q_no)` — section student list

### New: `analytics/interactors/student_exams.py` (replace stubs)
- `StudentExamListInteractor.list(user)` — exams the student participated in
- `StudentExamSubjectsInteractor.list(user, exam_id)` — subjects for exam
- `StudentSubjectQuestionsInteractor.list(user, exam_id, subject_id)` — question results

---

## 6. Presenter Changes

### `analytics/presenters/exams.py` (new)
- `create_exam_success(exam)` → `{id, exam_name, status, academic_class, section, created_at}`
- `exam_overview_success(exam, class_avgs, sections, top_students)`:
  ```json
  {
    "exam": { "id": "...", "exam_name": "...", "status": "DONE" },
    "class_avgs": [{ "subject": "MATHS", "avg": 72.5 }, ...],
    "sections": [{ "section_id": "...", "name": "A", "avg": 74.0 }, ...],
    "top_students": [{ "name": "...", "total_marks": 280, "rank": 1 }, ...]
  }
  ```

### `analytics/presenters/section.py` (update)
- `section_detail_success(section, subjects_with_delta)`:
  ```json
  {
    "section": { "id": "...", "name": "A" },
    "subjects": [
      { "subject": "MATHS", "section_avg": 74.0, "class_avg": 72.5, "delta": 1.5 },
      ...
    ]
  }
  ```

### `analytics/presenters/questions.py` (new)
- `question_list_success(questions)` → list with q_no, correct_count, wrong_count, unattempted_count, difficulty_tag
- `question_students_success(students)` → list with student name, status (C/W/U)

### `analytics/presenters/student.py` (update)
- `exam_list_success(exams)` → list with exam_id, name, date, status
- `exam_subjects_success(subjects)` → list with subject_id, subject_name, marks, correct, wrong, unattempted
- `subject_questions_success(questions)` → list with q_no, status (C/W/U)

---

## 7. View & URL Changes

### `analytics/views.py` — add/replace views:
```
create_exam_view                # POST exams/
list_exams_view                 # GET  exams/
upload_exam_view                # POST exams/{exam_id}/upload/
exam_overview_view              # GET  exams/{exam_id}/overview/
class_subject_questions_view    # GET  exams/{exam_id}/subjects/{sub_id}/questions/
class_question_students_view    # GET  exams/{exam_id}/subjects/{sub_id}/questions/{q_no}/students/
section_detail_view             # GET  exams/{exam_id}/sections/{sec_id}/
section_subject_questions_view  # GET  exams/{exam_id}/sections/{sec_id}/subjects/{sub_id}/questions/
section_question_students_view  # GET  exams/{exam_id}/sections/{sec_id}/subjects/{sub_id}/questions/{q_no}/students/
template_download_view          # GET  template/ (keep)
```

### `analytics/urls.py` — full replacement with exam-nested routes

### `student/views.py` — implement exam views (replace stubs):
```
student_exams_view              # GET student/exams/
student_exam_subjects_view      # GET student/exams/{exam_id}/subjects/
student_subject_questions_view  # GET student/exams/{exam_id}/subjects/{sub_id}/questions/
```

### `student/urls.py` — add new exam routes

---

## 8. API_SPEC Updates

- `analytics/API_SPEC.md` — full rewrite of endpoints section
- `student/API_SPEC.md` — replace 501 stubs with real spec
- `principal/API_SPEC.md` — update exam management section (now points to analytics endpoints)

---

## 9. Critical Files to Modify

| File | Change |
|------|--------|
| `analytics/models.py` | Add `academic_class`, `section` FKs; add `CREATED` status; nullable `exam_date`/`uploaded_by` |
| `analytics/migrations/XXXX_add_exam_class_section.py` | New migration |
| `analytics/storages/analytics_storage.py` | New/modified methods (see §3) |
| `analytics/interactors/upload.py` | Accept `exam_id`, call `update_exam_on_upload` |
| `analytics/interactors/exams.py` | New file — create + overview + class question flows |
| `analytics/interactors/section.py` | Refactor — section detail + question flows |
| `analytics/interactors/student_exams.py` | New file — student exam/subject/question flows |
| `analytics/presenters/exams.py` | New file |
| `analytics/presenters/section.py` | Update section_detail_success |
| `analytics/presenters/questions.py` | New file |
| `analytics/presenters/student.py` | Update for new student screens |
| `analytics/views.py` | Replace/add views |
| `analytics/urls.py` | Full URL restructure |
| `student/views.py` | Implement exam views |
| `student/urls.py` | Add exam sub-routes |
| `analytics/API_SPEC.md` | Full rewrite |
| `student/API_SPEC.md` | Update exam section |
| `principal/API_SPEC.md` | Update exam management section |

---

## 10. Verification

1. `POST /analytics/exams/` with `exam_name` + `class_id` → 201, status=CREATED
2. `POST /analytics/exams/{id}/upload/` with CSV → 202, analytics runs in background
3. `GET /analytics/exams/{id}/overview/` → class avgs, sections, top 5 students
4. `GET /analytics/exams/{id}/subjects/{sub_id}/questions/` → question list with C/W/U counts
5. `GET /analytics/exams/{id}/subjects/{sub_id}/questions/1/students/` → all class students for Q1 with status
6. `GET /analytics/exams/{id}/sections/{sec_id}/` → subject avgs + delta vs class avg
7. `GET /analytics/exams/{id}/sections/{sec_id}/subjects/{sub_id}/questions/` → section question stats
8. `GET /analytics/exams/{id}/sections/{sec_id}/subjects/{sub_id}/questions/1/students/` → section students for Q1
9. `GET /student/exams/` (as student) → list of exams student sat
10. `GET /student/exams/{id}/subjects/` → subjects with marks summary
11. `GET /student/exams/{id}/subjects/{sub_id}/questions/` → per-question C/W/U status
