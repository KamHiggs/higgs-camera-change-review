"""Deterministic human projection, not additional engineering logic."""
import json


def human_summary(summary):
    sections = [
        '# Higgs camera assessment — recorded decision',
        'Assessment contract: higgs-assessment-v0.1.2',
        '## Status\n\n' + summary['engineering_status'],
        'Camera: ' + summary['camera_id'] + '\n\n' + summary['notice'],
        'Real source captures; synthetic installation, requirements, timing assumptions and cost points. No hardware or deployment approval.',
    ]
    for title, key in [('Reason and counts','reasons'),('Counts','counts'),('Established blockers','blockers'),
                       ('Unknown constraints','unknowns'),('Decision-changing evidence','questions'),('Scope','scope')]:
        sections.append('## ' + title + '\n\n```json\n' + json.dumps(summary.get(key),sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False) + '\n```')
    sections.append('Full decision verification checks this deterministic view under the v0.1.2 contract. Engine reproduction alone does not. Recorded file integrity is not authorship, manufacturer truth, physical identity or engineering approval. Creation IDs/timestamps and display metadata are not authenticated. Any permitted operator note is manifest-covered but not semantically verified.')
    return '\n\n'.join(sections) + '\n'
