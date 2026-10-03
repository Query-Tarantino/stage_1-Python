import pytest

from tarantino_control.__main__ import main


def test_stops_before_any_work_without_the_candidates_file(monkeypatch, tmp_path):
    monkeypatch.setenv("TARANTINO_WORKLOAD", str(tmp_path))
    monkeypatch.setenv("TARANTINO_CONTROL", str(tmp_path / "control"))
    monkeypatch.setenv("TARANTINO_DATALAKE", str(tmp_path / "datalake"))

    with pytest.raises(SystemExit) as stop:
        main(["missing.txt"])

    assert "missing.txt" in str(stop.value.code)
    assert not (tmp_path / "control").exists()
    assert not (tmp_path / "datalake").exists()
