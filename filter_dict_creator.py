import re
import os
import json


def read_lines(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f.readlines()]


def update_bracket_stack(line, bracket_stack):
    for char in line:
        if char in "[(":
            bracket_stack.append((char, 0))
        elif char in ")]":
            if bracket_stack:
                bracket_stack.pop()


def check_brackets_and_close(bracket_stack, empty_line=False):
    for i in range(len(bracket_stack)):
        char, depth = bracket_stack[i]
        if depth >= 10 or empty_line:
            bracket_stack[i] = None
        else:
            bracket_stack[i] = (char, depth + 1)
    bracket_stack[:] = [b for b in bracket_stack if b is not None]


def is_inside_brackets(bracket_stack):
    return bool(bracket_stack)


def handle_hyphenated_words(incomplete_word, line, combine_hyphen):
    hyphen_match = combine_hyphen.match(line)
    if incomplete_word and hyphen_match:
        return incomplete_word + hyphen_match.group(1), ""
    elif hyphen_match:
        return hyphen_match.group(1) + '-', incomplete_word
    return "", incomplete_word


def process_line_for_entry(line, entry_pattern, incomplete_word):
    match = entry_pattern.match(line)
    if incomplete_word and match:
        return incomplete_word + match.group(), ""
    elif match:
        return match.group(), ""
    return None, incomplete_word


def should_skip_entry(current_entry, previous_entry, first_letters):
    if not previous_entry:
        return False

    prev_letter = previous_entry[0].lower()
    curr_letter = current_entry[0].lower()

    if abs(ord(curr_letter) - ord(prev_letter)) > 1:
        if curr_letter in first_letters:
            return False
        else:
            first_letters.add(curr_letter)
            return True
    return False


def extract_entries_from_lines(lines):
    entry_pattern = re.compile(r"^[A-Za-z\-']+(?=, {2})")
    combine_hyphen = re.compile(r". ([a-zA-Z]+)-$")
    entries = []
    previous_line_is_entry = False
    previous_entry = ""
    incomplete_word = ""
    bracket_stack = []  # Initialize bracket_stack here
    first_letters = set()

    for i, line in enumerate(lines):
        print(f"\nProcessing line {i + 1}: '{line}'")

        # Find potential entry FIRST
        current_entry, incomplete_word = process_line_for_entry(line, entry_pattern, incomplete_word)

        # THEN check for brackets ONLY AFTER the potential entry
        bracket_index = -1
        for char in "([":
            index = line.find(char)
            if index != -1 and (bracket_index == -1 or index < bracket_index):
                bracket_index = index

        if current_entry and bracket_index != -1 and bracket_index > line.find(current_entry):
            print(f"Entry '{current_entry}' found, but brackets start after it. Processing entry.")
            # We dont skip, we continue as it is a valid entry
            update_bracket_stack(line, bracket_stack)
            check_brackets_and_close(bracket_stack, not line)

        elif current_entry is None:
            print(f"No match for line {i + 1}.")
            previous_line_is_entry = False
            update_bracket_stack(line,
                                 bracket_stack)
            check_brackets_and_close(bracket_stack, not line)
            continue

        else:
            update_bracket_stack(line, bracket_stack)
            check_brackets_and_close(bracket_stack, not line)

            if is_inside_brackets(bracket_stack):
                print(f"Skipping line {i + 1} (inside brackets).")
                continue

        incomplete_word, previous_incomplete_word = handle_hyphenated_words(incomplete_word, line, combine_hyphen)
        if previous_incomplete_word:
            print(f"Found hyphenated word start: '{previous_incomplete_word}'")
            continue

        if previous_line_is_entry or should_skip_entry(current_entry, previous_entry, first_letters):
            print(f"Skipping entry: '{current_entry}'")
            previous_line_is_entry = False
            continue

        entries.append(current_entry)
        print(f"Added entry: '{current_entry}'")
        previous_line_is_entry = True
        previous_entry = current_entry

    return entries


def save_entries_to_json(entries, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sorted(set(entries)), f, ensure_ascii=False, indent=4)


def extract_entries(file_path, output_file):
    lines = read_lines(file_path)
    entries = extract_entries_from_lines(lines)
    save_entries_to_json(entries, output_file)
    print("\nExtraction complete.")
    print(f"Extracted {len(entries)} entries. Saved to {output_file}.")
    print(f"First 10 entries: {entries[:10]}")


if __name__ == "__main__":
    input_file = "data/chambersstwentie00daviiala_djvu.txt"
    output_directory = "data/dicts"

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    output_file = os.path.join(output_directory, "extracted_chamber_entries.json")
    extract_entries(input_file, output_file)