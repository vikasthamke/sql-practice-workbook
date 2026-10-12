# Validation report

Generated 2026-10-12 18:09 from `validation/results.json`.

- Engines: **PostgreSQL 18.6 (Homebrew)** and **MySQL 8.4.11**.
- Questions validated: **190 / 190** (171 practice, 3 capstones, 16 assessment).
- BOTH questions: 183; 175 returned **identical results** on PostgreSQL and MySQL (the remaining 8 produce execution plans or engine-specific catalogue output and are only required to run: 8 EXPLAIN exercises).
- Engine-specific questions: 7; 5 have a validated equivalent on the other engine that returns identical results.
- Alternative solutions executed: 25 (each must equal the main result).
- Assertions evaluated: 85. Independent Python re-computations matching SQL: 15.
- Additional checks: every result's column names match the documented expected columns; result-returning questions must return rows; ordered questions must end with ORDER BY.

## Failures

None.

## Per-question results

| ID | Status | PostgreSQL rows | MySQL rows | Cross-check |
|---|---|---:|---:|---|
| SQL-001 | PASS | 13 | 13 | engines identical |
| SQL-002 | PASS | 6 | 6 | engines identical |
| SQL-003 | PASS | 1 | 1 | engines identical, Python re-computation, 2 assert(s) |
| SQL-004 | PASS | 1 | 1 | engines identical |
| SQL-005 | PASS | 1 | 1 | engines identical, 2 assert(s) |
| SQL-006 | PASS | 14 | 14 | engines identical |
| SQL-007 | PASS | 5 | 5 | engines identical |
| SQL-008 | PASS | 13 | 13 | engines identical |
| SQL-009 | PASS | 26 | 26 | engines identical |
| SQL-010 | PASS | 4 | 4 | engines identical |
| SQL-011 | PASS | 7 | 7 | engines identical |
| SQL-012 | PASS | 10 | 10 | engines identical |
| SQL-013 | PASS | 1 | 1 | engines identical, 2 assert(s) |
| SQL-014 | PASS | 19 | 19 | engines identical |
| SQL-015 | PASS | 7 | 7 | engines identical |
| SQL-016 | PASS | 4 | 4 | engines identical, Python re-computation |
| SQL-017 | PASS | 1 | 1 | engines identical, 2 assert(s) |
| SQL-018 | PASS | 5 | 5 | engines identical |
| SQL-019 | PASS | 6 | 6 | engines identical |
| SQL-020 | PASS | 18 | 18 | engines identical, Python re-computation |
| SQL-021 | PASS | 3 | 3 | engines identical |
| SQL-022 | PASS | 7 | 7 | engines identical |
| SQL-023 | PASS | 19 | 19 | engines identical |
| SQL-024 | PASS | 3 | 3 | engines identical |
| SQL-025 | PASS | 30 | 30 | engines identical, Python re-computation |
| SQL-026 | PASS | 11 | 11 | engines identical |
| SQL-027 | PASS | 5 | 5 | engines identical |
| SQL-028 | PASS | 3 | 3 | engines identical |
| SQL-029 | PASS | 5 | 5 | engines identical |
| SQL-030 | PASS | 39 | 39 | engines identical |
| SQL-031 | PASS | 3 | 3 | engines identical, Python re-computation, 2 assert(s) |
| SQL-032 | PASS | 6 | 6 | engines identical |
| SQL-033 | PASS | 14 | 14 | engines identical |
| SQL-034 | PASS | 25 | 25 | engines identical, 1 assert(s) |
| SQL-035 | PASS | 3 | 3 | engines identical |
| SQL-036 | PASS | 24 | 24 | engines identical |
| SQL-037 | PASS | 10 | 10 | engines identical |
| SQL-038 | PASS | 3 | 3 | engines identical, 2 assert(s) |
| SQL-039 | PASS | 15 | 15 | engines identical, 1 assert(s) |
| SQL-040 | PASS | 1 | 1 | engines identical, 2 assert(s) |
| SQL-041 | PASS | 4 | 4 | engines identical |
| SQL-042 | PASS | 6 | 6 | engines identical |
| SQL-043 | PASS | 16 | 16 | engines identical, 1 assert(s) |
| SQL-044 | PASS | 26 | 26 | engines identical |
| SQL-045 | PASS | 4 | 4 | engines identical |
| SQL-046 | PASS | 6 | 6 | engines identical |
| SQL-047 | PASS | 22 | 22 | engines identical |
| SQL-048 | PASS | 15 | 15 | engines identical |
| SQL-049 | PASS | 16 | 16 | engines identical |
| SQL-050 | PASS | 85 | 85 | engines identical |
| SQL-051 | PASS | 5 | 5 | engines identical, 2 assert(s) |
| SQL-052 | PASS | 11 | 11 | engines identical, 1 assert(s) |
| SQL-053 | PASS | 30 | 30 | engines identical, 1 assert(s) |
| SQL-054 | PASS | 4 | 4 | engines identical, 1 assert(s) |
| SQL-055 | PASS | 23 | 23 | engines identical |
| SQL-056 | PASS | 6 | 6 | engines identical |
| SQL-057 | PASS | 24 | 24 | engines identical |
| SQL-058 | PASS | 17 | 17 | engines identical |
| SQL-059 | PASS | 12 | 12 | engines identical |
| SQL-060 | PASS | 14 | 14 | engines identical |
| SQL-061 | PASS | 10 | 10 | engines identical |
| SQL-062 | PASS | 63 | 63 | engines identical |
| SQL-063 | PASS | 87 | 87 | engines identical |
| SQL-064 | PASS | 10 | 10 | engines identical |
| SQL-065 | PASS | 91 | 91 | engines identical, 2 assert(s) |
| SQL-066 | PASS | 13 | 13 | engines identical |
| SQL-067 | PASS | 22 | 22 | engines identical |
| SQL-068 | PASS | 10 | 10 | engines identical, 2 assert(s) |
| SQL-069 | PASS | 18 | 18 | engines identical |
| SQL-070 | PASS | 10 | 10 | engines identical |
| SQL-071 | PASS | 27 | 27 | engines identical |
| SQL-072 | PASS | 18 | 18 | engines identical |
| SQL-073 | PASS | 10 | 10 | engines identical |
| SQL-074 | PASS | 11 | 11 | engines identical |
| SQL-075 | PASS | 6 | 6 | engines identical |
| SQL-076 | PASS | 20 | 20 | engines identical, 1 assert(s) |
| SQL-077 | PASS | 2 | 2 | engines identical, 1 assert(s) |
| SQL-078 | PASS | 6 | 6 | engines identical, Python re-computation |
| SQL-079 | PASS | 9 | 9 | engines identical, 1 assert(s) |
| SQL-080 | PASS | 6 | 6 | engines identical |
| SQL-081 | PASS | 4 | 4 | engines identical |
| SQL-082 | PASS | 3 | 3 | engines identical, 2 assert(s) |
| SQL-083 | PASS | 3 | 3 | engines identical |
| SQL-084 | PASS | 3 | 3 | engines identical, 1 assert(s) |
| SQL-085 | PASS | 9 | 9 | engines identical, 2 assert(s) |
| SQL-086 | PASS | 5 | 5 | engines identical, 2 assert(s) |
| SQL-087 | PASS | 1 | 1 | engines identical, Python re-computation |
| SQL-088 | PASS | 10 | 10 | engines identical |
| SQL-089 | PASS | 3 | 3 | engines identical, Python re-computation |
| SQL-090 | PASS | 37 | 37 | engines identical |
| SQL-091 | PASS | 64 | 64 | engines identical |
| SQL-092 | PASS | 30 | 30 | engines identical, 2 assert(s) |
| SQL-093 | PASS | 1 | 1 | engines identical |
| SQL-094 | PASS | 1 | 1 | engines identical |
| SQL-095 | PASS | 7 | 7 | engines identical |
| SQL-096 | PASS | 7 | 7 | engines identical, Python re-computation |
| SQL-097 | PASS | 17 | 17 | engines identical, 1 assert(s) |
| SQL-098 | PASS | 1 | 1 | engines identical, Python re-computation, 1 assert(s) |
| SQL-099 | PASS | 242 | 242 | engines identical, 1 assert(s) |
| SQL-100 | PASS | 7 | 7 | engines identical, 1 assert(s) |
| SQL-101 | PASS | 2 | 2 | engines identical, 1 assert(s) |
| SQL-102 | PASS | 3 | 3 | engines identical |
| SQL-103 | PASS | 6 | 6 | engines identical |
| SQL-104 | PASS | 2 | 2 | engines identical, 1 assert(s) |
| SQL-105 | PASS | 2 | 2 | engines identical, 1 assert(s) |
| SQL-106 | PASS | 373 | 373 | engines identical |
| SQL-107 | PASS | 4 | 4 | engines identical, Python re-computation, 1 assert(s) |
| SQL-108 | PASS | 2 | 2 | engines identical, 1 assert(s) |
| SQL-109 | PASS | 6 | 6 | engines identical, 2 assert(s) |
| SQL-110 | PASS | 10 | 10 | engines identical |
| SQL-111 | PASS | 216 | 216 | engines identical |
| SQL-112 | PASS | 8 | 8 | engines identical, 2 assert(s) |
| SQL-113 | PASS | 10 | 10 | engines identical, 1 assert(s) |
| SQL-114 | PASS | 4 | 4 | engines identical, Python re-computation, 1 assert(s) |
| SQL-115 | PASS | 9 | 9 | engines identical, 1 assert(s) |
| SQL-116 | PASS | 14 | 14 | engines identical |
| SQL-117 | PASS | 5 | 5 | engines identical, Python re-computation |
| SQL-118 | PASS | 27 | 27 | engines identical, Python re-computation |
| SQL-119 | PASS | 6 | 6 | engines identical |
| SQL-120 | PASS | 32 | 32 | engines identical, 1 assert(s) |
| SQL-121 | PASS | 12 | 12 | engines identical |
| SQL-122 | PASS | 14 | 14 | engines identical |
| SQL-123 | PASS | 7 | 7 | engines identical |
| SQL-124 | PASS | 5 | 5 | engines identical |
| SQL-125 | PASS | 5 | 5 | engines identical, 1 assert(s) |
| SQL-126 | PASS | 44 | 44 | engines identical |
| SQL-127 | PASS | 6 | 6 | engines identical |
| SQL-128 | PASS | 3 | 3 | engines identical |
| SQL-129 | PASS | 3 | 3 | engines identical, Python re-computation, 1 assert(s) |
| SQL-130 | PASS | 4 | 4 | engines identical |
| SQL-131 | PASS | 5 | 5 | engines identical |
| SQL-132 | PASS | 2 | 2 | engines identical, 1 assert(s) |
| SQL-133 | PASS | 11 | 11 | engines identical, 1 assert(s) |
| SQL-134 | PASS | 44 | 44 | engines identical |
| SQL-135 | PASS | 2 | 2 | engines identical, 1 assert(s) |
| SQL-136 | PASS | 1 | 1 | engines identical, 1 assert(s) |
| SQL-137 | PASS | 3 | 3 | engines identical |
| SQL-138 | PASS | 28 | 28 | engines identical |
| SQL-139 | PASS | 62 | 62 | engines identical, 1 assert(s) |
| SQL-140 | PASS | 10 | 10 | engines identical |
| SQL-141 | PASS | 8 | 8 | engines identical, 2 assert(s) |
| SQL-142 | PASS | 26 | 26 | engines identical |
| SQL-143 | PASS | 3 | 3 | engines identical |
| SQL-144 | PASS | 2 | 2 | engines identical |
| SQL-145 | PASS | 1 | 1 | engines identical |
| SQL-146 | PASS | 5 | 5 | engines identical, 1 assert(s) |
| SQL-147 | PASS | 1 | 1 | engines identical, 1 assert(s) |
| SQL-148 | PASS | 3 | 3 | engines identical, 1 assert(s) |
| SQL-149 | PASS | 3 | 3 | engines identical, 1 assert(s) |
| SQL-150 | PASS | 5 | 5 | engines identical |
| SQL-151 | PASS | 3 | 3 | engines identical |
| SQL-152 | PASS | 1 | 1 | engines identical, 1 assert(s) |
| SQL-153 | PASS | 3 | 3 | engines identical, 1 assert(s) |
| SQL-154 | PASS | 7 | 1 | 1 assert(s) |
| SQL-155 | PASS | 10 | 1 | 1 assert(s) |
| SQL-156 | PASS | 7 | 1 | 1 assert(s) |
| SQL-157 | PASS | 7 | 1 | 1 assert(s) |
| SQL-158 | PASS | 7 | 1 | 1 assert(s) |
| SQL-159 | PASS | 25 | 1 | 1 assert(s) |
| SQL-160 | PASS | 12 | 1 | 1 assert(s) |
| SQL-161 | PASS | 14 | 1 | 1 assert(s) |
| SQL-162 | PASS | 8 | 8 | equivalent identical |
| SQL-163 | PASS | 26 | 26 | engines identical |
| SQL-164 | PASS | 27 | 27 | equivalent identical, 1 assert(s) |
| SQL-165 | PASS | 5 | 5 | engines identical |
| SQL-166 | PASS | 10 |  |  |
| SQL-167 | PASS |  | 10 | 1 assert(s) |
| SQL-168 | PASS | 10 | 10 | equivalent identical |
| SQL-169 | PASS | 1 | 1 | equivalent identical, 1 assert(s) |
| SQL-170 | PASS | 30 | 30 | equivalent identical, 1 assert(s) |
| SQL-171 | PASS | 63 | 63 | engines identical |
| CAP-DS | PASS | 3 | 3 | engines identical, 1 assert(s) |
| CAP-ML | PASS | 4 | 4 | engines identical, 1 assert(s) |
| CAP-AI | PASS | 4 | 4 | engines identical, 1 assert(s) |
| ASM-01 | PASS | 3 | 3 | engines identical |
| ASM-02 | PASS | 3 | 3 | engines identical |
| ASM-03 | PASS | 3 | 3 | engines identical |
| ASM-04 | PASS | 1 | 1 | engines identical |
| ASM-05 | PASS | 3 | 3 | engines identical |
| ASM-06 | PASS | 12 | 12 | engines identical |
| ASM-07 | PASS | 6 | 6 | engines identical |
| ASM-08 | PASS | 1 | 1 | engines identical |
| ASM-09 | PASS | 10 | 10 | engines identical |
| ASM-10 | PASS | 6 | 6 | engines identical |
| ASM-11 | PASS | 1 | 1 | engines identical |
| ASM-12 | PASS | 3 | 3 | engines identical |
| ASM-13 | PASS | 1 | 1 | engines identical |
| ASM-14 | PASS | 8 | 8 | engines identical |
| ASM-15 | PASS | 10 | 10 | engines identical |
| ASM-16 | PASS | 2 | 2 | engines identical |
