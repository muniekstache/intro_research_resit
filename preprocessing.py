import os
import json
import re
import spacy
from tqdm import tqdm


def pre_clean(text):
    """
    Remove a block that resembles a table of contents and chapter headings.
    This function:
      - Removes the block starting at a line that contains "CONTENTS" (case insensitive)
        until the first double newline.
      - Removes lines starting with "CHAPTER" followed by a roman numeral.
      - Pre-cleans problematic punctuation sequences for the tokenizer.
    """
    # Remove the contents block (non-greedy until a double newline)
    text = re.sub(r'(?is)CONTENTS.*?\n\s*\n', '', text)
    # Remove chapter headings with roman numerals (e.g., "CHAPTER I", "CHAPTER II", etc.)
    text = re.sub(r'(?im)^CHAPTER\s+[IVXLCDM]+\b.*$', '', text)

    text = re.sub(r'([!?.,;:"\'\-]){2,}', r'\1', text)
    # Add a space after punctuation if it's stuck to a word (e.g., "word--another" -> "word -- another")
    text = re.sub(r'([!?.,;:"\'\-])([A-Za-z])', r'\1 \2', text)
    # Add a space before punctuation if it's stuck to a previous word (e.g., "hello,world" -> "hello, world")
    text = re.sub(r'([A-Za-z])([!?.,;:"\'\-])', r'\1 \2', text)
    # Replace multiple spaces/tabs with a single space, but preserve newlines for chunking
    text = re.sub(r'[ \t]+', ' ', text).strip()
    return text



# Preprocessor Class
class Preprocessor:
    def __init__(self, model_name="en_core_web_trf", chunk_size=50000):
        # Load the transformer-based spaCy model
        self.nlp = spacy.load(model_name)
        self.chunk_size = chunk_size

    def chunk_text(self, text):
        """
        Safely split a very long text into chunks no longer than self.chunk_size.
        Splitting is done on double newlines (paragraph breaks) to preserve sentence boundaries.
        """
        if len(text) <= self.chunk_size:
            return [text]
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 < self.chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para + "\n\n"
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    def process_text(self, text):
        """
        Process text with spaCy:
         - First, pre-clean text.
         - Then, if text is too long, split it into safe chunks.
         - Process each chunk using nlp.pipe in batches.
         - Aggregate enriched token data from all chunks.
        Returns a list of sentences (each a list of token dictionaries).
        """
        # Remove table of contents, chapters and punctuation sequences
        text = pre_clean(text)
        chunks = self.chunk_text(text)
        enriched_sentences = []
        for doc in tqdm(self.nlp.pipe(chunks, batch_size=5), total=len(chunks), desc="Processing chunks"):
            for sent in doc.sents:
                sentence_tokens = []
                for token in sent:
                    token_data = {
                        "text": token.text,               # Original token
                        "lemma": token.lemma_,            # Lemmatized form
                        "pos": token.pos_,                # POS tag
                        "ner": token.ent_type_ if token.ent_type_ else None,  # NER label
                        "is_stop": token.is_stop,         # Stopword flag
                        "is_punct": token.is_punct,       # Punctuation flag
                        "lower": token.lower_             # Lowercase version
                    }
                    sentence_tokens.append(token_data)
                enriched_sentences.append(sentence_tokens)
        return enriched_sentences

    def process_files_in_folder(self, raw_folder, processed_folder):
        """
        Process all .txt files in raw_folder using process_text, then save enriched output as JSON in processed_folder.
        """
        os.makedirs(processed_folder, exist_ok=True)
        txt_files = [f for f in os.listdir(raw_folder) if f.endswith(".txt")]
        for filename in tqdm(txt_files, desc=f"Processing files in {raw_folder}"):
            raw_filepath = os.path.join(raw_folder, filename)
            with open(raw_filepath, 'r', encoding='utf-8') as f:
                raw_text = f.read()
            enriched_data = self.process_text(raw_text)
            output_filename = filename.replace(".txt", "_enriched.json")
            output_filepath = os.path.join(processed_folder, output_filename)
            with open(output_filepath, 'w', encoding='utf-8') as f:
                json.dump(enriched_data, f, indent=4)
            print(f"Processed and saved: {output_filepath}")

# Filterer Class
class Filterer:
    def __init__(self):
        self.aggregated = {}
        self.total_tokens = 0

    def token_filter(self, token):
        """
        Return True if the token should be removed based on:
         - The token is tagged as a named entity.
         - The token is punctuation.
         - The token is a space (POS tag "SPACE").
         - The token is a numeral or contains any digits.
         - The token is a stopword.
        """
        if token["ner"] is not None:
            return True
        if token["is_punct"]:
            return True
        if token["pos"] in ["SPACE", "PROPN", "X", "PUNCT"]:
            return True
        if token["pos"] == "NUM" or re.search(r'\d', token["text"]):
            return True
        if token["is_stop"]:
            return True
        return False

    def aggregate_tokens_from_sentences(self, sentences):
        """
        Iterate over all sentences (list of token dictionaries) and aggregate tokens that pass the filter.
        For each token, record:
         - Full form (first encountered),
         - Lemma,
         - POS tag,
         - Frequency.
        Update self.total_tokens.
        """
        for sent in sentences:
            for token in sent:
                if self.token_filter(token):
                    continue
                self.total_tokens += 1
                key = token["lower"]
                if key in self.aggregated:
                    self.aggregated[key]["frequency"] += 1
                else:
                    self.aggregated[key] = {
                        "full_form": token["text"],
                        "lemma": token["lemma"],
                        "pos": token["pos"],
                        "frequency": 1
                    }

    def process_folder(self, processed_folder):
        """
        Process all enriched JSON files in processed_folder, aggregate tokens, and compute total/unique token counts.
        Returns aggregated dictionary, total token count, and unique token count.
        """
        self.aggregated = {}
        self.total_tokens = 0
        json_files = [f for f in os.listdir(processed_folder) if f.endswith("_enriched.json")]
        for filename in tqdm(json_files, desc=f"Aggregating tokens from {processed_folder}"):
            filepath = os.path.join(processed_folder, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                enriched_data = json.load(f)
            self.aggregate_tokens_from_sentences(enriched_data)
        unique_tokens = len(self.aggregated)
        return self.aggregated, self.total_tokens, unique_tokens

    def save_aggregated(self, aggregated, stats, output_filepath):
        """
        Save the aggregated tokens and stats (total tokens, unique tokens) as a JSON file.
        """
        output = {
            "aggregated_tokens": aggregated,
            "total_tokens": stats[0],
            "unique_tokens": stats[1]
        }
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=4)
        print(f"Aggregated filtered data saved to: {output_filepath}")



if __name__ == '__main__':
    genres = ["scifi", "romance"]

    # Preprocessing: Process raw texts in data/raw/<genre> and save enriched JSON to data/processed/<genre>
    preprocessor = Preprocessor()
    for genre in genres:
        raw_folder = os.path.join("data", "raw", genre)
        processed_folder = os.path.join("data", "processed", genre)
        preprocessor.process_files_in_folder(raw_folder, processed_folder)

    # Filtering and Aggregation: Process enriched files and save filtered aggregate per genre in data/filtered/
    filterer = Filterer()
    for genre in genres:
        processed_folder = os.path.join("data", "processed", genre)
        aggregated, total_tokens, unique_tokens = filterer.process_folder(processed_folder)
        print(f"\nGenre: {genre}")
        print(f"Total tokens (filtered): {total_tokens}")
        print(f"Unique tokens (filtered): {unique_tokens}")

        output_filepath = os.path.join("data", "filtered", f"{genre}_filtered.json")
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        filterer.save_aggregated(aggregated, (total_tokens, unique_tokens), output_filepath)
