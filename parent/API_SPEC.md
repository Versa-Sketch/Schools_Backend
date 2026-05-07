# Parent API Spec

## Purpose

This app owns parent-facing APIs for linked students, attendance, announcements, study materials, homework, calendar events, results, and parent-to-teacher communication.

All endpoints use `/api/v1/parent/`, require JWT authentication, and require role `PARENT`.

## ID Format

All `id` and `*_id` fields are UUID strings (`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`). URL path params `{student_id}` and `{query_id}` are UUIDs.

## Permissions

- Parents can only access students linked through `ParentProfile.students`.
- Parents cannot access unlinked students, even within the same school.
- Cross-school and unlinked student access returns `NOT_FOUND`, `PERMISSION_DENIED`, or `UNLINKED_STUDENT`.

## Profile Picture

### `PATCH /api/v1/parent/profile/pic/`

Uploads or replaces the parent's profile picture.

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

## Profile And Linked Students

### `GET /api/v1/parent/profile/`

Response:

```json
{
  "id": "77777777-7777-7777-7777-777777777777",
  "name": "Ramesh Kumar",
  "mobile_number": "9999999999",
  "school": {
    "id": "11111111-1111-1111-1111-111111111111",
    "name": "Green Valley School"
  },
  "students": [
    {
      "id": "66666666-6666-6666-6666-666666666666",
      "name": "Aarav Mehta",
      "roll_number": "1",
      "academic_class": {
        "id": "22222222-2222-2222-2222-222222222222",
        "name": "Class 5"
      },
      "section": {
        "id": "33333333-3333-3333-3333-333333333333",
        "name": "A"
      }
    }
  ]
}
```

### `GET /api/v1/parent/students/`

Response:

```json
{
  "count": 1,
  "results": [
    {
      "id": "66666666-6666-6666-6666-666666666666",
      "name": "Aarav Mehta",
      "roll_number": "1",
      "admission_number": "ADM001",
      "academic_class": {
        "id": "22222222-2222-2222-2222-222222222222",
        "name": "Class 5"
      },
      "section": {
        "id": "33333333-3333-3333-3333-333333333333",
        "name": "A"
      }
    }
  ]
}
```

## Student Attendance

### `GET /api/v1/parent/students/{student_id}/attendance/`

`{student_id}` is a UUID.

Query params: `date_from`, `date_to`, `slot`, `status`

Response:

```json
{
  "count": 1,
  "results": [
    {
      "date": "2026-05-05",
      "slot": "MORNING",
      "status": "ABSENT",
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

## Announcements

### `GET /api/v1/parent/students/{student_id}/announcements/`

`{student_id}` is a UUID.

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

### `GET /api/v1/parent/students/{student_id}/study-materials/`

`{student_id}` is a UUID. Query params: `subject_id` (UUID), `date_from`, `date_to`

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

### `GET /api/v1/parent/students/{student_id}/homework/`

`{student_id}` is a UUID. Query params: `subject_id` (UUID), `deadline_from`, `deadline_to`

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

### `GET /api/v1/parent/students/{student_id}/calendar-events/`

`{student_id}` is a UUID. Query params: `event_type`, `start_date`, `end_date`

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

## Results

### `GET /api/v1/parent/students/{student_id}/results/`

`{student_id}` is a UUID. Returns `501 EXAM_MODEL_NOT_IMPLEMENTED`.

## Parent Queries

### `POST /api/v1/parent/queries/`

Request:

```json
{
  "student_id": "66666666-6666-6666-6666-666666666666",
  "subject": "Homework doubt",
  "message": "Please explain today's homework."
}
```

Response:

```json
{
  "id": "ffffffff-ffff-ffff-ffff-ffffffffffff",
  "student": {
    "id": "66666666-6666-6666-6666-666666666666",
    "name": "Aarav Mehta"
  },
  "section_id": "33333333-3333-3333-3333-333333333333",
  "assigned_teacher": {
    "id": "55555555-5555-5555-5555-555555555555",
    "name": "Anita Sharma"
  },
  "subject": "Homework doubt",
  "message": "Please explain today's homework.",
  "status": "OPEN",
  "created_at": "2026-05-05T12:00:00Z"
}
```

Validation:

- `student_id` must be a UUID linked to the parent.
- Parent queries must be enabled in `SchoolConfiguration`.
- Student section must have a class teacher assigned.

### `GET /api/v1/parent/queries/`

Query params: `student_id` (UUID), `status` (`OPEN`/`ANSWERED`/`CLOSED`)

Response:

```json
{
  "count": 1,
  "results": [
    {
      "id": "ffffffff-ffff-ffff-ffff-ffffffffffff",
      "subject": "Homework doubt",
      "status": "OPEN",
      "student": {
        "id": "66666666-6666-6666-6666-666666666666",
        "name": "Aarav Mehta"
      },
      "assigned_teacher": {
        "id": "55555555-5555-5555-5555-555555555555",
        "name": "Anita Sharma"
      },
      "created_at": "2026-05-05T12:00:00Z"
    }
  ]
}
```

### `GET /api/v1/parent/queries/{id}/`

`{id}` is the query UUID.

Response:

```json
{
  "id": "ffffffff-ffff-ffff-ffff-ffffffffffff",
  "subject": "Homework doubt",
  "message": "Please explain today's homework.",
  "status": "OPEN",
  "student": {
    "id": "66666666-6666-6666-6666-666666666666",
    "name": "Aarav Mehta"
  },
  "assigned_teacher": {
    "id": "55555555-5555-5555-5555-555555555555",
    "name": "Anita Sharma"
  },
  "replies": [
    {
      "id": "b1b1b1b1-b1b1-b1b1-b1b1-b1b1b1b1b1b1",
      "sender_id": "88888888-8888-8888-8888-888888888888",
      "sender_role": "TEACHER",
      "message": "I will explain it again tomorrow.",
      "created_at": "2026-05-05T12:15:00Z"
    }
  ]
}
```

### `POST /api/v1/parent/queries/{id}/replies/`

`{id}` is the query UUID.

Request:

```json
{
  "message": "Thank you."
}
```

Response:

```json
{
  "id": "b1b1b1b1-b1b1-b1b1-b1b1-b1b1b1b1b1b2",
  "query_id": "ffffffff-ffff-ffff-ffff-ffffffffffff",
  "sender_id": "f0f0f0f0-f0f0-f0f0-f0f0-f0f0f0f0f0f0",
  "message": "Thank you.",
  "created_at": "2026-05-05T12:20:00Z"
}
```

## Parent Test Scenarios

- Parent profile returns only linked students.
- UUID path params (`student_id`, `query_id`) reject non-UUID values with 404.
- Parent cannot access unlinked student data — returns `UNLINKED_STUDENT`.
- Attendance shows only confirmed sessions.
- Announcements match the linked student's school, class, and section.
- Parent query creation fails when school configuration disables queries.
- Parent query creation fails when the student has no class teacher.
- Parent can read and reply only to their own queries.
- Closed queries reject new replies.
- All `id` fields in responses are UUID strings.
