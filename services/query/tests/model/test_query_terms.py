from tarantino_query.model.query_terms import QueryTerms


def test_normalizes_like_the_indexer_and_removes_duplicates():
    terms = QueryTerms.of("The ISLAND of a Shipwreck island", {"the", "of"})
    assert terms == {"island", "shipwreck"}
