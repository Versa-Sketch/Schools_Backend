# Core API Spec

## Purpose

This app owns shared authentication, school context, common lookup data, announcements, and calendar visibility. All endpoints use REST-style paths under `/api/v1/` and assume JWT authentication unless explicitly marked public.

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

Examples:

```json
{
  "success": false,
  "code": "PERMISSION_DENIED",
  "details": "You do not have permission to access this resource."
}
```

```json
{
  "success": false,
  "code": "VALIDATION_ERROR",
  "details": "The selected section does not belong to your school."
}
```

## Roles

- `PRINCIPAL`: full school administration access.
- `TEACHER`: assigned section and teaching workflow access.
- `STUDENT`: read-only access to own student and section data.
- `PARENT`: read-only access to linked student data, plus parent query actions.

## Authentication

### `POST /api/v1/auth/login/`

Public endpoint for username/password login.

Request:

```json
{
  "username": "teacher1",
  "password": "password"
}
```

Response:

```json
{
  "access": "jwt-access-token",
  "refresh": "jwt-refresh-token",
}
```

Validation:

- Use `AUTHENTICATION_FAILED` for invalid credentials.
- Use `PERMISSION_DENIED` if the user is inactive.
- Include the user's school only when the user has a profile linked to a school.

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

Invalidates the refresh token if token blacklisting is enabled.

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
  "id": 2,
  "username": "teacher1",
  "role": "TEACHER",
  "profile": {
    "id": 10,
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
  },
  "school": {
    "id": 1,
    "name": "Green Valley School",
    "subdomain": "green-valley"
  }
}
```

Response rules:

- Principal includes principal profile and school.
- Teacher includes assigned sections and class teacher sections.
- Student includes student profile, class, section, roll number, admission number.
- Parent includes parent profile and linked students.

### `GET /api/v1/school/`

Returns current school details.

Response:

```json
{
  "id": 1,
  "name": "Green Valley School",
  "subdomain": "green-valley",
  "address": "School address",
  "contact_email": "office@example.com",
  "contact_phone": "9999999999",
  "is_active": true
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
      "id": 1,
      "name": "Class 5",
      "display_order": 5
    }
  ]
}
```

### `GET /api/v1/sections/`

Lists sections for the current school.

Query params:

- `class_id`: optional class filter.

Response:

```json
{
  "count": 1,
  "results": [
    {
      "id": 7,
      "name": "A",
      "academic_class": {
        "id": 1,
        "name": "Class 5"
      },
      "class_teacher": {
        "id": 10,
        "name": "Anita Sharma"
      }
    }
  ]
}
```

### `GET /api/v1/subjects/`

Lists active subjects for the current school.

Query params:

- `class_id`: optional future filter.
- `section_id`: optional future filter.

Response:

```json
{
  "count": 1,
  "results": [
    {
      "id": 4,
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

Response:

```json
{
  "count": 1,
  "results": [
    {
      "id": 3,
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
      "id": 11,
      "title": "School Reopens",
      "body": "School reopens on Monday.",
      "author_role": "PRINCIPAL",
      "audience": "SCHOOL",
      "published_at": "2026-06-01T09:00:00Z",
      "attachments": [
        {
          "id": 8,
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

Returns the full announcement record with targets and attachments when visible to the current user.

Common errors:

- `NOT_FOUND`: announcement does not exist in the current school.
- `PERMISSION_DENIED`: announcement exists but is not visible to the current user.

## Shared Models

### `School`

Fields:

- `id`
- `name`
- `subdomain`
- `address`
- `contact_email`
- `contact_phone`
- `is_active`

### `SchoolConfiguration`

Fields:

- `attendance_frequency`: `ONCE` or `TWICE`
- `whatsapp_absent_automation_enabled`
- `parent_query_enabled`

### `AcademicClass`

Fields:

- `id`
- `school_id`
- `name`
- `display_order`

Rules:

- Class name is unique per school.

### `Section`

Fields:

- `id`
- `school_id`
- `academic_class_id`
- `name`
- `class_teacher_id`

Rules:

- Section name is unique per class.

### `Subject`

Fields:

- `id`
- `school_id`
- `name`
- `code`
- `is_active`

Rules:

- Subject name is unique per school.
- Subject code is unique per school when set.

### `AcademicCalendarEvent`

Fields:

- `id`
- `school_id`
- `title`
- `event_type`
- `start_date`
- `end_date`
- `description`
- `visible_to`

### `Announcement`

Fields:

- `id`
- `school_id`
- `author_id`
- `author_role`
- `title`
- `body`
- `audience`
- `published_at`
- `is_active`

### `AnnouncementAttachment`

Fields:

- `id`
- `announcement_id`
- `file`
- `filename`
- `content_type`

## Known Model Gaps

These models do not exist yet and are required before implementing the exam and result APIs:

- `Exam`
- `ExamSubject`
- `ExamSection`
- `StudentMark`
- Optional analytics read models or computed dashboard serializers.

## Core Test Scenarios

- Login succeeds for each role and returns the correct role payload.
- Login rejects inactive users and invalid passwords.
- `/me/` returns the correct role-specific profile.
- School lookup never leaks another school's data.
- Class, section, and subject lists are scoped to the current school.
- Calendar visibility respects `visible_to`.
- Announcement visibility respects school, class, section, and role.
