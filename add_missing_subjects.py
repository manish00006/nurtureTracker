from core.models import Subject, Concept

classes_to_update = ['1st', '2nd', '3rd', '4th']
new_subjects = ['English', 'ICT']

added = 0
for cls in classes_to_update:
    for subj_name in new_subjects:
        s, created = Subject.objects.get_or_create(
            name=subj_name,
            class_level=cls,
            board='SSC',
            defaults={'is_active': True}
        )
        if created:
            Concept.objects.create(subject=s, name=f"Basics of {subj_name}", chapter_number=1, order=1)
            Concept.objects.create(subject=s, name=f"Advanced {subj_name}", chapter_number=2, order=2)
            added += 1

print(f"Added {added} new subjects.")
