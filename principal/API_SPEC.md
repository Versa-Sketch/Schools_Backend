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

## Profile Picture

### `PATCH /api/v1/principal/profile/pic/`

Uploads or replaces the principal's profile picture.

Content type: `multipart/form-data`

Field: `profile_pic` — image file (JPEG, PNG, WebP, or GIF; maximum 50 MB).

Response:

```json
{
  "profile_pic_url": "https://bucket.s3.region.amazonaws.com/profile_pics/uuid.jpg"
}
```

The returned URL is also included in the `profile_pic_url` field of `GET /api/v1/me/`.

Validation:

- `profile_pic` field is required. Returns `VALIDATION_ERROR` otherwise.
- File MIME type must be one of: `image/jpeg`, `image/png`, `image/webp`, `image/gif`. Returns `VALIDATION_ERROR` otherwise.
- File size must not exceed 50 MB. Returns `VALIDATION_ERROR` otherwise.
- S3 upload failure returns `UPLOAD_FAILED`.

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

## School Logo

### `POST /api/v1/principal/school/logo/`

Uploads or replaces the school's logo.

Content type: `multipart/form-data`

Field: `logo` — image file (JPEG, PNG, WebP, or GIF; maximum 50 MB).

Response:

```json
{
  "logo": "https://bucket.s3.region.amazonaws.com/schools/logos/uuid.jpg"
}
```

Validation:

- `logo` field is required. Returns `VALIDATION_ERROR` otherwise.
- File MIME type must be a valid image type. Returns `VALIDATION_ERROR` otherwise.
- S3 upload failure returns `UPLOAD_FAILED`.

### `DELETE /api/v1/principal/school/logo/`

Removes the school's logo (sets it to `null`).

Response:

```json
{
  "logo": null
}
```

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

### `POST /api/v1/principal/teachers/bulk-upload/`

Request:

- Method: `POST`
- Content-Type: `multipart/form-data`
- Body:
  - `csv_file` (File, required)

Expected CSV Columns:
- `name` (required)
- `phone_number` (required)
- `username` (required)
- `primary_subject_id` (optional, UUID)
- `assigned_section_ids` (optional, comma-separated UUIDs)

> **Note:** The `password` column is no longer required or used. Each teacher's password is auto-generated as `pass@{phone_number}` (e.g. `pass@9999999999`), consistent with student and parent accounts.

Response (200 OK):

```json
{
  "batch_id": "775e4c3a-9e12-4c56-8a50-...",
  "status": "PROCESSING",
  "total_rows": 50,
  "success_count": 0,
  "error_count": 0
}
```

### `GET /api/v1/principal/teachers/bulk-upload/{batch_id}/`

Response (200 OK):

```json
{
  "batch_id": "775e4c3a-9e12-4c56-8a50-...",
  "status": "COMPLETED",
  "total_rows": 50,
  "success_count": 48,
  "error_count": 2,
  "error_report_url": "https://s3.amazonaws.com/..."
}
```
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

### `POST /api/v1/principal/teachers/{id}/assign-sections/`

`{id}` is the teacher profile UUID. This endpoint completely replaces the teacher's currently assigned sections and primary subject with the ones provided.

Request:

```json
{
  "subject_id": "44444444-4444-4444-4444-444444444444",
  "section_ids": [
    "33333333-3333-3333-3333-333333333333",
    "33333333-3333-3333-3333-333333333334"
  ]
}
```

Response (`200 OK`):

```json
{
  "message": "Sections and subject assigned successfully.",
  "teacher_id": "55555555-5555-5555-5555-555555555555",
  "primary_subject": {
    "id": "44444444-4444-4444-4444-444444444444",
    "name": "Mathematics"
  },
  "assigned_sections": [
    {
      "id": "33333333-3333-3333-3333-333333333333",
      "class": "Class 5",
      "name": "A"
    },
    {
      "id": "33333333-3333-3333-3333-333333333334",
      "class": "Class 5",
      "name": "B"
    }
  ]
}
```

Validation:

- `subject_id` and `section_ids` are required.
- All IDs must belong to the principal's school. If any ID is invalid or belongs to another school, a `400 ValidationException` is returned.
- If the teacher doesn't exist, `404 NOT_FOUND` is returned.

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
- Principal can update or delete any active announcement in their school, including teacher-created announcements.

### `PATCH /api/v1/principal/announcements/{announcement_id}/`

Content type: `multipart/form-data` when attachments are included.

Partial update fields: `title`, `body`, `audience`, `class_ids`, `section_ids`, `publish_now`, `attachments`.

If `audience` is changed to `CLASS`, `class_ids` is required. If `audience` is changed to `SECTION`, `section_ids` is required. New `attachments` are appended to the announcement.

### `DELETE /api/v1/principal/announcements/{announcement_id}/`

Soft deletes the announcement by marking it inactive. Inactive announcements are hidden from common announcement list/detail APIs.

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

Response (`201 Created`):

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

### `PATCH /api/v1/principal/calendar-events/{event_id}/`

`{event_id}` is the calendar event UUID. All fields are optional — only provided fields are updated.

Request:

```json
{
  "title": "Updated Annual Day",
  "event_type": "EVENT",
  "start_date": "2026-08-11",
  "end_date": "2026-08-11",
  "description": "Updated description.",
  "visible_to": ["TEACHER", "STUDENT"]
}
```

Response (`200 OK`): updated event object (same shape as POST response).

Errors:

- `404 NOT_FOUND` if `event_id` does not belong to the principal's school.
- `VALIDATION_ERROR` if `event_type` is invalid or `end_date` is before `start_date`.

### `DELETE /api/v1/principal/calendar-events/{event_id}/`

`{event_id}` is the calendar event UUID.

Response (`200 OK`):

```json
{
  "success": true,
  "message": "Calendar event deleted successfully."
}
```

Errors:

- `404 NOT_FOUND` if `event_id` does not belong to the principal's school.

## Classes, Subjects, and Sections Management

### `POST /api/v1/principal/classes/`
Create a new class.

Request:
```json
{
  "name": "Class 10",
  "display_order": 10
}
```
Response (`201 Created`):
```json
{
  "id": "22222222-2222-2222-2222-222222222222",
  "name": "Class 10",
  "display_order": 10
}
```

### `PATCH /api/v1/principal/classes/{class_id}/`
Update a class. Only provided fields are updated.

Request:
```json
{
  "name": "Class X"
}
```
Response (`200 OK`): Updated class object.

### `DELETE /api/v1/principal/classes/{class_id}/`
Deletes a class.
Returns `ValidationException` (400) if the class contains sections or students.

Response (`200 OK`):
```json
{
  "success": true,
  "message": "Class deleted successfully."
}
```

---

### `POST /api/v1/principal/subjects/`
Create a new subject.

Request:
```json
{
  "name": "Physics",
  "code": "PHY",
  "is_active": true
}
```
Response (`201 Created`):
```json
{
  "id": "44444444-4444-4444-4444-444444444444",
  "name": "Physics",
  "code": "PHY",
  "is_active": true
}
```

### `PATCH /api/v1/principal/subjects/{subject_id}/`
Update a subject.

Request:
```json
{
  "is_active": false
}
```
Response (`200 OK`): Updated subject object.

### `DELETE /api/v1/principal/subjects/{subject_id}/`
Deletes a subject.
Returns `ValidationException` (400) if the subject is in use.

Response (`200 OK`):
```json
{
  "success": true,
  "message": "Subject deleted successfully."
}
```

---

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

### `POST /api/v1/principal/sections/`
Create a new section within a class.

Request:
```json
{
  "class_id": "22222222-2222-2222-2222-222222222222",
  "name": "C",
  "class_teacher_id": "55555555-5555-5555-5555-555555555555",
  "parent_query_enabled": true
}
```
Response (`201 Created`): Same shape as a single item from the list above.

### `PATCH /api/v1/principal/sections/{section_id}/`

Updates a section's details. `class_teacher_id` can be set to `null` to remove the class teacher.

Request:

```json
{
  "name": "D",
  "class_teacher_id": null,
  "parent_query_enabled": false
}
```

Response (`200 OK`): updated section object.

### `DELETE /api/v1/principal/sections/{section_id}/`

Deletes a section.
Returns `ValidationException` (400) if the section contains students.

Response (`200 OK`):
```json
{
  "success": true,
  "message": "Section deleted successfully."
}
```

Rules:

- Section-level disable overrides the school-level `parent_query_enabled` setting.
- A parent can only create queries when **both** the school-level and section-level flags are `true`.
- The `is_parent_query_disabled` field returned in `GET /api/v1/parent/profile/` reflects the combined result of both flags.

## Attendance

### `GET /api/v1/principal/attendance/daily-summary/`

Returns class-wise attendance counts and percentage for a given date. Only confirmed attendance sessions are counted. A student is considered **present** for the day if they were marked present in any slot (MORNING or AFTERNOON).

Query params:

- `date`: optional `YYYY-MM-DD` — defaults to today. Invalid formats fall back to today.

Response:

```json
{
  "date": "2026-05-11",
  "classes": [
    {
      "class_id": "22222222-2222-2222-2222-222222222222",
      "class_name": "Class 5",
      "total_students": 80,
      "present_count": 72,
      "absent_count": 8,
      "attendance_percentage": 90.0
    },
    {
      "class_id": "22222222-2222-2222-2222-222222222223",
      "class_name": "Class 6",
      "total_students": 60,
      "present_count": 45,
      "absent_count": 15,
      "attendance_percentage": 75.0
    }
  ]
}
```

Notes:

- `attendance_percentage = present_count / total_students * 100`, rounded to 2 decimal places.
- `absent_count` includes students whose section's attendance has not been confirmed yet (i.e., `absent_count = total_students - present_count`).
- Classes are ordered by `display_order` then `name`.

---

### `GET /api/v1/principal/attendance/classes/{class_id}/`

Returns the full attendance breakdown for a single class: class-level present/absent student name lists, class percentage, and the same breakdown per section. `{class_id}` is a UUID.

Query params:

- `date`: optional `YYYY-MM-DD` — defaults to today.

Response:

```json
{
  "date": "2026-05-11",
  "class_id": "22222222-2222-2222-2222-222222222222",
  "class_name": "Class 5",
  "total_students": 80,
  "present_count": 72,
  "absent_count": 8,
  "attendance_percentage": 90.0,
  "present_students": [
    {"id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "name": "Alice", "section": "A"},
    {"id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "name": "Bob", "section": "B"}
  ],
  "absent_students": [
    {"id": "cccccccc-cccc-cccc-cccc-cccccccccccc", "name": "Charlie", "section": "A"}
  ],
  "sections": [
    {
      "section_id": "33333333-3333-3333-3333-333333333333",
      "section_name": "A",
      "total_students": 40,
      "present_count": 38,
      "absent_count": 2,
      "attendance_percentage": 95.0,
      "present_students": [
        {"id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "name": "Alice"}
      ],
      "absent_students": [
        {"id": "cccccccc-cccc-cccc-cccc-cccccccccccc", "name": "Charlie"}
      ]
    },
    {
      "section_id": "33333333-3333-3333-3333-333333333334",
      "section_name": "B",
      "total_students": 40,
      "present_count": 34,
      "absent_count": 6,
      "attendance_percentage": 85.0,
      "present_students": [
        {"id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "name": "Bob"}
      ],
      "absent_students": []
    }
  ]
}
```

Notes:

- `absent_count` reflects only students explicitly marked `ABSENT` in a confirmed session. It does **not** include students with no record (e.g. future dates or dates with no session taken).
- Students with no confirmed attendance record for the day are counted in `total_students` but **not listed** in `present_students` or `absent_students`, and are **not** counted in `absent_count`.
- For a future date or a date with no confirmed session: `present_count` and `absent_count` will both be `0`; `present_students` and `absent_students` will be empty arrays.
- Class-level `present_students` and `absent_students` include students from all sections, each with a `section` field showing the section name.
- Section-level name lists omit the `section` field.
- Sections are ordered alphabetically by name.

Errors:

- `404 NOT_FOUND` if `class_id` does not belong to the principal's school.

---

### `GET /api/v1/principal/students/{student_id}/attendance/`

Returns the attendance history for a specific student. The student must belong to the principal's school. `{student_id}` is a UUID.

Query params (all optional):

| Parameter | Type | Description |
|---|---|---|
| `date_from` | `YYYY-MM-DD` | Filter records on or after this date |
| `date_to` | `YYYY-MM-DD` | Filter records on or before this date |
| `slot` | `MORNING` \| `AFTERNOON` | Filter by attendance slot |
| `status` | `PRESENT` \| `ABSENT` | Filter by attendance status |

Response:

```json
{
  "count": 3,
  "results": [
    {
      "date": "2026-05-14",
      "slot": "MORNING",
      "status": "PRESENT",
      "confirmed_at": "2026-05-14T08:45:00+05:30"
    },
    {
      "date": "2026-05-13",
      "slot": "MORNING",
      "status": "ABSENT",
      "confirmed_at": "2026-05-13T08:50:00+05:30"
    },
    {
      "date": "2026-05-12",
      "slot": "MORNING",
      "status": "PRESENT",
      "confirmed_at": "2026-05-12T08:47:00+05:30"
    }
  ],
  "summary": {
    "present_count": 2,
    "absent_count": 1,
    "attendance_percentage": 66.7
  }
}
```

Notes:

- Results are ordered by date descending.
- Only confirmed attendance sessions are included.
- `attendance_percentage = present_count / (present_count + absent_count) * 100`, rounded to 1 decimal place.

Errors:

- `404 NOT_FOUND` if `student_id` does not belong to the principal's school.

---

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
- UUID path params (`teacher_id`, `batch_id`, `student_id`, `class_id`) reject non-UUID values with 404.
- Bulk upload processes valid rows and records invalid row errors.
- Calendar creation rejects invalid date ranges.
- Profile picture upload requires a valid image file; wrong MIME type returns `VALIDATION_ERROR`.
- Student attendance history returns `NOT_FOUND` for cross-school student UUIDs.
- Class attendance detail for a future date or a date with no confirmed session returns `present_count: 0`, `absent_count: 0`, and empty student lists.
