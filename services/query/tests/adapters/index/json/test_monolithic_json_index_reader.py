from tarantino_query.adapters.index.json.monolithic_json_index_reader import (
    MonolithicJsonIndexReader,
)


def test_reads_postings_from_the_index_file(tmp_path):
    file = tmp_path / "inverted_index.json"
    file.write_text('{"island":[5,1342]}', encoding="utf-8")
    index = MonolithicJsonIndexReader(file)

    assert index.postings("island") == {5, 1342}
    assert index.postings("whale") == set()


def test_treats_a_missing_index_as_empty(tmp_path):
    assert (
        MonolithicJsonIndexReader(tmp_path / "missing.json").postings("island") == set()
    )
