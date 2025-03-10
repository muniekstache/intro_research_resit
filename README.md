# FinalProject_iwo
Final project for Introduction Research Methods

## General Information (Abstract)
I will save the abstract for when my final project is finished as recommended in class.
For now I will paste the template that will be used to create the abstract:

Everyone agrees that this issue is really important. But we do not know much about this specific question, although it matters a great deal, for these reasons. We approach the problem from this perspective. Our research design focuses on these cases and relies on these data, which analyze using this method. Results show what we have learned about the question. They have these broader implications

## Background Information
Existing research has explored the introduction and frequency of new words (neologisms) in literature, but direct comparisons between genres remain limited.

**Pyo, J. (2023). Detection and Replacement of Neologisms for Translation. The Cooper Union for the Advancement of Science and Art.**

Pyo (2023) highlights a common problem in neologism detection, namely distinguishing between named entities and neologisms. Pyo recommends that future work leverage spaCy's Named Entity Recognition capabilities instead of relying solely on a pre-defined list of named entities, as implemented in his study.

**Kerremans, D. & Prokić, J. (2018). Mining the Web for New Words: Semi-Automatic Neologism Identification with the NeoCrawler. Anglia, 136(2), 239-268. https://doi.org/10.1515/ang-2018-0032**

Kerremans and Prokić (2018) employ a dictionary-based matching procedure to identify potential neologisms, which directly influenced the development of this project's methodology.

## Research Question and Hypothesis

**Research Question:**  
Do the texts of Science Fiction authors contain more neologisms than those of Romance authors?

**Hypothesis:**  
Science Fiction authors make more frequent use of neologisms than Romance authors.

## Method

### 1. Data Collection and Preprocessing

**Text Selection:**  
- Source texts from Project Gutenberg.  
- Identify a set of works clearly categorized as “Science Fiction” and another set as “Romance” using the metadata from Project Gutenberg.
- Attempt to select texts from a similar historical period or at least record publication years for later analysis.

**Cleaning and Tokenization:**  
- Convert all downloaded texts into plain text format.  
- Remove Project Gutenberg boilerplate metadata (e.g., disclaimers, licensing info).  
- Tokenize texts into words using Python libraries like `NLTK` or `spaCy`.  
- Convert tokens to lowercase.  
- Remove punctuation and purely numerical tokens, retaining alphanumeric tokens that may be genre-specific. 
- Optionally use lemmatization to group related word forms under a single lexeme (might be problematic for neologisms).

**Basic Filtering:**  
- Exclude words that appear only once in a single text to reduce noise from typos.

### 2. Identifying Candidate Neologisms

**Dictionary-Based Screening:**  
- Compare all tokens against a modern English dictionary or large lexical database accessible via Python (e.g., `NLTK` wordlists or third-party lexicons).  
- Flag any word not found in the dictionary as a candidate neologism.

**Temporal Adjustment Using a Historical Corpus:**  
- Identify a historical English reference corpus roughly matching the time period of the selected texts.  
- Check each candidate word against this historical corpus.  
  - If a candidate word appears above a minimal frequency threshold in the historical corpus, it is not considered a neologism.
  - If it does not appear or appears extremely rarely (below the threshold), keep it as a potential neologism.

**Filtering out named entities:**
- Pre-defined list of named entities (further research needed to find pre-established NE-corpera).
- Leverage spaCy's NER capabilities as suggested by Pyo (2023).

**Final Neologism Determination:**  
- After these dictionary, temporal, and NER filters, the remaining candidates are considered neologisms.

### 3. Measuring Relative Frequency

**Computing Relative Frequency:**  
- For each text, calculate the neologism frequency as the number of confirmed neologisms per a fixed number of tokens (e.g., per 10,000 words).  
- Formula:  
  Neologism Frequency = (Number of neologistic tokens ÷ Total tokens) × 10,000

**Aggregating by Genre:**  
- Compute the average neologism frequency for all Science Fiction texts and all Romance texts.  
- Use statistical tests if allowed (e.g., t-test or Mann-Whitney U, depending on data distribution) to compare the mean frequencies between the two genres.

### 4. Reporting and Interpretation

**Results:**  
- Present the average neologism frequency for Science Fiction and Romance texts.  
- Report the results of the statistical comparison and confidence intervals as appropriate.

**Limitations:**  
- The chosen dictionary and historical corpus may not perfectly represent the language environment of the time.
- Distinguishing proper nouns from neologisms is inherently a difficult task.

## Tools

- **Python:**  
  - Data extraction and cleaning: 'gutenberg', 'Requests', 'spaCy', 'NLTK'
  - Tokenization and lemmatization: 'NLTK', 'spaCy'  
  - Dictionary and corpus lookups: Custom Python scripts, data from online APIs (e.g. Oxford English Dictionary) or downloaded corpora.
  - Statistical analysis: 'scikit-learn'  
  - Visualization: 'matplotlib'
