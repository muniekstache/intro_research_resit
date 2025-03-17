import json
import os
import webbrowser
import sys
import time
import urllib.parse
from pathlib import Path
from tkinter import Tk, Label, Button, Frame, StringVar, Text, messagebox, font
from tkinter.ttk import Combobox
import threading

# Define paths
DATA_DIR = Path("data")
CANDIDATES_DIR = DATA_DIR / "candidates"
VALIDATED_DIR = DATA_DIR / "validated"

# Input directories
ROMANCE_INPUT_DIR = CANDIDATES_DIR / "romance"
SCIFI_INPUT_DIR = CANDIDATES_DIR / "scifi"

# Output directories
ROMANCE_OUTPUT_DIR = VALIDATED_DIR / "romance"
SCIFI_OUTPUT_DIR = VALIDATED_DIR / "scifi"

# Dictionary files
DICT_FILES = {
    "romance_neo_combinations": ROMANCE_INPUT_DIR / "neo_combinations.json",
    "romance_novel_neologisms": ROMANCE_INPUT_DIR / "novel_neologisms.json",
    "scifi_neo_combinations": SCIFI_INPUT_DIR / "neo_combinations.json",
    "scifi_novel_neologisms": SCIFI_INPUT_DIR / "novel_neologisms.json"
}

# Create output directories
os.makedirs(ROMANCE_OUTPUT_DIR, exist_ok=True)
os.makedirs(SCIFI_OUTPUT_DIR, exist_ok=True)

class NeologismValidator:
    def __init__(self, root):
        self.root = root
        self.root.title("Neologism Validator")
        self.root.geometry("1000x800")
        self.root.configure(bg="#f5f5f5")

        # Set up fonts
        self.title_font = font.Font(family="Arial", size=16, weight="bold")
        self.label_font = font.Font(family="Arial", size=12)
        self.info_font = font.Font(family="Arial", size=10)

        # Track current state
        self.current_dict_name = StringVar()
        self.current_dict_name.set("romance_neo_combinations")
        self.current_dict = None
        self.current_keys = []
        self.current_index = 0
        self.total_count = 0
        self.validated_true = {}
        self.validated_false = {}

        # Load progress if exists
        self.progress_file = VALIDATED_DIR / "progress.json"
        self.load_progress()

        # Create the UI
        self.setup_ui()

        # Load the first dictionary
        self.load_dictionary()

    def load_progress(self):
        """Load saved progress if it exists"""
        try:
            if self.progress_file.exists():
                with open(self.progress_file, 'r') as f:
                    progress = json.load(f)
                    self.validated_true = progress.get("validated_true", {})
                    self.validated_false = progress.get("validated_false", {})
                    print(f"Loaded progress: {len(self.validated_true)} true, {len(self.validated_false)} false")
        except Exception as e:
            print(f"Error loading progress: {e}")
            self.validated_true = {}
            self.validated_false = {}

    def save_progress(self):
        """Save current progress"""
        try:
            os.makedirs(self.progress_file.parent, exist_ok=True)
            progress = {
                "validated_true": self.validated_true,
                "validated_false": self.validated_false,
                "last_dict": self.current_dict_name.get(),
                "last_index": self.current_index
            }
            with open(self.progress_file, 'w') as f:
                json.dump(progress, f, indent=2)
            print(f"Progress saved: {len(self.validated_true)} true, {len(self.validated_false)} false")
        except Exception as e:
            print(f"Error saving progress: {e}")

    def setup_ui(self):
        """Set up the user interface"""
        # Main frame
        main_frame = Frame(self.root, bg="#f5f5f5", padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        # Title
        title_label = Label(main_frame, text="Neologism Validator", font=self.title_font, bg="#f5f5f5")
        title_label.pack(pady=(0, 20))

        # Dictionary selector
        dict_frame = Frame(main_frame, bg="#f5f5f5")
        dict_frame.pack(fill="x", pady=10)

        Label(dict_frame, text="Dictionary:", font=self.label_font, bg="#f5f5f5").pack(side="left", padx=(0, 10))
        dict_combo = Combobox(dict_frame, textvariable=self.current_dict_name, values=list(DICT_FILES.keys()), width=30)
        dict_combo.pack(side="left")
        dict_combo.bind("<<ComboboxSelected>>", lambda e: self.load_dictionary())

        # Progress info
        self.progress_var = StringVar()
        self.progress_var.set("0 / 0")
        progress_label = Label(dict_frame, textvariable=self.progress_var, font=self.label_font, bg="#f5f5f5")
        progress_label.pack(side="right")

        # Word info frame
        info_frame = Frame(main_frame, bg="white", padx=15, pady=15, relief="ridge", bd=1)
        info_frame.pack(fill="x", pady=15)

        # Current word
        self.word_var = StringVar()
        self.word_var.set("Loading...")
        word_label = Label(info_frame, textvariable=self.word_var, font=self.title_font, bg="white")
        word_label.pack(pady=(0, 10))

        # Word details
        self.details_text = Text(info_frame, height=8, width=80, font=self.info_font, wrap="word", bg="#f8f8f8")
        self.details_text.pack(fill="x", pady=10)

        # Ngram viewer button
        ngram_button = Button(info_frame, text="Open in Google Ngram Viewer",
                              command=self.open_ngram_viewer, bg="#e0e0ff", font=self.label_font,
                              padx=10, pady=5)
        ngram_button.pack(pady=10)

        # Decision buttons frame
        decision_frame = Frame(main_frame, bg="#f5f5f5")
        decision_frame.pack(fill="x", pady=15)

        # Buttons
        Button(decision_frame, text="← Previous", command=self.previous_word,
               bg="#e0e0e0", font=self.label_font, width=15).pack(side="left", padx=5)

        Button(decision_frame, text="Not a Neologism", command=lambda: self.make_decision(False),
               bg="#ffcccc", font=self.label_font, width=15).pack(side="left", padx=5)

        Button(decision_frame, text="True Neologism", command=lambda: self.make_decision(True),
               bg="#ccffcc", font=self.label_font, width=15).pack(side="left", padx=5)

        Button(decision_frame, text="Skip", command=self.next_word,
               bg="#ffffcc", font=self.label_font, width=15).pack(side="left", padx=5)

        Button(decision_frame, text="Save Progress", command=self.save_results,
               bg="#d0d0ff", font=self.label_font, width=15).pack(side="right", padx=5)

        # Status bar
        self.status_var = StringVar()
        self.status_var.set("Ready")
        status_bar = Label(self.root, textvariable=self.status_var, bd=1, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x")

    def load_dictionary(self):
        """Load the selected dictionary"""
        dict_name = self.current_dict_name.get()
        try:
            with open(DICT_FILES[dict_name], 'r') as f:
                self.current_dict = json.load(f)
                self.current_keys = list(self.current_dict["aggregated_tokens"].keys())
                self.total_count = len(self.current_keys)
                self.current_index = 0
                self.progress_var.set(f"1 / {self.total_count}")
                self.display_current_word()
                self.status_var.set(f"Loaded {dict_name} with {self.total_count} entries")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load dictionary: {e}")
            self.status_var.set(f"Error loading dictionary")

    def display_current_word(self):
        """Display the current word and its details"""
        if not self.current_keys or self.current_index >= len(self.current_keys):
            self.word_var.set("No more words")
            self.details_text.delete(1.0, "end")
            self.details_text.insert("end", "You've reviewed all words in this dictionary.")
            return

        # Get current word
        word = self.current_keys[self.current_index]
        word_data = self.current_dict["aggregated_tokens"][word]

        # Update UI
        self.word_var.set(word)
        self.progress_var.set(f"{self.current_index + 1} / {self.total_count}")

        # Display details
        self.details_text.delete(1.0, "end")
        details = f"Full form: {word_data.get('full_form', word)}\n"
        details += f"Lemma: {word_data.get('lemma', 'N/A')}\n"
        details += f"Part of Speech: {word_data.get('pos', 'N/A')}\n"
        details += f"Frequency: {word_data.get('frequency', 0)}\n\n"

        # Add dictionary type context
        dict_name = self.current_dict_name.get()
        if "neo_combinations" in dict_name:
            details += "Category: Neo-combination (lemma exists in reference dictionaries but this form does not)\n"
        else:
            details += "Category: Novel neologism (neither form nor lemma exists in reference dictionaries)\n"

        if "romance" in dict_name:
            details += "Genre: Romance"
        else:
            details += "Genre: Science Fiction"

        self.details_text.insert("end", details)

    def open_ngram_viewer(self):
        """Open the current word in Google Ngram Viewer"""
        if not self.current_keys or self.current_index >= len(self.current_keys):
            return

        word = self.current_keys[self.current_index]
        # Compare with similar words if we have a lemma
        lemma = self.current_dict["aggregated_tokens"][word].get("lemma", "")

        if lemma and lemma != word:
            # Include both the word and its lemma in the search
            query = f"{word},{lemma}"
        else:
            query = word

        # Create Google Ngram URL (1800-2019 time range)
        encoded_query = urllib.parse.quote(query)
        url = f"https://books.google.com/ngrams/graph?content={encoded_query}&year_start=1800&year_end=2019&corpus=26&smoothing=3"

        # Open in browser
        self.status_var.set(f"Opening Ngram Viewer for '{query}'")
        threading.Thread(target=lambda: webbrowser.open(url)).start()

    def make_decision(self, is_neologism):
        """Record decision and move to next word"""
        if not self.current_keys or self.current_index >= len(self.current_keys):
            return

        word = self.current_keys[self.current_index]
        dict_name = self.current_dict_name.get()
        word_data = self.current_dict["aggregated_tokens"][word]

        # Record the decision with metadata
        decision_data = {
            "word": word,
            "data": word_data,
            "dictionary": dict_name,
            "timestamp": time.time()
        }

        if is_neologism:
            self.validated_true[word] = decision_data
            self.status_var.set(f"Marked '{word}' as a true neologism")
        else:
            self.validated_false[word] = decision_data
            self.status_var.set(f"Marked '{word}' as not a neologism")

        # Move to next word
        self.next_word()

    def next_word(self):
        """Move to the next word"""
        if not self.current_keys:
            return

        if self.current_index < len(self.current_keys) - 1:
            self.current_index += 1
            self.display_current_word()
        else:
            messagebox.showinfo("End of Dictionary",
                                "You've reached the end of this dictionary. Please select another dictionary or save your results.")

    def previous_word(self):
        """Move to the previous word"""
        if not self.current_keys:
            return

        if self.current_index > 0:
            self.current_index -= 1
            self.display_current_word()
        else:
            self.status_var.set("Already at the first word")

    def save_results(self):
        """Save the validation results"""
        # First save progress
        self.save_progress()

        # Prepare output data for each category
        true_neologisms = {"romance": {}, "scifi": {}}
        false_neologisms = {"romance": {}, "scifi": {}}

        # Organize by genre
        for word, data in self.validated_true.items():
            genre = "romance" if "romance" in data["dictionary"] else "scifi"
            true_neologisms[genre][word] = data["data"]

        for word, data in self.validated_false.items():
            genre = "romance" if "romance" in data["dictionary"] else "scifi"
            false_neologisms[genre][word] = data["data"]

        # Save true neologisms for romance
        romance_true_output = {
            "aggregated_tokens": true_neologisms["romance"],
            "total_tokens": len(true_neologisms["romance"]),
            "unique_tokens": len(true_neologisms["romance"])
        }
        with open(ROMANCE_OUTPUT_DIR / "true_neologisms.json", 'w') as f:
            json.dump(romance_true_output, f, indent=2)

        # Save false neologisms for romance
        romance_false_output = {
            "aggregated_tokens": false_neologisms["romance"],
            "total_tokens": len(false_neologisms["romance"]),
            "unique_tokens": len(false_neologisms["romance"])
        }
        with open(ROMANCE_OUTPUT_DIR / "false_neologisms.json", 'w') as f:
            json.dump(romance_false_output, f, indent=2)

        # Save true neologisms for scifi
        scifi_true_output = {
            "aggregated_tokens": true_neologisms["scifi"],
            "total_tokens": len(true_neologisms["scifi"]),
            "unique_tokens": len(true_neologisms["scifi"])
        }
        with open(SCIFI_OUTPUT_DIR / "true_neologisms.json", 'w') as f:
            json.dump(scifi_true_output, f, indent=2)

        # Save false neologisms for scifi
        scifi_false_output = {
            "aggregated_tokens": false_neologisms["scifi"],
            "total_tokens": len(false_neologisms["scifi"]),
            "unique_tokens": len(false_neologisms["scifi"])
        }
        with open(SCIFI_OUTPUT_DIR / "false_neologisms.json", 'w') as f:
            json.dump(scifi_false_output, f, indent=2)

        self.status_var.set(
            f"Results saved. {len(self.validated_true)} true neologisms, {len(self.validated_false)} false neologisms")
        messagebox.showinfo("Save Complete",
                            f"Results saved successfully!\n\n"
                            f"Romance: {len(true_neologisms['romance'])} true, {len(false_neologisms['romance'])} false\n"
                            f"Sci-Fi: {len(true_neologisms['scifi'])} true, {len(false_neologisms['scifi'])} false")

def main():
    # Check if required directories exist
    for path in DICT_FILES.values():
        if not path.exists():
            print(f"Error: Required file not found: {path}")
            print("Please make sure you have generated the candidate neologism files first.")
            sys.exit(1)

    # Create tkinter root window
    root = Tk()
    app = NeologismValidator(root)

    # Center window
    window_width = 1000
    window_height = 800
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width / 2 - window_width / 2)
    center_y = int(screen_height / 2 - window_height / 2)
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

    # Start the application
    root.mainloop()

if __name__ == "__main__":
    main()