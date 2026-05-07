from rest_framework.response import Response


def _format_attachment(a):
    return {
        'id': a.id,
        'filename': a.filename,
        'content_type': a.content_type,
        'file_url': a.file or None,
    }


def format_announcement(ann):
    return {
        'id': ann.id,
        'title': ann.title,
        'body': ann.body,
        'author_role': ann.author_role,
        'audience': ann.audience,
        'published_at': ann.published_at.isoformat() if ann.published_at else None,
        'attachments': [_format_attachment(a) for a in ann.announcementattachment_set.all()],
    }


class AnnouncementPresenter:
    def announcement_list_success(self, announcements):
        results = [format_announcement(a) for a in announcements]
        return Response({'count': len(results), 'results': results}, status=200)

    def announcement_detail_success(self, announcement):
        return Response(format_announcement(announcement), status=200)
