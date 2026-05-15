from rest_framework.response import Response


def _format_attachment(a):
    return {
        'id': a.id,
        'filename': a.filename,
        'content_type': a.content_type,
        'file_url': a.file or None,
    }


class AnnouncementPresenter:
    def announcement_success(self, announcement, section_id):
        return Response(self._format(announcement, section_id), status=201)

    def announcement_update_success(self, announcement, section_id):
        return Response(self._format(announcement, section_id), status=200)

    def announcement_delete_success(self):
        return Response({'success': True, 'message': 'Announcement deleted successfully.'}, status=200)

    def _format(self, announcement, section_id):
        return {
            'id': announcement.id,
            'title': announcement.title,
            'body': announcement.body,
            'audience': announcement.audience,
            'section_id': section_id,
            'published_at': announcement.published_at.isoformat() if announcement.published_at else None,
            'attachments': [_format_attachment(a) for a in announcement.announcementattachment_set.all()],
        }
