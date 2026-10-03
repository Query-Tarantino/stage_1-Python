import pytest

from services.crawler.tests.benchmarking.support.datalake.recovery_scenario import (
    RecoveryScenario,
)

IDS = list(range(1, 21))


class SyntheticBooks:
    def raw_text(self, book_id: int) -> str:
        return (
            f"Title: Book {book_id}\n*** START OF THE PROJECT GUTENBERG EBOOK X ***\n"
            f"body {book_id}\n*** END OF THE PROJECT GUTENBERG EBOOK X ***"
        )


@pytest.mark.parametrize("layout", ["time", "book", "batch"])
def test_resumes_after_interruption_without_duplicates_or_losses(tmp_path, layout):
    outcome = RecoveryScenario(layout, tmp_path, SyntheticBooks()).run(IDS)

    assert outcome.recovered


@pytest.mark.parametrize("layout", ["time", "book", "batch"])
def test_leaves_no_files_behind_because_the_resumed_run_removes_incomplete_writes(
    tmp_path, layout
):
    outcome = RecoveryScenario(layout, tmp_path, SyntheticBooks()).run(IDS)

    assert outcome.leftover_files == 0
