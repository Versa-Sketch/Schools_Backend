# Principal API Spec

## Purpose

This app owns principal-only school administration APIs: configuration, teacher onboarding, student onboarding, announcements, calendar management, exams, result dashboard, and analytics dashboard.

All endpoints use `/api/v1/principal/`, require JWT authentication, and require role `PRINCIPAL`.

## ID Format

All `id` and `*_id` fields are UUID strings (`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`).

## Permissions

- Only authenticated principals can access these endpoints.
- Every object must belong to the principal's school.
- Cross-school object IDs use `NOT_FOUND` or `PERMISSION_DENIED`.

## School Configuration

### `GET /api/v1/principal/configuration/`

Response:

```json
{
  "school_id": "11111111-1111-1111-1111-111111111111",
  "attendance_frequency": "TWICE",
  "whatsapp_absent_automation_enabled": true,
  "parent_query_enabled": true,
  "subdomain": "green-valley"
}
```

### `PATCH /api/v1/principal/configuration/`

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

## Teacher Onboarding

### `POST /api/v1/principal/teachers/`

Request:

```json
{
  "name": "Anita Sharma",
  "mobile_number": "9999999999",
  "username": "anita.teacher",
  "password": "temporary-password",
  "primary_subject_id": "44444444-4444-4444-4444-444444444444",
  "assigned_section_ids": [
    "33333333-3333-3333-3333-333333333333",
    "33333333-3333-3333-3333-333333333334"
  ]
}
```

Response:

```json
{
  "id": "55555555-5555-5555-5555-555555555555",
  "user": {
    "id": "88888888-8888-8888-8888-888888888888",
    "username": "anita.teacher",
    "role": "TEACHER"
  },
  "name": "Anita Sharma",
  "mobile_number": "9999999999",
  "primary_subject": {
    "id": "44444444-4444-4444-4444-444444444444",
    "name": "Mathematics"
  },
  "assigned_sections": [
    {
      "id": "33333333-3333-3333-3333-333333333333",
      "class_name": "Class 5",
      "section_name": "A"
    }
  ]
}
```

Validation:

- `username` must be unique.
- `primary_subject_id` must be a valid UUID belonging to the principal's school.
- All `assigned_section_ids` must be valid UUIDs belonging to the principal's school.

### `GET /api/v1/principal/teachers/`

Query params:

- `subject_id`: optional UUID.
- `section_id`: optional UUID.
- `search`: optional name/mobile/username search.

### `PATCH /api/v1/principal/teachers/{id}/`

`{id}` is the teacher profile UUID.

Request:

```json
{
  "name": "Anita Sharma",
  "mobile_number": "9999999999",
  "primary_subject_id": "44444444-4444-4444-4444-444444444444",
  "assigned_section_ids": [
    "33333333-3333-3333-3333-333333333333"
  ]
}
```

## Student Onboarding

### `POST /api/v1/principal/students/bulk-upload/`

Content type: `multipart/form-data`

Fields:

- `csv_file`: required CSV file.

Required CSV columns: `student_name`, `class`, `section`, `parent_name`, `parent_mobile_number`

Optional CSV columns: `roll_number`, `admission_number`, `student_username`, `parent_username`

Response:

```json
{
  "batch_id": "a0a0a0a0-a0a0-a0a0-a0a0-a0a0a0a0a0a0",
  "status": "COMPLETED",
  "total_rows": 50,
  "success_count": 48,
  "error_count": 2
}
```

### `GET /api/v1/principal/students/bulk-upload/{batch_id}/`

`{batch_id}` is a UUID.

Response:

```json
{
  "batch_id": "a0a0a0a0-a0a0-a0a0-a0a0-a0a0a0a0a0a0",
  "status": "COMPLETED",
  "total_rows": 50,
  "success_count": 48,
  "error_count": 2
}
```

## Announcements

### `POST /api/v1/principal/announcements/`

Content type: `multipart/form-data` when attachments are included.

Request fields:

```json
{
  "title": "School Reopens",
  "body": "School reopens on Monday.",
  "audience": "SECTION",
  "class_ids": ["22222222-2222-2222-2222-222222222222"],
  "section_ids": ["33333333-3333-3333-3333-333333333333"],
  "publish_now": true
}
```

Response:

```json
{
  "id": "99999999-9999-9999-9999-999999999999",
  "title": "School Reopens",
  "audience": "SECTION",
  "published_at": "2026-06-01T09:00:00Z",
  "attachments": []
}
```

Rules:

- `SCHOOL` announcements do not require targets.
- `CLASS` announcements require one or more `class_ids` (UUID array).
- `SECTION` announcements require one or more `section_ids` (UUID array).

## Calendar Management

### `POST /api/v1/principal/calendar-events/`

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

Response:

```json
{
  "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
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

## Section Query Management

### `GET /api/v1/principal/sections/`

Lists all sections in the principal's school with their `parent_query_enabled` status.

Query params:

- `class_id`: optional UUID — filters sections belonging to that class.

Response:

```json
{
  "count": 2,
  "results": [
    {
      "id": "33333333-3333-3333-3333-333333333333",
      "name": "A",
      "academic_class": {
        "id": "22222222-2222-2222-2222-222222222222",
        "name": "Class 5"
      },
      "class_teacher": {
        "id": "55555555-5555-5555-5555-555555555555",
        "name": "Anita Sharma"
      },
      "parent_query_enabled": true
    }
  ]
}
```

### `PATCH /api/v1/principal/sections/{section_id}/`

Enables or disables parent queries for a specific section. `{section_id}` is a UUID.

Request:

```json
{
  "parent_query_enabled": false
}
```

Response: updated section object (same shape as a single item from the list above).

Validation:

- `section_id` must belong to the principal's school.
- `parent_query_enabled` is required and must be a boolean.

Rules:

- Section-level disable overrides the school-level `parent_query_enabled` setting.
- A parent can only create queries when **both** the school-level and section-level flags are `true`.
- The `is_parent_query_disabled` field returned in `GET /api/v1/parent/profile/` reflects the combined result of both flags.

## Exam Management

### `POST /api/v1/principal/exams/` and `GET /api/v1/principal/exams/`

Returns `501 EXAM_MODEL_NOT_IMPLEMENTED` — models `Exam`, `ExamSubject`, `ExamSection`, `StudentMark` not yet created.

## Result Dashboard

### `GET /api/v1/principal/results/`

Returns `501 EXAM_MODEL_NOT_IMPLEMENTED`.

## Analytics Dashboard

### `GET /api/v1/principal/analytics/`

Response:

```json
{
  "class_performance_trends": [],
  "subject_wise_analysis": [],
  "teacher_effectiveness": [],
  "student_growth_tracking": []
}
```

## Principal Test Scenarios

- Non-principal users receive `PERMISSION_DENIED` for all principal endpoints.
- Configuration updates only affect the current school.
- Teacher creation rejects non-UUID or cross-school subject/section IDs.
- UUID path params (`teacher_id`, `batch_id`) reject non-UUID values with 404.
- Bulk upload processes valid rows and records invalid row errors.
- Calendar creation rejects invalid date ranges.
