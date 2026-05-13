from rest_framework.response import Response


class BulkUploadPresenter:
    def bulk_upload_success(self, batch, rows=None):
        data = {
            'batch_id': batch.id,
            'status': batch.status,
            'total_rows': batch.total_rows,
            'success_count': batch.success_count,
            'error_count': batch.error_count,
        }
        if batch.error_report:
            data['error_report_url'] = batch.error_report.url

        if rows is not None:
            failed_rows = []
            for row in rows:
                if row.status == 'FAILED':
                    failed_rows.append({
                        'row_number': row.row_number,
                        'error': row.error_message,
                        'data': row.raw_data,
                    })
            data['failed_rows'] = failed_rows

        return Response(data, status=200)
