# P02 — Grading My Own Data Cleaning With an Answer Key

**1. Hook**

Everyone says "80% of data work is cleaning." Almost nobody can prove their
cleaning actually worked. I could — because I built the mess myself and kept
the answer key.

**2. What I built this week**

The bronze → silver cleaning stage of the ShopSphere warehouse. In M1 I had
deliberately injected 9 classes of realistic defects (duplicate orders,
malformed emails, impossible timestamps, orphaned rows, and more) and written
a ground-truth manifest of every one. This week the cleaning pipeline had to
find them — and got graded against that manifest.

**3. Why it matters**

Ungraded cleaning is just data mutation with good intentions. If you can't
say what you removed and why, your "clean" layer is as untrustworthy as the
raw one. The medallion pattern makes this auditable: bronze stays immutable,
silver is derived, and the diff between them is the cleaning — inspectable
forever.

**4. How**

- Bronze is append-only raw; cleaning writes a new silver layer, never edits
  in place
- Every cleaning rule is a named, tested transformation with a counter
- A quality report compares what was caught against the injected-defect
  manifest — every defect class must be caught or explicitly waived
- The whole thing runs in one command and fails loudly on any miss

**5. What the data said**

Quality gate: **9/9 defect classes caught (PERFECT)**. 2,362,710 bronze rows
became 2,362,203 silver rows across 9 tables. Example: 19,687 raw orders →
19,397 clean ones, with exactly 290 duplicates dropped — the same 290 the
injector planted.

**6. Suggested visual**

A before/after table of row counts per table with the defect classes caught,
styled as a report card with 9 green checks.

**7. What's next**

Clean data earns its first look: exploratory analysis, and the six numbers
that describe ShopSphere's health. As always: the data is synthetic,
calibrated to real 2026 industry benchmarks.

#DataAnalytics #Ecommerce #SQL #Python #DataQuality #DataEngineering #DataCleaning
