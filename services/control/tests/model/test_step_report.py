from tarantino_control.model.next_step import NextStep
from tarantino_control.model.outcome import Outcome
from tarantino_control.model.step_report import StepReport


def test_describes_the_action_book_and_outcome():
    report = StepReport(
        NextStep.download(1342), Outcome.success("stored in datalake/1342")
    )

    assert report.description() == "DOWNLOAD 1342: stored in datalake/1342"
    assert not report.idle()


def test_summarizes_the_books_of_a_batch():
    report = StepReport(NextStep.index([84, 1342, 2701]), Outcome.success("3 indexed"))

    assert report.description() == "INDEX 3 books (84…2701): 3 indexed"


def test_is_idle_only_for_idle_steps():
    assert StepReport(NextStep.idle(), Outcome.success("nothing left to do")).idle()
