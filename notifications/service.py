from notifications.signals import (
    announcement_published,
    homework_assigned,
    study_material_uploaded,
    attendance_confirmed,
    parent_query_created,
    query_reply_added,
    calendar_event_created,
    bulk_upload_completed,
)


class NotificationService:
    @staticmethod
    def announcement_published(announcement):
        if announcement.published_at is None:
            return
        announcement_published.send(sender=None, announcement=announcement)

    @staticmethod
    def homework_assigned(homework_id):
        from core.models import Homework
        try:
            hw = Homework.objects.select_related('school', 'subject', 'section').get(id=homework_id)
        except Homework.DoesNotExist:
            return
        homework_assigned.send(sender=None, homework=hw)

    @staticmethod
    def study_material_uploaded(material_id):
        from core.models import StudyMaterial
        try:
            mat = StudyMaterial.objects.select_related('school', 'subject', 'section').get(id=material_id)
        except StudyMaterial.DoesNotExist:
            return
        study_material_uploaded.send(sender=None, material=mat)

    @staticmethod
    def attendance_confirmed(session_id):
        from core.models import AttendanceSession
        try:
            session = AttendanceSession.objects.select_related('school', 'section').get(id=session_id)
        except AttendanceSession.DoesNotExist:
            return
        attendance_confirmed.send(sender=None, session=session)

    @staticmethod
    def parent_query_created(query_id):
        from core.models import ParentQuery
        try:
            query = ParentQuery.objects.select_related(
                'school', 'student', 'assigned_teacher__user', 'parent__user'
            ).get(id=query_id)
        except ParentQuery.DoesNotExist:
            return
        parent_query_created.send(sender=None, query=query)

    @staticmethod
    def query_reply_added(reply_id):
        from core.models import ParentQueryReply
        try:
            reply = ParentQueryReply.objects.select_related(
                'query__school',
                'query__parent__user',
                'query__assigned_teacher__user',
                'sender',
            ).get(id=reply_id)
        except ParentQueryReply.DoesNotExist:
            return
        query_reply_added.send(sender=None, reply=reply)

    @staticmethod
    def calendar_event_created(event_id):
        from core.models import AcademicCalendarEvent
        try:
            event = AcademicCalendarEvent.objects.select_related('school').get(id=event_id)
        except AcademicCalendarEvent.DoesNotExist:
            return
        calendar_event_created.send(sender=None, event=event)

    @staticmethod
    def bulk_upload_complete(batch_id, principal_user_id):
        from core.models import StudentBulkUploadBatch, User
        try:
            batch = StudentBulkUploadBatch.objects.select_related('school').get(id=batch_id)
            principal_user = User.objects.get(id=principal_user_id)
        except (StudentBulkUploadBatch.DoesNotExist, User.DoesNotExist):
            return
        bulk_upload_completed.send(sender=None, batch=batch, principal_user=principal_user)
