# An-Najah National University — Computer Engineering RAG/Planner Data (Final Hackathon Dataset)

Checked: 2026-11-07. **Single source of truth for course names, categories, credits and prerequisites:** https://www.najah.edu/ar/academic/undergraduate-programs/program/computer-engineering/study-plan/

## Data
- `computer_engineering_courses.csv`: 125 catalog-option entries (including remedial course and electives). Arabic course names copied from official page. English names left blank for the 30 additional electives rather than invent translations.
- `prerequisites.csv`: 61 non-empty prerequisite expressions, transcribed from the official course table. `AND` and `OR` have logical meanings. Do not derive requirements from the user's flowchart.
- `degree_requirements.csv`: 162 credits total: 19 university, 126 specialization required, 15 specialization elective, 2 free elective.
- `academic_rules.csv`: separate official source statements from user-provided hackathon rules.
- `academic_faq.csv`: supporting university FAQs, not a source for extra course prerequisites.
- `collection_gaps.csv`: current implementation and data exceptions.
- `source_registry.csv`: links.

## Prototype behavior (requested by project team)
1. Use the currently displayed plan only. Do not ask for academic-year selection.
2. Student marks **successfully completed** courses using a searchable Arabic checklist; do not require entering credit total or numeric grades.
3. User-supplied completion assumption: numeric grade >=60% passes; internships `10636304` / `10636305` pass/fail. As only passed subjects are selected, the input does not ask for every grade.
4. Earned credits = sum of successfully completed courses; **do not** sum every elective option as if all are required. Graduation needs category caps/checks: 19 university, 126 major required, 15 elective, 2 free.
5. Display all unfinished courses satisfying prerequisites in the official table. **Do not rank** them. Student selects a proposed set.
6. Below 12 selected credits: warn to consult dean. Above 18: reject as a prototype limit. No semester-offering or timetable checks.
7. No course equivalencies, individualized approvals, or FAQ conflict reconciliation.

## Critical source cautions
- `10221115` has a duplicated prerequisite `10221102` inside an OR group on official page; review before treating eligibility as definitive.
- `10641373` has two OR groups connected by AND. Preserve parentheses.
- `10636581` and `10636582` **both** explicitly show `10636410` as prerequisite; do not invent Project 1 -> Project 2.
- `10636305` may require department approval per course description. Prototype does not evaluate approval; do not claim registration is guaranteed.
- `11032102` table says 3 credits, description says non-credit. Keep official table value with flag.
- Some prerequisite alternate codes do not appear among the displayed CE curriculum rows. Never silently count those missing codes as passed.
- Grade 60%, internship pass/fail and 12–18 credit hard maximum are **user-selected prototype policies**; do not portray them as independently validated official policy exceptions.

This is a prototype academic planning aid, not an official university registration decision.
