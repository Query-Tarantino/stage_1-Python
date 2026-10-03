from tarantino_control.adapters.file_control_state_store import FileControlStateStore


def test_ignores_lines_that_are_not_whole_numbers_after_stripping(tmp_path):
    (tmp_path / "downloaded_books.txt").write_bytes(
        " 5 \r\n\n12\nabc\n\u00a07\n\u0663\n13".encode("utf-8")
    )

    assert FileControlStateStore(tmp_path).downloaded() == {5, 12, 13}


def test_appends_one_id_per_line(tmp_path):
    store = FileControlStateStore(tmp_path)
    store.mark_indexed(5)
    store.mark_indexed(84)

    assert (tmp_path / "indexed_books.txt").read_bytes() == b"5\n84\n"
    assert store.indexed() == {5, 84}
