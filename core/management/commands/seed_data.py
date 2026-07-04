"""
Management command to seed demo data for Nurture Coaching Class.
Creates admin, teachers, parents, batches, subjects, concepts, and students.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
import random

from core.models import User, Batch, Subject, Concept, Student
from academics.models import Attendance, TestScore, ConceptMastery, Homework


class Command(BaseCommand):
    help = 'Seeds the database with demo data for Nurture Coaching Class'

    def handle(self, *args, **options):
        self.stdout.write('🌱 Seeding Nurture Coaching Class demo data...\n')

        # ─── Users ──────────────────────────────────
        admin = User.objects.create_superuser(
            username='admin', email='admin@nurture.com', password='admin123',
            first_name='Manish', last_name='Panchwate', role='admin',
            phone='9876543210', whatsapp_number='+919876543210'
        )
        self.stdout.write(self.style.SUCCESS('  ✓ Admin: admin / admin123'))

        t1 = User.objects.create_user(
            username='priya_teacher', password='teacher123',
            first_name='Priya', last_name='Sharma', role='teacher',
            email='priya@nurture.com', phone='9876543211'
        )
        t2 = User.objects.create_user(
            username='rahul_teacher', password='teacher123',
            first_name='Rahul', last_name='Deshmukh', role='teacher',
            email='rahul@nurture.com', phone='9876543212'
        )
        self.stdout.write(self.style.SUCCESS('  ✓ Teachers: priya_teacher, rahul_teacher / teacher123'))

        parents = []
        parent_data = [
            ('aarav_parent', 'Sunita', 'Patil'), ('sara_parent', 'Meena', 'Kulkarni'),
            ('vivaan_parent', 'Rekha', 'Joshi'), ('ananya_parent', 'Kavita', 'Bhatt'),
            ('arjun_parent', 'Swati', 'Nair'),
        ]
        for uname, fname, lname in parent_data:
            phone_num = f'98765{random.randint(10000, 99999)}'
            p = User.objects.create_user(
                username=uname, password='parent123',
                first_name=fname, last_name=lname, role='parent',
                phone=phone_num, whatsapp_number=f'+91{phone_num}'
            )
            parents.append(p)
        self.stdout.write(self.style.SUCCESS('  ✓ Parents: *_parent / parent123'))

        # ─── Batches ────────────────────────────────
        b1 = Batch.objects.create(name='Morning Batch - 7th/8th', teacher=t1, class_level='7th-8th', schedule='Mon-Sat 8:00-10:00 AM')
        b2 = Batch.objects.create(name='Evening Batch - 5th/6th', teacher=t2, class_level='5th-6th', schedule='Mon-Sat 4:00-6:00 PM')
        b3 = Batch.objects.create(name='Weekend Batch - 9th', teacher=t1, class_level='9th', schedule='Sat-Sun 10:00 AM-1:00 PM')
        self.stdout.write(self.style.SUCCESS('  ✓ 3 Batches created'))

        # ─── Subjects & Concepts ────────────────────
        subjects = {}
        mapping = {
            'Jr.KG': ['English', 'Math'],
            'Sr.KG': ['Hindi', 'English', 'Math', 'EVS'],
            '1st': ['Hindi', 'Marathi', 'Maths', 'EVS', 'English', 'ICT'],
            '2nd': ['Hindi', 'Marathi', 'Maths', 'EVS', 'English', 'ICT'],
            '3rd': ['Hindi', 'Marathi', 'Maths', 'EVS', 'English', 'ICT'],
            '4th': ['Hindi', 'Marathi', 'Maths', 'EVS', 'English', 'ICT'],
            '5th': ['English', 'EVS', 'Hindi', 'Marathi', 'ICT', 'Social Science', 'Sanskrit', 'Maths'],
            '6th': ['English', 'EVS', 'Hindi', 'Marathi', 'ICT', 'Social Science', 'Sanskrit', 'Maths'],
            '7th': ['English', 'EVS', 'Hindi', 'Marathi', 'ICT', 'Social Science', 'Sanskrit', 'Maths'],
            '8th': ['English', 'EVS', 'Hindi', 'Marathi', 'ICT', 'Social Science', 'Sanskrit', 'Maths'],
            '9th': ['Mathematics', 'Science', 'English', 'Hindi', 'Social Studies'], # Kept for existing 9th batch compatibility
        }
        
        for cls, subj_names in mapping.items():
            for subj_name in subj_names:
                s = Subject.objects.create(name=subj_name, class_level=cls, board='SSC')
                subjects[f'{subj_name}_{cls}'] = s
                # Add a few dummy concepts for each subject so concept mastery UI works
                Concept.objects.create(subject=s, name=f"Basics of {subj_name}", chapter_number=1, order=1)
                Concept.objects.create(subject=s, name=f"Advanced {subj_name}", chapter_number=2, order=2)
                
        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(subjects)} Subjects with Concepts'))

        # ─── Students ───────────────────────────────
        student_data = [
            ('Aarav Patil', '7th', b1, parents[0]),
            ('Sara Kulkarni', '8th', b1, parents[1]),
            ('Vivaan Joshi', '5th', b2, parents[2]),
            ('Ananya Bhatt', '6th', b2, parents[3]),
            ('Arjun Nair', '9th', b3, parents[4]),
        ]
        students = []
        for name, cls, batch, parent in student_data:
            s = Student.objects.create(name=name, class_level=cls, board='SSC', batch=batch, parent=parent)
            # Assign subjects
            for key, subj in subjects.items():
                if cls in key:
                    s.subjects.add(subj)
            students.append(s)
        self.stdout.write(self.style.SUCCESS('  ✓ 5 Students created and linked'))

        # ─── Attendance (last 20 days) ──────────────
        today = date.today()
        att_count = 0
        for student in students:
            teacher = student.batch.teacher
            for i in range(20):
                d = today - timedelta(days=i)
                if d.weekday() < 6:  # Mon-Sat
                    status = random.choices(['present', 'absent', 'late'], weights=[80, 12, 8])[0]
                    Attendance.objects.create(student=student, date=d, status=status, marked_by=teacher)
                    att_count += 1
        self.stdout.write(self.style.SUCCESS(f'  ✓ {att_count} Attendance records'))

        # ─── Test Scores ────────────────────────────
        score_count = 0
        test_types = ['weekly', 'monthly', 'unit']
        for student in students:
            for subj in student.subjects.all():
                for i in range(4):
                    d = today - timedelta(days=random.randint(1, 60))
                    obtained = random.randint(40, 100)
                    TestScore.objects.create(
                        student=student, subject=subj,
                        test_name=f'{subj.name} {random.choice(["Weekly", "Monthly", "Unit"])} Test {i+1}',
                        date=d, marks_obtained=obtained, total_marks=100,
                        test_type=random.choice(test_types), entered_by=student.batch.teacher
                    )
                    score_count += 1
        self.stdout.write(self.style.SUCCESS(f'  ✓ {score_count} Test scores'))

        # ─── Concept Mastery ────────────────────────
        mastery_count = 0
        statuses = ['mastered', 'needs_work', 'not_started']
        for student in students:
            for subj in student.subjects.all():
                for concept in subj.concepts.all():
                    ConceptMastery.objects.create(
                        student=student, concept=concept,
                        status=random.choices(statuses, weights=[40, 35, 25])[0],
                        updated_by=student.batch.teacher
                    )
                    mastery_count += 1
        self.stdout.write(self.style.SUCCESS(f'  ✓ {mastery_count} Concept mastery records'))

        # ─── Homework ───────────────────────────────
        hw_statuses = ['assigned', 'submitted', 'pending', 'late']
        hw_count = 0
        for batch in [b1, b2, b3]:
            for subj_key, subj in subjects.items():
                if batch.class_level.split('-')[0] in subj_key or batch.class_level in subj_key:
                    for i in range(3):
                        Homework.objects.create(
                            batch=batch, subject=subj,
                            description=f'Complete {subj.name} Chapter {i+1} exercises (Q1-Q10)',
                            due_date=today + timedelta(days=random.randint(-3, 5)),
                            status=random.choice(hw_statuses),
                            assigned_by=batch.teacher
                        )
                        hw_count += 1
        self.stdout.write(self.style.SUCCESS(f'  ✓ {hw_count} Homework assignments'))

        self.stdout.write(self.style.SUCCESS('\n🎉 Seeding complete! You can now login:'))
        self.stdout.write('   Admin:   admin / admin123')
        self.stdout.write('   Teacher: priya_teacher / teacher123')
        self.stdout.write('   Parent:  aarav_parent / parent123')
