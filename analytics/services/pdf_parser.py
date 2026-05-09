"""
PDF rank-card parser for analytics exam uploads.

Public API:
    parse_pdf_file(file_obj, class_name, section_name) → ParseResult

The PDF contains one student rank card per page (some students span 2 pages).
Text is extracted line-by-line using pdfplumber. Student blocks are identified
by "STUDENT RANK CARD" or "Student Name :" markers.

Question numbers in the PDF are global (Q1–Q160). They are remapped to
local per-subject numbers (MATHS q_no 1–80, PHYSICS q_no 1–40, etc.)
using the subject order and total_questions from each student's summary row.
"""

import io
import re
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple

import pdfplumber

from analytics.services.csv_parser import (
    ParsedExamMeta,
    ParsedRow,
    ParsedStudent,
    ParsedSubjectResult,
    ParseResult,
    RowError,
)
from analytics.exceptions import AnalyticsValidationError

# Subjects expected in the summary (in order they appear in the file)
_KNOWN_SUBJECTS = {'MATHS', 'PHYSICS', 'CHEMISTRY'}

# Maps subject name → column prefix used in ParseResult.question_cols
_PREFIX_MAP = {'MATHS': 'm_q', 'PHYSICS': 'p_q', 'CHEMISTRY': 'c_q'}


# ------------------------------------------------------------------ public API

def parse_pdf_file(file_obj) -> ParseResult:
    """
    Parse a PDF rank-card file and return a ParseResult compatible with
    the CSV-upload pipeline.

    Section and class are resolved later in the storage layer by matching
    StudentProfile.admission_number — no manual input needed from the principal.
    """
    raw = file_obj.read()
    if isinstance(raw, str):
        raw = raw.encode('utf-8')

    lines = _extract_lines(io.BytesIO(raw))

    if not lines:
        raise AnalyticsValidationError('PDF file is empty or could not be read.')

    student_blocks = _split_into_student_blocks(lines)

    if not student_blocks:
        raise AnalyticsValidationError('No student rank cards found in the PDF.')

    exam_meta: Optional[ParsedExamMeta] = None
    parsed_rows: List[ParsedRow] = []
    skipped: List[RowError] = []
    question_cols: Optional[Dict[str, List[str]]] = None

    for block_idx, block_lines in enumerate(student_blocks):
        try:
            parsed_row, meta, q_cols = _parse_student_block(
                block_lines, block_idx + 1
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
        raise AnalyticsValidationError('No valid student data found in the PDF.')

    return ParseResult(
        exam_meta=exam_meta,
        question_cols=question_cols or {},
        rows=parsed_rows,
        skipped=skipped,
    )


# ------------------------------------------------------------------ extraction

def _extract_lines(file_obj) -> List[str]:
    """Extract all text lines from all pages, preserving order."""
    lines = []
    with pdfplumber.open(file_obj) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ''
            for line in text.split('\n'):
                stripped = line.strip()
                if stripped:
                    lines.append(stripped)
    return lines


def _split_into_student_blocks(lines: List[str]) -> List[List[str]]:
    """
    Split the full line stream into per-student blocks.
    A new block starts only on "Student Name :" — the first data-bearing
    line for each student. "STUDENT RANK CARD" is a decorative header that
    appears on the line just before "Student Name :" and is kept inside
    the current block (not used as a split trigger).
    """
    blocks: List[List[str]] = []
    current: Optional[List[str]] = None   # None = before first student block

    for line in lines:
        if line.startswith('Student Name :'):
            if current is not None:
                blocks.append(current)
            current = [line]
        elif current is not None:
            current.append(line)
        # lines before the first 'Student Name :' are discarded

    if current is not None:
        blocks.append(current)

    return blocks


# ------------------------------------------------------------------ per-block parser

def _parse_student_block(
    block: List[str],
    block_number: int,
) -> Tuple['ParsedRow', 'ParsedExamMeta', Dict[str, List[str]]]:
    """
    Parse one student's block of lines. Returns (ParsedRow, ParsedExamMeta, question_cols).
    Raises ValueError with a readable message on parse failure.
    """
    name = adm_no = exam_name = exam_date_str = None
    subject_summaries: Dict[str, dict] = {}   # {MATHS: {total_marks, rank, total_q, correct, wrong, unattempted}}
    subject_order: List[str] = []
    actual_q_statuses: Dict[int, str] = {}    # {global_q_no: C/W/U}

    i = 0
    while i < len(block):
        line = block[i]

        if line.startswith('Student Name :'):
            name = line.split(':', 1)[1].strip()

        elif line.startswith('ADM No :'):
            adm_no = line.split(':', 1)[1].strip()

        elif line.startswith('Exam Name :'):
            exam_name = line.split(':', 1)[1].strip()

        elif line.startswith('Exam Date :'):
            exam_date_str = line.split(':', 1)[1].strip()

        elif adm_no and line.startswith(adm_no):
            # Summary data row: "2251863 MATHS 42 641 80 42 42 38 0 0"
            parts = line.split()
            if len(parts) >= 10 and parts[1] in _KNOWN_SUBJECTS:
                subj = parts[1]
                try:
                    summary = {
                        'total_marks':  int(parts[2]),
                        'rank':         int(parts[3]),
                        'total_q':      int(parts[4]),
                        'correct':      int(parts[5]),
                        'wrong':        int(parts[7]),
                        'unattempted':  int(parts[9]),
                    }
                    subject_summaries[subj] = summary
                    if subj not in subject_order:
                        subject_order.append(subj)
                except (ValueError, IndexError):
                    pass  # malformed summary line — skip silently

        elif line.startswith('QNo '):
            # Question batch: next lines are Ans, Key, Status
            q_nos = _parse_int_list(line[4:])
            if i + 3 < len(block) and block[i + 3].startswith('Status '):
                statuses = block[i + 3][7:].split()
                for q_no, status in zip(q_nos, statuses):
                    s = status.strip().upper()
                    actual_q_statuses[q_no] = s if s in ('C', 'W', 'U') else 'U'
                i += 3  # skip Ans, Key, Status lines
        i += 1

    # Validate required fields
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

    # Build subject results and question_statuses using global→local q_no mapping
    results: Dict[str, ParsedSubjectResult] = {}
    question_statuses: Dict[str, Dict[int, str]] = {}
    question_cols: Dict[str, List[str]] = {}

    subject_totals_ordered = [(s, subject_summaries[s]['total_q']) for s in subject_order]

    for subj in subject_order:
        summary = subject_summaries[subj]
        results[subj] = ParsedSubjectResult(
            total_marks=summary['total_marks'],
            rank=summary['rank'],
            correct=summary['correct'],
            wrong=summary['wrong'],
            unattempted=summary['unattempted'],
        )
        prefix = _PREFIX_MAP.get(subj, subj.lower()[0] + '_q')
        question_cols[subj] = [f'{prefix}{j}' for j in range(1, summary['total_q'] + 1)]
        question_statuses[subj] = {}

    # Remap global q_no → (subject, local q_no)
    for actual_q_no, status in actual_q_statuses.items():
        subj, local_q_no = _map_to_local(actual_q_no, subject_totals_ordered)
        if subj is not None:
            question_statuses[subj][local_q_no] = status

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


# ------------------------------------------------------------------ helpers

def _parse_exam_date(raw: str) -> date:
    """Parse "14(19/04/2026)" → date(2026, 4, 19)."""
    match = re.search(r'\((\d{2}/\d{2}/\d{4})\)', raw)
    if match:
        return datetime.strptime(match.group(1), '%d/%m/%Y').date()
    # Fallback: try plain DD/MM/YYYY or YYYY-MM-DD
    for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(raw.strip(), fmt).date()
        except ValueError:
            pass
    raise ValueError(f'Cannot parse exam date: {raw!r}')


def _parse_int_list(text: str) -> List[int]:
    """Parse "1 2 3 4 ..." → [1, 2, 3, 4, ...]."""
    result = []
    for token in text.split():
        try:
            result.append(int(token))
        except ValueError:
            pass
    return result


def _map_to_local(
    actual_q_no: int,
    subject_totals_ordered: List[Tuple[str, int]],
) -> Tuple[Optional[str], Optional[int]]:
    """
    Map a global question number to (subject_name, local_q_no).
    E.g. with MATHS=80, PHYSICS=40, CHEMISTRY=40:
        Q81 → ('PHYSICS', 1)
        Q121 → ('CHEMISTRY', 1)
    """
    offset = 0
    for subj, total in subject_totals_ordered:
        if actual_q_no <= offset + total:
            return subj, actual_q_no - offset
        offset += total
    return None, None
