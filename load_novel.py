import os
from gutenbergdammit.ziputils import searchandretrieve

# Path to the Gutenberg-dammit ZIP archive
ZIP_PATH = "gutenberg-dammit-files-v002.zip"

# Dictionaries for each genre (keys are title keywords)
scifi_novels = {
    "The War in the Air": "H. G. Wells",           # 1908
    "A Princess of Mars": "Edgar Rice Burroughs",    # 1912
    "The Night Land": "William Hope Hodgson"         # 1912
}

romance_novels = {
    "Three Weeks": "Elinor Glyn",                    # 1907
    "The Shuttle": "Frances Hodgson Burnett",         # 1907
    "The Rosary": "Florence L. Barclay"               # 1909
}

def get_novel_by_title(zip_path, title_keyword):
    """
    Retrieve a novel from the Gutenberg-dammit archive using a substring search in the Title metadata.
    Returns the first matching (metadata, text) tuple.
    """
    results = list(searchandretrieve(zip_path, {"Title": title_keyword}))
    if results:
        metadata, text = results[0]
        return metadata, text
    else:
        return None, None

def save_raw_novels(novels_dict, genre):
    """
    For each novel in novels_dict, retrieve its text from the archive and save it
    to a file in data/raw/<genre>/.
    """
    raw_dir = os.path.join("data", "raw", genre)
    os.makedirs(raw_dir, exist_ok=True)

    for title in novels_dict.keys():
        metadata, text = get_novel_by_title(ZIP_PATH, title)
        if text is not None:
            filename = f"{title.replace(' ', '_')}.txt"
            filepath = os.path.join(raw_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Saved raw text for '{title}' to {filepath}")
        else:
            print(f"Could not find '{title}' in the archive.")

if __name__ == '__main__':
    # Save raw texts for both genres
    save_raw_novels(scifi_novels, "scifi")
    save_raw_novels(romance_novels, "romance")
