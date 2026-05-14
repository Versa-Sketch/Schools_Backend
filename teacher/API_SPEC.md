# Teacher API Spec

## Purpose

This app owns teacher workflows: assigned sections, attendance, class teacher announcements, study materials, homework, exam marks entry, and parent query replies.

All endpoints use `/api/v1/teacher/`, require JWT authentication, and require role `TEACHER`.

## ID Format

All `id` and `*_id` fields are UUID strings (`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`).

## Permissions

- Teachers can access sections assigned through `TeacherProfile.assigned_sections`.
- Teachers can access sections where they are set as `Section.class_teacher`.
- Cross-school or unassigned section access returns `NOT_FOUND` or `PERMISSION_DENIED`.

## Profile Picture

### `PATCH /api/v1/teacher/profile/pic/`

Uploads or replaces the teacher's profile picture.

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

## Sections And Students

### `GET /api/v1/teacher/sections/`

Response:

```json
{
  "count": 1,
  "results": [
    {
      "id": "33333333-3333-3333-3333-333333333333",
      "class_id": "22222222-2222-2222-2222-222222222222",
      "class_name": "Class 5",
      "section_name": "A",
      "is_class_teacher": true,
      "student_count": 40
    }
  ]
}
```

### `GET /api/v1/teacher/sections/{section_id}/students/`

`{section_id}` is a UUID.

Response:

```json
{
  "count": 2,
  "results": [
    {
      "id": "66666666-6666-6666-6666-666666666666",
      "name": "Aarav Mehta",
      "roll_number": "1",
      "admission_number": "ADM001"
    },
    {
      "id": "66666666-6666-6666-6666-666666666667",
      "name": "Bhavya Rao",
      "roll_number": "2",
      "admission_number": "ADM002"
    }
  ]
}
```

## Attendance

### `POST /api/v1/teacher/attendance-sessions/`

Request:

```json
{
  "section_id": "33333333-3333-3333-3333-333333333333",
  "date": "2026-05-05",
  "slot": "MORNING"
}
```

Response:

```json
{
  "id": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
  "section_id": "33333333-3333-3333-3333-333333333333",
  "date": "2026-05-05",
  "slot": "MORNING",
  "taken_by": {
    "id": "55555555-5555-5555-5555-555555555555",
    "name": "Anita Sharma"
  },
  "confirmed_at": null,
  "records": []
}
```

Validation:

- `slot` must be `MORNING` or `AFTERNOON`.
- If school attendance frequency is `ONCE`, only `MORNING` is allowed.
- If a session already exists for section/date/slot, return it instead of creating a duplicate.

### `PUT /api/v1/teacher/attendance-sessions/{id}/students/`

`{id}` is the session UUID.

Request:

```json
{
  "records": [
    {
      "student_id": "66666666-6666-6666-6666-666666666666",
      "status": "PRESENT"
    },
    {
      "student_id": "66666666-6666-6666-6666-666666666667",
      "status": "ABSENT"
    }
  ]
}
```

Response:

```json
{
  "session_id": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
  "records": [
    {
      "student_id": "66666666-6666-6666-6666-666666666666",
      "student_name": "Aarav Mehta",
      "status": "PRESENT"
    },
    {
      "student_id": "66666666-6666-6666-6666-666666666667",
      "student_name": "Bhavya Rao",
      "status": "ABSENT"
    }
  ]
}
```

### `POST /api/v1/teacher/attendance-sessions/{id}/confirm/`

`{id}` is the session UUID.

Response:

```json
{
  "session_id": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
  "confirmed_at": "2026-05-05T09:30:00Z",
  "absent_count": 1,
  "notification_logs_created": 1
}
```

## Announcements

### `POST /api/v1/teacher/announcements/`

Request:

```json
{
  "section_id": "33333333-3333-3333-3333-333333333333",
  "title": "Math Notebook",
  "body": "Bring your math notebook tomorrow.",
  "publish_now": true
}
```

Response:

```json
{
  "id": "99999999-9999-9999-9999-999999999999",
  "title": "Math Notebook",
  "audience": "SECTION",
  "section_id": "33333333-3333-3333-3333-333333333333",
  "published_at": "2026-05-05T10:00:00Z",
  "attachments": []
}
```

Validation:

- Teacher must be the class teacher for the section.

## Study Materials

### `POST /api/v1/teacher/study-materials/`

Content type: `multipart/form-data`

Fields: `section_id` (UUID), `subject_id` (UUID), `title`, `description`, `material_date`, `file`

Response:

```json
{
  "id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
  "section_id": "33333333-3333-3333-3333-333333333333",
  "subject": {
    "id": "44444444-4444-4444-4444-444444444444",
    "name": "Mathematics"
  },
  "title": "Fractions Worksheet",
  "description": "Practice worksheet.",
  "material_date": "2026-05-05",
  "file_url": "/media/study_materials/fractions.pdf",
  "uploaded_by": {
    "id": "55555555-5555-5555-5555-555555555555",
    "name": "Anita Sharma"
  }
}
```

### `GET /api/v1/teacher/study-materials/`

Query params: `section_id` (UUID), `subject_id` (UUID), `date_from`, `date_to`

## Homework

### `POST /api/v1/teacher/homework/`

Content type: `application/json` or `multipart/form-data`

Request:

```json
{
  "section_id": "33333333-3333-3333-3333-333333333333",
  "subject_id": "44444444-4444-4444-4444-444444444444",
  "description": "Complete exercise 5.1.",
  "deadline": "2026-05-06T17:00:00Z"
}
```

For file attachments, send the same fields as multipart form data and include 0-N `files` fields.

Response:

```json
{
  "id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
  "section_id": "33333333-3333-3333-3333-333333333333",
  "subject": {
    "id": "44444444-4444-4444-4444-444444444444",
    "name": "Mathematics"
  },
  "description": "Complete exercise 5.1.",
  "deadline": "2026-05-06T17:00:00Z",
  "attachments": [
    {
      "url": "https://bucket.s3.region.amazonaws.com/homework/uuid.pdf",
      "filename": "exercise-5-1.pdf"
    }
  ]
}
```

### `GET /api/v1/teacher/homework/`

Query params: `section_id` (UUID), `subject_id` (UUID), `deadline_from`, `deadline_to`

Each result includes `attachments` with `url` and `filename`.

## Exam Marks

### `GET /api/v1/teacher/exams/{exam_id}/marks/` and `PUT /api/v1/teacher/exams/{exam_id}/marks/`

`{exam_id}` is a UUID. Returns `501 EXAM_MODEL_NOT_IMPLEMENTED`.

## Parent Queries

### `GET /api/v1/teacher/parent-queries/`

Query params: `status` (`OPEN`, `ANSWERED`, `CLOSED`), `section_id` (UUID)

Response:

```json
{
  "count": 1,
  "results": [
    {
      "id": "ffffffff-ffff-ffff-ffff-ffffffffffff",
      "subject": "Homework doubt",
      "message": "Please explain the homework.",
      "status": "OPEN",
      "parent": {
        "id": "77777777-7777-7777-7777-777777777777",
        "name": "Ramesh Kumar"
      },
      "student": {
        "id": "66666666-6666-6666-6666-666666666666",
        "name": "Aarav Mehta"
      },
      "section_id": "33333333-3333-3333-3333-333333333333",
      "created_at": "2026-05-05T12:00:00Z"
    }
  ]
}
```

### `GET /api/v1/teacher/parent-queries/{id}/`

`{id}` is the query UUID. Returns the query detail with full reply thread.

Response:

```json
{
  "id": "ffffffff-ffff-ffff-ffff-ffffffffffff",
  "subject": "Homework doubt",
  "message": "Please explain the homework.",
  "status": "OPEN",
  "parent": {
    "id": "77777777-7777-7777-7777-777777777777",
    "name": "Ramesh Kumar"
  },
  "student": {
    "id": "66666666-6666-6666-6666-666666666666",
    "name": "Aarav Mehta"
  },
  "section_id": "33333333-3333-3333-3333-333333333333",
  "created_at": "2026-05-05T12:00:00Z",
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

Errors:
- `404` if query not found or does not belong to this teacher

### `POST /api/v1/teacher/parent-queries/{id}/replies/`

`{id}` is the query UUID.

Request:

```json
{
  "message": "I will explain it again tomorrow.",
  "mark_answered": true
}
```

Response:

```json
{
  "id": "b1b1b1b1-b1b1-b1b1-b1b1-b1b1b1b1b1b1",
  "query_id": "ffffffff-ffff-ffff-ffff-ffffffffffff",
  "sender_id": "88888888-8888-8888-8888-888888888888",
  "message": "I will explain it again tomorrow.",
  "query_status": "ANSWERED",
  "created_at": "2026-05-05T12:15:00Z"
}
```

### `POST /api/v1/teacher/parent-queries/{id}/close/`

`{id}` is the query UUID. No request body required.

Response:

```json
{
  "id": "ffffffff-ffff-ffff-ffff-ffffffffffff",
  "status": "CLOSED"
}
```

Errors:
- `404` if query not found or does not belong to this teacher
- `400` if query is already `CLOSED`

## Teacher Test Scenarios

- Teacher sees only assigned and class teacher sections.
- UUID path params (`section_id`, `session_id`, `query_id`, `exam_id`) reject non-UUID values with 404.
- Attendance session uniqueness enforced per section/date/slot.
- Once-per-day schools reject afternoon attendance.
- Confirmed attendance cannot be edited.
- Teacher announcements limited to class teacher sections.
- Study materials and homework reject unassigned section UUIDs.
- Parent query replies update status when `mark_answered` is true.
