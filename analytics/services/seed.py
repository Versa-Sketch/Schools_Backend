"""
Seed data generator for analytics testing.

Produces a fully valid upload CSV with 21 students across 2 sections,
covering all 5 performance labels (EXCEPTIONAL → NEEDS_ATTENTION).

Only used in development (DEBUG=True). Never call in production.
"""

import csv
import io

from analytics.constants import REQUIRED_INFO_COLUMNS, REQUIRED_SUBJECT_COLUMNS

SEED_EXAM_NAME = 'CRASH-SR-MPC-EAM-PROG-II'
SEED_EXAM_DATE = '2026-05-01'
SEED_CLASS     = 'Class 11'

MATHS_Q_COUNT   = 80
PHYSICS_Q_COUNT = 40
CHEM_Q_COUNT    = 40

# fmt: off
# (name, section, maths_tuple, physics_tuple, chem_tuple)
# Each tuple = (total_marks, rank, correct, wrong, unattempted)
_STUDENTS = [
    # ── EXCEPTIONAL (3) ──────────────────────────────────────────────
    ('Arjun Mehta',   '11-A', (80, 1,  77, 2,  1), (39, 1,  37, 1, 2), (38, 1,  36, 1, 3)),
    ('Priya Sharma',  '11-A', (78, 2,  75, 3,  2), (37, 2,  35, 2, 3), (36, 2,  34, 2, 4)),
    ('Rahul Kumar',   '11-B', (77, 3,  74, 3,  3), (36, 3,  34, 3, 3), (35, 3,  33, 3, 4)),
    # ── ABOVE_AVERAGE (5) ────────────────────────────────────────────
    ('Sneha Reddy',   '11-A', (66, 4,  63, 7, 10), (32, 4,  30, 5, 5), (31, 4,  29, 5, 6)),
    ('Vikram Singh',  '11-B', (63, 5,  60, 8, 12), (30, 5,  28, 6, 6), (29, 5,  27, 5, 8)),
    ('Deepika Nair',  '11-A', (61, 6,  58, 9, 13), (29, 6,  27, 6, 7), (28, 6,  26, 6, 8)),
    ('Aditya Patel',  '11-B', (59, 7,  56, 9, 15), (28, 7,  26, 6, 8), (27, 7,  25, 6, 9)),
    ('Kavya Iyer',    '11-A', (58, 8,  55, 9, 16), (27, 8,  25, 7, 8), (26, 8,  24, 6,10)),
    # ── AVERAGE (8) ──────────────────────────────────────────────────
    ('Rohan Das',     '11-A', (55, 9,  52,11, 17), (25, 9,  23, 8, 9), (24, 9,  22, 7,11)),
    ('Anjali Gupta',  '11-B', (53,10,  50,11, 19), (24,10,  22, 9, 9), (23,10,  21, 8,11)),
    ('Manish Tiwari', '11-A', (52,11,  49,12, 19), (23,11,  21, 9,10), (22,11,  20, 8,12)),
    ('Pooja Joshi',   '11-B', (50,12,  47,13, 20), (22,12,  20,10,10), (21,12,  19, 9,12)),
    ('Sanjay Yadav',  '11-A', (49,13,  46,13, 21), (21,13,  19,10,11), (20,13,  18,10,12)),
    ('Ritu Verma',    '11-B', (47,14,  44,14, 22), (20,14,  18,11,11), (20,14,  18, 9,13)),
    ('Harish Bose',   '11-A', (46,15,  43,14, 23), (19,15,  17,11,12), (19,15,  17,10,13)),
    ('Meena Pillai',  '11-B', (44,16,  42,14, 24), (18,16,  16,12,12), (18,16,  16,10,14)),
    # ── BELOW_AVERAGE (3) ────────────────────────────────────────────
    ('Suresh Ghosh',  '11-A', (40,17,  37,18, 25), (15,17,  13,14,13), (14,17,  12,14,14)),
    ('Lakshmi Rao',   '11-B', (37,18,  34,20, 26), (13,18,  11,15,14), (13,18,  11,15,14)),
    ('Nilesh Jain',   '11-A', (34,19,  31,21, 28), (11,19,  10,16,14), (11,19,  10,16,14)),
    # ── NEEDS_ATTENTION (2) ──────────────────────────────────────────
    ('Reena Saxena',  '11-B', (24,20,  22,26, 32), ( 8,20,   7,18,15), ( 7,20,   6,19,15)),
    ('Pavan Hegde',   '11-A', (16,21,  14,30, 36), ( 5,21,   4,22,14), ( 5,21,   4,22,14)),
]
# fmt: on


def generate_seed_csv() -> str:
    maths_q_cols   = [f'm_q{i}' for i in range(1, MATHS_Q_COUNT   + 1)]
    physics_q_cols = [f'p_q{i}' for i in range(1, PHYSICS_Q_COUNT + 1)]
    chem_q_cols    = [f'c_q{i}' for i in range(1, CHEM_Q_COUNT    + 1)]

    all_headers = (
        REQUIRED_INFO_COLUMNS
        + REQUIRED_SUBJECT_COLUMNS
        + maths_q_cols
        + physics_q_cols
        + chem_q_cols
    )

    rows = []
    for idx, (name, section, m, p, c) in enumerate(_STUDENTS, start=1):
        row = {
            'student_id':   f'SEED{idx:03}',
            'student_name': name,
            'exam_name':    SEED_EXAM_NAME,
            'exam_date':    SEED_EXAM_DATE,
            'class':        SEED_CLASS,
            'section':      section,
            # maths
            'maths_total':       m[0], 'maths_rank':       m[1],
            'maths_correct':     m[2], 'maths_wrong':      m[3], 'maths_unattempted': m[4],
            # physics
            'physics_total':     p[0], 'physics_rank':     p[1],
            'physics_correct':   p[2], 'physics_wrong':    p[3], 'physics_unattempted': p[4],
            # chem
            'chem_total':        c[0], 'chem_rank':        c[1],
            'chem_correct':      c[2], 'chem_wrong':       c[3], 'chem_unattempted': c[4],
        }
        # question statuses — deterministic: C first, then W, then U
        for cols, (_, _, correct, wrong, _unattempted) in [
            (maths_q_cols,   m),
            (physics_q_cols, p),
            (chem_q_cols,    c),
        ]:
            for i, col in enumerate(cols, start=1):
                if i <= correct:
                    row[col] = 'C'
                elif i <= correct + wrong:
                    row[col] = 'W'
                else:
                    row[col] = 'U'
        rows.append(row)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=all_headers, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
