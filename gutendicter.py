import asyncio
import json
import os
import pickle
import argparse
from collections import Counter
import re
from tqdm import tqdm
from gutenbergdammit.ziputils import loadmetadata, retrieve_one

# Path to the Gutenberg-dammit ZIP archive
ZIP_PATH = "gutenberg-dammit-files-v002.zip"
DATA_DIR = "data/dicts"
CHECKPOINT_FILE = os.path.join(DATA_DIR, "processing_checkpoint.pkl")
TEMP_RESULTS_FILE = os.path.join(DATA_DIR, "temp_results.json")

# Global variables for checkpointing
processed_records = set()
master_counter = Counter()

def filter_metadata(metadata):
    """
    Filter metadata to include only those records for which:
    1. The "Author Death" (first value) is a number less than 1900
    2. The language is English
    """
    filtered = []
    for record in metadata:
        # Check author death year
        if "Author Death" in record and record["Author Death"]:
            try:
                death_year = int(record["Author Death"][0])
                if death_year < 1900:
                    # Check if language is English
                    if "Language" in record and record["Language"]:
                        languages = [lang.lower() for lang in record["Language"]]
                        if "english" in languages:
                            filtered.append(record)
            except Exception as e:
                continue
    return filtered

def chunk_text(text, chunk_size=900000):
    """
    Safely split a long text into chunks no longer than chunk_size.
    Splitting is done on double newlines (paragraph breaks) to preserve sentence boundaries.
    """
    if len(text) <= chunk_size:
        return [text]
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""
    for para in paragraphs:
        # If adding this paragraph would exceed chunk_size, start a new chunk.
        if len(current_chunk) + len(para) + 2 < chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = para + "\n\n"
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def retrieve_text(gd_path):
    """
    Retrieve the text for a given Gutenberg file path.
    """
    return retrieve_one(ZIP_PATH, gd_path)

def tokenize_with_regex(text):
    """
    Tokenization method using regex that preserves hyphenated words.
    """
    # Regex to include hyphenated words (e.g., self-quarantine)
    tokens = re.findall(r'\b[a-zA-Z]+(?:-[a-zA-Z]+)*\b', text.lower())

    # Filter tokens to ensure they have at least 2 characters
    tokens = [token for token in tokens if len(token) >= 2]

    return Counter(tokens)

async def process_record(record):
    """
    Asynchronously process one metadata record.
    """
    gd_path = record.get("gd-path")
    record_id = record.get("id", gd_path)

    if not gd_path or record_id in processed_records:
        return None

    try:
        # Retrieve text thread-safe
        text = await asyncio.to_thread(retrieve_text, gd_path)

        # Process text with regex
        counter = await asyncio.to_thread(tokenize_with_regex, text)

        # Update processed records
        processed_records.add(record_id)

        return counter
    except Exception as e:
        print(f"Error processing {gd_path}: {e}")
        return None

def save_checkpoint():
    """
    Save the current state of processing to a checkpoint file.
    """
    # Ensure directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    checkpoint_data = {
        'processed_records': processed_records,
        'master_counter': master_counter
    }

    # Save checkpoint to a temporary file first
    with open(f"{CHECKPOINT_FILE}.tmp", 'wb') as f:
        pickle.dump(checkpoint_data, f)

    # Replace the old checkpoint file with the new one
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
    os.rename(f"{CHECKPOINT_FILE}.tmp", CHECKPOINT_FILE)

    # Also save the current results as JSON
    with open(TEMP_RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(dict(master_counter), f)

def load_checkpoint():
    """
    Load the checkpoint file if it exists.
    """
    global processed_records, master_counter

    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'rb') as f:
            checkpoint_data = pickle.load(f)
            processed_records = checkpoint_data['processed_records']
            master_counter = checkpoint_data['master_counter']
        return True
    return False

async def main(batch_size=20, limit=None, checkpoint_frequency=5):
    global master_counter

    print("Using regex tokenization for processing.")

    # Create data directory if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)

    # Load checkpoint if it exists
    if load_checkpoint():
        print(f"Resuming from checkpoint. {len(processed_records)} records already processed.")
        print(f"Current dictionary has {len(master_counter)} unique tokens.")
    else:
        print("Starting new processing run.")

    # Load metadata
    print("Loading metadata from ZIP file...")
    metadata = loadmetadata(ZIP_PATH)
    print(f"Loaded {len(metadata)} metadata records.")

    # Filter records for English texts with authors who died before 1900
    filtered_records = filter_metadata(metadata)
    print(f"Found {len(filtered_records)} English records with Author Death < 1900.")

    # Filter out already processed records
    records_to_process = [r for r in filtered_records if r.get("id", r.get("gd-path")) not in processed_records]
    print(f"{len(records_to_process)} records remaining to process.")

    # Apply optional limit
    if limit and limit < len(records_to_process):
        records_to_process = records_to_process[:limit]
        print(f"Limited to processing {limit} records as requested.")

    if not records_to_process:
        print("All records already processed!")
        return

    # Process in batches
    total_batches = (len(records_to_process) + batch_size - 1) // batch_size
    print(f"Processing in {total_batches} batches of {batch_size} records each.")

    for i in range(0, len(records_to_process), batch_size):
        batch = records_to_process[i:i+batch_size]
        batch_num = i // batch_size + 1
        print(f"Starting batch {batch_num}/{total_batches}")

        tasks = [process_record(record) for record in batch]

        completed_count = 0
        for future in tqdm(asyncio.as_completed(tasks), total=len(tasks),
                           desc=f"Batch {batch_num}/{total_batches}"):
            counter = await future
            if counter:
                master_counter.update(counter)

            completed_count += 1
            # Save checkpoint based on frequency
            if completed_count % checkpoint_frequency == 0:
                save_checkpoint()

        print(f"Completed batch {batch_num}/{total_batches}")
        print(f"Dictionary now has {len(master_counter)} unique tokens.")

        # Save checkpoint after each batch
        save_checkpoint()

    # Save final results
    output_filepath = os.path.join(DATA_DIR, "corpus_filter_dictionary.json")
    print(f"Saving final results to {output_filepath}...")
    with open(output_filepath, "w", encoding="utf-8") as f:
        json.dump(dict(master_counter), f, indent=4)

    print(f"Corpus dictionary built. Total unique tokens: {len(master_counter)}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process Gutenberg texts with checkpointing capability')
    parser.add_argument('--batch-size', type=int, default=20, help='Number of records to process in each batch')
    parser.add_argument('--limit', type=int, help='Limit the number of records to process')
    parser.add_argument('--checkpoint-freq', type=int, default=5, help='How often to save checkpoints within a batch')

    args = parser.parse_args()

    asyncio.run(main(
        batch_size=args.batch_size,
        limit=args.limit,
        checkpoint_frequency=args.checkpoint_freq
    ))