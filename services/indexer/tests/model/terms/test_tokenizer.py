from tarantino_indexer.model.terms.tokenizer import Tokenizer


def test_counts_lowercased_terms_without_stopwords_or_short_tokens():
    tokenizer = Tokenizer({"the", "of"})
    text = "The Island of the island, a SHIPWRECK!"
    term_occurrences = tokenizer.occurrences(1, text)

    assert term_occurrences.frequencies == {"island": 2, "shipwreck": 1}


def test_keeps_accented_letters_and_splits_on_digits_and_apostrophes():
    tokenizer = Tokenizer({"the", "of"})
    text = "Café don't 1984year"
    term_occurrences = tokenizer.occurrences(1, text)

    assert term_occurrences.frequencies == {"café": 1, "don": 1, "year": 1}
