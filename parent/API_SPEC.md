# Parent API Spec

## Purpose

This app owns parent-facing APIs for linked students, attendance, announcements, study materials, homework, calendar events, results, and parent-to-teacher communication.

All endpoints use `/api/v1/`, require JWT authentication, and require role `PARENT`.

## Permissions

- Parents can only access students linked through `ParentProfile.students`.
- Parents cannot access unlinked students, even within the same school.
- Parents can create and reply to queries only when parent queries are enabled for the school.
- Cross-school and unlinked student access must return `403` or `404`.

## Profile And Linked Students

### `GET /api/v1/parent/profile/`

Returns the current parent profile and linked students.

Response:

```json
{
  "id": 9,
  "name": "Ramesh Kumar",
  "mobile_number": "9999999999",
  "school": {
    "id": 1,
    "name": "Green Valley School"
  },
  "students": [
    {
      "id": 101,
      "name": "Aarav Mehta",
      "roll_number": "1",
      "academic_class": {
        "id": 1,
        "name": "Class 5"
      },
      "section": {
        "id": 7,
        "name": "A"
      }
    }
  ]
}
```

### `GET /api/v1/parent/students/`

Lists students linked to the parent.

Response:

```json
{
  "count": 1,
  "results": [
    {
      "id": 101,
      "name": "Aarav Mehta",
      "roll_number": "1",
      "admission_number": "ADM001",
      "academic_class": {
        "id": 1,
        "name": "Class 5"
      },
      "section": {
        "id": 7,
        "name": "A"
      }
    }
  ]
}
```

## Student Attendance

### `GET /api/v1/parent/students/{student_id}/attendance/`

Returns attendance for a linked student.

Query params:

- `date_from`: optional ISO date.
- `date_to`: optional ISO date.
- `slot`: optional, one of `MORNING`, `AFTERNOON`.
- `status`: optional, one of `PRESENT`, `ABSENT`.

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

Rules:

- Only confirmed attendance sessions are visible.
- `student_id` must be linked to the parent.

## Announcements

### `GET /api/v1/parent/students/{student_id}/announcements/`

Returns announcements visible to the linked student's parent.

Visible announcements:

- School-wide announcements.
- Class announcements for the student's class.
- Section announcements for the student's section.
- Parent-targeted principal communication if role targeting is added later.

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
      "attachments": []
    }
  ]
}
```

## Study Materials

### `GET /api/v1/parent/students/{student_id}/study-materials/`

Returns materials for the linked student's section.

Query params:

- `subject_id`: optional.
- `date_from`: optional ISO date.
- `date_to`: optional ISO date.

Response:

```json
{
  "count": 1,
  "results": [
    {
      "id": 40,
      "title": "Fractions Worksheet",
      "description": "Practice worksheet.",
      "subject": {
        "id": 4,
        "name": "Mathematics"
      },
      "material_date": "2026-05-05",
      "file_url": "/media/study_materials/fractions.pdf",
      "uploaded_by": {
        "id": 10,
        "name": "Anita Sharma"
      }
    }
  ]
}
```

## Homework

### `GET /api/v1/parent/students/{student_id}/homework/`

Returns homework for the linked student's section.

Query params:

- `subject_id`: optional.
- `deadline_from`: optional datetime.
- `deadline_to`: optional datetime.

Response:

```json
{
  "count": 1,
  "results": [
    {
      "id": 50,
      "subject": {
        "id": 4,
        "name": "Mathematics"
      },
      "description": "Complete exercise 5.1.",
      "deadline": "2026-05-06T17:00:00Z",
      "assigned_by": {
        "id": 10,
        "name": "Anita Sharma"
      }
    }
  ]
}
```

## Calendar

### `GET /api/v1/parent/students/{student_id}/calendar-events/`

Returns parent-visible calendar events for the linked student's school.

Query params:

- `event_type`: optional, one of `HOLIDAY`, `EXAM`, `EVENT`.
- `start_date`: optional.
- `end_date`: optional.

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
      "description": "Annual school event."
    }
  ]
}
```

## Results

### `GET /api/v1/parent/students/{student_id}/results/`

Returns result summary for a linked student.

Query params:

- `exam_id`: optional.

Response:

```json
{
  "student": {
    "id": 101,
    "name": "Aarav Mehta",
    "roll_number": "1"
  },
  "exam": {
    "id": 20,
    "name": "Mid Term Exam"
  },
  "summary": {
    "total_marks": 430,
    "max_marks": 500,
    "percentage": 86.0,
    "section_rank": 3,
    "class_rank": 8
  },
  "subjects": [
    {
      "subject_id": 4,
      "subject_name": "Mathematics",
      "marks_obtained": 92,
      "max_marks": 100,
      "pass_marks": 35,
      "grade": "A"
    }
  ],
  "growth_trend": []
}
```

Required future models:

- `Exam`
- `ExamSubject`
- `ExamSection`
- `StudentMark`

## Parent Queries

### `POST /api/v1/parent/queries/`

Raises a query to the linked student's class teacher.

Request:

```json
{
  "student_id": 101,
  "subject": "Homework doubt",
  "message": "Please explain today's homework."
}
```

Response:

```json
{
  "id": 60,
  "student": {
    "id": 101,
    "name": "Aarav Mehta"
  },
  "section_id": 7,
  "assigned_teacher": {
    "id": 10,
    "name": "Anita Sharma"
  },
  "subject": "Homework doubt",
  "message": "Please explain today's homework.",
  "status": "OPEN",
  "created_at": "2026-05-05T12:00:00Z"
}
```

Validation:

- Parent queries must be enabled in `SchoolConfiguration`.
- `student_id` must be linked to the parent.
- Student section must have a class teacher.
- If parent queries are disabled, return `403`.

### `GET /api/v1/parent/queries/`

Lists the parent's query history.

Query params:

- `student_id`: optional linked student filter.
- `status`: optional, one of `OPEN`, `ANSWERED`, `CLOSED`.

Response:

```json
{
  "count": 1,
  "results": [
    {
      "id": 60,
      "subject": "Homework doubt",
      "status": "OPEN",
      "student": {
        "id": 101,
        "name": "Aarav Mehta"
      },
      "assigned_teacher": {
        "id": 10,
        "name": "Anita Sharma"
      },
      "created_at": "2026-05-05T12:00:00Z"
    }
  ]
}
```

### `GET /api/v1/parent/queries/{id}/`

Returns query detail with replies.

Response:

```json
{
  "id": 60,
  "subject": "Homework doubt",
  "message": "Please explain today's homework.",
  "status": "OPEN",
  "student": {
    "id": 101,
    "name": "Aarav Mehta"
  },
  "assigned_teacher": {
    "id": 10,
    "name": "Anita Sharma"
  },
  "replies": [
    {
      "id": 70,
      "sender_id": 25,
      "sender_role": "TEACHER",
      "message": "I will explain it again tomorrow.",
      "created_at": "2026-05-05T12:15:00Z"
    }
  ]
}
```

### `POST /api/v1/parent/queries/{id}/replies/`

Adds a parent reply to an open or answered query.

Request:

```json
{
  "message": "Thank you."
}
```

Response:

```json
{
  "id": 71,
  "query_id": 60,
  "sender_id": 30,
  "message": "Thank you.",
  "created_at": "2026-05-05T12:20:00Z"
}
```

Validation:

- Query must belong to the parent.
- Closed queries cannot receive replies unless reopened.
- If parent queries are disabled, return `403` for new query creation. Existing query history remains readable.

## Parent Test Scenarios

- Parent profile returns only linked students.
- Parent cannot access unlinked student attendance, homework, materials, results, or calendar context.
- Attendance shows only confirmed sessions.
- Announcements match the linked student's school, class, and section.
- Parent query creation fails when school configuration disables queries.
- Parent query creation fails when the student has no class teacher.
- Parent can read and reply only to their own queries.
- Closed queries reject new replies.
