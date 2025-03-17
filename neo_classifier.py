import json
import os
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm

# Personal note: How did I never know about pathlib?? It's so convenient :)
# Define paths
DATA_DIR = Path("data")
DICT_DIR = DATA_DIR / "dicts"
FILTERED_DIR = DATA_DIR / "filtered"
CANDIDATES_DIR = DATA_DIR / "candidates"

# Input files
CHAMBER_DICT_PATH = DICT_DIR / "extracted_chamber_entries.json"
CORPUS_DICT_PATH = DICT_DIR / "corpus_filter_dictionary.json"
ROMANCE_FILTERED_PATH = FILTERED_DIR / "romance_filtered.json"
SCIFI_FILTERED_PATH = FILTERED_DIR / "scifi_filtered.json"

# Output directories
ROMANCE_OUTPUT_DIR = CANDIDATES_DIR / "romance"
SCIFI_OUTPUT_DIR = CANDIDATES_DIR / "scifi"

def load_dictionaries():
    """Load both dictionaries and combine them into a single set for faster lookups."""
    print("Loading dictionaries...")
    start_time = time.time()

    # Load Chamber entries (list format)
    with open(CHAMBER_DICT_PATH, 'r', encoding='utf-8') as f:
        chamber_entries = set(json.load(f))

    # Load corpus dictionary (dict format with counts)
    with open(CORPUS_DICT_PATH, 'r', encoding='utf-8') as f:
        corpus_dict = json.load(f)

    # Combine into a single set (lowercase for case-insensitive comparison)
    combined_dict = {word.lower() for word in chamber_entries}
    combined_dict.update(word.lower() for word in corpus_dict.keys())

    print(f"Dictionaries loaded in {time.time() - start_time:.2f} seconds")
    print(f"Total unique dictionary entries: {len(combined_dict)}")

    return combined_dict

def process_genre(genre_name, filtered_path, output_dir, combined_dict):
    """Process a single genre file and classify entries."""
    print(f"Processing {genre_name} entries...")
    start_time = time.time()

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Load filtered entries
    with open(filtered_path, 'r', encoding='utf-8') as f:
        filtered_data = json.load(f)

    neo_combinations = {}
    novel_neologisms = {}

    # Track progress
    total = len(filtered_data["aggregated_tokens"])

    # Process each token
    for token, data in tqdm(filtered_data["aggregated_tokens"].items(),
                            desc=f"Classifying {genre_name} tokens",
                            total=total):
        # Skip single-character tokens
        if len(token) <= 1:
            continue
        token_lower = token.lower()
        lemma_lower = data["lemma"].lower()
        if len(lemma_lower) <= 1:
            continue

        # Skip if the token itself is in the dictionaries (not a neologism)
        if token_lower in combined_dict:
            continue

        # If lemma exists in dictionaries but not the token, it's a neo-combination
        if lemma_lower in combined_dict:
            neo_combinations[token] = data
        # If neither token nor lemma exist in dictionaries, it's a novel neologism
        else:
            novel_neologisms[token] = data

    # Save results
    neo_combinations_output = {
        "aggregated_tokens": neo_combinations,
        "total_tokens": len(neo_combinations),
        "unique_tokens": len(neo_combinations)
    }

    novel_neologisms_output = {
        "aggregated_tokens": novel_neologisms,
        "total_tokens": len(novel_neologisms),
        "unique_tokens": len(novel_neologisms)
    }

    with open(output_dir / f"neo_combinations.json", 'w', encoding='utf-8') as f:
        json.dump(neo_combinations_output, f, indent=2)

    with open(output_dir / f"novel_neologisms.json", 'w', encoding='utf-8') as f:
        json.dump(novel_neologisms_output, f, indent=2)

    print(f"{genre_name} processing completed in {time.time() - start_time:.2f} seconds")
    print(f"{genre_name} neo-combinations: {len(neo_combinations)}")
    print(f"{genre_name} novel neologisms: {len(novel_neologisms)}")

    return genre_name, len(neo_combinations), len(novel_neologisms)

def main():
    """Main function to process both genres."""
    overall_start = time.time()

    # Create necessary directories
    os.makedirs(ROMANCE_OUTPUT_DIR, exist_ok=True)
    os.makedirs(SCIFI_OUTPUT_DIR, exist_ok=True)

    # Load dictionaries into memory once
    combined_dict = load_dictionaries()

    # Define processing tasks
    tasks = [
        ("romance", ROMANCE_FILTERED_PATH, ROMANCE_OUTPUT_DIR, combined_dict),
        ("scifi", SCIFI_FILTERED_PATH, SCIFI_OUTPUT_DIR, combined_dict)
    ]

    # Process genres in parallel
    with ProcessPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(process_genre, *task) for task in tasks]
        for future in as_completed(futures):
            genre, neo_count, novel_count = future.result()
            print(f"✓ {genre.capitalize()} processing complete: {neo_count} neo-combinations, {novel_count} novel neologisms")

    print(f"All processing completed in {time.time() - overall_start:.2f} seconds")
    print(f"Results saved to:")
    print(f"  - {ROMANCE_OUTPUT_DIR}")
    print(f"  - {SCIFI_OUTPUT_DIR}")

if __name__ == "__main__":
    main()