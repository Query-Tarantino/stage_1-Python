from tarantino_query.adapters.index.folders.folder_per_term_index_reader import (
    FolderPerTermIndexReader,
)


def test_reads_the_postings_of_a_term_and_nothing_for_unknown_terms(tmp_path):
    (tmp_path / "i").mkdir()
    (tmp_path / "i" / "island.txt").write_bytes(b"5\n1342\n")
    index = FolderPerTermIndexReader(tmp_path)

    assert index.postings("island") == {5, 1342}
    assert index.postings("whale") == set()


def test_reads_non_ascii_terms_from_their_encoded_file_name(tmp_path):
    (tmp_path / "%C3%A9").mkdir()
    (tmp_path / "%C3%A9" / "%C3%A9cume.txt").write_bytes(b"1342\n")

    assert FolderPerTermIndexReader(tmp_path).postings("écume") == {1342}
