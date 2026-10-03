import pytest

from services.query.tests.benchmarking.query_workload import QueryWorkload
from services.query.tests.benchmarking.reference_results import ReferenceResults
from services.query.tests.benchmarking.workload_query import WorkloadQuery


def test_reads_the_category_and_the_query_of_a_line():
    assert WorkloadQuery.parse("long: ship captain sea voyage") == WorkloadQuery(
        "long", "ship captain sea voyage"
    )


def test_rejects_a_line_without_category():
    with pytest.raises(ValueError):
        WorkloadQuery.parse("ship captain")


def test_selects_the_queries_of_a_category_or_all_of_them():
    workload = [WorkloadQuery("rare", "liliput"), WorkloadQuery("frequent", "love")]

    assert QueryWorkload.texts(workload, "frequent") == ["love"]
    assert QueryWorkload.texts(workload, QueryWorkload.ALL_CATEGORIES) == [
        "liliput",
        "love",
    ]


def test_reads_back_the_reference_results_it_writes(tmp_path):
    results = {"love": [11, 1342], "cæsar façade": []}

    ReferenceResults.write(tmp_path / "reference.tsv", results)

    assert ReferenceResults.read(tmp_path / "reference.tsv") == results
