# Testkatalog

Automatisch erzeugt mit `Phase4/testkatalog.py` am 15.11.2026. Erklärung und ausgewählte Fälle im Detail: `Phase4/Testdokumentation.md`.

Spalte **Input → erwartet** zeigt die erste Prüfung des Tests; „→ Fehlerklasse“ heißt, der Aufruf muss genau diesen Fehler werfen. **Tatsächlich** ist das Ergebnis des letzten Laufs: „wie erwartet“ heißt, das tatsächliche Output stimmt mit dem erwarteten überein.

## Übersicht

| Modul | Normalfall | Randfall | Fehlerfall | gesamt | wie erwartet |
|---|---|---|---|---|---|
| `sources` | 24 | 15 | 11 | 50 | 50 |
| `chunking` | 6 | 10 | 8 | 24 | 24 |
| `bm25` | 13 | 38 | 0 | 51 | 51 |
| `vector_search` | 19 | 17 | 17 | 53 | 53 |
| `ranking` | 7 | 9 | 1 | 17 | 17 |
| `pipeline` | 13 | 8 | 4 | 25 | 25 |
| `mcp_server` | 10 | 1 | 7 | 18 | 18 |
| `storage` | 13 | 14 | 8 | 35 | 35 |
| `cache` | 7 | 2 | 3 | 12 | 12 |
| **gesamt** | **112** | **114** | **59** | **285** | **285** |

## `sources`

| Nr. | Test | Kategorie | Input → erwartet | Tatsächlich |
|---|---|---|---|---|
| 1 | `TestNormalizeKeywords.test_normalize_does_not_mutate_input` | Randfall | `keywords → [' UML ', 'uml']` | ✓ wie erwartet |
| 2 | `TestNormalizeKeywords.test_normalize_drops_case_insensitive_duplicates` | Randfall | `sources.normalize_keywords(['UML', 'uml', 'Uml']) → ['UML']` | ✓ wie erwartet |
| 3 | `TestNormalizeKeywords.test_normalize_drops_empty` | Randfall | `sources.normalize_keywords(['', ' ', 'uml']) → ['uml']` | ✓ wie erwartet |
| 4 | `TestNormalizeKeywords.test_normalize_empty_list` | Randfall | `sources.normalize_keywords([]) → []` | ✓ wie erwartet |
| 5 | `TestNormalizeKeywords.test_normalize_example` | Normalfall | `sources.normalize_keywords([' UML ', 'class diagram']) → ['UML', 'class diagram']` | ✓ wie erwartet |
| 6 | `TestNormalizeKeywords.test_normalize_keeps_order` | Normalfall | `sources.normalize_keywords(['b', 'a', 'c']) → ['b', 'a', 'c']` | ✓ wie erwartet |
| 7 | `TestBuildArxivUrl.test_url_base` | Normalfall | `url.startswith('https://export.arxiv.org/api/query?') → wahr` | ✓ wie erwartet |
| 8 | `TestBuildArxivUrl.test_url_date_from_only` | Normalfall | `params['search_query'] → 'all:"uml" AND submittedDate:[202301010000 TO 999912312359]'` | ✓ wie erwartet |
| 9 | `TestBuildArxivUrl.test_url_date_range` | Normalfall | `params['search_query'] → 'all:"uml" AND submittedDate:[202301010000 TO 202406302359]'` | ✓ wie erwartet |
| 10 | `TestBuildArxivUrl.test_url_date_with_categories` | Normalfall | `params['search_query'] → '(all:"uml") AND (cat:cs.SE) AND submittedDate:[199101010000 TO 202012312359]'` | ✓ wie erwartet |
| 11 | `TestBuildArxivUrl.test_url_empty_keywords` | Fehlerfall | `sources.build_arxiv_url([], 5) → ValueError` | ✓ wie erwartet |
| 12 | `TestBuildArxivUrl.test_url_keywords_or_combined` | Normalfall | `params['search_query'] → 'all:"uml" OR all:"class diagram"'` | ✓ wie erwartet |
| 13 | `TestBuildArxivUrl.test_url_max_results_zero` | Fehlerfall | `sources.build_arxiv_url(['uml'], 0) → ValueError` | ✓ wie erwartet |
| 14 | `TestBuildArxivUrl.test_url_paging_and_sorting` | Normalfall | `(params['start'], params['max_results'], params['sortBy'], params['sortOrder']) → ('0', '7', 'relevance', 'descending')` | ✓ wie erwartet |
| 15 | `TestBuildArxivUrl.test_url_single_keyword` | Randfall | `params['search_query'] → 'all:"uml"'` | ✓ wie erwartet |
| 16 | `TestBuildArxivUrl.test_url_strips_double_quotes_from_keywords` | Randfall | `params['search_query'] → 'all:"C Sharp"'` | ✓ wie erwartet |
| 17 | `TestBuildArxivUrl.test_url_umlauts_round_trip` | Randfall | `params['search_query'] → 'all:"Müller"'` | ✓ wie erwartet |
| 18 | `TestBuildArxivUrl.test_url_with_categories` | Normalfall | `params['search_query'] → '(all:"uml") AND (cat:cs.SE OR cat:cs.PL)'` | ✓ wie erwartet |
| 19 | `TestParseArxivFeed.test_parse_empty_feed` | Randfall | `sources.parse_arxiv_feed(feed()) → []` | ✓ wie erwartet |
| 20 | `TestParseArxivFeed.test_parse_error_entry` | Fehlerfall | `sources.parse_arxiv_feed(feed(ENTRY_ERROR)) → sources.SourceError` | ✓ wie erwartet |
| 21 | `TestParseArxivFeed.test_parse_example` | Normalfall | `sources.parse_arxiv_feed(feed(ENTRY_UML)) → [sources.Document(id='1409.6928', title='Developing the UML as a Formal Modelling Notation', ab…` | ✓ wie erwartet |
| 22 | `TestParseArxivFeed.test_parse_invalid_xml` | Fehlerfall | `sources.parse_arxiv_feed('<feed><entry>') → sources.SourceError` | ✓ wie erwartet |
| 23 | `TestParseArxivFeed.test_parse_keeps_feed_order` | Normalfall | `ids → ['1409.6928', 'cs/0112017']` | ✓ wie erwartet |
| 24 | `TestParseArxivFeed.test_parse_old_style_id` | Randfall | `sources.parse_arxiv_feed(feed(ENTRY_OLD_ID))[0].id → 'cs/0112017'` | ✓ wie erwartet |
| 25 | `TestParseArxivFeed.test_parse_preprint_without_journal_ref_and_doi` | Randfall | `(document.categories, document.journal_ref, document.doi) → ((), '', '')` | ✓ wie erwartet |
| 26 | `TestParseArxivFeed.test_parse_skips_incomplete_entry` | Fehlerfall | `ids → ['1409.6928']` | ✓ wie erwartet |
| 27 | `TestParseArxivFeed.test_parse_url_falls_back_to_id` | Randfall | `sources.parse_arxiv_feed(feed(ENTRY_OLD_ID))[0].url → 'http://arxiv.org/abs/cs/0112017v2'` | ✓ wie erwartet |
| 28 | `TestDocument.test_document_is_immutable` | Fehlerfall | `document.title = 'anders' → AttributeError` | ✓ wie erwartet |
| 29 | `TestDocument.test_document_peer_reviewed_with_doi` | Normalfall | `sources.Document('x', 'T', '', (), date(2024, 1, 1), 'u', 'arxiv', doi='10.1/x').peer_reviewed → wahr` | ✓ wie erwartet |
| 30 | `TestDocument.test_document_peer_reviewed_with_journal_ref` | Normalfall | `sources.Document('x', 'T', '', (), date(2024, 1, 1), 'u', 'arxiv', journal_ref='J').peer_reviewed → wahr` | ✓ wie erwartet |
| 31 | `TestDocument.test_document_preprint_is_not_peer_reviewed` | Normalfall | `sources.Document('x', 'T', '', (), date(2024, 1, 1), 'u', 'arxiv').peer_reviewed → falsch` | ✓ wie erwartet |
| 32 | `TestDocument.test_document_text` | Normalfall | `document.text → 'An old style identifier\n\nAbstract.'` | ✓ wie erwartet |
| 33 | `TestDocument.test_document_text_without_abstract` | Randfall | `document.text → 'Title'` | ✓ wie erwartet |
| 34 | `TestSearchFilter.test_filter_defaults_restrict_nothing` | Normalfall | `sources.SearchFilter() → sources.SearchFilter(None, None, (), False)` | ✓ wie erwartet |
| 35 | `TestSearchFilter.test_filter_from_after_to` | Fehlerfall | `sources.SearchFilter(published_from=date(2024, 1, 1), published_to=date(2023, 1, 1)) → ValueError` | ✓ wie erwartet |
| 36 | `TestSearchFilter.test_filter_same_day` | Randfall | `sources.SearchFilter(date(2024, 1, 1), date(2024, 1, 1)).published_from → date(2024, 1, 1)` | ✓ wie erwartet |
| 37 | `TestArxivSource.test_arxiv_source_is_a_source` | Normalfall | `assertIsInstance(sources.ArxivSource(), sources.Source)` | ✓ wie erwartet |
| 38 | `TestArxivSource.test_search_blank_keywords_without_fetch` | Fehlerfall | `sources.ArxivSource(fetch=fetch).search([' ', ''], 5) → ValueError (+1 weitere Prüfungen)` | ✓ wie erwartet |
| 39 | `TestArxivSource.test_search_fetches_once` | Normalfall | `len(fetch.urls) → 1` | ✓ wie erwartet |
| 40 | `TestArxivSource.test_search_filter_categories_override_source` | Normalfall | `query_params(fetch.urls[0])['search_query'] → '(all:"uml") AND (cat:cs.AI)'` | ✓ wie erwartet |
| 41 | `TestArxivSource.test_search_filter_dates_in_url` | Normalfall | `assertIn('submittedDate:[202301010000', query_params(fetch.urls[0])['search_query'])` | ✓ wie erwartet |
| 42 | `TestArxivSource.test_search_network_error` | Fehlerfall | `source.search(['uml'], 5) → sources.SourceError` | ✓ wie erwartet |
| 43 | `TestArxivSource.test_search_normalizes_keywords` | Normalfall | `query_params(fetch.urls[0])['search_query'] → 'all:"UML"'` | ✓ wie erwartet |
| 44 | `TestArxivSource.test_search_peer_reviewed_only` | Normalfall | `[document.id for document in documents] → ['1409.6928']` | ✓ wie erwartet |
| 45 | `TestArxivSource.test_search_peer_reviewed_only_fetches_more` | Randfall | `query_params(fetch.urls[0])['max_results'] → str(5 * sources.PEER_REVIEW_OVERFETCH)` | ✓ wie erwartet |
| 46 | `TestArxivSource.test_search_peer_reviewed_only_respects_max_results` | Randfall | `len(source.search(['uml'], 2, sources.SearchFilter(peer_reviewed_only=True))) → 2` | ✓ wie erwartet |
| 47 | `TestArxivSource.test_search_returns_documents` | Normalfall | `[document.id for document in source.search(['uml'], 5)] → ['1409.6928']` | ✓ wie erwartet |
| 48 | `TestArxivSource.test_search_timeout` | Fehlerfall | `source.search(['uml'], 5) → sources.SourceError` | ✓ wie erwartet |
| 49 | `TestArxivSource.test_search_uses_categories` | Normalfall | `query_params(fetch.urls[0])['search_query'] → '(all:"uml") AND (cat:cs.SE)'` | ✓ wie erwartet |
| 50 | `TestArxivSource.test_source_is_abstract` | Fehlerfall | `sources.Source() → TypeError` | ✓ wie erwartet |

## `chunking`

| Nr. | Test | Kategorie | Input → erwartet | Tatsächlich |
|---|---|---|---|---|
| 1 | `TestSplitIntoChunks.test_split_chunk_size_zero` | Fehlerfall | `chunking.split_into_chunks(ZEHN_WOERTER, 0, 0) → ValueError` | ✓ wie erwartet |
| 2 | `TestSplitIntoChunks.test_split_chunks_have_chunk_size_except_last` | Normalfall | `all((len(chunk.split()) == 6 for chunk in chunks[:-1])) → wahr (+1 weitere Prüfungen)` | ✓ wie erwartet |
| 3 | `TestSplitIntoChunks.test_split_consecutive_chunks_share_overlap` | Normalfall | `current.split()[-2:] → following.split()[:2]` | ✓ wie erwartet |
| 4 | `TestSplitIntoChunks.test_split_covers_all_words_in_order` | Normalfall | `rebuilt → ZWANZIG_WOERTER.split()` | ✓ wie erwartet |
| 5 | `TestSplitIntoChunks.test_split_empty_string` | Randfall | `chunking.split_into_chunks('', 4, 1) → []` | ✓ wie erwartet |
| 6 | `TestSplitIntoChunks.test_split_exactly_one_chunk` | Randfall | `chunking.split_into_chunks('w1 w2 w3 w4', 4, 1) → ['w1 w2 w3 w4']` | ✓ wie erwartet |
| 7 | `TestSplitIntoChunks.test_split_example_with_overlap` | Normalfall | `chunking.split_into_chunks(ZEHN_WOERTER, 4, 1) → ['w1 w2 w3 w4', 'w4 w5 w6 w7', 'w7 w8 w9 w10']` | ✓ wie erwartet |
| 8 | `TestSplitIntoChunks.test_split_negative_overlap` | Fehlerfall | `chunking.split_into_chunks(ZEHN_WOERTER, 4, -1) → ValueError` | ✓ wie erwartet |
| 9 | `TestSplitIntoChunks.test_split_no_chunk_of_only_overlap` | Randfall | `chunking.split_into_chunks('w1 w2 w3 w4 w5 w6 w7', 4, 1) → ['w1 w2 w3 w4', 'w4 w5 w6 w7']` | ✓ wie erwartet |
| 10 | `TestSplitIntoChunks.test_split_normalizes_whitespace` | Randfall | `chunking.split_into_chunks('w1\n\nw2 w3\tw4', 10, 0) → ['w1 w2 w3 w4']` | ✓ wie erwartet |
| 11 | `TestSplitIntoChunks.test_split_only_whitespace` | Randfall | `chunking.split_into_chunks(' \n ', 4, 1) → []` | ✓ wie erwartet |
| 12 | `TestSplitIntoChunks.test_split_overlap_equals_chunk_size` | Fehlerfall | `chunking.split_into_chunks(ZEHN_WOERTER, 4, 4) → ValueError` | ✓ wie erwartet |
| 13 | `TestSplitIntoChunks.test_split_overlap_greater_than_chunk_size` | Fehlerfall | `chunking.split_into_chunks(ZEHN_WOERTER, 4, 5) → ValueError` | ✓ wie erwartet |
| 14 | `TestSplitIntoChunks.test_split_short_last_chunk` | Randfall | `chunking.split_into_chunks('w1 w2 w3 w4 w5 w6 w7 w8', 4, 1) → ['w1 w2 w3 w4', 'w4 w5 w6 w7', 'w7 w8']` | ✓ wie erwartet |
| 15 | `TestSplitIntoChunks.test_split_shorter_than_chunk` | Randfall | `chunking.split_into_chunks('w1 w2 w3', 5, 1) → ['w1 w2 w3']` | ✓ wie erwartet |
| 16 | `TestSplitIntoChunks.test_split_without_overlap` | Randfall | `chunking.split_into_chunks(ZEHN_WOERTER, 5, 0) → ['w1 w2 w3 w4 w5', 'w6 w7 w8 w9 w10']` | ✓ wie erwartet |
| 17 | `TestCreateChunks.test_create_chunks_empty_document_id` | Fehlerfall | `chunking.create_chunks('', ZEHN_WOERTER, 4, 1) → ValueError` | ✓ wie erwartet |
| 18 | `TestCreateChunks.test_create_chunks_empty_text` | Randfall | `chunking.create_chunks('doc', '', 4, 1) → []` | ✓ wie erwartet |
| 19 | `TestCreateChunks.test_create_chunks_example` | Normalfall | `chunking.create_chunks('2401.00001', 'w1 w2 w3 w4 w5 w6 w7', 4, 1) → [chunking.Chunk('2401.00001', 0, 'w1 w2 w3 w4'), chunking.Chunk('2401.…` | ✓ wie erwartet |
| 20 | `TestCreateChunks.test_create_chunks_invalid_parameters` | Fehlerfall | `chunking.create_chunks('doc', ZEHN_WOERTER, 4, 4) → ValueError` | ✓ wie erwartet |
| 21 | `TestCreateChunks.test_create_chunks_positions_start_at_zero` | Randfall | `positions → [0, 1, 2]` | ✓ wie erwartet |
| 22 | `TestCreateChunks.test_create_chunks_texts_match_split` | Normalfall | `texts → chunking.split_into_chunks(ZWANZIG_WOERTER, 5, 2)` | ✓ wie erwartet |
| 23 | `TestCreateChunks.test_create_chunks_whitespace_document_id` | Fehlerfall | `chunking.create_chunks(' ', ZEHN_WOERTER, 4, 1) → ValueError` | ✓ wie erwartet |
| 24 | `TestChunk.test_chunk_is_immutable` | Fehlerfall | `chunk.text = 'anders' → AttributeError` | ✓ wie erwartet |

## `bm25`

| Nr. | Test | Kategorie | Input → erwartet | Tatsächlich |
|---|---|---|---|---|
| 1 | `TestTokenize.test_tokenize_apostrophe` | Randfall | `bm25.tokenize("don't") → ['dont']` | ✓ wie erwartet |
| 2 | `TestTokenize.test_tokenize_casefold_eszett` | Randfall | `bm25.tokenize('Straße') → ['strasse']` | ✓ wie erwartet |
| 3 | `TestTokenize.test_tokenize_em_dash` | Randfall | `bm25.tokenize('kam—und') → ['kam', 'und']` | ✓ wie erwartet |
| 4 | `TestTokenize.test_tokenize_empty_string` | Randfall | `bm25.tokenize('') → []` | ✓ wie erwartet |
| 5 | `TestTokenize.test_tokenize_en_dash_range` | Randfall | `bm25.tokenize('Seiten 10–20') → ['seiten', '10', '20']` | ✓ wie erwartet |
| 6 | `TestTokenize.test_tokenize_example` | Normalfall | `bm25.tokenize('DEr Apfel-Baum ist grün.') → ['der', 'apfelbaum', 'ist', 'grün']` | ✓ wie erwartet |
| 7 | `TestTokenize.test_tokenize_inner_dash` | Randfall | `bm25.tokenize('Apfel–Baum') → ['apfel', 'baum']` | ✓ wie erwartet |
| 8 | `TestTokenize.test_tokenize_inner_hyphen` | Randfall | `bm25.tokenize('E-Mail') → ['email']` | ✓ wie erwartet |
| 9 | `TestTokenize.test_tokenize_letter_digit_hyphen` | Randfall | `bm25.tokenize('COVID-19') → ['covid19']` | ✓ wie erwartet |
| 10 | `TestTokenize.test_tokenize_only_hyphens` | Randfall | `bm25.tokenize('- -- ---') → []` | ✓ wie erwartet |
| 11 | `TestTokenize.test_tokenize_only_punctuation` | Randfall | `bm25.tokenize('.!?') → []` | ✓ wie erwartet |
| 12 | `TestTokenize.test_tokenize_only_whitespace` | Randfall | `bm25.tokenize(' ') → []` | ✓ wie erwartet |
| 13 | `TestTokenize.test_tokenize_single_quotes` | Randfall | `bm25.tokenize("'Apfel'") → ['apfel']` | ✓ wie erwartet |
| 14 | `TestTokenize.test_tokenize_standalone_dash` | Randfall | `bm25.tokenize('Apfel – Baum') → ['apfel', 'baum']` | ✓ wie erwartet |
| 15 | `TestTokenize.test_tokenize_standalone_hyphen` | Randfall | `bm25.tokenize('Wort - Wort') → ['wort', 'wort']` | ✓ wie erwartet |
| 16 | `TestTokenize.test_tokenize_trailing_hyphen` | Randfall | `bm25.tokenize('Vor- und Nachteile') → ['vor', 'und', 'nachteile']` | ✓ wie erwartet |
| 17 | `TestTokenize.test_tokenize_typographic_apostrophe` | Randfall | `bm25.tokenize('don’t') → ['dont']` | ✓ wie erwartet |
| 18 | `TestBuildIndex.test_build_index_avgdl` | Normalfall | `n_docs → 2 (+2 weitere Prüfungen)` | ✓ wie erwartet |
| 19 | `TestBuildIndex.test_build_index_casefold_merges_terms` | Normalfall | `index['dog'] → {0: 3} (+2 weitere Prüfungen)` | ✓ wie erwartet |
| 20 | `TestBuildIndex.test_build_index_does_not_mutate_corpus` | Randfall | `corpus → original` | ✓ wie erwartet |
| 21 | `TestBuildIndex.test_build_index_empty_corpus` | Randfall | `bm25.build_index([]) → ({}, {}, 0, 0.0)` | ✓ wie erwartet |
| 22 | `TestBuildIndex.test_build_index_example` | Normalfall | `index['apfel'] → {0: 2, 3: 1} (+4 weitere Prüfungen)` | ✓ wie erwartet |
| 23 | `TestBuildIndex.test_build_index_identical_documents_get_separate_ids` | Randfall | `index['dog'] → {0: 1, 1: 1} (+1 weitere Prüfungen)` | ✓ wie erwartet |
| 24 | `TestBuildIndex.test_build_index_invariants` | Normalfall | `sum((p.get(doc_id, 0) for p in index.values())) → length (+3 weitere Prüfungen)` | ✓ wie erwartet |
| 25 | `TestBuildIndex.test_build_index_joiner_variants_merge` | Normalfall | `index → {'email': {0: 3}} (+1 weitere Prüfungen)` | ✓ wie erwartet |
| 26 | `TestBuildIndex.test_build_index_only_empty_documents` | Randfall | `index → {} (+3 weitere Prüfungen)` | ✓ wie erwartet |
| 27 | `TestBuildIndex.test_build_index_stable_ids_with_empty_document` | Randfall | `doc_lengths → {0: 1, 2: 1} (+2 weitere Prüfungen)` | ✓ wie erwartet |
| 28 | `TestBuildIndex.test_build_index_term_frequency` | Normalfall | `index['dog'] → {0: 3} (+2 weitere Prüfungen)` | ✓ wie erwartet |
| 29 | `TestIDF.test_compute_idf_known_values` | Normalfall | `bm25.compute_idf(df, n_docs) → expected` | ✓ wie erwartet |
| 30 | `TestIDF.test_compute_idf_always_positive` | Normalfall | `assertGreater(bm25.compute_idf(df, n_docs), 0)` | ✓ wie erwartet |
| 31 | `TestIDF.test_compute_idf_decreases_with_df` | Normalfall | `assertGreater(rarer, more_common)` | ✓ wie erwartet |
| 32 | `TestScore.test_score_reference_values` | Normalfall | `self._score(doc_id) → expected` | ✓ wie erwartet |
| 33 | `TestScore.test_term_score_zero_frequency` | Randfall | `bm25.compute_term_score(0, 3, 10 / 3, 0.47, 1.5, 0.75) → 0.0` | ✓ wie erwartet |
| 34 | `TestScore.test_term_score_k1_zero_missing_term` | Randfall | `bm25.compute_term_score(0, 3, 10 / 3, 0.47, 0, 0.75) → 0.0` | ✓ wie erwartet |
| 35 | `TestScore.test_term_score_k1_zero_is_binary` | Randfall | `bm25.compute_term_score(2, 3, 10 / 3, 0.47, 0, 0.75) → 0.47` | ✓ wie erwartet |
| 36 | `TestScore.test_top_m_k1_zero_does_not_crash` | Randfall | `[doc_id for doc_id, _ in ranking] → [3, 0, 1]` | ✓ wie erwartet |
| 37 | `TestScore.test_score_unknown_terms` | Randfall | `self._score(0, {'xyz'}) → 0.0` | ✓ wie erwartet |
| 38 | `TestScore.test_score_unknown_term_does_not_change_score` | Randfall | `self._score(3, self.query \| {'pizza'}) → self._score(3)` | ✓ wie erwartet |
| 39 | `TestScore.test_score_empty_index` | Randfall | `bm25.compute_score(0, {}, {}, {'apfel': 1.0}, 0.0) → 0.0` | ✓ wie erwartet |
| 40 | `TestScore.test_score_unknown_doc_id` | Randfall | `self._score(99) → 0.0` | ✓ wie erwartet |
| 41 | `TestTopM.test_top_m_reference_m2` | Normalfall | `siehe Testcode` | ✓ wie erwartet |
| 42 | `TestTopM.test_top_m_m_larger_than_hits` | Randfall | `siehe Testcode` | ✓ wie erwartet |
| 43 | `TestTopM.test_top_m_zero_m` | Randfall | `self._top('apfel milch', 0) → []` | ✓ wie erwartet |
| 44 | `TestTopM.test_top_m_empty_index` | Randfall | `bm25.top_m('apfel', {}, {}, 0, 0.0, 5) → []` | ✓ wie erwartet |
| 45 | `TestTopM.test_top_m_empty_query` | Randfall | `self._top('', 5) → []` | ✓ wie erwartet |
| 46 | `TestTopM.test_top_m_only_unknown_terms` | Randfall | `self._top('pizza', 5) → []` | ✓ wie erwartet |
| 47 | `TestTopM.test_top_m_query_is_normalized` | Randfall | `self._top('APFEL, Milch!', 10) → self._top('apfel milch', 10)` | ✓ wie erwartet |
| 48 | `TestTopM.test_top_m_duplicate_query_terms_count_once` | Randfall | `self._top('apfel apfel milch milch', 10) → self._top('apfel milch', 10)` | ✓ wie erwartet |
| 49 | `TestTopM.test_top_m_no_duplicate_documents` | Randfall | `len(doc_ids) → len(set(doc_ids))` | ✓ wie erwartet |
| 50 | `TestTopM.test_top_m_tie_breaks_by_smaller_doc_id` | Randfall | `[doc_id for doc_id, _ in result] → [0, 2] (+1 weitere Prüfungen)` | ✓ wie erwartet |
| 51 | `TestTopM.test_top_m_scores_are_positive_and_descending` | Normalfall | `all((score > 0 for score in scores)) → wahr (+1 weitere Prüfungen)` | ✓ wie erwartet |

## `vector_search`

| Nr. | Test | Kategorie | Input → erwartet | Tatsächlich |
|---|---|---|---|---|
| 1 | `TestCosineSimilarity.test_cosine_different_lengths` | Fehlerfall | `vector_search.cosine_similarity([1, 2], [1, 2, 3]) → ValueError` | ✓ wie erwartet |
| 2 | `TestCosineSimilarity.test_cosine_empty_vectors` | Fehlerfall | `vector_search.cosine_similarity([], []) → ValueError` | ✓ wie erwartet |
| 3 | `TestCosineSimilarity.test_cosine_hand_calculated` | Normalfall | `vector_search.cosine_similarity([1, 2, 2], [2, 0, 1]) → 4 / (3 * 5 ** 0.5)` | ✓ wie erwartet |
| 4 | `TestCosineSimilarity.test_cosine_identical` | Randfall | `vector_search.cosine_similarity([1, 2, 3], [1, 2, 3]) → 1.0` | ✓ wie erwartet |
| 5 | `TestCosineSimilarity.test_cosine_in_range` | Normalfall | `-1.0 <= vector_search.cosine_similarity(a, b) <= 1.0 → wahr` | ✓ wie erwartet |
| 6 | `TestCosineSimilarity.test_cosine_opposite` | Randfall | `vector_search.cosine_similarity([1, 1], [-1, -1]) → -1.0` | ✓ wie erwartet |
| 7 | `TestCosineSimilarity.test_cosine_orthogonal` | Randfall | `vector_search.cosine_similarity([1, 0], [0, 1]) → 0.0` | ✓ wie erwartet |
| 8 | `TestCosineSimilarity.test_cosine_same_direction_different_length` | Normalfall | `vector_search.cosine_similarity([1, 2], [2, 4]) → 1.0` | ✓ wie erwartet |
| 9 | `TestCosineSimilarity.test_cosine_symmetric` | Normalfall | `vector_search.cosine_similarity([1, 2, 2], [2, 0, 1]) → vector_search.cosine_similarity([2, 0, 1], [1, 2, 2])` | ✓ wie erwartet |
| 10 | `TestCosineSimilarity.test_cosine_zero_vector` | Randfall | `vector_search.cosine_similarity([0, 0], [1, 2]) → 0.0` | ✓ wie erwartet |
| 11 | `TestTopK.test_top_k_does_not_change_input` | Randfall | `scores → [0.2, 0.9, 0.5]` | ✓ wie erwartet |
| 12 | `TestTopK.test_top_k_empty_scores` | Randfall | `vector_search.top_k([], 3) → []` | ✓ wie erwartet |
| 13 | `TestTopK.test_top_k_example` | Normalfall | `vector_search.top_k([0.2, 0.9, 0.5, 0.7], 2) → [(1, 0.9), (3, 0.7)]` | ✓ wie erwartet |
| 14 | `TestTopK.test_top_k_larger_than_list` | Randfall | `vector_search.top_k([0.3, 0.6], 5) → [(1, 0.6), (0, 0.3)]` | ✓ wie erwartet |
| 15 | `TestTopK.test_top_k_length_is_min_of_k_and_n` | Normalfall | `len(vector_search.top_k([0.3, 0.1, 0.9, 0.5], k)) → min(k, 4)` | ✓ wie erwartet |
| 16 | `TestTopK.test_top_k_matches_full_sort` | Normalfall | `vector_search.top_k(scores, 3) → expected` | ✓ wie erwartet |
| 17 | `TestTopK.test_top_k_negative_scores` | Randfall | `vector_search.top_k([-0.5, -0.1, -0.9], 1) → [(1, -0.1)]` | ✓ wie erwartet |
| 18 | `TestTopK.test_top_k_sorted_descending` | Normalfall | `scores → [0.8, 0.6, 0.4, 0.3, 0.1]` | ✓ wie erwartet |
| 19 | `TestTopK.test_top_k_ties_keep_lower_position` | Randfall | `vector_search.top_k([0.5, 0.5, 0.5], 2) → [(0, 0.5), (1, 0.5)]` | ✓ wie erwartet |
| 20 | `TestTopK.test_top_k_zero` | Fehlerfall | `vector_search.top_k([0.1], 0) → ValueError` | ✓ wie erwartet |
| 21 | `TestMostSimilar.test_most_similar_dimension_mismatch` | Fehlerfall | `vector_search.most_similar([1, 0], [[1, 0, 0]], 1) → ValueError` | ✓ wie erwartet |
| 22 | `TestMostSimilar.test_most_similar_example` | Normalfall | `[position for position, _ in result] → [1, 2]` | ✓ wie erwartet |
| 23 | `TestMostSimilar.test_most_similar_no_candidates` | Randfall | `vector_search.most_similar([1, 0], [], 3) → []` | ✓ wie erwartet |
| 24 | `TestMostSimilar.test_most_similar_scores` | Normalfall | `result[0][1] → 1 / 2 ** 0.5` | ✓ wie erwartet |
| 25 | `TestEmbedder.test_embed_default_input_type_is_document` | Normalfall | `embedder.calls → [(['a'], 'document')]` | ✓ wie erwartet |
| 26 | `TestEmbedder.test_embed_empty_vector` | Fehlerfall | `FakeEmbedder([[]]).embed(['a']) → vector_search.EmbeddingError` | ✓ wie erwartet |
| 27 | `TestEmbedder.test_embed_empty_without_request` | Randfall | `embedder.embed([]) → [] (+1 weitere Prüfungen)` | ✓ wie erwartet |
| 28 | `TestEmbedder.test_embed_invalid_input_type` | Fehlerfall | `FakeEmbedder([[1.0]]).embed(['a'], 'passage') → ValueError` | ✓ wie erwartet |
| 29 | `TestEmbedder.test_embed_passes_query_input_type` | Normalfall | `embedder.calls → [(['a'], 'query')]` | ✓ wie erwartet |
| 30 | `TestEmbedder.test_embed_returns_vectors` | Normalfall | `embedder.embed(['a', 'b']) → [[1.0, 0.0], [0.0, 1.0]]` | ✓ wie erwartet |
| 31 | `TestEmbedder.test_embed_unequal_lengths` | Fehlerfall | `FakeEmbedder([[1.0, 0.0], [1.0]]).embed(['a', 'b']) → vector_search.EmbeddingError` | ✓ wie erwartet |
| 32 | `TestEmbedder.test_embed_wrong_count` | Fehlerfall | `FakeEmbedder([[1.0, 0.0]]).embed(['a', 'b']) → vector_search.EmbeddingError` | ✓ wie erwartet |
| 33 | `TestEmbedder.test_embedder_is_abstract` | Fehlerfall | `vector_search.Embedder() → TypeError` | ✓ wie erwartet |
| 34 | `TestMmrSelect.test_mmr_does_not_mutate_input` | Randfall | `(relevance, vectors) → ([1.0, 0.95, 0.6], DUPLICATE_VECTORS)` | ✓ wie erwartet |
| 35 | `TestMmrSelect.test_mmr_first_pick_is_most_relevant` | Normalfall | `vector_search.mmr_select([0.2, 0.9, 0.5], DUPLICATE_VECTORS, 1, 0.5) → [1]` | ✓ wie erwartet |
| 36 | `TestMmrSelect.test_mmr_k_larger_than_candidates` | Randfall | `sorted(vector_search.mmr_select([1.0, 0.5, 0.2], DUPLICATE_VECTORS, 10)) → [0, 1, 2]` | ✓ wie erwartet |
| 37 | `TestMmrSelect.test_mmr_k_zero` | Fehlerfall | `vector_search.mmr_select([1.0], [[1.0]], 0) → ValueError` | ✓ wie erwartet |
| 38 | `TestMmrSelect.test_mmr_lambda_one_is_pure_relevance` | Randfall | `vector_search.mmr_select([1.0, 0.95, 0.6], DUPLICATE_VECTORS, 2, 1.0) → [0, 1]` | ✓ wie erwartet |
| 39 | `TestMmrSelect.test_mmr_lambda_out_of_range` | Fehlerfall | `vector_search.mmr_select([1.0], [[1.0]], 1, 1.5) → ValueError` | ✓ wie erwartet |
| 40 | `TestMmrSelect.test_mmr_length_mismatch` | Fehlerfall | `vector_search.mmr_select([1.0], DUPLICATE_VECTORS, 1) → ValueError` | ✓ wie erwartet |
| 41 | `TestMmrSelect.test_mmr_no_candidates` | Randfall | `vector_search.mmr_select([], [], 3) → []` | ✓ wie erwartet |
| 42 | `TestMmrSelect.test_mmr_selects_each_position_once` | Normalfall | `len(selected) → len(set(selected))` | ✓ wie erwartet |
| 43 | `TestMmrSelect.test_mmr_skips_near_duplicate` | Randfall | `vector_search.mmr_select([1.0, 0.95, 0.6], DUPLICATE_VECTORS, 2, 0.5) → [0, 2]` | ✓ wie erwartet |
| 44 | `TestMmrSelect.test_mmr_ties_keep_lower_position` | Randfall | `vector_search.mmr_select([0.5, 0.5], [[1.0, 0.0], [0.0, 1.0]], 1) → [0]` | ✓ wie erwartet |
| 45 | `TestVoyageEmbedder.test_voyage_bad_response_format` | Fehlerfall | `embedder.embed(['a']) → vector_search.EmbeddingError` | ✓ wie erwartet |
| 46 | `TestVoyageEmbedder.test_voyage_http_error` | Fehlerfall | `'401'(…) → vector_search.EmbeddingError (+1 weitere Prüfungen)` | ✓ wie erwartet |
| 47 | `TestVoyageEmbedder.test_voyage_key_from_environment` | Normalfall | `vector_search.VoyageEmbedder().api_key → 'env-key'` | ✓ wie erwartet |
| 48 | `TestVoyageEmbedder.test_voyage_missing_key` | Fehlerfall | `vector_search.VoyageEmbedder() → vector_search.EmbeddingError` | ✓ wie erwartet |
| 49 | `TestVoyageEmbedder.test_voyage_network_error` | Fehlerfall | `embedder.embed(['a']) → vector_search.EmbeddingError` | ✓ wie erwartet |
| 50 | `TestVoyageEmbedder.test_voyage_orders_by_index` | Normalfall | `embedder.embed(['a', 'b']) → [[1.0, 0.0], [0.0, 1.0]]` | ✓ wie erwartet |
| 51 | `TestVoyageEmbedder.test_voyage_request` | Normalfall | `post.calls → [(vector_search.VOYAGE_API_URL, {'input': ['frage'], 'model': 'voyage-4-lite', 'input_type': 'query'}, {'Authorization': 'Bear…` | ✓ wie erwartet |
| 52 | `TestVoyageEmbedder.test_voyage_returns_vectors` | Normalfall | `embedder.embed(['a', 'b']) → [[1.0, 0.0], [0.0, 1.0]]` | ✓ wie erwartet |
| 53 | `TestVoyageEmbedder.test_voyage_timeout` | Fehlerfall | `embedder.embed(['a']) → vector_search.EmbeddingError` | ✓ wie erwartet |

## `ranking`

| Nr. | Test | Kategorie | Input → erwartet | Tatsächlich |
|---|---|---|---|---|
| 1 | `TestReciprocalRankFusion.test_rrf_candidate_in_both_lists_wins` | Normalfall | `result[0][0] → 3` | ✓ wie erwartet |
| 2 | `TestReciprocalRankFusion.test_rrf_default_constant` | Normalfall | `result[0][1] → 1 / 61` | ✓ wie erwartet |
| 3 | `TestReciprocalRankFusion.test_rrf_does_not_mutate_input` | Randfall | `rankings → [[1, 2], [2, 3]]` | ✓ wie erwartet |
| 4 | `TestReciprocalRankFusion.test_rrf_hand_calculated` | Normalfall | `[candidate_id for candidate_id, _ in result] → [2, 1, 3] (+1 weitere Prüfungen)` | ✓ wie erwartet |
| 5 | `TestReciprocalRankFusion.test_rrf_negative_constant` | Fehlerfall | `ranking.reciprocal_rank_fusion([[1]], k_rrf=-1) → ValueError` | ✓ wie erwartet |
| 6 | `TestReciprocalRankFusion.test_rrf_no_rankings` | Randfall | `ranking.reciprocal_rank_fusion([]) → []` | ✓ wie erwartet |
| 7 | `TestReciprocalRankFusion.test_rrf_one_empty_ranking` | Randfall | `[candidate_id for candidate_id, _ in result] → [4, 2]` | ✓ wie erwartet |
| 8 | `TestReciprocalRankFusion.test_rrf_scores_positive_and_bounded` | Normalfall | `all((0 < score <= 3 / 61 for _, score in result)) → wahr` | ✓ wie erwartet |
| 9 | `TestReciprocalRankFusion.test_rrf_single_ranking_keeps_order` | Randfall | `[candidate_id for candidate_id, _ in result] → [5, 3, 9]` | ✓ wie erwartet |
| 10 | `TestReciprocalRankFusion.test_rrf_ties_keep_lower_id` | Randfall | `[candidate_id for candidate_id, _ in result] → [1, 2]` | ✓ wie erwartet |
| 11 | `TestReciprocalRankFusion.test_rrf_top_in_all_lists_wins` | Normalfall | `result[0][0] → 4` | ✓ wie erwartet |
| 12 | `TestNormalizeScores.test_normalize_all_equal` | Randfall | `ranking.normalize_scores([0.3, 0.3]) → [1.0, 1.0]` | ✓ wie erwartet |
| 13 | `TestNormalizeScores.test_normalize_does_not_mutate_input` | Randfall | `scores → [2.0, 4.0, 3.0]` | ✓ wie erwartet |
| 14 | `TestNormalizeScores.test_normalize_empty` | Randfall | `ranking.normalize_scores([]) → []` | ✓ wie erwartet |
| 15 | `TestNormalizeScores.test_normalize_example` | Normalfall | `ranking.normalize_scores([2.0, 4.0, 3.0]) → [0.0, 1.0, 0.5]` | ✓ wie erwartet |
| 16 | `TestNormalizeScores.test_normalize_min_zero_max_one` | Normalfall | `(min(result), max(result)) → (0.0, 1.0)` | ✓ wie erwartet |
| 17 | `TestNormalizeScores.test_normalize_negative_values` | Randfall | `ranking.normalize_scores([-1.0, 1.0]) → [0.0, 1.0]` | ✓ wie erwartet |

## `pipeline`

| Nr. | Test | Kategorie | Input → erwartet | Tatsächlich |
|---|---|---|---|---|
| 1 | `TestResearchBm25Only.test_research_blank_keywords` | Fehlerfall | `pipeline.research([' ', ''], 3, source) → ValueError (+1 weitere Prüfungen)` | ✓ wie erwartet |
| 2 | `TestResearchBm25Only.test_research_k_zero` | Fehlerfall | `pipeline.research(['uml'], 0, FakeSource([UML])) → ValueError` | ✓ wie erwartet |
| 3 | `TestResearchBm25Only.test_research_long_document_gives_several_chunks` | Randfall | `assertGreater(len(result.hits), 1) (+1 weitere Prüfungen)` | ✓ wie erwartet |
| 4 | `TestResearchBm25Only.test_research_matching_document_first` | Normalfall | `result.hits[0].document.id → '1'` | ✓ wie erwartet |
| 5 | `TestResearchBm25Only.test_research_no_documents` | Randfall | `(result.hits, result.warnings) → ((), ('Keine Treffer',))` | ✓ wie erwartet |
| 6 | `TestResearchBm25Only.test_research_documents_without_text` | Randfall | `(result.hits, result.warnings) → ((), ('Keine verwertbaren Quellen',))` | ✓ wie erwartet |
| 7 | `TestResearchBm25Only.test_research_no_keyword_in_chunks` | Randfall | `(result.hits, result.warnings) → ((), ('Kein Chunk enthält ein Schlagwort',))` | ✓ wie erwartet |
| 8 | `TestResearchBm25Only.test_research_only_matching_documents` | Randfall | `sorted((hit.document.id for hit in result.hits)) → ['1', '3']` | ✓ wie erwartet |
| 9 | `TestResearchBm25Only.test_research_passes_filter_to_source` | Normalfall | `assertIs(source.calls[0][2], search_filter)` | ✓ wie erwartet |
| 10 | `TestResearchBm25Only.test_research_passes_normalized_keywords_and_limit` | Normalfall | `source.calls → [(['UML', 'class'], 7, None)]` | ✓ wie erwartet |
| 11 | `TestResearchBm25Only.test_research_respects_k` | Normalfall | `len(result.hits) → 1` | ✓ wie erwartet |
| 12 | `TestResearchBm25Only.test_research_scores_descending` | Normalfall | `scores → sorted(scores, reverse=True)` | ✓ wie erwartet |
| 13 | `TestResearchBm25Only.test_research_source_error_propagates` | Fehlerfall | `pipeline.research(['uml'], 3, FakeSource(error=SourceError('down'))) → SourceError` | ✓ wie erwartet |
| 14 | `TestResultToDict.test_hit_to_dict` | Normalfall | `{key: value for key, value in hit.to_dict().items() if key != 'score'} → {'document_id': '1', 'title': 'UML class diagrams', 'authors': ['A…` | ✓ wie erwartet |
| 15 | `TestResultToDict.test_result_to_dict_empty` | Randfall | `pipeline.research(['uml'], 3, FakeSource([])).to_dict() → {'hits': [], 'warnings': ['Keine Treffer']}` | ✓ wie erwartet |
| 16 | `TestResearchHybrid.test_hybrid_embedding_error_falls_back_to_bm25` | Fehlerfall | `sorted((hit.document.id for hit in result.hits)) → ['1', '3'] (+1 weitere Prüfungen)` | ✓ wie erwartet |
| 17 | `TestResearchHybrid.test_hybrid_embeds_query_and_bm25_candidates` | Normalfall | `(query_texts, query_type) → (['uml'], 'query') (+1 weitere Prüfungen)` | ✓ wie erwartet |
| 18 | `TestResearchHybrid.test_hybrid_matching_document_first` | Normalfall | `result.hits[0].document.id → '1'` | ✓ wie erwartet |
| 19 | `TestResearchHybrid.test_hybrid_no_keyword_hit_uses_all_chunks` | Randfall | `len(embedder.calls[1][0]) → 2 (+1 weitere Prüfungen)` | ✓ wie erwartet |
| 20 | `TestResearchHybrid.test_hybrid_question_is_embedded_instead_of_keywords` | Normalfall | `embedder.calls[0][0] → ['How do class diagrams work?']` | ✓ wie erwartet |
| 21 | `TestResearchHybrid.test_hybrid_respects_k` | Normalfall | `len(result.hits) → 1` | ✓ wie erwartet |
| 22 | `TestResearchHybrid.test_hybrid_selects_distinct_chunks` | Normalfall | `len(keys) → len(set(keys))` | ✓ wie erwartet |
| 23 | `TestSourceNotes.test_source_notes_reach_warnings` | Normalfall | `result.warnings → ('Dokumente aus dem Cache',)` | ✓ wie erwartet |
| 24 | `TestSourceNotes.test_source_notes_before_pipeline_warnings` | Normalfall | `result.warnings → ('Dokumente aus dem Cache', 'Keine Treffer')` | ✓ wie erwartet |
| 25 | `TestSourceNotes.test_plain_source_has_no_notes` | Randfall | `FakeSource([UML]).notes → ()` | ✓ wie erwartet |

## `mcp_server`

| Nr. | Test | Kategorie | Input → erwartet | Tatsächlich |
|---|---|---|---|---|
| 1 | `TestMcpServer.test_tool_blank_keywords` | Fehlerfall | `result.is_error → wahr` | ✓ wie erwartet |
| 2 | `TestMcpServer.test_tool_default_k_is_five` | Normalfall | `len(result.structured_content['hits']) → 5` | ✓ wie erwartet |
| 3 | `TestMcpServer.test_tool_filter_reaches_source` | Normalfall | `source.filters[0] → SearchFilter(published_from=date(2023, 1, 1), peer_reviewed_only=True)` | ✓ wie erwartet |
| 4 | `TestMcpServer.test_tool_invalid_date` | Fehlerfall | `result.is_error → wahr` | ✓ wie erwartet |
| 5 | `TestMcpServer.test_tool_is_listed_read_only` | Normalfall | `[tool.name for tool in tools] → ['research_papers'] (+1 weitere Prüfungen)` | ✓ wie erwartet |
| 6 | `TestMcpServer.test_tool_k_too_large` | Fehlerfall | `result.is_error → wahr` | ✓ wie erwartet |
| 7 | `TestMcpServer.test_tool_k_zero` | Fehlerfall | `result.is_error → wahr` | ✓ wie erwartet |
| 8 | `TestMcpServer.test_tool_returns_hits` | Normalfall | `(hit['document_id'], hit['title'], hit['url']) → ('1', 'UML class diagrams', 'https://arxiv.org/abs/1')` | ✓ wie erwartet |
| 9 | `TestMcpServer.test_tool_returns_warnings` | Normalfall | `result.structured_content → {'hits': [], 'warnings': ['Keine Treffer']}` | ✓ wie erwartet |
| 10 | `TestMcpServer.test_tool_source_error` | Fehlerfall | `result.is_error → wahr (+1 weitere Prüfungen)` | ✓ wie erwartet |
| 11 | `TestMcpServer.test_tool_uses_embedder_and_question` | Normalfall | `embedder.calls[0] → (['Was sind Klassendiagramme?'], 'query')` | ✓ wie erwartet |
| 12 | `TestParseDate.test_parse_date_empty` | Randfall | `parse_date(' ') → None` | ✓ wie erwartet |
| 13 | `TestParseDate.test_parse_date_full` | Normalfall | `parse_date('2023-05-17') → date(2023, 5, 17)` | ✓ wie erwartet |
| 14 | `TestParseDate.test_parse_date_invalid` | Fehlerfall | `parse_date('17.05.2023') → ValueError` | ✓ wie erwartet |
| 15 | `TestParseDate.test_parse_date_year` | Normalfall | `parse_date('2023') → date(2023, 1, 1)` | ✓ wie erwartet |
| 16 | `TestDefaultEmbedder.test_default_embedder_with_key` | Normalfall | `default_embedder() → nicht None` | ✓ wie erwartet |
| 17 | `TestDefaultEmbedder.test_default_embedder_without_key` | Fehlerfall | `default_embedder() → None` | ✓ wie erwartet |
| 18 | `TestDefaultSource.test_default_source_is_cached_arxiv` | Normalfall | `assertIsInstance(source, CachedSource) (+2 weitere Prüfungen)` | ✓ wie erwartet |

## `storage`

| Nr. | Test | Kategorie | Input → erwartet | Tatsächlich |
|---|---|---|---|---|
| 1 | `TestStorageConfig.test_database_url_default` | Normalfall | `database_url() → DEFAULT_DATABASE_URL` | ✓ wie erwartet |
| 2 | `TestStorageConfig.test_database_url_from_environment` | Normalfall | `database_url() → 'postgresql://server/db'` | ✓ wie erwartet |
| 3 | `TestStorageConfig.test_load_sql_existing_file` | Normalfall | `load_sql('query', Path(directory)) → 'SELECT 1;'` | ✓ wie erwartet |
| 4 | `TestStorageConfig.test_load_sql_missing_file` | Fehlerfall | `'schema.sql'(…) → StorageError (+1 weitere Prüfungen)` | ✓ wie erwartet |
| 5 | `TestStorageConfig.test_connect_unreachable` | Fehlerfall | `connect('postgresql://127.0.0.1:1/nothing?connect_timeout=1') → StorageError` | ✓ wie erwartet |
| 6 | `TestStorageDatabase.test_apply_schema_runs_file` | Normalfall | `siehe Testcode` | ✓ wie erwartet |
| 7 | `TestStorageDatabase.test_connect_test_database` | Normalfall | `connection.execute('SELECT 1').fetchone() → (1,)` | ✓ wie erwartet |
| 8 | `TestStorageHelpers.test_normalize_key_lowercase_and_sorted` | Normalfall | `normalize_key(['UML', 'bm25', 'Class Diagram']) → ['bm25', 'class diagram', 'uml']` | ✓ wie erwartet |
| 9 | `TestStorageHelpers.test_normalize_key_same_result_for_different_order` | Normalfall | `normalize_key(['B', 'a']) → normalize_key(['A', 'b'])` | ✓ wie erwartet |
| 10 | `TestStorageHelpers.test_normalize_key_empty` | Randfall | `normalize_key([]) → []` | ✓ wie erwartet |
| 11 | `TestStorageHelpers.test_document_params_empty_strings_become_null` | Randfall | `params['doi'] → None (+1 weitere Prüfungen)` | ✓ wie erwartet |
| 12 | `TestStorageHelpers.test_document_params_fields` | Normalfall | `params['source_id'] → '2401.00001' (+4 weitere Prüfungen)` | ✓ wie erwartet |
| 13 | `TestStorageHelpers.test_save_embedding_rejects_empty_vector` | Fehlerfall | `save_embedding(None, 1, 0, 'voyage-4', []) → ValueError` | ✓ wie erwartet |
| 14 | `TestStorageRepository.test_save_document_returns_id` | Normalfall | `assertIsInstance(save_document(self.connection, make_document(), 200, 40), int)` | ✓ wie erwartet |
| 15 | `TestStorageRepository.test_save_document_twice_keeps_id_and_updates` | Randfall | `first → second (+1 weitere Prüfungen)` | ✓ wie erwartet |
| 16 | `TestStorageRepository.test_save_document_full_text_without_text_fails` | Fehlerfall | `'documents_invalid_full_text'(…) → StorageError (+1 weitere Prüfungen)` | ✓ wie erwartet |
| 17 | `TestStorageRepository.test_save_chunks_and_find_in_order` | Normalfall | `find_chunks(self.connection, [document_id]) → [(document_id, 0, 'eins'), (document_id, 1, 'zwei'), (document_id, 2, 'drei')]` | ✓ wie erwartet |
| 18 | `TestStorageRepository.test_save_chunks_replaces_old_chunks` | Randfall | `find_chunks(self.connection, [document_id]) → [(document_id, 0, 'neu')]` | ✓ wie erwartet |
| 19 | `TestStorageRepository.test_save_chunks_empty_text_fails` | Fehlerfall | `'chunks_invalid_text'(…) → StorageError (+1 weitere Prüfungen)` | ✓ wie erwartet |
| 20 | `TestStorageRepository.test_find_chunks_empty_ids` | Randfall | `find_chunks(self.connection, []) → []` | ✓ wie erwartet |
| 21 | `TestStorageRepository.test_embeddings_round_trip_and_duplicate_ignored` | Randfall | `find_embeddings(self.connection, [document_id], 'voyage-4') → {(document_id, 0): [0.5, 0.25]}` | ✓ wie erwartet |
| 22 | `TestStorageRepository.test_find_embeddings_other_model_empty` | Randfall | `find_embeddings(self.connection, [document_id], 'anderes-modell') → {}` | ✓ wie erwartet |
| 23 | `TestStorageRepository.test_save_embedding_unknown_chunk_fails` | Fehlerfall | `save_embedding(self.connection, document_id, 7, 'voyage-4', [0.5]) → StorageError` | ✓ wie erwartet |
| 24 | `TestStorageRepository.test_cached_search_found_with_other_order_and_case` | Randfall | `find_cached_search(self.connection, ['bm25', 'uml'], SearchFilter()) → [second, first]` | ✓ wie erwartet |
| 25 | `TestStorageRepository.test_cached_search_other_filter_not_found` | Randfall | `find_cached_search(self.connection, ['uml'], SearchFilter(peer_reviewed_only=True)) → []` | ✓ wie erwartet |
| 26 | `TestStorageRepository.test_cached_search_too_old_not_found` | Randfall | `find_cached_search(self.connection, ['uml'], SearchFilter()) → []` | ✓ wie erwartet |
| 27 | `TestStorageRepository.test_save_run_and_rate` | Normalfall | `found → wahr` | ✓ wie erwartet |
| 28 | `TestStorageRepository.test_rate_unknown_run_fails` | Fehlerfall | `rate_run(self.connection, -1, True) → StorageError` | ✓ wie erwartet |
| 29 | `TestStorageRepository.test_save_run_invalid_variant_fails` | Fehlerfall | `'runs_invalid_variant'(…) → StorageError (+1 weitere Prüfungen)` | ✓ wie erwartet |
| 30 | `TestStorageRepository.test_kpi_by_variant_floats_and_unrated_none` | Randfall | `kpi['bm25']['runs'] → 2 (+4 weitere Prüfungen)` | ✓ wie erwartet |
| 31 | `TestFindDocuments.test_find_documents_round_trip` | Normalfall | `stored → [StoredDocument(document_id, original, 'abstract', None, 200, 40)]` | ✓ wie erwartet |
| 32 | `TestFindDocuments.test_find_documents_null_becomes_empty_string` | Randfall | `(document.doi, document.journal_ref) → ('', '')` | ✓ wie erwartet |
| 33 | `TestFindDocuments.test_find_documents_keeps_given_order` | Normalfall | `ids → [second, first]` | ✓ wie erwartet |
| 34 | `TestFindDocuments.test_find_documents_unknown_id_skipped` | Randfall | `[stored.id for stored in find_documents(self.connection, [-1, document_id])] → [document_id]` | ✓ wie erwartet |
| 35 | `TestFindDocuments.test_find_documents_empty_ids` | Randfall | `find_documents(self.connection, []) → []` | ✓ wie erwartet |

## `cache`

| Nr. | Test | Kategorie | Input → erwartet | Tatsächlich |
|---|---|---|---|---|
| 1 | `TestCachedSourceWithoutDatabase.test_is_a_source` | Normalfall | `assertIsInstance(CachedSource(FakeSource(), connect=unreachable), Source)` | ✓ wie erwartet |
| 2 | `TestCachedSourceWithoutDatabase.test_database_unreachable_falls_back_to_source` | Fehlerfall | `[document.id for document in documents] → ['9999.00001', '9999.00002'] (+2 weitere Prüfungen)` | ✓ wie erwartet |
| 3 | `TestCachedSourceWithoutDatabase.test_source_error_propagates` | Fehlerfall | `cached.search([KEYWORD], 2) → SourceError` | ✓ wie erwartet |
| 4 | `TestCachedSourceWithoutDatabase.test_default_notes_empty` | Randfall | `CachedSource(FakeSource(), connect=unreachable).notes → ()` | ✓ wie erwartet |
| 5 | `TestCachedSourceWithDatabase.test_miss_asks_source_and_saves` | Normalfall | `self.inner.calls → 1 (+3 weitere Prüfungen)` | ✓ wie erwartet |
| 6 | `TestCachedSourceWithDatabase.test_hit_skips_source_and_keeps_order` | Normalfall | `self.inner.calls → 1 (+2 weitere Prüfungen)` | ✓ wie erwartet |
| 7 | `TestCachedSourceWithDatabase.test_more_results_than_cached_asks_source_again` | Normalfall | `self.inner.calls → 2 (+1 weitere Prüfungen)` | ✓ wie erwartet |
| 8 | `TestCachedSourceWithDatabase.test_fewer_results_than_cached_uses_cache` | Normalfall | `self.inner.calls → 1 (+1 weitere Prüfungen)` | ✓ wie erwartet |
| 9 | `TestCachedSourceWithDatabase.test_other_filter_asks_source_again` | Randfall | `self.inner.calls → 2` | ✓ wie erwartet |
| 10 | `TestCachedSourceWithDatabase.test_save_failure_still_returns_documents` | Normalfall | `len(documents) → 2 (+1 weitere Prüfungen)` | ✓ wie erwartet |
| 11 | `TestCachedSourceWithDatabase.test_notes_reset_between_calls` | Normalfall | `self.cached.notes → ()` | ✓ wie erwartet |
| 12 | `TestCachedSourceWithDatabase.test_source_without_documents_is_no_cache_error` | Fehlerfall | `cached.search([KEYWORD], 2) → [] (+1 weitere Prüfungen)` | ✓ wie erwartet |
