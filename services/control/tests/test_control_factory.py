from pathlib import Path

from tarantino_control.control_config import ControlConfig
from tarantino_control.control_factory import ControlFactory


def config(workload: Path) -> ControlConfig:
    return ControlConfig(control=workload / "control", workload=workload)


def test_reads_the_candidates_of_a_workload_file_in_order(tmp_path):
    (tmp_path / "candidates.txt").write_bytes(b" 1342 \r\n\n84\n11")

    assert ControlFactory.candidates(config(tmp_path), "candidates.txt") == [
        1342,
        84,
        11,
    ]


def test_takes_the_sample_dataset_without_a_candidates_file(tmp_path):
    (tmp_path / "sample_ids.txt").write_bytes(b"11\n84\n")

    assert ControlFactory.candidates(config(tmp_path), None) == [11, 84]
