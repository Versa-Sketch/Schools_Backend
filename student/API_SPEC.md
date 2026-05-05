# Student API Spec

## Purpose

This app owns student-facing read-only APIs for profile, attendance, announcements, study materials, homework, calendar, exams, and results.

All endpoints use `/api/v1/`, require JWT authentication, and require role `STUDENT`.

## Error Format

All errors follow the common error format defined in `core/API_SPEC.md`:

```json
{
  "success": false,
  "code": "PERMISSION_DENIED",
  "details": "Students can only access their own data."
}
```

## Permissions

- Students can only access their own profile and own section data.
- Students cannot mutate attendance, homework, materials, announcements, exams, or results.
- Cross-school and other-student access uses `NOT_FOUND` or `PERMISSION_DENIED`.

## Profile

### `GET /api/v1/student/profile/`

Returns the current student profile.

Response:

```json
{
  "id": 101,
  "name": "Aarav Mehta",
  "roll_number": "1",
  "admission_number": "ADM001",
  "is_active": true,
  "academic_class": {
    "id": 1,
    "name": "Class 5"
  },
  "section": {
    "id": 7,
    "name": "A"
  },
  "school": {
    "id": 1,
    "name": "Green Valley School"
  }
}
```

## Attendance

### `GET /api/v1/student/attendance/`

Returns the student's own attendance history.

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

Returns announcements visible to the student.

Visible announcements:

- School-wide announcements.
- Class announcements for the student's class.
- Section announcements for the student's section.

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

### `GET /api/v1/student/study-materials/`

Returns materials for the student's section.

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

### `GET /api/v1/student/homework/`

Returns homework for the student's section.

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

### `GET /api/v1/student/calendar-events/`

Returns calendar events visible to students.

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

## Exams

### `GET /api/v1/student/exams/`

Returns exams applicable to the student's class or section.

Response:

```json
{
  "count": 1,
  "results": [
    {
      "id": 20,
      "name": "Mid Term Exam",
      "start_date": "2026-09-01",
      "end_date": "2026-09-10",
      "subjects": [
        {
          "subject_id": 4,
          "subject_name": "Mathematics",
          "max_marks": 100,
          "pass_marks": 35
        }
      ]
    }
  ]
}
```

Required future models:

- `Exam`
- `ExamSubject`
- `ExamSection`
- `StudentMark`

## Results

### `GET /api/v1/student/results/`

Returns the student's own results, rank, subject performance, and growth trend.

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

Visibility:

- Results are visible only after marks are published, if a publish workflow is added.
- Until publish workflow exists, visibility is controlled by implementation policy and should be documented before release.

## Student Test Scenarios

- Student profile returns only the authenticated student's profile.
- Attendance endpoint shows only confirmed sessions.
- Student cannot see another student's attendance or results.
- Announcements include school, class, and section targets.
- Study materials and homework are limited to the student's section.
- Calendar events respect student visibility.
- Exams include only exams assigned to the student's class or section.
- Results include only the student's own marks.
