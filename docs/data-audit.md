# Supplied-data audit

Inspected locally: 7 November 2026. Institution: An-Najah National University.
The PDF has 135 pages and identifies itself as the 2026–2027 student guide.
The catalog contains 125 entries, including elective options, not 125 mandatory
courses. The prerequisite CSV has 61 entries. The course-plan effective year is
not established by the supplied extraction.

Important differences:

- Supplied plan: 162 credits (19 university, 126 major required, 15 major elective,
  2 free elective). PDF page 47 lists Computer Engineering as 163; page 48 also
  lists a different category breakdown. No automatic precedence is justified.
- PDF page 83 states engineering-specific academic-warning conditions. FAQ
  summaries of 1.7 must not override the program-specific exception.
- Course 10221115 has an ambiguous duplicated prerequisite and is excluded from
  the eligible list pending review.
- Course 11032102 has a table/description credit conflict; it requires review.
- Projects 10636581 and 10636582 both list 10636410. The planner does not invent
  a Project I prerequisite for Project II.
- The current offering schedule, equivalencies, section times, and individual
  approvals are absent. Satisfied listed prerequisites do not guarantee enrollment.

Extraction findings:

- PyMuPDF natural extraction preserves Arabic word order better than geometric
  sorting for this PDF. Original excerpts still contain PDF artifacts.
- Repeated university/page headers are removed from search text, not quotations.
- Some lam-alef artifacts are normalized for search only.
- Numeric curriculum tables requiring reliable column alignment are quarantined
  rather than treated as coherent paragraphs. The structured course CSV supplies
  course lookups. Do not claim every PDF table has been parsed.
- Blank, image-heavy, and divider pages are logged for review; no OCR was needed
  to extract the core academic policies tested on pages 76–89.
- User-selected prototype rules, README files, gap notes, and source registries
  are not indexed as university policy.

The generated data/processed/inspection.json contains the current page warnings
and documented degree conflict. Original documents are preserved unchanged.
Public accessibility does not establish redistribution rights; confirm terms
before publishing a copy of the university PDF outside this local prototype.
