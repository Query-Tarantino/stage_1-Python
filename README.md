# Query Tarantino Stage 1: Data Layer (Python)

Python implementation of the data layer of a search engine over [Project Gutenberg](https://www.gutenberg.org/) books:
a **datalake** with the raw texts, **datamarts** with metadata and an inverted index, and a minimal **control layer**
that coordinates downloading and indexing.

The behavior shared with the Java and C++ implementations (split rules, datalake layouts, tokenizer,
datamart formats, control algorithm and benchmark format) is defined in [SPEC.md](SPEC.md).

## Repository structure

```
services/                one package per service (SPEC §16)
  crawler/               downloads books, splits header/body and stores them in the datalake
  indexer/               reads the datalake and builds the inverted index and the metadata datamart
  query/                 searches the datamarts
  control/               orchestrates crawler -> indexer and tracks progress in control files
scripts/                 shared by every language implementation, copied unchanged from the Java repository
  fill_cache.sh          copies the benchmark dataset from Gutenberg's official mirrors
  compare_results.py     builds the comparison report from the benchmark results of every language
workload/                experiment definition shared by every language implementation, copied unchanged too
  book_ids.txt           candidate ids for the benchmark cache, in order
  sample_ids.txt         small sample dataset to test the pipeline quickly
  stopwords.txt          stopwords removed by the tokenizer
  queries.txt            search benchmark workload, one `<category>: <query>` per line
  conformance/           conformance cases every implementation must pass (SPEC §13)
```

Each service is a package with its own `pyproject.toml` and the same layers, with the class names of the Java
implementation:

```
services/<service>/
  pyproject.toml
  src/tarantino_<service>/
    __main__.py, <service>_config.py, <service>_factory.py
    model/      frozen dataclasses and pure domain logic, grouped by concept
    ports/      typing.Protocol interfaces the service depends on
    adapters/   implementations of the ports, one subpackage per functionality and per compared structure
    commands/   use cases
  tests/        mirror the packages of what they test
    benchmarking/   benchmarks of the service's structures (SPEC §11), with their shared code in support/
```

The control service uses the packages of the crawler and the indexer.

The following directories are **created at runtime** in the project root and are not versioned:

| Directory     | Written by | Content                                                              |
|---------------|------------|----------------------------------------------------------------------|
| `datalake/`   | crawler    | header and body files of each book, in the selected layout           |
| `datamarts/`  | indexer    | `inverted_index.json`, `inverted_index/`, `metadata.db`              |
| `control/`    | control    | `downloaded_books.txt`, `indexed_books.txt`                          |
| `benchmarks/` | benchmarks | download cache, results and temporary data                           |

## Requirements

- Python 3.13+
- pip
- MongoDB 7.0 (only for the `mongo` index or metadata backends), e.g.
  `docker run -d -p 27017:27017 --name tarantino-mongo mongo:7.0`; the benchmarks need it installed natively on macOS
  (see [Benchmarks](#prepare-the-machine))

## Installation

From the project root:

```bash
python -m venv .venv
source .venv/Scripts/activate      # On Windows Git Bash
# .\.venv\Scripts\Activate.ps1     # On Windows PowerShell
# source .venv/bin/activate        # On Linux/Mac
python -m pip install -r requirements.txt
```

`requirements.txt` installs the four services in editable mode, with their dependencies, and pytest.

## Configuration

Every setting has a default that works when running from the project root. Override them with environment variables:

| Variable                       | Default                     | Values                     |
|--------------------------------|-----------------------------|----------------------------|
| `TARANTINO_DATALAKE`           | `datalake`                  | path                       |
| `TARANTINO_DATAMARTS`          | `datamarts`                 | path                       |
| `TARANTINO_CONTROL`            | `control`                   | path                       |
| `TARANTINO_BENCHMARKS`         | `benchmarks`                | path                       |
| `TARANTINO_WORKLOAD`           | `workload`                  | path                       |
| `TARANTINO_DATALAKE_LAYOUT`    | `time`                      | `time`, `book`, `batch`    |
| `TARANTINO_INDEX`              | `json`                      | `json`, `folders`, `mongo` |
| `TARANTINO_METADATA`           | `sqlite`                    | `sqlite`, `mongo`          |
| `TARANTINO_MONGO_URI`          | `mongodb://localhost:27017` | connection string          |
| `TARANTINO_PARALLEL_DOWNLOADS` | `8`                         | positive integer           |
| `TARANTINO_INDEX_BATCH`        | `100`                       | positive integer           |
| `TARANTINO_MIRROR`             | (none)                      | path, or empty             |

The crawler and the indexer must use the same `TARANTINO_DATALAKE_LAYOUT`; the indexer and the query service must use
the same `TARANTINO_INDEX` and `TARANTINO_METADATA`. The control layer downloads up to `TARANTINO_PARALLEL_DOWNLOADS`
books at once and indexes them in batches of `TARANTINO_INDEX_BATCH`, with one index flush per batch.

Books are downloaded from `mirror.cs.odu.edu`, the official Project Gutenberg mirror of Old Dominion University, never
from `www.gutenberg.org`, whose robot policy forbids automated access. To ingest many books, copy the plain texts once
with rsync and point `TARANTINO_MIRROR` to the copy: the crawler then reads `<mirror>/<id>/pg<id>.txt` instead of
downloading it, and the control layer takes every book of the mirror when no candidates file is given.

```bash
rsync -av --include='*/' --include='pg[0-9]*.txt' --exclude='*' rsync.ibiblio.org::gutenberg-epub/ mirror/
TARANTINO_MIRROR=mirror python -m tarantino_control
```

## Running

Always run from the project root so the runtime directories are created there.

```bash
python -m tarantino_control                     # full pipeline over workload/sample_ids.txt (or TARANTINO_MIRROR)
python -m tarantino_control book_ids.txt        # candidates from another file of the workload

python -m tarantino_crawler 1342 84             # ingest specific books
python -m tarantino_indexer 1342 84             # index specific books
python -m tarantino_query adventure island      # search
```

## Tests

```bash
python -m pytest                                     # tests of every service
python -m pytest services/indexer/tests              # tests of one service
python -m unittest discover -s scripts -t scripts    # tests of the comparison report
```

The MongoDB tests use the server of `TARANTINO_MONGO_URI` (`mongodb://localhost:27017` by default), each one in a
temporary database of its own that is dropped afterwards, and are skipped when no server answers.

## Benchmarks

The data structure benchmarks of [SPEC.md §11](SPEC.md#11-benchmarks) live in the test tree of each service, under
`tests/benchmarking/`. Each service has a runner that writes `benchmarks/results/python-<service>.csv`, which
`scripts/compare_results.py` joins with the results of the other languages into the comparison report. Every command
runs from the **project root**.

### Quick reference

```bash
scripts/fill_cache.sh                                      # 1. dataset, once
for service in crawler indexer query; do                   # 2. check the setup in a few minutes
    TARANTINO_BENCHMARK_QUICK=true TARANTINO_BENCHMARK_BOOKS=20 \
        python -m services.$service.tests.benchmarking.benchmark_runner || break
done
caffeinate -i sh -c 'for service in crawler indexer query; do
    python -m services.$service.tests.benchmarking.benchmark_runner || exit 1
done'                                                      # 3. full run (Linux: systemd-inhibit --what=idle:sleep)
python scripts/compare_results.py                          # 4. comparison report
```

### Prepare the machine

- The services installed with `python -m pip install -r requirements.txt` (see [Installation](#installation)): the
  runners and the processes they start import them.
- **MongoDB 7.0** running on the machine itself, not inside a virtual machine, with its cache fixed at 1 GB (SPEC §11).
  On macOS install it natively, since Docker runs it inside a virtual machine there:

  ```bash
  brew tap mongodb/brew && brew install mongodb-community@7.0
  brew services start mongodb-community@7.0
  ```

  and set the cache inside the existing `storage:` section of `/opt/homebrew/etc/mongod.conf` (`/etc/mongod.conf` on
  Linux), then restart it:

  ```yaml
  storage:
    wiredTiger:
      engineConfig:
        cacheSizeGB: 1
  ```

  To run without MongoDB, set `TARANTINO_BENCHMARK_SKIP_MONGO=true`.
- **matplotlib**, optionally, to add charts to the report: `python -m pip install matplotlib`.

### Fill the dataset cache

Benchmarks read the books from `benchmarks/cache/`, so the network is never measured. `scripts/fill_cache.sh` fills it
once with the 2 800 books of `workload/book_ids.txt` (about 1.3 GB); it can be interrupted and resumes where it stopped,
and `TARANTINO_CACHE_SOURCE=http` downloads them over HTTP where the rsync port is blocked. Every implementation reads
the same files, so a cache already filled in the Java repository can be linked instead of copied:

```bash
mkdir -p benchmarks && ln -s ../../Query_Tarantino-Java/benchmarks/cache benchmarks/cache
```

### Run the benchmarks

Before a full run, check that the dataset, MongoDB and every benchmark work with a quick run: 1 pass of 1 process,
1 warm-up and 1 measured iteration per configuration, so its numbers are not meaningful, only its errors. It overwrites
the results of an earlier run.

Each runner runs its benchmarks in **two passes** of one operating-system process per benchmark, structure and size
(SPEC §11); the second takes the structures and the sizes in reverse order, so whatever drifts during a run, such as
the temperature, weighs alike on every structure and size. Each process runs its warm-up iterations, which are
discarded, and then its measured iterations. A process that fails stops the run, and a runner writes its results file
only when both passes end: an interrupted service writes nothing, and running it again replaces only its own results.

Keep the machine as SPEC §11 requires: plugged in, out of any power-saving mode, with nothing else running, and awake
for the whole run, which the full-run command above ensures with `caffeinate -i` on macOS
(`systemd-inhibit --what=idle:sleep` on Linux). The scratch files go under `benchmarks/tmp.noindex/`, which Spotlight
skips on macOS; on a Linux desktop with KDE Baloo, exclude `benchmarks/` in its settings.

| Comparison               | Structures                 | Benchmarks                                                                    |
|--------------------------|----------------------------|-------------------------------------------------------------------------------|
| Datalake (PDF 3.1)       | `time`, `book`, `batch`    | crawler `DatalakeWriteBenchmark`, `DatalakeLookupBenchmark`, `NewBooksDetectionBenchmark`, `RecoveryScenario` |
| Inverted index (PDF 4.2) | `json`, `folders`, `mongo` | indexer `FullIndexBuildBenchmark`, `IncrementalUpdateBenchmark`, query `IndexOpenBenchmark`, `QueryTimeBenchmark` |
| Metadata (PDF 4.1)       | `sqlite`, `mongo`          | indexer `MetadataInsertionBenchmark`, query `MetadataQueryBenchmark`          |

| Variable                         | Effect                                                                         |
|----------------------------------|--------------------------------------------------------------------------------|
| `TARANTINO_BENCHMARK_BOOKS`      | Sizes to run, e.g. `100,300` (default `100,300,1000`)                           |
| `TARANTINO_BENCHMARK_QUICK`      | `true`: 1 pass of 1 process, 1 warm-up and 1 measured iteration of 0.2 s        |
| `TARANTINO_BENCHMARK_SKIP_MONGO` | `true`: skip the `mongo` index and metadata structures                         |
| `TARANTINO_MONGO_URI`            | MongoDB server (default `mongodb://localhost:27017`)                           |
| `TARANTINO_BENCHMARKS`           | Directory of the cache, results and scratch files (default `benchmarks`)       |
| `TARANTINO_WORKLOAD`             | Directory of the workload files (default `workload`)                           |

### Build the comparison report

```bash
python scripts/compare_results.py
```

It reads every CSV in `benchmarks/results/` and writes `benchmarks/report/comparison.md`, with one table and, if
matplotlib is installed, one chart per metric. Copy the `java-*.csv` and `cpp-*.csv` results of the other
implementations, run on the same machine, into `benchmarks/results/` to compare the languages: every table then has a
row per language and structure.

The analysis of the Python results, the structure chosen for each component and the comparison with Java are in
[ANALYSIS.md](ANALYSIS.md).

### Output files

Everything is under `benchmarks/`, which is not versioned:

| Path                                  | Content                                                        |
|---------------------------------------|----------------------------------------------------------------|
| `cache/<id>.txt`, `cache/skipped.txt` | The dataset, and the candidate ids left out of it              |
| `results/python-<service>.csv`        | Results shared with the other languages (SPEC §11 format)      |
| `report/comparison.md`, `report/*.png`| The comparison report and its charts                           |
| `tmp.noindex/`                        | Scratch datalakes and indexes, deleted and rebuilt by each run |

### How the Python runner works

Java runs its benchmarks with JMH; Python has its own runner, as SPEC §14 says, in the test tree of the crawler, which
the indexer and query benchmarks import as Java's do through the crawler's test-jar:

```
services/crawler/tests/benchmarking/support/
  harness/     what JMH's annotations do: Benchmark, with its setup and teardown hooks, and the three ways a method
               is measured, whole_run (SingleShotTime), timed_operation (AverageTime) and sampled_operation (SampleTime)
  processes/   what JMH's Runner does: one process per configuration, started with subprocess, in two passes
  results/     the rows of the CSV, the metrics and the 95% confidence intervals
```

A benchmark is a subclass of `Benchmark` with its `STRUCTURES`, whose measured methods are marked with one of those
decorators. Python has no counter of every allocation, so it writes no `memory_allocated` rows; `build_memory` and
`index_memory` are measured with `tracemalloc`, which runs only around those measures because it slows Python down
several times (SPEC §11).
