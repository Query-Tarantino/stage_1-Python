# Stage 1 benchmark analysis (Python)

This document interprets the full Python benchmark run of October 3, 2026 (`benchmarks/results/python-*.csv`), and
compares it with the Java run of October 2, 2026 (`java-*.csv`, analysed in the Java repository's `ANALYSIS.md`), made
on the same machine. `scripts/compare_results.py` joins both in `benchmarks/report/comparison.md`. It has two parts:

1. **Python alone:** the winning structure of each component, chosen only with the Python measurements.
2. **Python against Java:** where each implementation is faster and why, and the final verdict.

The rule for choosing is the one of the Java analysis: **the structure with the best complexity in the operations that
grow with the number of books; on a tie, the one with the best measured constants.**

`benchmarks/` is not in git, so this document keeps the numbers it relies on. A few numbers come from short measurements
made outside the runner, with the same code and data, to explain a result; they are marked as **probes**.

## 1. Summary

### 1.1 The winners

| Component | Python's choice | Java's choice | Decision | Why |
|---|---|---|---|---|
| Datalake | `batch` | `batch` | **`batch`** | Stores and looks up in O(1) with O(N/1 000) directories; `time` looks up in O(N) |
| Inverted index | `mongo` | `mongo` | **`mongo`** | Never worse in complexity; memory, opening and freshness in O(1). In Python it also updates book by book 4.7 times faster than json |
| Metadata | `sqlite` | `sqlite` | **`sqlite`** | Same complexity as `mongo`, 14 times faster by id (5.7 against 78 µs) |

Both languages choose the same structures, because the choice depends on complexity, which is the same in both, and the
constants that break the ties go the same way.

### 1.2 Python against Java

With 1 000 books, of the 51 time metrics that both languages measure, **Java is faster in 38, Python in 6, and 7 are
tied** (their 95% intervals overlap). Java is faster wherever the language itself does the work item by item:
tokenizing, building result objects, serializing JSON, handling paths. The two tie where a storage engine does the work:
writing the datalake, inserting metadata, MongoDB updates. Python wins only where its code does less work than Java's:
the `time` lookup reads directory names without file attributes, and the `json` index intersects hash sets.

### 1.3 Findings that `comparison.md` does not show

1. **Python's queries are slow in building the results, not in the index.** In a frequent `json` query with 1 000 books,
   95% of the time (229 of 242 µs) goes to creating one `BookMetadata` per result, at 258 ns each. The index part (parsing,
   copying the list, intersecting and sorting) takes ~6 µs, less than Java's whole query (39 µs).
2. **Rewriting the `json` index costs 10 times more in Python:** 190 ns per posting against 19 ns. The postings live in
   hash sets, so every flush sorts all of them again. `json` is already the worst structure but one to update book by book
   with 1 000 books (1 241 ms/book against 265 for `mongo`), and only ties with `mongo` in batches.
3. **Python's `json` index takes 86 B per posting once loaded**, because every posting gets its own `int` object (28 B):
   611 MB with 1 000 books, ~55 GB with 100 000.
4. **Python's MongoDB queries with 1 000 books are inflated by a measurement effect.** MongoDB stays idle while Python
   processes the long lists of the frequent queries, and the next round trip costs ~190–280 µs instead of ~70 µs. On its
   own a rare query takes ~76 µs with both 100 and 1 000 books, but 186 µs inside the mixed workload with 1 000.
5. **Where the disk does the work, the two languages are close.** A `folders` term file costs 190–250 µs in Python and
   150–165 µs in Java, both write the datalake at the same speed with 1 000 books, and every size on disk is identical
   byte for byte.

## 2. Data, method and notation

### 2.1 The run

- **Machine:** the one of the Java run, a fanless MacBook Air M4 with 24 GB of RAM and an SSD, macOS 26.6.2 (APFS).
- **Software:** CPython 3.13.9 without flags, Unicode 15.1.0, SQLite 3.51.0 (Python's `sqlite3`), pymongo 4.18.2, and
  MongoDB 7.0.43 running natively on the same machine with a 1 GB cache.
- **Sizes:** 100, 300 and 1 000 books from `benchmarks/cache/`, in the order of `workload/book_ids.txt`. Updates add the
  next 100 books (positions 1 001–1 100).
- **Runner:** Python's own, as SPEC §14 requires (README, "How the Python runner works"). It runs two passes of one process
  per benchmark, structure and size, the second in reverse order, with JMH's warm-up and measured iterations. Each value
  is the mean ± the half-width of its 95% confidence interval. Two structures tie when their intervals overlap.
- **Duration:** 2 h 12 min (crawler 6.5 min, indexer 1 h 53 min, query 12 min). Java's run took 2 h 10 min.
- **Correctness:**
  - before measuring, every benchmark checks its results: the three indexes hold the same vocabulary, and every query
    returns the expected books;
  - every exact measure is identical to Java's: the datalake (454 014 783 bytes with 1 000 books), the `json` and
    `folders` indexes (31 041 791 and 25 390 195 bytes), the number of terms and the number of files and directories.

### 2.2 Notation

The same as in the Java analysis (§2.2 there):

| Symbol | Meaning | With 1 000 books |
|---|---|---:|
| N | books indexed | 1 000 |
| V(N) | distinct terms (vocabulary) | 434 996 |
| P(N) | postings: (term, book) pairs | 6 425 580 |
| df(t) | books that contain term t | ≤ N; 888–957 for the frequent terms |
| R | books in the result of a query | up to 957 (`time`) |
| K | books per indexing batch | 100 |
| T_batch | distinct terms in a batch | 78 643 |
| c_fs | cost of one file system operation | — |

A probe recomputed V and P with Python's tokenizer, and they match the Java analysis exactly: 106 410 terms and 625 651
postings with 100 books, 224 350 and 1 882 575 with 300, 434 996 and 6 425 580 with 1 000. The batch of 100 new books
touches 78 643 terms. Of these, 61 788 were already indexed and hold 5 530 810 of the 6 425 580 postings (86.1%). So, as in
Java, updating touches most of the index. The growth laws are those of the Java analysis (§2.3 there): V(N) ≈ 7 878·N^0.575
and P(N) ≈ 6 200·N.

### 2.3 What differs between the two implementations

Both follow the same SPEC, and their structures write the same bytes. The code that does the work is different:

| | Java | Python | Effect |
|---|---|---|---|
| Tokenizer | scans code points with `Character.isLetter` | regular expression `[^\W\d_]+` and `str.isalpha` | Python: 16.9 ms per book (probe). Java: 5.8 ms (its `BENCHMARKS.md`) |
| Postings in memory | `TreeMap<String, TreeSet<Integer>>`, always sorted | `dict[str, set[int]]` (hash), sorted only when written | Python adds in O(1) but sorts every list at every flush |
| Query (`SearchCommand`) | copies each list into a `TreeSet`, `retainAll` | copies each list into a `set`, intersects (CPython walks the smaller set) and sorts once | Python: O(Σ df + R·log R) instead of O(Σ df·log df) |
| Result objects | a `record` per result, too cheap to show in Java's query times | a frozen dataclass per result, 258 ns (probe) | Dominates Python's queries with many results |
| Paths | `java.nio.file` | `pathlib` | ~3.7 µs of interpreter work per lookup in Python (§4.2) |
| Retained memory | heap in use after `System.gc()` | `tracemalloc` after `gc.collect()` | Not the same measure; both leave out native memory |
| Allocated memory | `memory_allocated` | not measurable | Python has no rows for it |
| MongoDB driver | `mongodb-driver-sync` | `pymongo` | Python adds ~22–30 µs per round trip (§4.3, §4.4) |

### 2.4 How the constants and estimates are made

As in the Java analysis: each operation is modelled by its complexity, the constants are fitted with 100 and 1 000 books,
and the model is validated by predicting 300 books. In Python the errors range from −3% to +9%. Applied to the Java CSVs,
the same method gives back the Java analysis' own constants (json: 4.3 µs per term and 2.1 µs per posting). The 100 000
and 1 000 000 columns are orders of magnitude, not predictions, and use the V(N) and P(N) of the Java analysis.

The `folders` builds are too noisy (±43% with 100 books) to split their cost between terms and postings. Its cost per
term file is therefore taken as the difference with `json` divided by V, at each size.

## 3. Part 1: choosing with Python's measurements

### 3.1 Datalake

**Complexity.** As in Java (§4.2 there): `book` and `batch` compute the path from the id, so they store and look up in
O(1); `time` does not know the hour a book was stored in, and looks it up in O(N). Python's `time` lookup walks the tree
with `os.scandir`, compares names and stops at the first match.

**Measurements.**

| | N = 100 | N = 300 | N = 1 000 | With 10 times more books |
|---|---:|---:|---:|---|
| Look up, `time` | 95.5 µs | 181 µs | 453 µs | ×4.7: O(N), plus a fixed 56 µs |
| Look up, `book` | 4.76 µs | 4.98 µs | 4.89 µs | ×1.0: O(1) |
| Look up, `batch` | 4.97 µs | 5.12 µs | 5.14 µs | ×1.0: O(1) |
| Store, `time` | 499 books/s | 528 books/s | 495 books/s | Tied with `batch` at every size |
| Store, `batch` | 552 books/s | 594 books/s | 597 books/s | Does not drop |
| Detect new, `time` | 0.41 ms | 0.41 ms | 0.42 ms | Constant |
| Detect new, `book` | 0.90 ms | 1.63 ms | 4.86 ms | Grows with N |
| Detect new, `batch` | 1.02 ms | 1.97 ms | 5.83 ms | Grows with N |

- **Recovery:** all three recover from a crash (`recovery_ok` = 1, no leftover files, with 100 books).
- **Disk:** the three take 454 MB with 1 000 books (459 MB allocated).
- **Storing with `time`** costs 0.34 s more than with `batch` with 1 000 books (2.02 against 1.67 s), what its lookups
  cost. It is still within the noise of the throughput, but it grows with N²: every book stored searches the books
  stored before it.

**Constants.**

| | Python | Validation with N = 300 |
|---|---:|---|
| Look up, `time` | 56 µs + 0.40 µs per book stored | −3% |
| Detect new, `book` | 0.46 ms + 4.4 µs per book | +9% |
| Detect new, `batch` | 0.49 ms + 5.3 µs per book | +6% |

**Estimates.**

| | 1 000 (measured) | 10 000 | 100 000 | 1 000 000 |
|---|---:|---:|---:|---:|
| Look up a book, `time` | 0.45 ms | 4.0 ms | 40 ms | 0.40 s |
| Look up a book, `book` and `batch` | 5 µs | 5 µs | 5 µs | 5 µs |
| Detect new, `book` / `batch` | 4.9 / 5.8 ms | 44 / 54 ms | 0.44 / 0.53 s | 4.4 / 5.3 s |
| Directories, `book` / `batch` | 1 000 / 2 | 10 000 / ~10 | 100 000 / ~100 | 1 000 000 / ~1 000 |

**Choice: `batch`.** `book` and `batch` have the same complexity in every operation that grows with N except the number
of directories: O(N/1 000) against O(N), 75 against 75 000 for all of Gutenberg. `book` looks up 5% faster (4.89
against 5.14 µs), but constants only decide a tie. `time` looks up in O(N), and its constant detection is not needed, for
the reasons of the Java analysis (§4.5 there): the control layer queues each book as soon as it is downloaded, and a
manifest would detect new books in O(new) with any structure.

### 3.2 Inverted index

**How Python stores each structure.**

- **json:** the whole index in memory as a `dict` of `set`s. Every flush sorts the terms and every list, and writes the
  whole file with `json.dumps`. The reader loads the file with `json.load` and turns each list into a `set`.
- **folders:** one file per term with one id per line, as in Java; a flush rewrites only the files that gain an id.
- **mongo:** one `{term, postings}` document per term, updated with one `$addToSet` upsert per term in an unordered bulk
  write, as in Java.

**Complexity.** The same as in Java (§5.2 there), except the query, which loses the log factor:

| Operation | json | folders | mongo |
|---|---|---|---|
| Build with N books | O(P·log N + V·log V) | O(P·log N + V·c_fs) | O(P·log N + V·log V) |
| Update a batch of K books | O(P·log N + V): rewrites and sorts everything | O(T_batch·c_fs + Σ_touched df) | at least O(T_batch·log V + Σ_touched df) |
| Index N books in batches | O(N²/K) | O(N²/K) | at least O(N²/K) |
| Open or reload the index | O(P + V) | O(1) | O(1) |
| Memory in the process | O(P + V) | O(1) | O(1) |
| Query with q terms | O(Σ df + R·log R) | O(Σ (c_fs + df) + R·log R) | O(Σ (log V + df) + R·log R) |
| See new books | Reload: O(P + V) | O(1) | O(1) |

Every query also builds R result objects, which is O(R) and, in Python, its largest cost.

**Measurements with 1 000 books.**

| | json | folders | mongo |
|---|---:|---:|---:|
| Full build | 24.5 ± 3.6 s | 134 ± 17 s | 36.7 ± 0.3 s |
| Update book by book | 1 241 ± 250 ms/book | 2 100 ± 387 ms/book | 265 ± 17 ms/book |
| Update in batches of 100 | 38.7 ± 20.0 ms/book | 287 ± 39 ms/book | 66.4 ± 21.2 ms/book |
| Open the index | 1 148 ± 167 ms | 0.39 ms | 0.60 ms |
| Memory in the process, building (`build_memory`) | 474 MB | 474 MB | 474 MB |
| Memory in the process, open (`index_memory`) | 611 MB | ~0 | ~0 |
| Disk (data) | 31.0 MB | 25.4 MB | 58.5 MB |
| Disk allocated | 31.0 MB | 1 782 MB | 58.5 MB |
| Mean query | 91.0 ± 3.3 µs | 205 ± 7 µs | 431 ± 16 µs |
| p99 query | 333 ± 13 µs | 674 ± 25 µs | 1 146 ± 44 µs |

- `build_memory` is the same in all three because it measures the same in-memory postings before the flush.
- The "~0" memory of `folders` and `mongo` (2–3.5 KB) means the index lives outside the process: in the file system cache
  and in MongoDB's cache.
- Indexing in batches of 100 makes each book 32 times cheaper in `json`, 7 times in `folders` and 4 times in `mongo`.

The query categories show where the time goes:

| Query (µs) | df of its terms | Books returned | json | folders | mongo |
|---|---|---:|---:|---:|---:|
| `rare` | 1–3 | 1–3 | 2.70 | 26.8 | 186 |
| `empty` (2 rare) | 1–3 each | 0 | 2.52 | 49.3 | 366 |
| `frequent` | 888–957 | 888–957 | 301 | 400 | 456 |
| `mixed` (frequent + rare) | 888–957 and 1–3 | 1–3 | 6.36 | 137 | 392 |
| `long` (4 common) | 414–944 | 296–659 | 192 | 541 | 959 |
| `nonascii` | 23–71 | 23–71 | 18.1 | 46.7 | 203 |

In `json`, the cost follows the size of the **result**, not of the lists. `mixed` reads a list of 888–957 ids like
`frequent`, yet takes 6.4 µs against 301 µs, because it returns 1–3 books instead of ~900. A probe of single queries
shows why:

| Query (`json`, 1 000 books) | df | R | Total | Parse terms | Copy lists | Intersect and sort | Build results |
|---|---|---:|---:|---:|---:|---:|---:|
| `love` | 888 | 888 | 242 µs | 0.6 µs | 2.3 µs | 2.9 µs | 229 µs |
| `love pyromaniac` | 888, 2 | 2 | 4.4 µs | 0.8 µs | 2.4 µs | 0.2 µs | 0.6 µs |
| `ship captain sea voyage` | 615, 566, 804, 419 | 314 | 117 µs | 1.2 µs | 9.5 µs | 20.2 µs | 80.5 µs |

Each result is a frozen dataclass that costs 258 ns to create, and even with constant metadata it dominates every query
with more than a few dozen results.

**Constants.**

| Constant | json | folders | mongo | Validation with N = 300 |
|---|---:|---:|---:|---|
| Tokenizing (shared) | 16.9 ms per book, 2.6 µs per posting | same | same | (probe) |
| Build: per term | 4.2 µs | 190–250 µs more than json, per term file | 28.3 µs | json +4%, mongo +1% |
| Build: per posting | 3.5 µs (2.6 of them tokenizing) | — | 3.8 µs | |
| Rewrite the whole index (flush) | 190 ns per posting: 1.1–1.3 s with 1 000 books | — | — | batches: −17% to +11%, inside their intervals |
| Open | ~180 ns per posting: ~30% parsing, ~70% building sets (probe) | O(1) | O(1) | |
| Memory, building | 226 B per term + 58 B per posting | 0 | 0 | −0.2% |
| Memory, loaded | + 28 B per posting (one `int` per posting) | 0 | 0 | exact with 1 000 books |
| Query: each result object | 258 ns | same | same | (probe) |
| Query: one MongoDB round trip | — | — | 69–72 µs back to back | (probe) |
| Update in batches: per book | 20 ms + the flush | 247–302 ms, no trend | 53–66 ms, no trend | |

What the constants say:

- **Tokenizing is 81% of a `json` build** (16.9 of ~20.8 s in a probe), and the same 16.9 s are part of every structure's
  build.
- **A `folders` term file costs about 190–250 µs more than a `json` term**, the cost of creating, writing and renaming a
  file, as in Java.
- **A `json` flush is mostly sorting.** Measured apart, turning the 434 996 sets into sorted lists takes ~1.1 s with
  1 000 books, and `json.dumps` 0.2 s; the whole flush takes 1.1–1.3 s.
- **The `json` memory is explained to the byte.** With 1 000 books, the sets take 437 MB, the dictionary 15 MB and the
  term strings 22 MB: 474 MB, which is `build_memory`. A loaded index also creates one `int` object for each of 4 915 951
  postings whose id is above 256 (CPython shares the integers from −5 to 256): 4 915 951 × 28 B = 138 MB more, 611 MB,
  which is `index_memory`. With 100 books every id is at most 104, and both measures are equal (60.6 MB).
- **The per-posting cost of `mongo` and `folders` updates cannot be measured,** as in Java: with ≤ 1 000 books it stays
  within the noise.

**Estimates.**

| | 1 000 (measured) | 10 000 | 100 000 | 1 000 000 |
|---|---:|---:|---:|---:|
| **json** | | | | |
| Memory, query service (loaded) | 0.61 GB | 5.7 GB | 55 GB | 540 GB |
| Memory, indexer (building) | 0.47 GB | 4.0 GB | 37 GB | 367 GB |
| Open or reload | 1.1 s | 11 s | 1.9 min | 19 min |
| Update in batches | 39 ms/book | 138 ms/book | 1.2 s/book | 12 s/book |
| Index N books in batches | 27 s | 13 min | 17 h | 68 days |
| Frequent query (constant metadata) | 0.30 ms | 2.5 ms | 25 ms | 0.25 s |
| **folders** | | | | |
| Files | 0.43 M | 1.5–1.6 M | 5.1–5.9 M | 18–22 M |
| Disk allocated | 1.8 GB | 7 GB | 28 GB | 135 GB |
| Frequent query (constant metadata) | 0.40 ms | ~4 ms | ~40 ms | ~0.4 s |
| **mongo** | | | | |
| Memory in the process | 0 | 0 | 0 | 0 |
| Open | 0.6 ms | 0.6 ms | 0.6 ms | 0.6 ms |
| Frequent query (constant metadata) | 0.46 ms | ~3 ms | ~27 ms | ~0.27 s |

- The `folders` files and disk come from the data, so they are those of the Java analysis.
- `mongo`'s updates and its 16 MB document limit (~1.4 million books) depend on MongoDB, not on the language: their
  growth is the one estimated in the Java analysis. Python's batches cost 53–66 ms per book, against Java's 32–45. The
  difference is mostly tokenizing (16.9 against 5.8 ms per book) and building the updates.
- The frequent queries add, per result, 258 ns for its object and the cost of reading its id: 2.6 ns in `json`,
  ~170 ns parsing a line in `folders` and ~22 ns decoding BSON in `mongo`.

What the estimates show:

1. **Memory is `json`'s limit.** Python sets no heap limit, so the process takes RAM until the system swaps. With 86 B per
   posting, the query service alone would fill the 24 GB machine at ~43 000 books. With the indexer's copy (58 B per
   posting), the two would fill it at ~25 000 books.
2. **`json` rewrites 10 times slower than Java's.** Reaching 100 000 books in batches would take ~17 h (Java: ~2 h), if it
   had the memory.
3. **Queries end up even, and dominated by the results.** With 100 000 books, a frequent query takes ~25 ms (`json`),
   ~27 ms (`mongo`) and ~40 ms (`folders`): about 24 ms of each is creating ~92 000 result objects.
4. **`folders` does not scale in number of files**, exactly as in Java.

**Choice: `mongo`.** By complexity, as in Java (§5.8 there):

| Operation | json | folders | mongo |
|---|:---:|:---:|:---:|
| Build | = | = | = |
| Update in batches | = | = | = |
| Query | = | = | = |
| Open or reload | worse, O(P + V) | = | = |
| Memory in the process | worse, O(P + V) | = | = |
| See new books | worse, O(P + V) | = | = |
| Number of files | = | worse, O(V) | = |

- `mongo` is never worse than the other two.
- In Python, the measurements back this more than in Java:
  - updating book by book, `mongo` is the fastest of the three (265 against 1 241 ms/book for `json`);
  - in batches it ties with `json` (66 ± 21 against 39 ± 20 ms/book);
  - `json` needs 86 B of memory per posting.
- `json` wins the full build and the queries with 1 000 books, but by constants, in operations of the same complexity.

### 3.3 Metadata

**Complexity.** The same as in Java (§6.2 there): O(log N) by id in both, O(N) by author ("contains" cannot use an index),
and one transaction (`sqlite`) or one round trip (`mongo`) per book stored.

**Measurements and constants.**

| | sqlite | mongo |
|---|---:|---:|
| Book by id, with 100 / 300 / 1 000 books | 5.55 / 5.54 / 5.68 µs | 78.6 / 77.4 / 78.1 µs |
| Books by an author: fixed part + each book scanned | 9.4 µs + 54 ns (300: +4%) | 78 µs + 0.57 µs (fitted on 100 and 300) |
| Store 1 000 books | 175 ± 10 ms | 99 ± 7 ms |

- **By id:** `sqlite` runs in the process; `mongo` pays a round trip.
- **By author, `mongo` with 1 000 books is not reliable:** 2 953 ± 981 µs in the run, but 659–714 µs in three probes, and
  the model predicts 647 µs. Some seconds of the run were much slower, which the ±33% interval shows (§6).
- **Storing is not a fair comparison,** for the reasons of the Java analysis (§6.3 there): `sqlite` syncs every book to
  disk; MongoDB acknowledges before writing its journal.

**Estimates.**

| | 1 000 (measured) | 10 000 | 100 000 | 1 000 000 |
|---|---:|---:|---:|---:|
| Book by id, `sqlite` / `mongo` | 5.7 / 78 µs | same | same | same |
| Books by an author, `sqlite` | 64 µs | 0.55 ms | 5.5 ms | 55 ms |
| Books by an author, `mongo` | ~0.65 ms | 5.8 ms | 57 ms | 0.57 s |
| Store N books, `sqlite` (autocommit) | 0.18 s | 1.8 s | 18 s | 2.9 min |
| Store N books, `mongo` | 0.10 s | 1.0 s | 10 s | 1.7 min |

**Choice: `sqlite`.** Same complexity as `mongo` in every operation, 14 times faster by id and ~10 times by author, and
no server. Its limit, one writer at a time, and the move to PostgreSQL for concurrent writers are discussed in the Java
analysis (§6.5 there) and apply unchanged.

### 3.4 Python's choice

| Component | Choice | Reason |
|---|---|---|
| Datalake | `batch` | O(1) store and lookup with O(N/1 000) directories |
| Inverted index | `mongo` | Never worse in complexity; fastest to update book by book, tied in batches, O(1) memory and opening |
| Metadata | `sqlite` | Same complexity as `mongo`, 14 times faster by id |

## 4. Part 2: Python against Java

### 4.1 The score

Of the time metrics both languages measure (sizes, memory and `memory_allocated` aside), with the winner decided by the
95% intervals:

| | N = 100 | N = 300 | N = 1 000 |
|---|---:|---:|---:|
| Java faster | 35 | 35 | 38 |
| Python faster | 6 | 7 | 6 |
| Tied | 10 | 9 | 7 |

Python is faster, with 1 000 books, in the `time` lookup and the `time` write, the `folders` update book by book, the
opening of `folders` and `mongo`, and the `mixed` queries of `json`.

### 4.2 Datalake

| N = 1 000 | Python | Java | Python / Java | Faster |
|---|---:|---:|---:|---|
| Look up, `book` | 4.89 µs | 0.83 µs | 5.9× | Java |
| Look up, `batch` | 5.14 µs | 0.59 µs | 8.7× | Java |
| Look up, `time` | 453 µs | 2 103 µs | 0.22× | Python |
| Store, `batch` | 597 books/s | 555 books/s | — | tie |
| Store, `time` | 495 books/s | 280 books/s | — | Python |
| Detect new, `time` | 0.42 ms | 0.17 ms | 2.5× | Java |
| Detect new, `batch` | 5.83 ms | 2.76 ms | 2.1× | Java |

- **O(1) lookups are interpreter-bound in Python.** A probe splits Python's 5.0 µs into 1.3 µs building the two `pathlib`
  paths and 3.6 µs checking that the body exists, of which the `stat` system call itself is 1.3 µs. Java does the whole
  lookup in 0.6–0.8 µs.
- **The `time` lookup is 4.6 times faster in Python** because it does less work per entry, not because Python is faster:
  - Java's `Files.find` reads the attributes of every entry it visits: 2.1 µs per book stored;
  - Python's `os.scandir` compares names, and tells directories apart without a `stat`: 0.40 µs per book.

  Both are O(N) and stop at the first match. As a consequence, Python stores with `time` almost as fast as with `batch`,
  and Java does not.
- **Detecting new books** takes 4.4–5.3 µs per book in Python against 2.0–2.5 µs in Java: a `stat` per body, through
  `pathlib` and a Python loop.
- **Writing is I/O-bound, and ties with 1 000 books.** With 100 books Python is faster (552 against 369 books/s for
  `batch`), but Java's throughput rises with N (369, 498, 555) while Python's barely moves (552, 594, 597). Each Java
  sample of 100 books lasts ~0.3 s after a single warm-up run, probably not enough for the JIT to compile the code. This
  has not been checked.

### 4.3 Inverted index

| N = 1 000 | Python | Java | Python / Java | Faster |
|---|---:|---:|---:|---|
| Full build, `json` | 24.5 s | 15.6 s | 1.57× | Java |
| Full build, `mongo` | 36.7 s | 22.5 s | 1.63× | Java |
| Full build, `folders` | 134 s | 86.8 s | 1.55× | Java |
| Update book by book, `json` | 1 241 ms/book | 133 ms/book | 9.4× | Java |
| Update book by book, `mongo` | 265 ms/book | 379 ms/book | 0.70× | tie |
| Update book by book, `folders` | 2 100 ms/book | 3 607 ms/book | 0.58× | Python |
| Update in batches, `json` | 38.7 ms/book | 15.6 ms/book | 2.5× | Java |
| Update in batches, `mongo` | 66.4 ms/book | 44.9 ms/book | 1.5× | tie |
| Update in batches, `folders` | 287 ms/book | 415 ms/book | 0.69× | tie |
| Open, `json` | 1 148 ms | 507 ms | 2.3× | Java |
| Open, `folders` | 0.39 ms | 0.70 ms | 0.56× | Python |
| Open, `mongo` | 0.60 ms | 1.38 ms | 0.44× | Python |
| Mean query, `json` / `folders` / `mongo` | 91 / 205 / 431 µs | 41 / 83 / 157 µs | 2.2–2.7× | Java |
| `mixed` query, `json` | 6.4 µs | 39.0 µs | 0.16× | Python |
| Memory building, `json` | 474 MB | 418 MB | 1.13× | Java |
| Memory loaded, `json` | 611 MB | 445 MB | 1.37× | Java |

**Builds: Java is ~1.6 times faster, mostly from tokenizing.**

- **Tokenizing:** Python takes 16.9 ms per book and Java's scanner 5.8 ms. With 1 000 books that is 11 s of difference,
  more than the 8.9 s between the two `json` builds.
- **`folders` term files:** a file costs 190–250 µs more than a `json` term in Python, and 150–165 µs in Java. The file
  system does most of the work, and Python adds its own path and string handling.
- **`mongo` terms:** 28 µs in Python against 15 µs in Java, because pymongo builds one `UpdateOne` per term and encodes it.

**Updates: Python loses where it rewrites in Python, and ties where MongoDB or the disk work.**

- **`json`:** each flush rewrites the whole index at 190 ns per posting, against 19 ns in Java. Java's `TreeSet`s are
  already sorted, and Jackson streams them. Python's sets have to be sorted again at every flush. Book by book that is
  9.4 times slower, and in batches, where tokenizing weighs more, 2.5 times.
- **`mongo`:** the server's `$addToSet` dominates, so the two tie in both kinds of update.
- **`folders`:** Python's update book by book comes out faster, but `folders` is the least reliable measurement in both
  runs. Java's passes differed by factors of 0.3 to 2.4, and Python's by up to 1.8 (§6). It should be read as a tie: both
  pay the file system for every term touched.

**Opening: `json` loses, `folders` and `mongo` win.**

- **`json`:** Python's 1.15 s go ~30% to parsing the file and ~70% to turning its lists into sets (probe). Java takes
  0.5 s.
- **`folders` and `mongo`:** opening means a new reader answering the first query, `love`.
  - Python does it at its usual speed: 0.39 ms with `folders`, the same as a warm frequent query (0.40 ms).
  - Java takes 0.70 ms with `folders` and 1.38 ms with `mongo`: 10 and 12 times its own warm frequent queries (70 and
    116 µs). A single-shot benchmark with one warm-up run measures Java's code before the JIT has compiled it.

**Queries: Python is 2.2–2.7 times slower on average, for three reasons.**

1. **Results:** 258 ns per result object (§3.2), a cost that does not show in Java's query times. `frequent`, with
   888–957 results, is 7.7 times slower in `json`.
2. **Fixed cost per query:** a `rare` query takes 2.7 µs in Python and 0.37 µs in Java: the interpreter's work to parse
   the terms, create the sets and call the reader.
3. **MongoDB round trips:** a lookup costs 69–72 µs from Python and 47 µs from Java, back to back. With 1 000 books,
   Python's long client-side work between round trips leaves MongoDB idle, and the next one costs more. A probe of rare
   lookups on the same index:

   | Between two rare lookups | Mean rare lookup |
   |---|---:|
   | nothing | 69–71 µs |
   | another lookup, of `love` (888 ids) | 71–72 µs |
   | 300 µs of computation in Python | 186–188 µs |
   | a 300 µs sleep | 274–285 µs |

   It is not Python's garbage collector: it ran 45 times and took 6–13 ms in 2 s of queries, under 1%. With 100 and 300
   books the lists are shorter, the pauses too, and `rare` stays at 81 µs; with 1 000 it rises to 186 µs.

   This is a cost of the single-client benchmark more than of the structure: a MongoDB server that is always busy would
   not pay it. It inflates Python's `mongo` query rows with 1 000 books, and not Java's.

But where the result is small, Python's algorithm wins: a `mixed` query takes 6.4 µs against Java's 39 µs. Python copies
the frequent list (888–957 ids) into a hash set in 2.4 µs and intersects by walking the 1–3 ids of the rare term. Java
copies it into a `TreeSet` in O(df·log df).

**Memory: Python takes 13% more while building and 37% more once loaded.** The two are not the same measure (heap after
a GC against `tracemalloc`), but they are close in size:

- **while building,** Python's sets take 58 B per posting and Java's 64 B. Python shares one `int` per book among all its
  postings, while Java boxes an `Integer` for each one;
- **once loaded,** Java still has an `Integer` per posting, so its two measures are close (418 and 445 MB). Python now
  creates an `int` of 28 B for each posting, and its loaded index is 137 MB larger (474 and 611 MB).

### 4.4 Metadata

| N = 1 000 | Python | Java | Python / Java | Faster |
|---|---:|---:|---:|---|
| Book by id, `sqlite` | 5.68 µs | 4.58 µs | 1.24× | Java |
| Book by id, `mongo` | 78.1 µs | 47.9 µs | 1.63× | Java |
| Books by an author, `sqlite` | 63.8 µs | 59.9 µs | 1.07× | Java |
| Books by an author, `mongo` | 2 953 µs (659–714 µs in probes) | 624 µs | 4.7× (~1.1× in probes) | Java |
| Store 1 000 books, `sqlite` | 175 ms | 461 ms | — | tie |
| Store 1 000 books, `mongo` | 99 ms | 105 ms | — | tie |

- **SQLite and MongoDB do the work, so the gaps are small.**
  - By id, Python adds ~1 µs to SQLite (cursor, row tuple, result object) and ~30 µs to MongoDB (pymongo's round trip).
  - Scanning by author costs the same in both: 54 against 52 ns per book in `sqlite`, 0.57 against 0.59 µs in `mongo`.
- **Storing ties:** both are bound by the disk (`sqlite`) and the server (`mongo`). Java's `sqlite` interval (±321 ms) comes
  from its own drift: 654 ms in its first pass and 267 ms in its second.

### 4.5 The pattern

| Where the work is | Example | Result |
|---|---|---|
| In the language, item by item | tokenizing, result objects, JSON rewrite, paths | Java 1.5–9 times faster |
| In a storage engine | datalake writes, `folders` updates, SQLite, MongoDB updates | tie, or close |
| In an algorithm that differs | `time` lookup without attributes, hash intersection, lazy readers | Python faster |
| Short single-shot runs | opening `folders` and `mongo`, writing 100 books | Python faster: Java's JIT has not compiled the code yet (shown for opening, likely for writing) |

## 5. Verdict

### 5.1 Structures: `batch`, `mongo` and `sqlite`

Both languages, analysed separately with the same rule, choose the same three structures. The choice is therefore a
property of the structures and their complexity, not of the implementation:

| Component | Decision | What Python adds to the Java analysis |
|---|---|---|
| Datalake | `batch` | `time`'s O(N) lookup has a smaller constant in Python (0.40 µs per book), but it is still O(N) |
| Inverted index | `mongo` | `json` is worse in Python: rewriting costs 10 times more, it loses the update book by book even with 1 000 books, and it needs 86 B per posting |
| Metadata | `sqlite` | Same result: 14 times faster than `mongo` by id, ~10 times by author |

### 5.2 Implementation: Java

Java is the faster implementation of this data layer: 38 of 51 time metrics with 1 000 books, against 6 for Python and
7 tied.

- **Its advantage is CPU work in the language:** tokenizing (2.9 times), building results (258 ns per object in Python,
  invisible in Java), rewriting JSON (10 times) and O(1) lookups (6–9 times).
- **Where a storage engine works, Python keeps up:** writing the datalake, updating `folders`, SQLite and MongoDB.
- **Python's wins come from doing less work,** not from being faster: reading names without attributes, intersecting from
  the smaller set, and reading lazily. Its one hard limit is memory with `json`, which the chosen structures avoid.

### 5.3 Improvements

The improvements of the Java analysis (§9 there) apply to both implementations:

- paginate and fetch the page's metadata in one query;
- intersect starting from the shortest list;
- store `mongo`'s postings in buckets;
- one `sqlite` transaction per batch, and an index on the author;
- a manifest for the `batch` datalake.

Python adds four of its own, ordered by impact:

| Improvement | Operation | Now | After |
|---|---|---|---|
| Build results lazily, or as tuples or `__slots__` classes, for the page only | Query | 258 ns × R, ~24 ms with 100 000 books | Only the books of the page |
| Fetch every term of a query in one MongoDB round trip (`$in`) | Query with `mongo` | q round trips, each after a pause | One round trip per query |
| Use `os.path` and `os.stat` instead of `pathlib` in the datalake's hot paths | Lookup, detection | 5 µs per lookup | ~1.5 µs, mostly the `stat` |
| If `json` were kept: store each list sorted and merge on flush | `json` flush | Sorts P postings again: 190 ns each | Writes them in order |

## 6. Reliability of the measurements

- **Python's run had little drift.** `json` and `mongo` builds took the same time in both passes: their processes lasted
  0.98–1.07 times as long in the second. The indexer took 58 min in the first pass and 55 min in the second; Java's took
  37 and 75 min.
- **`folders` depends on the state of the file system, in both languages.**
  - Python: the second pass ran the `folders` builds of 300 and 100 books right after the one of 1 000 books, which
    creates and deletes ~435 000 files several times, and those processes took 1.5 and 1.8 times longer.
  - Java: its `folders` scores differed between passes by factors of 0.31 to 2.44.

  The `folders` comparisons between languages are therefore within the noise.
- **Rows to read with care:**
  - `mongo`'s update book by book with 100 books: 654 ± 730 ms;
  - `json`'s update in batches with 1 000 books: 38.7 ± 20.0 ms, ±52%;
  - `mongo`'s books by author with 1 000 books: 2 953 ± 981 µs, against 659–714 µs in probes.

  Their intervals show a few very slow samples, which two processes cannot average out.
- **Python's `mongo` queries with 1 000 books include the idle effect of §4.3.** They compare the structures as a single
  Python client sees them, but they overstate the index's own cost.
- **Memory:** `tracemalloc` and the Java heap measure different things, and neither counts native memory. The comparison is
  only about orders of magnitude and growth.
- **Not checked:**
  - whether Java's slower small single-shot runs are only the JIT (§4.2, §4.3);
  - the cause of MongoDB's slower round trips after a pause: it could be the operating system waking up the server's
    thread or lowering its core's frequency;
  - the per-posting cost of `mongo`'s updates, within the noise with ≤ 1 000 books in both languages.
- **Estimates:** those for 100 000 and 1 000 000 books extrapolate one or two orders of magnitude. They compare structures
  and find limits, as in the Java analysis; they are not predictions.
