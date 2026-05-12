# Student API Spec

## Purpose

This app owns student-facing read-only APIs for profile, attendance, announcements, study materials, homework, calendar, exams, and results.

All endpoints use `/api/v1/student/`, require JWT authentication, and require role `STUDENT`.

## ID Format

All `id` and `*_id` fields are UUID strings (`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`).

## Permissions

- Students can only access their own profile and own section data.
- Students cannot mutate attendance, homework, materials, announcements, exams, or results.

## Profile Picture

### `PATCH /api/v1/student/profile/pic/`

Uploads or replaces the student's profile picture.

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

- `profile_pic` field is required.
- File MIME type must be one of: `image/jpeg`, `image/png`, `image/webp`, `image/gif`. Returns `VALIDATION_ERROR` otherwise.
- File size must not exceed 50 MB. Returns `VALIDATION_ERROR` otherwise.
- S3 upload failure returns `UPLOAD_FAILED`.

## Profile

### `GET /api/v1/student/profile/`

Response:

```json
{
  "id": "66666666-6666-6666-6666-666666666666",
  "name": "Aarav Mehta",
  "roll_number": "1",
  "admission_number": "ADM001",
  "is_active": true,
  "academic_class": {
    "id": "22222222-2222-2222-2222-222222222222",
    "name": "Class 5"
  },
  "section": {
    "id": "33333333-3333-3333-3333-333333333333",
    "name": "A"
  },
  "school": {
    "id": "11111111-1111-1111-1111-111111111111",
    "name": "Green Valley School"
  }
}
```

## Attendance

### `GET /api/v1/student/attendance/`

Query params: `date_from`, `date_to`, `slot` (`MORNING`/`AFTERNOON`), `status` (`PRESENT`/`ABSENT`)

Response:

```json
{
  "count": 1,
  "results": [
    {
      "date": "2026-05-05",
      "slot": "MORNING",
      "status": "PRESENT",
      "confirmed_at": "2026-05-05T09:30:00Z"
    }
  ],
  "summary": {
    "present_count": 20,
    "absent_count": 2,
    "attendance_percentage": 90.9
  }
}
```

Rules:

- Only confirmed attendance sessions are visible.

## Announcements

### `GET /api/v1/student/announcements/`

Visible announcements: school-wide, class-level for student's class, section-level for student's section.

Response:

```json
{
  "count": 1,
  "results": [
    {
      "id": "99999999-9999-9999-9999-999999999999",
      "title": "School Reopens",
      "body": "School reopens on Monday.",
      "author_role": "PRINCIPAL",
      "audience": "SCHOOL",
      "published_at": "2026-06-01T09:00:00Z",
      "attachments": []
    }
  ]
}
```

## Study Materials

### `GET /api/v1/student/study-materials/`

Query params: `subject_id` (UUID), `date_from`, `date_to`

Response:

```json
{
  "count": 1,
  "results": [
    {
      "id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
      "title": "Fractions Worksheet",
      "description": "Practice worksheet.",
      "subject": {
        "id": "44444444-4444-4444-4444-444444444444",
        "name": "Mathematics"
      },
      "material_date": "2026-05-05",
      "file_url": "/media/study_materials/fractions.pdf",
      "uploaded_by": {
        "id": "55555555-5555-5555-5555-555555555555",
        "name": "Anita Sharma"
      }
    }
  ]
}
```

## Homework

### `GET /api/v1/student/homework/`

Query params: `subject_id` (UUID), `deadline_from`, `deadline_to`

Response:

```json
{
  "count": 1,
  "results": [
    {
      "id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
      "subject": {
        "id": "44444444-4444-4444-4444-444444444444",
        "name": "Mathematics"
      },
      "description": "Complete exercise 5.1.",
      "deadline": "2026-05-06T17:00:00Z",
      "assigned_by": {
        "id": "55555555-5555-5555-5555-555555555555",
        "name": "Anita Sharma"
      }
    }
  ]
}
```

## Calendar

### `GET /api/v1/student/calendar-events/`

Query params: `event_type`, `start_date`, `end_date`

Response:

```json
{
  "count": 1,
  "results": [
    {
      "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
      "title": "Annual Day",
      "event_type": "EVENT",
      "start_date": "2026-08-10",
      "end_date": "2026-08-10",
      "description": "Annual school event."
    }
  ]
}
```

## Exams

### `GET /api/v1/student/exams/`

Returns all exams the student participated in (requires linked `AnalyticsStudent` record).

Response `200`:
```json
{
  "count": 2,
  "exams": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "exam_name": "Unit Test 1",
      "exam_date": "2026-04-15",
      "analytics_status": "DONE"
    }
  ]
}
```

### `GET /api/v1/student/exams/{exam_id}/subjects/`

Returns subjects with the student's marks summary for a given exam.

Response `200`:
```json
{
  "exam": { "id": "...", "exam_name": "Unit Test 1", "exam_date": "2026-04-15" },
  "subjects": [
    {
      "subject_id": "...",
      "subject_name": "MATHS",
      "total_marks": 65,
      "max_marks": 80,
      "percentage": 81.3,
      "correct": 65,
      "wrong": 10,
      "unattempted": 5,
      "exam_rank": 3
    }
  ]
}
```

### `GET /api/v1/student/exams/{exam_id}/subjects/{subject_id}/questions/`

Returns per-question result (correct / wrong / unattempted) for the student.

Response `200`:
```json
{
  "exam": { "id": "...", "exam_name": "Unit Test 1" },
  "subject": { "id": "...", "name": "MATHS" },
  "questions": [
    { "q_no": 1, "status": "C" },
    { "q_no": 2, "status": "W" },
    { "q_no": 3, "status": "U" }
  ]
}
```

Status values: `C` = Correct, `W` = Wrong, `U` = Unattempted.

## Student Test Scenarios

- Student profile returns only the authenticated student's profile.
- Attendance endpoint shows only confirmed sessions.
- Student cannot see another student's data.
- Announcements include school, class, and section targets.
- Study materials and homework are limited to the student's section.
- All `id` fields in responses are UUID strings.
