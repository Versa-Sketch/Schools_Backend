"""
Excel rank-card parser for analytics exam uploads.

Public API:
    parse_excel_file(file_obj, class_name, section_name) → ParseResult

The workbook contains multiple sheets ("Table 1".."Table N"). Each student's data
spans one or more sheets as a continuous block of rows. A new student block begins
when a row's first cell is "STUDENT RANK CARD" or "Student Name :".

Questions are shown in batches of (QNo / Ans / Key / Status) 4-row groups.
The same question may appear in multiple sheets — the last seen status wins.
Wrong and unattempted are computed from the question-level C/W/U counts because
the Excel summary does not include them.
"""

from datetime import datetime, date
from typing import Dict, Iterator, List, Optional, Tuple
import re

import openpyxl

from analytics.services.csv_parser import (
    ParsedExamMeta,
    ParsedRow,
    ParsedStudent,
    ParsedSubjectResult,
    ParseResult,
    RowError,
)
from analytics.exceptions import AnalyticsValidationError

_KNOWN_SUBJECTS = {'MATHS', 'PHYSICS', 'CHEMISTRY'}
_PREFIX_MAP = {'MATHS': 'm_q', 'PHYSICS': 'p_q', 'CHEMISTRY': 'c_q'}

# Excel summary column positions (0-indexed)
_COL_SUBJECT     = 2
_COL_TOTAL_MARKS = 9
_COL_RANK        = 11
_COL_TOTAL_Q     = 14
_COL_CORRECT     = 18


# ------------------------------------------------------------------ public API

def parse_excel_file(file_obj) -> ParseResult:
    """
    Parse an Excel rank-card workbook and return a ParseResult compatible
    with the CSV-upload pipeline.

    Section and class are resolved later in the storage layer by matching
    StudentProfile.admission_number — no manual input needed from the principal.
    """
    wb = openpyxl.load_workbook(file_obj, read_only=True, data_only=True)
    all_rows = list(_iter_all_rows(wb))
    wb.close()

    if not all_rows:
        raise AnalyticsValidationError('Excel file is empty or could not be read.')

    student_blocks = _split_into_student_blocks(all_rows)

    if not student_blocks:
        raise AnalyticsValidationError('No student rank cards found in the Excel file.')

    exam_meta: Optional[ParsedExamMeta] = None
    parsed_rows: List[ParsedRow] = []
    skipped: List[RowError] = []
    question_cols: Optional[Dict[str, List[str]]] = None

    for block_idx, block_rows in enumerate(student_blocks):
        try:
            parsed_row, meta, q_cols = _parse_student_block(
                block_rows, block_idx + 1
            )
            if exam_meta is None:
                exam_meta = meta
                question_cols = q_cols
            parsed_rows.append(parsed_row)
        except Exception as exc:
            skipped.append(RowError(
                row_number=block_idx + 1,
                student_id='',
                reason=str(exc),
            ))

    if exam_meta is None:
        raise AnalyticsValidationError('No valid student data found in the Excel file.')

    return ParseResult(
        exam_meta=exam_meta,
        question_cols=question_cols or {},
        rows=parsed_rows,
        skipped=skipped,
    )


# ------------------------------------------------------------------ row iteration

def _iter_all_rows(wb) -> List[tuple]:
    """Flatten all sheets into a single ordered list of row tuples."""
    rows = []
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        for row in ws.iter_rows(values_only=True):
            rows.append(row)
    return rows


def _cell(row: tuple, idx: int):
    """Safely get a cell value, returning None if out of bounds."""
    try:
        return row[idx]
    except IndexError:
        return None


def _str(value) -> str:
    """Convert a cell value to a stripped string, empty string if None."""
    if value is None:
        return ''
    return str(value).strip()


# ------------------------------------------------------------------ block splitting

def _is_student_start(row: tuple) -> bool:
    """
    Return True if this row marks the start of a new student block.
    Only split on 'Student Name :' — 'STUDENT RANK CARD' is a decorative
    header that immediately precedes 'Student Name :' in the same block
    and must not trigger an independent split.
    """
    first = _str(_cell(row, 0))
    return first.startswith('Student Name :')


def _split_into_student_blocks(all_rows: List[tuple]) -> List[List[tuple]]:
    """Group rows into per-student blocks, split on student-start markers."""
    blocks: List[List[tuple]] = []
    current: List[tuple] = []

    for row in all_rows:
        if _is_student_start(row):
            if current:
                blocks.append(current)
            current = [row]
        elif current:
            current.append(row)

    if current:
        blocks.append(current)

    return blocks


# ------------------------------------------------------------------ per-block parser

def _parse_student_block(
    block: List[tuple],
    block_number: int,
) -> Tuple['ParsedRow', 'ParsedExamMeta', Dict[str, List[str]]]:
    """
    Parse one student's block of rows. Returns (ParsedRow, ParsedExamMeta, question_cols).
    Raises ValueError on parse failure.
    """
    name = adm_no = exam_name = exam_date_str = None
    subject_summaries: Dict[str, dict] = {}
    subject_order: List[str] = []
    actual_q_statuses: Dict[int, str] = {}   # global q_no → C/W/U (last seen wins)

    i = 0
    while i < len(block):
        row = block[i]
        first = _str(_cell(row, 0))

        if first.startswith('Student Name :'):
            name = first.split(':', 1)[1].strip() or _str(_cell(row, 5))

        elif first.startswith('ADM No :'):
            adm_no = first.split(':', 1)[1].strip() or _str(_cell(row, 5))

        elif first.startswith('Exam Name :'):
            # Value may be in col 4 or col 5
            val = _str(_cell(row, 4)) or _str(_cell(row, 5))
            exam_name = val

        elif first.startswith('Exam Date :'):
            val = _str(_cell(row, 4)) or _str(_cell(row, 5))
            exam_date_str = val

        elif _str(_cell(row, _COL_SUBJECT)) in _KNOWN_SUBJECTS:
            # Summary data row — subject name at col 2
            subj = _str(_cell(row, _COL_SUBJECT))
            try:
                total_marks = int(_cell(row, _COL_TOTAL_MARKS) or 0)
                rank        = int(_cell(row, _COL_RANK)        or 0)
                total_q     = int(_cell(row, _COL_TOTAL_Q)     or 0)
                correct     = int(_cell(row, _COL_CORRECT)     or 0)
                if total_q > 0:
                    subject_summaries[subj] = {
                        'total_marks': total_marks,
                        'rank':        rank,
                        'total_q':     total_q,
                        'correct':     correct,
                    }
                    if subj not in subject_order:
                        subject_order.append(subj)
            except (ValueError, TypeError):
                pass

        elif first == 'QNo':
            # Question batch: QNo row + skip Ans + skip Key + Status row
            q_nos = _extract_q_nos(row)
            status_row = _find_status_row(block, i)
            if status_row is not None and q_nos:
                statuses = _extract_statuses(row, status_row)
                for q_no, status in statuses.items():
                    actual_q_statuses[q_no] = status   # last seen wins

        i += 1

    # Validate
    if not adm_no:
        raise ValueError(f'Block {block_number}: ADM No not found')
    if not name:
        raise ValueError(f'Block {block_number}: Student Name not found')
    if not exam_name:
        raise ValueError(f'Block {block_number}: Exam Name not found')
    if not exam_date_str:
        raise ValueError(f'Block {block_number}: Exam Date not found')
    if not subject_summaries:
        raise ValueError(f'Block {block_number}: No subject summary found')

    exam_date = _parse_exam_date(exam_date_str)
    subject_totals_ordered = [(s, subject_summaries[s]['total_q']) for s in subject_order]

    # Build results + question_statuses from question-level data
    results: Dict[str, 'ParsedSubjectResult'] = {}
    question_statuses: Dict[str, Dict[int, str]] = {}
    question_cols: Dict[str, List[str]] = {}

    for subj in subject_order:
        summary = subject_summaries[subj]
        prefix  = _PREFIX_MAP.get(subj, subj.lower()[0] + '_q')
        question_cols[subj] = [f'{prefix}{j}' for j in range(1, summary['total_q'] + 1)]
        question_statuses[subj] = {}

    # Remap global q_no → (subject, local q_no) and count wrong/unattempted
    for actual_q_no, status in actual_q_statuses.items():
        subj, local_q_no = _map_to_local(actual_q_no, subject_totals_ordered)
        if subj is not None:
            question_statuses[subj][local_q_no] = status

    for subj in subject_order:
        summary = subject_summaries[subj]
        q_map   = question_statuses[subj]
        correct     = sum(1 for s in q_map.values() if s == 'C')
        wrong       = sum(1 for s in q_map.values() if s == 'W')
        unattempted = summary['total_q'] - correct - wrong

        # Fill missing questions as unattempted
        for j in range(1, summary['total_q'] + 1):
            if j not in q_map:
                q_map[j] = 'U'

        results[subj] = ParsedSubjectResult(
            total_marks=summary['total_marks'],
            rank=summary['rank'],
            correct=correct,
            wrong=wrong,
            unattempted=unattempted,
        )

    parsed_row = ParsedRow(
        student=ParsedStudent(
            student_ref_id=adm_no,
            name=name,
            class_name='',    # resolved from StudentProfile.admission_number in storage
            section_name='',
        ),
        results=results,
        question_statuses=question_statuses,
    )
    exam_meta = ParsedExamMeta(exam_name=exam_name, exam_date=exam_date)
    return parsed_row, exam_meta, question_cols


# ------------------------------------------------------------------ question helpers

def _extract_q_nos(q_row: tuple) -> List[int]:
    """Extract non-None integer values from a QNo row (skipping 'QNo' label at col 0)."""
    result = []
    for val in q_row[1:]:
        if val is not None:
            try:
                result.append(int(val))
            except (ValueError, TypeError):
                pass
    return result


def _find_status_row(block: List[tuple], q_row_idx: int) -> Optional[tuple]:
    """
    Find the Status row that follows the QNo row at q_row_idx.
    The Status row is expected within the next 3 rows.
    """
    for offset in range(1, 4):
        idx = q_row_idx + offset
        if idx < len(block) and _str(_cell(block[idx], 0)) == 'Status':
            return block[idx]
    return None


def _extract_statuses(q_row: tuple, status_row: tuple) -> Dict[int, str]:
    """
    Zip QNo row and Status row to build {q_no: status} dict.
    Only positions where QNo is a non-None integer are included.
    """
    result = {}
    for q_val, s_val in zip(q_row[1:], status_row[1:]):
        if q_val is not None:
            try:
                q_no   = int(q_val)
                status = _str(s_val).upper()
                result[q_no] = status if status in ('C', 'W', 'U') else 'U'
            except (ValueError, TypeError):
                pass
    return result


# ------------------------------------------------------------------ shared helpers

def _parse_exam_date(raw: str) -> date:
    """Parse "14(19/04/2026)" → date(2026, 4, 19)."""
    match = re.search(r'\((\d{2}/\d{2}/\d{4})\)', raw)
    if match:
        return datetime.strptime(match.group(1), '%d/%m/%Y').date()
    for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(raw.strip(), fmt).date()
        except ValueError:
            pass
    raise ValueError(f'Cannot parse exam date: {raw!r}')


def _map_to_local(
    actual_q_no: int,
    subject_totals_ordered: List[Tuple[str, int]],
) -> Tuple[Optional[str], Optional[int]]:
    """Map a global question number to (subject_name, local_q_no)."""
    offset = 0
    for subj, total in subject_totals_ordered:
        if actual_q_no <= offset + total:
            return subj, actual_q_no - offset
        offset += total
    return None, None
