# Teacher API Spec

## Purpose

This app owns teacher workflows: assigned sections, attendance, class teacher announcements, study materials, homework, exam marks entry, and parent query replies.

All endpoints use `/api/v1/`, require JWT authentication, and require role `TEACHER`.

## Permissions

- Teachers can access sections assigned through `TeacherProfile.assigned_sections`.
- Teachers can access sections where they are set as `Section.class_teacher`.
- Class teacher announcements, study materials, homework, attendance, and parent queries are section-scoped.
- Cross-school or unassigned section access returns `403` or `404`.

## Sections And Students

### `GET /api/v1/teacher/sections/`

Lists assigned sections and class teacher sections.

Response:

```json
{
  "count": 1,
  "results": [
    {
      "id": 7,
      "class_name": "Class 5",
      "section_name": "A",
      "is_class_teacher": true,
      "student_count": 40
    }
  ]
}
```

### `GET /api/v1/teacher/sections/{section_id}/students/`

Lists active students in alphabetical order.

Response:

```json
{
  "count": 2,
  "results": [
    {
      "id": 101,
      "name": "Aarav Mehta",
      "roll_number": "1",
      "admission_number": "ADM001"
    },
    {
      "id": 102,
      "name": "Bhavya Rao",
      "roll_number": "2",
      "admission_number": "ADM002"
    }
  ]
}
```

Validation:

- `section_id` must be assigned to the teacher or taught by the teacher.

## Attendance

### `POST /api/v1/teacher/attendance-sessions/`

Creates or fetches an attendance session for section, date, and slot.

Request:

```json
{
  "section_id": 7,
  "date": "2026-05-05",
  "slot": "MORNING"
}
```

Response:

```json
{
  "id": 30,
  "section_id": 7,
  "date": "2026-05-05",
  "slot": "MORNING",
  "taken_by": {
    "id": 10,
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

Marks attendance for all students in the session.

Request:

```json
{
  "records": [
    {
      "student_id": 101,
      "status": "PRESENT"
    },
    {
      "student_id": 102,
      "status": "ABSENT"
    }
  ]
}
```

Response:

```json
{
  "session_id": 30,
  "records": [
    {
      "student_id": 101,
      "student_name": "Aarav Mehta",
      "status": "PRESENT"
    },
    {
      "student_id": 102,
      "student_name": "Bhavya Rao",
      "status": "ABSENT"
    }
  ]
}
```

Validation:

- Each `student_id` must belong to the session section.
- `status` must be `PRESENT` or `ABSENT`.
- Confirmed sessions cannot be edited unless an explicit correction workflow is added later.

### `POST /api/v1/teacher/attendance-sessions/{id}/confirm/`

Confirms attendance for the session and triggers absent notification logs.

Response:

```json
{
  "session_id": 30,
  "confirmed_at": "2026-05-05T09:30:00Z",
  "absent_count": 1,
  "notification_logs_created": 1
}
```

Automation:

- Only absent students trigger WhatsApp notification logs.
- Notification logs are created only when `whatsapp_absent_automation_enabled` is true.
- Parents linked to absent students receive notifications.

## Announcements

### `POST /api/v1/teacher/announcements/`

Creates a class teacher announcement for the teacher's own section.

Content type: `multipart/form-data` when attachments are included.

Request fields:

```json
{
  "section_id": 7,
  "title": "Math Notebook",
  "body": "Bring your math notebook tomorrow.",
  "publish_now": true
}
```

Response:

```json
{
  "id": 12,
  "title": "Math Notebook",
  "audience": "SECTION",
  "section_id": 7,
  "published_at": "2026-05-05T10:00:00Z",
  "attachments": []
}
```

Validation:

- Teacher must be the class teacher for the section.
- Audience is always `SECTION`.
- Push notifications are sent on publish.

## Study Materials

### `POST /api/v1/teacher/study-materials/`

Uploads material for a section and subject.

Content type: `multipart/form-data`

Fields:

- `section_id`
- `subject_id`
- `title`
- `description`
- `material_date`
- `file`

Response:

```json
{
  "id": 40,
  "section_id": 7,
  "subject": {
    "id": 4,
    "name": "Mathematics"
  },
  "title": "Fractions Worksheet",
  "description": "Practice worksheet.",
  "material_date": "2026-05-05",
  "file_url": "/media/study_materials/fractions.pdf",
  "uploaded_by": {
    "id": 10,
    "name": "Anita Sharma"
  }
}
```

Visibility:

- Students and parents of the section can view the material.

### `GET /api/v1/teacher/study-materials/`

Lists materials uploaded by the teacher.

Query params:

- `section_id`
- `subject_id`
- `date_from`
- `date_to`

## Homework

### `POST /api/v1/teacher/homework/`

Creates homework for a section.

Request:

```json
{
  "section_id": 7,
  "subject_id": 4,
  "description": "Complete exercise 5.1.",
  "deadline": "2026-05-06T17:00:00Z"
}
```

Response:

```json
{
  "id": 50,
  "section_id": 7,
  "subject": {
    "id": 4,
    "name": "Mathematics"
  },
  "description": "Complete exercise 5.1.",
  "deadline": "2026-05-06T17:00:00Z"
}
```

Visibility:

- Students and parents of the section can view the homework.

### `GET /api/v1/teacher/homework/`

Lists homework created by the teacher.

Query params:

- `section_id`
- `subject_id`
- `deadline_from`
- `deadline_to`

## Exam Marks

### `GET /api/v1/teacher/exams/{exam_id}/marks/`

Returns students and subjects requiring marks entry for the teacher.

Response:

```json
{
  "exam": {
    "id": 20,
    "name": "Mid Term Exam"
  },
  "subjects": [
    {
      "subject_id": 4,
      "subject_name": "Mathematics",
      "max_marks": 100,
      "pass_marks": 35
    }
  ],
  "students": [
    {
      "student_id": 101,
      "student_name": "Aarav Mehta",
      "roll_number": "1",
      "marks": [
        {
          "subject_id": 4,
          "marks_obtained": null
        }
      ]
    }
  ]
}
```

### `PUT /api/v1/teacher/exams/{exam_id}/marks/`

Creates or updates student marks.

Request:

```json
{
  "records": [
    {
      "student_id": 101,
      "subject_id": 4,
      "marks_obtained": 92,
      "remarks": "Excellent"
    }
  ]
}
```

Response:

```json
{
  "exam_id": 20,
  "updated_count": 1
}
```

Validation:

- Exam must apply to one of the teacher's assigned sections.
- Subject must be part of the exam.
- Marks must be between `0` and `max_marks`.

Required future models:

- `Exam`
- `ExamSubject`
- `ExamSection`
- `StudentMark`

## Parent Queries

### `GET /api/v1/teacher/parent-queries/`

Lists queries assigned to the teacher.

Query params:

- `status`: optional, one of `OPEN`, `ANSWERED`, `CLOSED`.
- `section_id`: optional.

Response:

```json
{
  "count": 1,
  "results": [
    {
      "id": 60,
      "subject": "Homework doubt",
      "message": "Please explain the homework.",
      "status": "OPEN",
      "parent": {
        "id": 9,
        "name": "Ramesh Kumar"
      },
      "student": {
        "id": 101,
        "name": "Aarav Mehta"
      },
      "section_id": 7,
      "created_at": "2026-05-05T12:00:00Z"
    }
  ]
}
```

### `POST /api/v1/teacher/parent-queries/{id}/replies/`

Replies to a parent query.

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
  "id": 70,
  "query_id": 60,
  "sender_id": 25,
  "message": "I will explain it again tomorrow.",
  "query_status": "ANSWERED",
  "created_at": "2026-05-05T12:15:00Z"
}
```

Validation:

- Query must be assigned to the teacher.
- Closed queries cannot receive replies unless reopened.

## Teacher Test Scenarios

- Teacher sees only assigned and class teacher sections.
- Student list is alphabetical and scoped to the selected section.
- Attendance session uniqueness is enforced per section/date/slot.
- Once-per-day schools reject afternoon attendance.
- Confirming attendance creates notification logs only for absent students.
- Confirmed attendance cannot be edited by default.
- Teacher announcements are limited to class teacher sections.
- Study materials and homework reject unassigned sections.
- Marks entry rejects invalid marks and unauthorized sections.
- Parent query replies update status when `mark_answered` is true.
