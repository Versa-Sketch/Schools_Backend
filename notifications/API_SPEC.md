# Notifications API Spec

## Purpose

This app delivers in-app notifications to all roles. Notifications are created automatically by the system when significant events occur (announcements published, homework assigned, attendance confirmed, etc.). Users read and manage their own notifications via these endpoints.

All endpoints use `/api/v1/notifications/`, require JWT authentication, and are accessible by **all roles** (PRINCIPAL, TEACHER, STUDENT, PARENT).

## ID Format

All `id` fields are UUID strings (`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`).

## Notification Types

| Type | Triggered by | Recipients |
|---|---|---|
| `ANNOUNCEMENT_PUBLISHED` | Principal or teacher publishes an announcement | All targeted users (school-wide, class, or section) |
| `HOMEWORK_ASSIGNED` | Teacher creates homework | Students and parents in the section |
| `STUDY_MATERIAL_UPLOADED` | Teacher uploads a study material | Students and parents in the section |
| `ATTENDANCE_ABSENT` | Teacher confirms an attendance session | Parents of absent students |
| `PARENT_QUERY_RECEIVED` | Parent creates a query | Assigned class teacher |
| `QUERY_REPLY_RECEIVED` | Teacher or parent replies to a query | The other party (parent or teacher) |
| `CALENDAR_EVENT_CREATED` | Principal creates a calendar event | All users whose role is in `visible_to` |
| `BULK_UPLOAD_COMPLETE` | Student bulk upload batch finishes | The uploading principal |

## Endpoints

### `GET /api/v1/notifications/`

Returns the authenticated user's notifications, newest first.

Query params:

- `unread`: optional. Pass `unread=true` to return only unread notifications.

Response:

```json
{
  "count": 2,
  "unread_count": 1,
  "results": [
    {
      "id": "ffffffff-ffff-ffff-ffff-ffffffffffff",
      "type": "HOMEWORK_ASSIGNED",
      "title": "New Homework: Mathematics",
      "body": "Complete exercise 5.1.",
      "data": {
        "homework_id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
        "section_id": "33333333-3333-3333-3333-333333333333",
        "subject_id": "44444444-4444-4444-4444-444444444444"
      },
      "is_read": false,
      "created_at": "2026-05-07T10:00:00Z"
    },
    {
      "id": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
      "type": "ANNOUNCEMENT_PUBLISHED",
      "title": "School Reopens",
      "body": "School reopens on Monday.",
      "data": {
        "announcement_id": "99999999-9999-9999-9999-999999999999",
        "audience": "SCHOOL"
      },
      "is_read": true,
      "created_at": "2026-05-06T08:00:00Z"
    }
  ]
}
```

Fields:

- `count`: total number of notifications returned.
- `unread_count`: total unread count for the user (regardless of the `unread` filter).
- `results[].type`: one of the notification type constants above.
- `results[].data`: JSON object with context IDs for deep-linking (content varies by type).
- `results[].is_read`: `false` until the notification is marked read.

### `POST /api/v1/notifications/read/`

Marks one or more notifications as read.

Request — mark specific notifications:

```json
{
  "ids": [
    "ffffffff-ffff-ffff-ffff-ffffffffffff",
    "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
  ]
}
```

Request — mark **all** unread notifications as read (empty body or omit `ids`):

```json
{}
```

Response:

```json
{
  "marked_read": 2
}
```

Fields:

- `marked_read`: number of notifications that were updated (already-read notifications are ignored).

Validation:

- `ids` is optional. If provided, must be an array of UUIDs.
- Only the authenticated user's own notifications can be marked read.

### `GET /api/v1/notifications/unread-count/`

Returns the number of unread notifications for the authenticated user. Intended for badge display in clients.

Response:

```json
{
  "count": 5
}
```

## Notification Delivery

Notifications are created synchronously via Django signals when events occur. There is no push delivery (FCM/APNs) at this time — clients should poll `unread-count/` or `notifications/` to check for new items.

## Notifications Test Scenarios

- Authenticated user sees only their own notifications.
- `unread=true` filter returns only `is_read: false` items.
- Empty-body POST to `/read/` marks all unread as read; `marked_read` equals prior unread count.
- POST to `/read/` with specific `ids` marks only those notifications as read.
- `/unread-count/` returns `0` after all notifications are marked read.
- Notifications from other users or schools are never visible.
