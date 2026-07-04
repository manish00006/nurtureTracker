from core.models import Subject, Concept
import sys

mapping = {
    'Jr.KG': ['English', 'Math'],
    'Sr.KG': ['Hindi', 'English', 'Math', 'EVS'],
    '1st': ['Hindi', 'Marathi', 'Maths', 'EVS'],
    '2nd': ['Hindi', 'Marathi', 'Maths', 'EVS'],
    '3rd': ['Hindi', 'Marathi', 'Maths', 'EVS'],
    '4th': ['Hindi', 'Marathi', 'Maths', 'EVS'],
    '5th': ['English', 'EVS', 'Hindi', 'Marathi', 'ICT', 'Social Science', 'Sanskrit', 'Maths'],
    '6th': ['English', 'EVS', 'Hindi', 'Marathi', 'ICT', 'Social Science', 'Sanskrit', 'Maths'],
    '7th': ['English', 'EVS', 'Hindi', 'Marathi', 'ICT', 'Social Science', 'Sanskrit', 'Maths'],
    '8th': ['English', 'EVS', 'Hindi', 'Marathi', 'ICT', 'Social Science', 'Sanskrit', 'Maths'],
}

added_count = 0
for class_level, subjects in mapping.items():
    for subj_name in subjects:
        s, created = Subject.objects.get_or_create(
            name=subj_name,
            class_level=class_level,
            board='SSC'
        )
        if created:
            s.is_active = True
            s.save()
            Concept.objects.create(subject=s, name=f"Chapter 1", chapter_number=1, order=1)
            added_count += 1

print(f"Added {added_count} new subjects successfully!")
