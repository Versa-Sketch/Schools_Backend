from django.db.models import Q
from django.dispatch import receiver

from .signals import (
    announcement_published,
    homework_assigned,
    study_material_uploaded,
    attendance_confirmed,
    parent_query_created,
    query_reply_added,
    calendar_event_created,
    bulk_upload_completed,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_all_school_users(school_id):
    from core.models import User
    return list(User.objects.filter(
        Q(principalprofile__school_id=school_id) |
        Q(teacherprofile__school_id=school_id) |
        Q(studentprofile__school_id=school_id) |
        Q(parentprofile__school_id=school_id)
    ).distinct())


def _get_school_users_by_roles(school_id, roles):
    from core.models import User
    q = Q()
    if 'PRINCIPAL' in roles:
        q |= Q(principalprofile__school_id=school_id)
    if 'TEACHER' in roles:
        q |= Q(teacherprofile__school_id=school_id)
    if 'STUDENT' in roles:
        q |= Q(studentprofile__school_id=school_id)
    if 'PARENT' in roles:
        q |= Q(parentprofile__school_id=school_id)
    if not q:
        return []
    return list(User.objects.filter(q).distinct())


def _get_users_for_classes(school_id, class_ids):
    from core.models import User
    return list(User.objects.filter(
        Q(studentprofile__school_id=school_id, studentprofile__academic_class_id__in=class_ids) |
        Q(parentprofile__school_id=school_id, parentprofile__students__academic_class_id__in=class_ids)
    ).distinct())


def _get_users_for_sections(school_id, section_ids):
    from core.models import User
    return list(User.objects.filter(
        Q(studentprofile__section_id__in=section_ids) |
        Q(parentprofile__students__section_id__in=section_ids) |
        Q(teacherprofile__section__id__in=section_ids)
    ).distinct())


def _bulk_notify(recipients, school, notif_type, title, body, data, exclude_user_id=None):
    from notifications.models import Notification
    objs = [
        Notification(
            recipient=user,
            school=school,
            notif_type=notif_type,
            title=title,
            body=body,
            data=data,
        )
        for user in recipients
        if exclude_user_id is None or user.id != exclude_user_id
    ]
    if objs:
        Notification.objects.bulk_create(objs, ignore_conflicts=True)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

@receiver(announcement_published)
def handle_announcement_published(sender, announcement, **kwargs):
    from notifications.constants import ANNOUNCEMENT_PUBLISHED

    ann = announcement
    school = ann.school

    if ann.audience == 'SCHOOL':
        recipients = _get_all_school_users(school.id)
    elif ann.audience == 'CLASS':
        class_ids = list(ann.announcementtarget_set.values_list('academic_class_id', flat=True))
        recipients = _get_users_for_classes(school.id, class_ids)
    else:
        section_ids = list(ann.announcementtarget_set.values_list('section_id', flat=True))
        recipients = _get_users_for_sections(school.id, section_ids)

    _bulk_notify(
        recipients=recipients,
        school=school,
        notif_type=ANNOUNCEMENT_PUBLISHED,
        title=ann.title,
        body=ann.body[:200],
        data={'announcement_id': ann.id, 'audience': ann.audience},
        exclude_user_id=ann.author_id,
    )


@receiver(homework_assigned)
def handle_homework_assigned(sender, homework, **kwargs):
    from core.models import User
    from notifications.constants import HOMEWORK_ASSIGNED

    hw = homework
    recipients = list(User.objects.filter(
        Q(studentprofile__section=hw.section, studentprofile__is_active=True) |
        Q(parentprofile__students__section=hw.section)
    ).distinct())

    _bulk_notify(
        recipients=recipients,
        school=hw.school,
        notif_type=HOMEWORK_ASSIGNED,
        title=f'New Homework: {hw.subject.name}',
        body=hw.description[:200],
        data={'homework_id': hw.id, 'section_id': hw.section_id, 'subject_id': hw.subject_id},
    )


@receiver(study_material_uploaded)
def handle_study_material_uploaded(sender, material, **kwargs):
    from core.models import User
    from notifications.constants import STUDY_MATERIAL_UPLOADED

    mat = material
    recipients = list(User.objects.filter(
        Q(studentprofile__section=mat.section, studentprofile__is_active=True) |
        Q(parentprofile__students__section=mat.section)
    ).distinct())

    _bulk_notify(
        recipients=recipients,
        school=mat.school,
        notif_type=STUDY_MATERIAL_UPLOADED,
        title=f'New Study Material: {mat.subject.name}',
        body=mat.title,
        data={'material_id': mat.id, 'section_id': mat.section_id, 'subject_id': mat.subject_id},
    )


@receiver(attendance_confirmed)
def handle_attendance_confirmed(sender, session, **kwargs):
    from core.models import StudentAttendance, User, ATTENDANCE_STATUS_ABSENT
    from notifications.constants import ATTENDANCE_ABSENT

    absent_student_ids = list(
        StudentAttendance.objects.filter(
            session=session, status=ATTENDANCE_STATUS_ABSENT
        ).values_list('student_id', flat=True)
    )
    if not absent_student_ids:
        return

    parent_users = list(User.objects.filter(
        parentprofile__students__id__in=absent_student_ids
    ).distinct())

    _bulk_notify(
        recipients=parent_users,
        school=session.school,
        notif_type=ATTENDANCE_ABSENT,
        title=f'Absent: {session.date}',
        body=f'Your child was marked absent for the {session.slot.lower()} session on {session.date}.',
        data={'session_id': session.id, 'date': str(session.date), 'slot': session.slot},
    )


@receiver(parent_query_created)
def handle_parent_query_created(sender, query, **kwargs):
    from notifications.constants import PARENT_QUERY_RECEIVED
    from notifications.models import Notification

    Notification.objects.create(
        recipient=query.assigned_teacher.user,
        school=query.school,
        notif_type=PARENT_QUERY_RECEIVED,
        title=f'New Query: {query.subject}',
        body=query.message[:200],
        data={'query_id': query.id, 'student_id': query.student_id},
    )


@receiver(query_reply_added)
def handle_query_reply_added(sender, reply, **kwargs):
    from notifications.constants import QUERY_REPLY_RECEIVED
    from notifications.models import Notification

    query = reply.query
    recipient = (
        query.parent.user
        if reply.sender.role == 'TEACHER'
        else query.assigned_teacher.user
    )

    Notification.objects.create(
        recipient=recipient,
        school=query.school,
        notif_type=QUERY_REPLY_RECEIVED,
        title=f'Reply: {query.subject}',
        body=reply.message[:200],
        data={'query_id': query.id, 'reply_id': reply.id},
    )


@receiver(calendar_event_created)
def handle_calendar_event_created(sender, event, **kwargs):
    from notifications.constants import CALENDAR_EVENT_CREATED

    if not event.visible_to:
        return

    recipients = _get_school_users_by_roles(event.school_id, event.visible_to)
    description_snippet = f' — {event.description[:80]}' if event.description else ''

    _bulk_notify(
        recipients=recipients,
        school=event.school,
        notif_type=CALENDAR_EVENT_CREATED,
        title=event.title,
        body=f'{event.event_type}: {event.start_date} to {event.end_date}{description_snippet}',
        data={'event_id': event.id, 'event_type': event.event_type},
    )


@receiver(bulk_upload_completed)
def handle_bulk_upload_completed(sender, batch, principal_user, **kwargs):
    from notifications.constants import BULK_UPLOAD_COMPLETE
    from notifications.models import Notification

    Notification.objects.create(
        recipient=principal_user,
        school=batch.school,
        notif_type=BULK_UPLOAD_COMPLETE,
        title='Bulk Upload Complete',
        body=(
            f'Upload finished: {batch.success_count} created, '
            f'{batch.error_count} failed out of {batch.total_rows} rows.'
        ),
        data={
            'batch_id': batch.id,
            'success_count': batch.success_count,
            'error_count': batch.error_count,
            'total_rows': batch.total_rows,
        },
    )
