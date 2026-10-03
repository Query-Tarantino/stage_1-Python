from tarantino_control.adapters.file_control_state_store import FileControlStateStore

NO_BREAK_SPACE, ARABIC_INDIC_THREE = chr(0x00A0), chr(0x0663)


def test_starts_empty_when_no_control_files_exist(tmp_path):
    state = FileControlStateStore(tmp_path / "control")

    assert state.downloaded() == []
    assert state.indexed() == []


def test_appends_ids_with_lf_keeping_file_order(tmp_path):
    state = FileControlStateStore(tmp_path / "control")
    state.mark_downloaded(1342)
    state.mark_downloaded(84)
    state.mark_indexed(84)

    assert state.downloaded() == [1342, 84]
    assert state.indexed() == [84]
    assert (tmp_path / "control" / "downloaded_books.txt").read_bytes() == b"1342\n84\n"


def test_ignores_lines_that_are_not_whole_numbers_after_stripping(tmp_path):
    lines = [" 5 \r", "", "84", "abc", NO_BREAK_SPACE + "7", ARABIC_INDIC_THREE, "13x"]
    (tmp_path / "downloaded_books.txt").write_bytes("\n".join(lines).encode("utf-8"))

    assert FileControlStateStore(tmp_path).downloaded() == [5, 84]


def test_keeps_each_id_once_in_the_order_of_its_first_line(tmp_path):
    (tmp_path / "downloaded_books.txt").write_bytes(b"84\n5\n84\n")

    assert FileControlStateStore(tmp_path).downloaded() == [84, 5]
