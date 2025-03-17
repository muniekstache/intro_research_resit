# intro_research_resit
Final project for Introduction Research Methods

## General Information (Abstract)
This paper investigates whether Science
Fiction texts exhibit a higher frequency
of neologisms compared to Romance lit-
erature. Employing exclusion dictionary
architecture (EDA) alongside established
natural language processing (NLP) tech-
niques provided by SpaCy, we systemat-
ically identify and validate lexical neolo-
gisms within texts from the early 20th cen-
tury. By analyzing selected novels from
both genres, we anticipate that science
fiction authors utilize neologisms more
frequently, reflecting genre-specific needs
to articulate novel concepts and futuristic
contexts. Our methodological approach
includes detailed data preprocessing, can-
didate neologism identification, and man-
ual validation steps through Google’s n-
gram viewer. Results indicate a substan-
tially higher frequency of neologisms in
science fiction (0.44%) compared to ro-
mance novels (0.085%), supporting the
hypothesis that lexical creativity is more
prevalent in science fiction.

## References

**Jamet:Terry:2018**  
**Editors:** Denis Jamet and Adeline Terry  
**Year:** 2018  
**Title:** Lexical and Semantic Neology in English  
**Publisher:** Lexis, Volume 12  
**URL:** <https://journals.openedition.org/lexis/2521>  
**Rationale:** Cited to illustrate the conceptual ambiguity surrounding “neology” (e.g., treating certain items as neologisms vs. nonce formations)

---

**poix:2018**  
**Author:** Poix, Cécile  
**Year:** 2018  
**Title:** Neology in children’s literature: A typology of occasionalisms  
**Journal:** Lexis, Volume 12  
**URL:** <https://journals.openedition.org/lexis/2111>  
**Rationale:** This paper looks at how new words show up in children’s books. We referenced it because it shows how imaginative writing (like science fiction) encourages authors to invent new words to describe unique ideas or worlds

---

**pruvost2003neologismes**  
**Authors:** Pruvost, J. and Sablayrolles, JF  
**Year:** 2003  
**Title:** Les n{\'e}ologismes, n 3674  
**Journal:** Paris, «Que sais-je», p.17  
**URL:** <https://journals-openedition-org.proxy-ub.rug.nl/studifrancesi/38567>  
**Rationale:** They distinguish between new words (lexical neology) and new meanings of existing words (semantic neology). We turned to this work to keep our focus on genuinely new word forms rather than just new meanings

---

**cartier2017neoveille**  
**Author:** Cartier, Emmanuel  
**Year:** 2017  
**Title:** Neoveille, a web platform for neologism tracking  
**In:** Proceedings of the Software Demonstrations of the 15th Conference of the European Chapter of the Association for Computational Linguistics, pp.95–98  
**URL:** <https://aclanthology.org/E17-3024/>  
**Rationale:** Used as an example of an exclusion dictionary architecture (Neoveille)

---

**zalmout2019unsupervised**  
**Authors:** Zalmout, Nasser and Thadani, Kapil and Pappu, Aasish  
**Year:** 2019  
**Title:** Unsupervised neologism normalization using embedding space mapping  
**In:** Proceedings of the 5th Workshop on Noisy User-generated Text (W-NUT 2019), pp.425–430  
**URL:** <https://aclanthology.org/D19-5555/>  
**Rationale:** This study combines word filtering with language processing tools (like spaCy) to cut down on mistaken hits (e.g., named entities). We drew from their approach to refine our own process for identifying true neologisms


## Research Question and Hypothesis

**Research Question:**  
Do the texts of Science Fiction authors contain more neologisms than those of Romance authors?

**Hypothesis:**  
Science Fiction authors make more frequent use of neologisms than Romance authors.

## Method

### Loading Texts
**Scripts:** `load_novel.py`  
**Input Directory/File:** `Gutenberg-dammit-files-v002.zip`  
**Output Directory/Files:** `data/raw/romance/*.txt` and `data/raw/scifi/*.txt`  

| Genre   | Title                 | Author                   | Year |
|---------|-----------------------|--------------------------|------|
| Sci-Fi  | *The War in the Air*  | H. G. Wells             | 1908 |
| Sci-Fi  | *A Princess of Mars*  | Edgar Rice Burroughs    | 1912 |
| Sci-Fi  | *The Night Land*      | William Hope Hodgson    | 1912 |
| Romance | *Three Weeks*         | Elinor Glyn             | 1907 |
| Romance | *The Shuttle*         | Frances Hodgson Burnett | 1907 |
| Romance | *The Rosary*          | Florence L. Barclay     | 1909 |

To ensure a manageable and meaningful analysis, three influential books per genre were selected, each written by a different author and published within a similar time frame. This approach was chosen because:

- It allows for filtering words using a historical dictionary.
- It aligns with the project’s scope constraints.
- Influential books provide strong representations of their genres.
- Avoiding multiple works by the same author helps reduce author-specific bias.

We source these books from Project Gutenberg via the “Gutenberg-dammit” GitHub repository. The “Gutenberg-dammit” resource is particularly convenient because it provides plain-text versions of the novels (most boilerplate removed) and enables easy filtering by metadata.

---

### Creation of Filter Dictionaries
**Scripts:** `filter_dict_creator.py` and `gutendicter.py`  
**Input:** `data/chambersstwentie00daviiala_djvu.txt` and `enberg-dammit-files-v002.zip`  
**Output:** `data/dicts/extracted_chamber_entries.json` and `data/dicts/corpus_filter_dictionary.json`

To identify potential neologisms, individual tokens from the selected Romance and Science Fiction novels are compared against two historical dictionaries:

1. **Chambers Twentieth Century Dictionary (1901)**  
   - Source: www.archive.org (OCR-scanned text).  
   - We extracted 42,392 individual entries by detecting patterns (e.g., alphabetical ordering) from the scanned file, then saved them in JSON format.

2. **Corpus-Derived Dictionary**  
   - Built by scanning all English Gutenberg texts whose authors died before 1900 (based on metadata).  
   - We used fast regex-based token extraction rather than spaCy for this large corpus.  
   - This yielded 1,611,708 unique entries in JSON format.

These two dictionaries collectively form the “exclusion dictionaries” used later to filter out words that are already attested in older English usage.

---

### Preprocessing
**Script:** `preprocessing.py`  
**Input:** `data/raw/romance/*.txt` and `data/raw/scifi/*.txt`  
**Output:**  
- `data/processed/romance/*.json`  
- `data/processed/scifi/*.json`  
- `data/filtered/*.json`

Even after the initial Gutenberg-dammit cleanup, some metadata remains in the texts (e.g., contents sections, chapter headings). We remove these leftovers, as well as certain artifacts that would interfere with tokenization. Next:

1. **Tokenization and NLP Enrichment:**  
   - Each novel is processed using spaCy’s `en_core_web_trf` model.  
   - Every token is annotated with lemma, part-of-speech (POS), named entity recognition (NER) tags, etc.

2. **Filtering and Unique Token Dictionaries:**  
   - From each novel’s processed output, we build dictionaries of unique lowercased tokens.  
   - We exclude tokens tagged as punctuation, stop words, named entities, or POS types like `PROPN`, `PUNCT`, `X`, and `SPACE`.  
   - We track the total count of unique tokens for each genre, which will later help us normalize neologism frequencies.

---

### Detecting Neologism Candidates
**Script:** `Neo_classifier.py`  
**Input:**  
- `data/filtered/romance_filtered.json` + `data/filtered/scifi_filtered.json`  
- `data/dicts/extracted_chamber_entries.json` + `data/dicts/corpus_filter_dictionary.json`  
**Output:**  
- `data/candidates/romance/*.json`  
- `data/candidates/scifi/*.json`

Following the “exclusion dictionary architecture” (Cartier, 2017), we compare each token against both dictionaries. Any token found in either dictionary is removed from the list of potential neologisms. However, because neologisms often arise through new prefixes or suffixes, we also include tokens in which only the lemma (rather than the raw token form) is in the dictionary. This process yields:

- **Romance:** 63 candidate neologisms  
- **Science Fiction:** 187 candidate neologisms

---

### Manual Evaluation
**Script:** `neo_validator.py`  
**Input:**  
- `data/candidates/romance/*.json`  
- `data/candidates/scifi/*.json`  
**Output:**  
- `data/validated/romance/*.json`  
- `data/validated/scifi/*.json`

Given the limited scope (six novels total), we manually inspect all candidate neologisms. A custom interface presents each candidate’s metadata—such as raw form, lemma, POS, and frequency—along with a link to Google’s Ngram Viewer auto-filled with that token. A candidate is confirmed as a true neologism if:

- It shows minimal or no usage before 1900 but spikes thereafter, **or**  
- It is absent from Google’s Ngram Viewer without being a typographical error.

After manual validation, we end up with:

- **12 true Romance neologisms** (out of 63 candidates)  
- **59 true Science Fiction neologisms** (out of 187 candidates)

---

### Final Neologism Counts and Normalization
To account for differences in total unique tokens, we compute:

- **Romance:** 12 neologisms out of 14,181 unique tokens  
  - ≈ 0.085%  
- **Science Fiction:** 59 neologisms out of 13,502 unique tokens  
  - ≈ 0.44%

This final normalization confirms a significantly higher proportion of new words in Science Fiction than in Romance texts.

## Tools

- **Python:**  
  - Data extraction and cleaning: 'gutenberg-dammit', 'regex'
  - Tokenization, NER, POS, lemmatization: 'NLTK', 'spaCy', 'en_core_web_trf'
  - Dictionary and corpus lookups: archive.com chambers early 20th century dictionary 1901 and gutenberg-dammit
  - Keeping track of script progress to mantain sanity: 'tqdm'