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
  `docker run -d -p 27017:27017 --name tarantino-mongo mongo:7.0`

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

Not available in this version: the previous pytest-benchmark suite did not follow
[SPEC.md §11](SPEC.md#11-benchmarks) and was removed. The new benchmarks will live in the test tree of each service,
under `tests/benchmarking/`, and write `benchmarks/results/python-<service>.csv`, which `scripts/compare_results.py`
joins with the results of the other languages into the comparison report (matplotlib, optional, adds its charts).
