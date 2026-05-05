# Principal API Spec

## Purpose

This app owns principal-only school administration APIs: configuration, teacher onboarding, student onboarding, announcements, calendar management, exams, result dashboard, and analytics dashboard.

All endpoints use `/api/v1/`, require JWT authentication, and require role `PRINCIPAL`.

## Error Format

All errors follow the common error format defined in `core/API_SPEC.md`:

```json
{
  "success": false,
  "code": "PERMISSION_DENIED",
  "details": "Only principals can access this endpoint."
}
```

## Permissions

- Only authenticated principals can access these endpoints.
- Every object must belong to the principal's school.
- Cross-school object IDs use `NOT_FOUND` or `PERMISSION_DENIED`.

## School Configuration

### `GET /api/v1/principal/configuration/`

Returns the current school's configuration.

Response:

```json
{
  "school_id": 1,
  "attendance_frequency": "TWICE",
  "whatsapp_absent_automation_enabled": true,
  "parent_query_enabled": true,
  "subdomain": "green-valley"
}
```

### `PATCH /api/v1/principal/configuration/`

Updates configurable school settings.

Request:

```json
{
  "attendance_frequency": "ONCE",
  "whatsapp_absent_automation_enabled": false,
  "parent_query_enabled": true
}
```

Validation:

- `attendance_frequency` must be `ONCE` or `TWICE`.
- `subdomain` is documented as school configuration, but subdomain changes should be handled through a separate maintenance flow if implemented later.

## Teacher Onboarding

### `POST /api/v1/principal/teachers/`

Creates a teacher user and teacher profile.

Request:

```json
{
  "name": "Anita Sharma",
  "mobile_number": "9999999999",
  "username": "anita.teacher",
  "password": "temporary-password",
  "primary_subject_id": 4,
  "assigned_section_ids": [7, 8]
}
```

Response:

```json
{
  "id": 10,
  "user": {
    "id": 25,
    "username": "anita.teacher",
    "role": "TEACHER"
  },
  "name": "Anita Sharma",
  "mobile_number": "9999999999",
  "primary_subject": {
    "id": 4,
    "name": "Mathematics"
  },
  "assigned_sections": [
    {
      "id": 7,
      "class_name": "Class 5",
      "section_name": "A"
    }
  ]
}
```

Validation:

- `username` must be unique.
- `primary_subject_id` must belong to the principal's school.
- All `assigned_section_ids` must belong to the principal's school.
- Created user role must be `TEACHER`.

### `GET /api/v1/principal/teachers/`

Lists teachers in the principal's school.

Query params:

- `subject_id`: optional.
- `section_id`: optional.
- `search`: optional name/mobile/username search.

### `PATCH /api/v1/principal/teachers/{id}/`

Updates teacher profile fields.

Request:

```json
{
  "name": "Anita Sharma",
  "mobile_number": "9999999999",
  "primary_subject_id": 4,
  "assigned_section_ids": [7, 8]
}
```

Validation:

- Teacher must belong to the principal's school.
- Assigned sections replace the existing assignment set.

## Student Onboarding

### `POST /api/v1/principal/students/bulk-upload/`

Uploads a CSV file for student and parent account creation.

Content type: `multipart/form-data`

Fields:

- `csv_file`: required CSV file.

Required CSV columns:

- `student_name`
- `class`
- `section`
- `parent_name`
- `parent_mobile_number`

Optional CSV columns:

- `roll_number`
- `admission_number`
- `student_username`
- `parent_username`

Response:

```json
{
  "batch_id": 15,
  "status": "PENDING",
  "total_rows": 0,
  "success_count": 0,
  "error_count": 0
}
```

Processing rules:

- Create a `StudentBulkUploadBatch`.
- For each CSV row, create a `StudentBulkUploadRow`.
- Create student user with role `STUDENT`.
- Create parent user with role `PARENT`.
- Create `StudentProfile`.
- Create or reuse `ParentProfile` by mobile number within the same school.
- Link parent to student.
- Store generated credentials in the response only if the implementation has a secure credential delivery policy.

Validation:

- Class and section must exist in the principal's school.
- Admission number must be unique per school when set.
- Roll number must be unique per section when set.
- Invalid rows should not block valid rows.

### `GET /api/v1/principal/students/bulk-upload/{batch_id}/`

Returns upload status and error report.

Response:

```json
{
  "batch_id": 15,
  "status": "COMPLETED",
  "total_rows": 50,
  "success_count": 48,
  "error_count": 2,
  "error_report_url": "/media/student_upload_errors/report.csv"
}
```

## Announcements

### `POST /api/v1/principal/announcements/`

Creates and publishes a principal announcement.

Content type: `multipart/form-data` when attachments are included.

Request fields:

```json
{
  "title": "School Reopens",
  "body": "School reopens on Monday.",
  "audience": "SECTION",
  "class_ids": [1],
  "section_ids": [7],
  "publish_now": true
}
```

Response:

```json
{
  "id": 11,
  "title": "School Reopens",
  "audience": "SECTION",
  "published_at": "2026-06-01T09:00:00Z",
  "attachments": []
}
```

Rules:

- `SCHOOL` announcements do not require targets.
- `CLASS` announcements require one or more `class_ids`.
- `SECTION` announcements require one or more `section_ids`.
- Push notifications are sent on publish.

## Calendar Management

### `POST /api/v1/principal/calendar-events/`

Adds a holiday, exam, or event.

Request:

```json
{
  "title": "Annual Day",
  "event_type": "EVENT",
  "start_date": "2026-08-10",
  "end_date": "2026-08-10",
  "description": "Annual school event.",
  "visible_to": ["TEACHER", "STUDENT", "PARENT"]
}
```

Validation:

- `event_type` must be `HOLIDAY`, `EXAM`, or `EVENT`.
- `end_date` must be on or after `start_date`.
- `visible_to` may include `TEACHER`, `STUDENT`, and `PARENT`.

## Exam Management

### `POST /api/v1/principal/exams/`

Creates an exam and assigns it to classes or sections.

Request:

```json
{
  "name": "Mid Term Exam",
  "start_date": "2026-09-01",
  "end_date": "2026-09-10",
  "class_ids": [1, 2],
  "section_ids": [7, 8],
  "subjects": [
    {
      "subject_id": 4,
      "max_marks": 100,
      "pass_marks": 35
    }
  ]
}
```

Response:

```json
{
  "id": 20,
  "name": "Mid Term Exam",
  "start_date": "2026-09-01",
  "end_date": "2026-09-10",
  "status": "DRAFT",
  "subjects": [
    {
      "subject_id": 4,
      "subject_name": "Mathematics",
      "max_marks": 100,
      "pass_marks": 35
    }
  ]
}
```

Required future models:

- `Exam`
- `ExamSubject`
- `ExamSection`
- `StudentMark`

Validation:

- Exam name should be unique per school and date range if the implementation requires uniqueness.
- Dates must be valid.
- Subjects, classes, and sections must belong to the principal's school.

### `GET /api/v1/principal/exams/`

Lists exams for the principal's school.

Query params:

- `status`: optional.
- `class_id`: optional.
- `section_id`: optional.

## Result Dashboard

### `GET /api/v1/principal/results/`

Returns marks, ranks, comparison, and subject totals.

Query params:

- `exam_id`: optional.
- `class_id`: optional.
- `section_id`: optional.
- `subject_id`: optional.
- `student_id`: optional.

Response:

```json
{
  "filters": {
    "exam_id": 20,
    "class_id": 1,
    "section_id": 7
  },
  "summary": {
    "student_count": 40,
    "average_percentage": 78.5,
    "highest_percentage": 96.0,
    "lowest_percentage": 42.0
  },
  "results": [
    {
      "student_id": 101,
      "student_name": "Ravi Kumar",
      "roll_number": "12",
      "total_marks": 430,
      "max_marks": 500,
      "percentage": 86.0,
      "rank": 3,
      "subjects": [
        {
          "subject_id": 4,
          "subject_name": "Mathematics",
          "marks_obtained": 92,
          "max_marks": 100
        }
      ]
    }
  ]
}
```

## Analytics Dashboard

### `GET /api/v1/principal/analytics/`

Returns principal analytics.

Query params:

- `class_id`: optional.
- `section_id`: optional.
- `subject_id`: optional.
- `teacher_id`: optional.
- `date_from`: optional.
- `date_to`: optional.

Response:

```json
{
  "class_performance_trends": [],
  "subject_wise_analysis": [],
  "teacher_effectiveness": [],
  "student_growth_tracking": []
}
```

Analytics may be computed live from attendance, homework, exam marks, and content activity, or backed by future read models.

## Principal Test Scenarios

- Non-principal users receive `PERMISSION_DENIED` for all principal endpoints.
- Configuration updates only affect the current school.
- Teacher onboarding creates a user with role `TEACHER`.
- Teacher update rejects cross-school subjects and sections.
- Bulk upload processes valid rows and records invalid row errors.
- Announcement targeting validates audience and target fields.
- Calendar creation rejects invalid date ranges.
- Exam creation rejects cross-school sections and subjects.
- Result and analytics endpoints never expose another school's data.
