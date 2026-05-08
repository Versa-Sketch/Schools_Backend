from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import (
    AcademicCalendarEvent,
    AcademicClass,
    Announcement,
    AnnouncementTarget,
    AttendanceSession,
    Homework,
    ParentQuery,
    ParentQueryReply,
    School,
    Section,
    StudentAttendance,
    StudyMaterial,
    Subject,
    User,
    AUTHOR_ROLE_PRINCIPAL,
    AUTHOR_ROLE_TEACHER,
    ANNOUNCEMENT_AUDIENCE_SCHOOL,
    ANNOUNCEMENT_AUDIENCE_CLASS,
    ANNOUNCEMENT_AUDIENCE_SECTION,
    ATTENDANCE_STATUS_PRESENT,
    ATTENDANCE_STATUS_ABSENT,
    CALENDAR_EVENT_TYPE_HOLIDAY,
    CALENDAR_EVENT_TYPE_EVENT,
    CALENDAR_EVENT_TYPE_EXAM,
    PARENT_QUERY_STATUS_ANSWERED,
)
from principal.models import PrincipalProfile
from teacher.models import TeacherProfile
from student.models import StudentProfile
from parent.models import ParentProfile


SEED_PASSWORD = 'Seed@1234'
SEED_SUBDOMAIN = 'green-valley'
PLACEHOLDER_FILE = 'https://placehold.co/sample.pdf'

SEEDED_USERNAMES = [
    'principal1',
    'teacher1', 'teacher2', 'teacher3',
    'student_5a_1', 'student_5a_2', 'student_5a_3',
    'student_5b_1', 'student_5b_2', 'student_5b_3',
    'student_4a_1', 'student_4a_2', 'student_4a_3',
    'student_4b_1', 'student_4b_2', 'student_4b_3',
    'parent1', 'parent2', 'parent3', 'parent4', 'parent5', 'parent6',
]


def _first_or_create(model_cls, lookup, defaults):
    obj = model_cls.objects.filter(**lookup).first()
    if obj:
        return obj, False
    return model_cls.objects.create(**lookup, **defaults), True


class Command(BaseCommand):
    help = 'Seed the database with sample data for all apps.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all previously seeded data before re-seeding.',
        )

    def handle(self, *args, **options):
        if options['flush']:
            self._flush()

        self.stdout.write('Seeding data...\n')

        with transaction.atomic():
            school   = self._seed_school()
            subjects = self._seed_subjects(school)
            classes  = self._seed_classes(school)
            principal = self._seed_principal(school)
            teachers  = self._seed_teachers(school, subjects)
            sections  = self._seed_sections(school, classes, teachers)
            self._assign_teacher_sections(teachers, sections)
            students  = self._seed_students(school, classes, sections)
            parents   = self._seed_parents(school, students)
            self._seed_attendance(school, sections, students, teachers)
            self._seed_announcements(school, principal, teachers, classes, sections)
            self._seed_study_materials(school, sections, subjects, teachers)
            self._seed_homework(school, sections, subjects, teachers)
            self._seed_calendar_events(school)
            self._seed_parent_queries(school, parents, students, sections, teachers)

        self._print_summary()

    # ------------------------------------------------------------------
    # Flush
    # ------------------------------------------------------------------

    def _flush(self):
        from core.models import (
            AbsentNotificationLog, AnnouncementAttachment, AnnouncementTarget,
            StudentBulkUploadRow, StudentBulkUploadBatch,
        )
        from notifications.models import Notification

        self.stdout.write(self.style.WARNING('  Flushing seed data...'))
        school = School.objects.filter(subdomain=SEED_SUBDOMAIN).first()

        if school:
            # Delete leaf nodes first (PROTECT relations must be cleared before parents)
            ParentQueryReply.objects.filter(query__school=school).delete()
            ParentQuery.objects.filter(school=school).delete()
            AbsentNotificationLog.objects.filter(attendance__session__school=school).delete()
            StudentAttendance.objects.filter(session__school=school).delete()
            AttendanceSession.objects.filter(school=school).delete()
            AnnouncementAttachment.objects.filter(announcement__school=school).delete()
            AnnouncementTarget.objects.filter(announcement__school=school).delete()
            Announcement.objects.filter(school=school).delete()
            StudyMaterial.objects.filter(school=school).delete()
            Homework.objects.filter(school=school).delete()
            StudentBulkUploadRow.objects.filter(batch__school=school).delete()
            StudentBulkUploadBatch.objects.filter(school=school).delete()
            AcademicCalendarEvent.objects.filter(school=school).delete()

        # Notifications tied to seeded users
        Notification.objects.filter(recipient__username__in=SEEDED_USERNAMES).delete()

        # Profiles (reverse FK order: parents → students → teachers → principal)
        for pp in ParentProfile.objects.filter(user__username__in=SEEDED_USERNAMES):
            pp.students.clear()
        ParentProfile.objects.filter(user__username__in=SEEDED_USERNAMES).delete()
        StudentProfile.objects.filter(user__username__in=SEEDED_USERNAMES).delete()

        if school:
            for tp in TeacherProfile.objects.filter(school=school):
                tp.assigned_sections.clear()
            # Now school → section, class, subject can be deleted safely
            Section.objects.filter(school=school).delete()
            AcademicClass.objects.filter(school=school).delete()
            Subject.objects.filter(school=school).delete()

        TeacherProfile.objects.filter(user__username__in=SEEDED_USERNAMES).delete()
        PrincipalProfile.objects.filter(user__username__in=SEEDED_USERNAMES).delete()

        if school:
            school.delete()

        User.objects.filter(username__in=SEEDED_USERNAMES).delete()
        self.stdout.write(self.style.SUCCESS('  Flush complete.\n'))

    # ------------------------------------------------------------------
    # Layer 1 – School
    # ------------------------------------------------------------------

    def _seed_school(self):
        school, created = School.objects.get_or_create(
            subdomain=SEED_SUBDOMAIN,
            defaults={
                'name': 'Green Valley Public School',
                'address': '123 Green Valley Road, Bengaluru - 560001',
                'contact_email': 'admin@greenvalley.edu',
                'contact_phone': '9000000000',
                'is_active': True,
            },
        )
        label = 'Created' if created else 'Found'
        self.stdout.write(f'  [{label}] School: {school.name}')
        return school

    # ------------------------------------------------------------------
    # Layer 2 – Academic structure
    # ------------------------------------------------------------------

    def _seed_subjects(self, school):
        data = [
            ('Mathematics',      'MATH'),
            ('Science',          'SCI'),
            ('English',          'ENG'),
            ('Social Studies',   'SST'),
            ('Hindi',            'HIN'),
            ('Computer Science', 'CS'),
        ]
        subjects = {}
        for name, code in data:
            obj, _ = Subject.objects.get_or_create(
                school=school, name=name,
                defaults={'code': code, 'is_active': True},
            )
            subjects[code] = obj
        self.stdout.write(f'  Seeded {len(subjects)} subjects.')
        return subjects

    def _seed_classes(self, school):
        data = [
            ('Class 1', 1), ('Class 2', 2), ('Class 3', 3),
            ('Class 4', 4), ('Class 5', 5),
        ]
        classes = {}
        for name, order in data:
            obj, _ = AcademicClass.objects.get_or_create(
                school=school, name=name,
                defaults={'display_order': order},
            )
            classes[name] = obj
        self.stdout.write(f'  Seeded {len(classes)} classes.')
        return classes

    # ------------------------------------------------------------------
    # Layer 3 – Principal
    # ------------------------------------------------------------------

    def _seed_principal(self, school):
        user, created = User.objects.get_or_create(
            username='principal1',
            defaults={'role': 'PRINCIPAL', 'phone_number': '9000000001'},
        )
        if created:
            user.set_password(SEED_PASSWORD)
            user.save()
        PrincipalProfile.objects.get_or_create(
            user=user,
            defaults={'school': school},
        )
        self.stdout.write('  Seeded 1 principal.')
        return user

    # ------------------------------------------------------------------
    # Layer 4 – Teachers (profiles without sections yet)
    # ------------------------------------------------------------------

    def _seed_teachers(self, school, subjects):
        data = [
            ('teacher1', '9000000002', 'Teacher One',   'MATH'),
            ('teacher2', '9000000003', 'Teacher Two',   'SCI'),
            ('teacher3', '9000000004', 'Teacher Three', 'ENG'),
        ]
        teachers = {}
        for username, phone, name, subj_code in data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'role': 'TEACHER', 'phone_number': phone},
            )
            if created:
                user.set_password(SEED_PASSWORD)
                user.save()
            profile, _ = TeacherProfile.objects.get_or_create(
                user=user,
                defaults={
                    'school': school,
                    'name': name,
                    'primary_subject': subjects[subj_code],
                },
            )
            teachers[username] = (user, profile)
        self.stdout.write(f'  Seeded {len(teachers)} teachers.')
        return teachers

    # ------------------------------------------------------------------
    # Layer 5 – Sections (use teacher profiles for class_teacher FK)
    # ------------------------------------------------------------------

    def _seed_sections(self, school, classes, teachers):
        t1 = teachers['teacher1'][1]
        t2 = teachers['teacher2'][1]
        t3 = teachers['teacher3'][1]

        data = [
            ('5A', classes['Class 5'], t1),
            ('5B', classes['Class 5'], t2),
            ('4A', classes['Class 4'], t3),
            ('4B', classes['Class 4'], None),
        ]
        sections = {}
        for name, cls, teacher_profile in data:
            obj, _ = Section.objects.get_or_create(
                academic_class=cls, name=name,
                defaults={'school': school, 'class_teacher': teacher_profile},
            )
            sections[name] = obj
        self.stdout.write(f'  Seeded {len(sections)} sections.')
        return sections

    def _assign_teacher_sections(self, teachers, sections):
        # teacher1 → assigned to 5A, 5B  (class teacher: 5A)
        t1 = teachers['teacher1'][1]
        if not t1.assigned_sections.exists():
            t1.assigned_sections.set([sections['5A'], sections['5B']])

        # teacher2 → assigned to 5A, 5B  (class teacher: 5B)
        t2 = teachers['teacher2'][1]
        if not t2.assigned_sections.exists():
            t2.assigned_sections.set([sections['5A'], sections['5B']])

        # teacher3 → assigned to 4A, 4B  (class teacher: 4A)
        t3 = teachers['teacher3'][1]
        if not t3.assigned_sections.exists():
            t3.assigned_sections.set([sections['4A'], sections['4B']])

        self.stdout.write('  Assigned sections to teachers (M2M).')

    # ------------------------------------------------------------------
    # Layer 6 – Students
    # ------------------------------------------------------------------

    def _seed_students(self, school, classes, sections):
        data = [
            ('student_5a_1', '9100000001', 'Aarav Mehta',    sections['5A'], classes['Class 5'], '1', 'ADM5A001'),
            ('student_5a_2', '9100000002', 'Bhavya Rao',     sections['5A'], classes['Class 5'], '2', 'ADM5A002'),
            ('student_5a_3', '9100000003', 'Chetan Verma',   sections['5A'], classes['Class 5'], '3', 'ADM5A003'),
            ('student_5b_1', '9100000004', 'Divya Nair',     sections['5B'], classes['Class 5'], '1', 'ADM5B001'),
            ('student_5b_2', '9100000005', 'Esha Gupta',     sections['5B'], classes['Class 5'], '2', 'ADM5B002'),
            ('student_5b_3', '9100000006', 'Farhan Khan',    sections['5B'], classes['Class 5'], '3', 'ADM5B003'),
            ('student_4a_1', '9100000007', 'Gauri Sharma',   sections['4A'], classes['Class 4'], '1', 'ADM4A001'),
            ('student_4a_2', '9100000008', 'Hari Prasad',    sections['4A'], classes['Class 4'], '2', 'ADM4A002'),
            ('student_4a_3', '9100000009', 'Isha Patel',     sections['4A'], classes['Class 4'], '3', 'ADM4A003'),
            ('student_4b_1', '9100000010', 'Jai Malhotra',   sections['4B'], classes['Class 4'], '1', 'ADM4B001'),
            ('student_4b_2', '9100000011', 'Kavya Reddy',    sections['4B'], classes['Class 4'], '2', 'ADM4B002'),
            ('student_4b_3', '9100000012', 'Lakshmi Iyer',   sections['4B'], classes['Class 4'], '3', 'ADM4B003'),
        ]
        students = {}
        for username, phone, name, section, cls, roll, adm in data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'role': 'STUDENT', 'phone_number': phone},
            )
            if created:
                user.set_password(SEED_PASSWORD)
                user.save()
            profile, _ = StudentProfile.objects.get_or_create(
                user=user,
                defaults={
                    'school': school,
                    'name': name,
                    'academic_class': cls,
                    'section': section,
                    'roll_number': roll,
                    'admission_number': adm,
                    'is_active': True,
                },
            )
            students[username] = profile
        self.stdout.write(f'  Seeded {len(students)} students.')
        return students

    # ------------------------------------------------------------------
    # Layer 7 – Parents
    # ------------------------------------------------------------------

    def _seed_parents(self, school, students):
        data = [
            ('parent1', '9200000001', 'Ramesh Kumar',  ['student_5a_1']),
            ('parent2', '9200000002', 'Sunita Sharma', ['student_5a_2']),
            ('parent3', '9200000003', 'Vijay Mehta',   ['student_5a_3', 'student_5b_1']),
            ('parent4', '9200000004', 'Priya Singh',   ['student_5b_2']),
            ('parent5', '9200000005', 'Arjun Nair',    ['student_4a_1', 'student_4b_1']),
            ('parent6', '9200000006', 'Deepa Reddy',   ['student_4a_2']),
        ]
        parents = {}
        for username, phone, name, student_keys in data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'role': 'PARENT', 'phone_number': phone},
            )
            if created:
                user.set_password(SEED_PASSWORD)
                user.save()
            profile, _ = ParentProfile.objects.get_or_create(
                user=user,
                defaults={'school': school, 'name': name},
            )
            if not profile.students.exists():
                for key in student_keys:
                    profile.students.add(students[key])
            parents[username] = profile
        self.stdout.write(f'  Seeded {len(parents)} parents.')
        return parents

    # ------------------------------------------------------------------
    # Layer 8 – Attendance
    # ------------------------------------------------------------------

    def _seed_attendance(self, school, sections, students, teachers):
        today = timezone.now().date()
        t1 = teachers['teacher1'][1]
        t2 = teachers['teacher2'][1]
        sec_5a = sections['5A']
        sec_5b = sections['5B']

        # ── Session 1 : 5A MORNING  (CONFIRMED) ──────────────────────
        s1, _ = AttendanceSession.objects.get_or_create(
            section=sec_5a, date=today, slot='MORNING',
            defaults={'school': school, 'taken_by': t1},
        )
        StudentAttendance.objects.get_or_create(
            session=s1, student=students['student_5a_1'],
            defaults={'status': ATTENDANCE_STATUS_PRESENT},
        )
        StudentAttendance.objects.get_or_create(
            session=s1, student=students['student_5a_2'],
            defaults={'status': ATTENDANCE_STATUS_PRESENT},
        )
        StudentAttendance.objects.get_or_create(
            session=s1, student=students['student_5a_3'],
            defaults={'status': ATTENDANCE_STATUS_ABSENT},
        )
        if not s1.confirmed_at:
            s1.confirmed_at = timezone.now()
            s1.save(update_fields=['confirmed_at', 'updated_at'])

        # ── Session 2 : 5A AFTERNOON (CONFIRMED) ─────────────────────
        s2, _ = AttendanceSession.objects.get_or_create(
            section=sec_5a, date=today, slot='AFTERNOON',
            defaults={'school': school, 'taken_by': t1},
        )
        StudentAttendance.objects.get_or_create(
            session=s2, student=students['student_5a_1'],
            defaults={'status': ATTENDANCE_STATUS_PRESENT},
        )
        StudentAttendance.objects.get_or_create(
            session=s2, student=students['student_5a_2'],
            defaults={'status': ATTENDANCE_STATUS_ABSENT},
        )
        StudentAttendance.objects.get_or_create(
            session=s2, student=students['student_5a_3'],
            defaults={'status': ATTENDANCE_STATUS_PRESENT},
        )
        if not s2.confirmed_at:
            s2.confirmed_at = timezone.now()
            s2.save(update_fields=['confirmed_at', 'updated_at'])

        # ── Session 3 : 5B MORNING  (PENDING – not confirmed) ────────
        AttendanceSession.objects.get_or_create(
            section=sec_5b, date=today, slot='MORNING',
            defaults={'school': school, 'taken_by': t2},
        )

        self.stdout.write('  Seeded 3 attendance sessions (2 confirmed, 1 pending).')

    # ------------------------------------------------------------------
    # Layer 9 – Announcements
    # ------------------------------------------------------------------

    def _seed_announcements(self, school, principal, teachers, classes, sections):
        t1_user = teachers['teacher1'][0]
        now = timezone.now()

        # School-wide — by principal
        if not Announcement.objects.filter(school=school, title='Annual Sports Day Announcement').exists():
            Announcement.objects.create(
                school=school,
                author=principal,
                author_role=AUTHOR_ROLE_PRINCIPAL,
                title='Annual Sports Day Announcement',
                body=(
                    'Our Annual Sports Day will be held on August 14th. '
                    'All students are encouraged to participate in at least one event. '
                    'Practice sessions start next week.'
                ),
                audience=ANNOUNCEMENT_AUDIENCE_SCHOOL,
                published_at=now,
                is_active=True,
            )

        # Class-level — by principal
        ann2 = Announcement.objects.filter(school=school, title='Class 5 Syllabus Update').first()
        if not ann2:
            ann2 = Announcement.objects.create(
                school=school,
                author=principal,
                author_role=AUTHOR_ROLE_PRINCIPAL,
                title='Class 5 Syllabus Update',
                body=(
                    'The syllabus for Class 5 has been revised for the upcoming term. '
                    'Students will be provided printed copies. '
                    'Parents may contact the office for details.'
                ),
                audience=ANNOUNCEMENT_AUDIENCE_CLASS,
                published_at=now,
                is_active=True,
            )
            AnnouncementTarget.objects.create(announcement=ann2, academic_class=classes['Class 5'])

        # Section-level — by class teacher (teacher1 → 5A)
        ann3 = Announcement.objects.filter(school=school, title='Math Test Tomorrow').first()
        if not ann3:
            ann3 = Announcement.objects.create(
                school=school,
                author=t1_user,
                author_role=AUTHOR_ROLE_TEACHER,
                title='Math Test Tomorrow',
                body=(
                    'There will be a Mathematics test tomorrow covering Chapter 3 (Fractions). '
                    'Please revise exercises 3.1 to 3.5. Bring your geometry box.'
                ),
                audience=ANNOUNCEMENT_AUDIENCE_SECTION,
                published_at=now,
                is_active=True,
            )
            AnnouncementTarget.objects.create(announcement=ann3, section=sections['5A'])

        self.stdout.write('  Seeded 3 announcements (school-wide, Class 5, Section 5A).')

    # ------------------------------------------------------------------
    # Layer 10 – Study Materials
    # ------------------------------------------------------------------

    def _seed_study_materials(self, school, sections, subjects, teachers):
        t1 = teachers['teacher1'][1]
        t2 = teachers['teacher2'][1]
        today = timezone.now().date()

        if not StudyMaterial.objects.filter(school=school, title='Chapter 3 – Fractions Notes').exists():
            StudyMaterial.objects.create(
                school=school,
                section=sections['5A'],
                subject=subjects['MATH'],
                uploaded_by=t1,
                title='Chapter 3 – Fractions Notes',
                description='Detailed notes on addition, subtraction, and multiplication of fractions with solved examples.',
                file=PLACEHOLDER_FILE,
                material_date=today,
            )

        if not StudyMaterial.objects.filter(school=school, title='Water Cycle Worksheet').exists():
            StudyMaterial.objects.create(
                school=school,
                section=sections['5B'],
                subject=subjects['SCI'],
                uploaded_by=t2,
                title='Water Cycle Worksheet',
                description='Label the diagram and answer short questions on the water cycle.',
                file=PLACEHOLDER_FILE,
                material_date=today,
            )

        self.stdout.write('  Seeded 2 study materials.')

    # ------------------------------------------------------------------
    # Layer 11 – Homework
    # ------------------------------------------------------------------

    def _seed_homework(self, school, sections, subjects, teachers):
        t1 = teachers['teacher1'][1]
        t2 = teachers['teacher2'][1]
        tomorrow   = timezone.now() + timedelta(days=1)
        day_after  = timezone.now() + timedelta(days=2)

        if not Homework.objects.filter(school=school, section=sections['5A'], subject=subjects['MATH']).exists():
            Homework.objects.create(
                school=school,
                section=sections['5A'],
                subject=subjects['MATH'],
                assigned_by=t1,
                description='Complete exercises 3.1 to 3.5 from the textbook. Show all working steps.',
                deadline=tomorrow,
            )

        if not Homework.objects.filter(school=school, section=sections['5B'], subject=subjects['SCI']).exists():
            Homework.objects.create(
                school=school,
                section=sections['5B'],
                subject=subjects['SCI'],
                assigned_by=t2,
                description='Draw and label a diagram of the water cycle. Write 3 sentences about each stage.',
                deadline=day_after,
            )

        self.stdout.write('  Seeded 2 homework assignments.')

    # ------------------------------------------------------------------
    # Layer 12 – Calendar Events
    # ------------------------------------------------------------------

    def _seed_calendar_events(self, school):
        today     = timezone.now().date()
        all_roles = ['TEACHER', 'STUDENT', 'PARENT']

        events = [
            (
                'Diwali Holiday',
                CALENDAR_EVENT_TYPE_HOLIDAY,
                today + timedelta(days=7),
                today + timedelta(days=7),
                'School closed for Diwali. Classes resume the following Monday.',
            ),
            (
                'Annual Sports Day',
                CALENDAR_EVENT_TYPE_EVENT,
                today + timedelta(days=14),
                today + timedelta(days=14),
                'Annual inter-class sports competition. Participation is compulsory for all students.',
            ),
            (
                'Mid-Term Examination',
                CALENDAR_EVENT_TYPE_EXAM,
                today + timedelta(days=30),
                today + timedelta(days=34),
                'Mid-term examinations for Classes 1–5. Timetable will be shared separately.',
            ),
        ]
        for title, etype, start, end, desc in events:
            if not AcademicCalendarEvent.objects.filter(school=school, title=title).exists():
                AcademicCalendarEvent.objects.create(
                    school=school,
                    title=title,
                    event_type=etype,
                    start_date=start,
                    end_date=end,
                    description=desc,
                    visible_to=all_roles,
                )

        self.stdout.write('  Seeded 3 calendar events (holiday, event, exam).')

    # ------------------------------------------------------------------
    # Layer 13 – Parent Query + Reply
    # ------------------------------------------------------------------

    def _seed_parent_queries(self, school, parents, students, sections, teachers):
        parent1   = parents['parent1']
        student   = students['student_5a_1']
        sec_5a    = sections['5A']
        t1_profile = teachers['teacher1'][1]
        t1_user    = teachers['teacher1'][0]

        query = ParentQuery.objects.filter(
            school=school, parent=parent1, student=student,
            subject='Math homework clarification',
        ).first()

        if not query:
            query = ParentQuery.objects.create(
                school=school,
                parent=parent1,
                student=student,
                section=sec_5a,
                assigned_teacher=t1_profile,
                subject='Math homework clarification',
                message=(
                    'My child is having difficulty with question 4 in exercise 3.2. '
                    'Could you please explain the steps involved?'
                ),
                status=PARENT_QUERY_STATUS_ANSWERED,
            )
            ParentQueryReply.objects.create(
                query=query,
                sender=t1_user,
                message=(
                    'Hello! For question 4, please apply the BODMAS rule. '
                    'Start by solving the expression inside the brackets, '
                    'then handle division, followed by multiplication, '
                    'and finally addition and subtraction. '
                    'Feel free to reach out if further clarification is needed.'
                ),
            )

        self.stdout.write('  Seeded 1 parent query with teacher reply.')

    # ------------------------------------------------------------------
    # Summary output
    # ------------------------------------------------------------------

    def _print_summary(self):
        w = self.stdout.write
        s = self.style.SUCCESS
        b = self.style.HTTP_INFO

        w('\n')
        w(s('=' * 66))
        w(s('  SEED DATA COMPLETE'))
        w(s('=' * 66))
        w('')
        w(b('  School:      Green Valley Public School'))
        w(b('  Subdomain:   green-valley'))
        w('')
        w('  PRINCIPAL                                    password: Seed@1234')
        w('    username: principal1       phone: 9000000001')
        w('')
        w('  TEACHERS                                     password: Seed@1234')
        w('    teacher1  Mathematics   phone: 9000000002  (class teacher: 5A, teaches: 5A + 5B)')
        w('    teacher2  Science       phone: 9000000003  (class teacher: 5B, teaches: 5A + 5B)')
        w('    teacher3  English       phone: 9000000004  (class teacher: 4A, teaches: 4A + 4B)')
        w('')
        w('  STUDENTS                                     password: Seed@1234')
        w('    Class 5A  student_5a_1 Aarav Mehta    phone: 9100000001')
        w('              student_5a_2 Bhavya Rao     phone: 9100000002')
        w('              student_5a_3 Chetan Verma   phone: 9100000003  [absent in morning session]')
        w('    Class 5B  student_5b_1 Divya Nair     phone: 9100000004')
        w('              student_5b_2 Esha Gupta     phone: 9100000005')
        w('              student_5b_3 Farhan Khan    phone: 9100000006')
        w('    Class 4A  student_4a_1 Gauri Sharma   phone: 9100000007')
        w('              student_4a_2 Hari Prasad    phone: 9100000008')
        w('              student_4a_3 Isha Patel     phone: 9100000009')
        w('    Class 4B  student_4b_1 Jai Malhotra   phone: 9100000010')
        w('              student_4b_2 Kavya Reddy    phone: 9100000011')
        w('              student_4b_3 Lakshmi Iyer   phone: 9100000012')
        w('')
        w('  PARENTS                                      password: Seed@1234')
        w('    parent1 Ramesh Kumar   phone: 9200000001  -> student_5a_1')
        w('    parent2 Sunita Sharma  phone: 9200000002  -> student_5a_2')
        w('    parent3 Vijay Mehta    phone: 9200000003  -> student_5a_3 + student_5b_1  [2 children]')
        w('    parent4 Priya Singh    phone: 9200000004  -> student_5b_2')
        w('    parent5 Arjun Nair     phone: 9200000005  -> student_4a_1 + student_4b_1  [2 children]')
        w('    parent6 Deepa Reddy    phone: 9200000006  -> student_4a_2')
        w('')
        w('  CONTENT SEEDED')
        w('    Attendance:       2 confirmed sessions (5A morning + afternoon), 1 pending (5B morning)')
        w('    Announcements:    3 — school-wide, Class 5, Section 5A')
        w('    Study materials:  2 — Math (5A), Science (5B)')
        w('    Homework:         2 — Math (5A), Science (5B)')
        w('    Calendar events:  3 — holiday, event, exam')
        w('    Parent queries:   1 - ANSWERED, parent1 <-> teacher1')
        w('')
        w('  USEFUL TEST SCENARIOS')
        w('    Attendance history (has absence):  login as student_5a_3 or parent3')
        w('    Multi-child parent:                login as parent3 or parent5')
        w('    Class teacher announcements:       login as teacher1 (5A) or teacher2 (5B)')
        w('    Pending attendance session:        login as teacher2, check 5B morning')
        w('    Section with no class teacher:     section 4B')
        w('    Parent query flow:                 parent1 + teacher1')
        w('')
        w('  To reset and re-seed:')
        w('    python manage.py seed_data --flush')
        w(s('=' * 66))
