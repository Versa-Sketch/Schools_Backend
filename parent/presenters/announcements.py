from rest_framework.response import Response


class ParentAnnouncementsPresenter:
    def announcement_list_success(self, announcements):
        results = [
            {
                'id': a.id,
                'title': a.title,
                'body': a.body,
                'author_role': a.author_role,
                'audience': a.audience,
                'published_at': a.published_at.isoformat() if a.published_at else None,
                'attachments': [
                    {'id': att.id, 'filename': att.filename, 'content_type': att.content_type,
                     'file_url': att.file or None}
                    for att in a.announcementattachment_set.all()
                ],
            }
            for a in announcements
        ]
        return Response({'count': len(results), 'results': results}, status=200)
