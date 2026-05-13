# Core API Spec

## Purpose

This app owns shared authentication, school context, common lookup data, announcements, and calendar visibility. All endpoints use REST-style paths under `/api/v1/` and assume JWT authentication unless explicitly marked public.

## ID Format

All model IDs are UUIDs. Every `id` and `*_id` field in requests and responses is a UUID string in the format `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`.

## Shared API Defaults

- Base path: `/api/v1/`
- Auth: JWT access and refresh tokens.
- School scoping: every authenticated request is scoped to the current user's school.
- List response:

```json
{
  "count": 1,
  "results": []
}
```

- Object response: a single JSON object.

## Common Error API

All API errors must use this common response format:

```json
{
  "success": false,
  "code": "VALIDATION_ERROR",
  "details": "Human readable error message."
}
```

Fields:

- `success`: always `false` for error responses.
- `code`: stable machine-readable error code.
- `details`: human-readable explanation.

Common error codes:

- `AUTHENTICATION_FAILED`
- `PERMISSION_DENIED`
- `NOT_FOUND`
- `VALIDATION_ERROR`
- `SCHOOL_SCOPE_ERROR`
- `ROLE_NOT_ALLOWED`
- `PARENT_QUERY_DISABLED`
- `ATTENDANCE_ALREADY_CONFIRMED`
- `INVALID_ATTENDANCE_SLOT`
- `UNLINKED_STUDENT`
- `UPLOAD_FAILED`
- `EXAM_MODEL_NOT_IMPLEMENTED`

## Roles

- `PRINCIPAL`: full school administration access.
- `TEACHER`: assigned section and teaching workflow access.
- `STUDENT`: read-only access to own student and section data.
- `PARENT`: read-only access to linked student data, plus parent query actions.

## Authentication

### `POST /api/v1/auth/login/`

Public endpoint. Authenticates by phone number and password.

Request:

```json
{
  "phone_number": "9999999999",
  "password": "password"
}
```

Response:

```json
{
  "access": "jwt-access-token",
  "refresh": "jwt-refresh-token"
}
```

Validation:

- Use `AUTHENTICATION_FAILED` for invalid credentials.
- Use `PERMISSION_DENIED` if the user is inactive.

### `POST /api/v1/auth/refresh/`

Request:

```json
{
  "refresh": "jwt-refresh-token"
}
```

Response:

```json
{
  "access": "new-jwt-access-token"
}
```

### `POST /api/v1/auth/logout/`

Request:

```json
{
  "refresh": "jwt-refresh-token"
}
```

Response:

```json
{
  "success": true
}
```

## Current User And School

### `GET /api/v1/me/`

Returns the current user, role, profile, school, and role-specific assignments.

Response for teacher:

```json
{
  "success": true,
  "user": {
    "id": "88888888-8888-8888-8888-888888888888",
    "username": "teacher1",
    "phone_number": "9999999999",
    "email": "",
    "role": "TEACHER",
    "school_id": "11111111-1111-1111-1111-111111111111",
    "school_name": "Green Valley School",
    "profile_pic_url": null
  },
  "profile": {
    "id": "55555555-5555-5555-5555-555555555555",
    "school_id": "11111111-1111-1111-1111-111111111111",
    "school_name": "Green Valley School",
    "name": "Anita Sharma",
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
}
```

Response for student:

```json
{
  "success": true,
  "user": {
    "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    "username": "student1",
    "role": "STUDENT",
    "school_id": "11111111-1111-1111-1111-111111111111",
    "school_name": "Green Valley School",
    "profile_pic_url": null
  },
  "profile": {
    "id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
    "school_id": "11111111-1111-1111-1111-111111111111",
    "school_name": "Green Valley School",
    "name": "Alice",
    "roll_number": "101",
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
}
```

Response for parent:

```json
{
  "success": true,
  "user": {
    "id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
    "username": "parent1",
    "role": "PARENT",
    "school_id": "11111111-1111-1111-1111-111111111111",
    "school_name": "Green Valley School",
    "profile_pic_url": null
  },
  "profile": {
    "id": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
    "school_id": "11111111-1111-1111-1111-111111111111",
    "school_name": "Green Valley School",
    "name": "Anil Sharma",
    "students": [
      {
        "id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
        "name": "Alice",
        "academic_class_name": "Class 5",
        "section_name": "A"
      }
    ]
  }
}
```

Response rules:

- `profile_pic_url` is `null` until the user uploads a picture via their role-specific profile pic endpoint.
- Principal includes principal profile and school.
- Teacher includes assigned sections and class teacher sections.
- Student includes student profile, class, section, roll number, admission number.
- Parent includes parent profile and linked students.

### `GET /api/v1/school/`

Returns current school details.

Response:

```json
{
  "id": "11111111-1111-1111-1111-111111111111",
  "name": "Green Valley School",
  "subdomain": "green-valley",
  "address": "School address",
  "contact_email": "office@example.com",
  "contact_phone": "9999999999",
  "is_active": true,
  "configuration": {
    "attendance_frequency": "TWICE",
    "whatsapp_absent_automation_enabled": true,
    "parent_query_enabled": true
  }
}
```

## Lookup Data

### `GET /api/v1/classes/`

Lists classes for the current school.

Response:

```json
{
  "count": 1,
  "results": [
    {
      "id": "22222222-2222-2222-2222-222222222222",
      "name": "Class 5",
      "display_order": 5
    }
  ]
}
```

### `GET /api/v1/sections/`

Lists sections for the current school.

Query params:

- `class_id`: optional UUID class filter.

Response:

```json
{
  "count": 1,
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
      }
    }
  ]
}
```

### `GET /api/v1/subjects/`

Lists active subjects for the current school.

Response:

```json
{
  "count": 1,
  "results": [
    {
      "id": "44444444-4444-4444-4444-444444444444",
      "name": "Mathematics",
      "code": "MATH",
      "is_active": true
    }
  ]
}
```

## Calendar

### `GET /api/v1/calendar-events/`

Lists visible holidays, exams, and events.

Query params:

- `event_type`: optional, one of `HOLIDAY`, `EXAM`, `EVENT`.
- `start_date`: optional ISO date.
- `end_date`: optional ISO date.
- `month`: optional, 1-12 integer. (Overrides `start_date`/`end_date` if provided with `year`).
- `year`: optional integer, e.g., 2026.

Response:

```json
{
  "today": "2026-05-12",
  "count": 1,
  "results": [
    {
      "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
      "title": "Annual Day",
      "event_type": "EVENT",
      "start_date": "2026-08-10",
      "end_date": "2026-08-10",
      "description": "Annual school event.",
      "visible_to": ["TEACHER", "STUDENT", "PARENT"]
    }
  ]
}
```

Visibility:

- Principal sees all events in their school.
- Teacher, student, and parent see events where their role is included in `visible_to`.

## Announcements

### `GET /api/v1/announcements/`

Lists announcements visible to the current user.

Query params:

- `audience`: optional, one of `SCHOOL`, `CLASS`, `SECTION`.
- `published_after`: optional datetime.

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
      "attachments": [
        {
          "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
          "filename": "notice.pdf",
          "content_type": "application/pdf",
          "file_url": "/media/announcements/notice.pdf"
        }
      ]
    }
  ]
}
```

### `GET /api/v1/announcements/{id}/`

Returns the full announcement record. `{id}` is a UUID.

Common errors:

- `NOT_FOUND`: announcement does not exist in the current school.
- `PERMISSION_DENIED`: announcement exists but is not visible to the current user.

## Shared Models

### `School`

Fields: `id` (UUID), `name`, `subdomain`, `address`, `contact_email`, `contact_phone`, `is_active`

### `SchoolConfiguration`

Fields: `attendance_frequency` (`ONCE` or `TWICE`), `whatsapp_absent_automation_enabled`, `parent_query_enabled`

### `AcademicClass`

Fields: `id` (UUID), `school_id` (UUID), `name`, `display_order`

Rules: Class name is unique per school.

### `Section`

Fields: `id` (UUID), `school_id` (UUID), `academic_class_id` (UUID), `name`, `class_teacher_id` (UUID)

Rules: Section name is unique per class.

### `Subject`

Fields: `id` (UUID), `school_id` (UUID), `name`, `code`, `is_active`

Rules: Subject name unique per school. Subject code unique per school when set.

### `AcademicCalendarEvent`

Fields: `id` (UUID), `school_id` (UUID), `title`, `event_type`, `start_date`, `end_date`, `description`, `visible_to`

### `Announcement`

Fields: `id` (UUID), `school_id` (UUID), `author_id` (UUID), `author_role`, `title`, `body`, `audience`, `published_at`, `is_active`

### `AnnouncementAttachment`

Fields: `id` (UUID), `announcement_id` (UUID), `file`, `filename`, `content_type`

## Known Model Gaps

These models do not exist yet and are required before implementing the exam and result APIs:

- `Exam`
- `ExamSubject`
- `ExamSection`
- `StudentMark`

## Core Test Scenarios

- Login succeeds for each role and returns the correct role payload.
- Login rejects inactive users and invalid passwords.
- `/me/` returns the correct role-specific profile.
- School lookup never leaks another school's data.
- Class, section, and subject lists are scoped to the current school.
- Calendar visibility respects `visible_to`.
- Announcement visibility respects school, class, section, and role.
- All `id` fields in responses are UUID strings.
- UUID path params are accepted; non-UUID values return 404.
