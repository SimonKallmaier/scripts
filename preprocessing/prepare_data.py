import os
import zipfile
from glob import glob

import pandas as pd
import spacy
from spacy.matcher import Matcher

# Load the German spaCy model
nlp = spacy.load("de_core_news_sm")

# Initialize the Matcher
matcher = Matcher(nlp.vocab)
common_phrases = [
    "Sehr geehrte Damen und Herren",
    "Mit freundlichen Grüßen",
    # Add more phrases as needed
]

# Create patterns for the Matcher
patterns = [[{"LOWER": token.lower_} for token in nlp(text)] for text in common_phrases]
matcher.add("COMMON_PHRASES", patterns)


def unzip_files(zip_dir, output_dir, month, force=False):
    zip_files = glob(os.path.join(zip_dir, "*.zip"))
    for zip_path in zip_files:
        zip_name = os.path.basename(zip_path)
        zip_name_no_ext = os.path.splitext(zip_name)[0]
        extract_dir = os.path.join(output_dir, month, zip_name_no_ext)
        if not force and os.path.exists(extract_dir):
            print(f"Skipping {zip_name} as it already exists in {extract_dir}")
            continue
        os.makedirs(extract_dir, exist_ok=True)
        print(f"Extracting {zip_name} to {extract_dir}")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)
    print("All zip files processed.")


def find_index_files(root_dir):
    index_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith("_index.txt"):
                index_files.append(os.path.join(dirpath, filename))
    return index_files


def parse_index_file(index_file_path):
    with open(index_file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    # Split by commas, remove quotes
    items = [item.strip().strip('"') for item in content.split(",")]

    data = {"BATCHKLASSE": items[0], "BATCHCONTENT": items[1]}

    # Start from the third element
    for i in range(2, len(items), 2):
        key = items[i]
        value = items[i + 1] if i + 1 < len(items) else ""
        data[key] = value

    return data


def is_expected_format(data):
    expected_columns = [
        "BATCHKLASSE",
        "BATCHCONTENT",
        "{BatchID}",
        "{DocumentID}",
        "docType",
        "{pageCount}",
    ]
    for column in expected_columns:
        if column not in data:
            print(f"Missing column: {column}")
            return False
    return True


def get_text_file_path(index_file_path):
    base_dir = os.path.dirname(index_file_path)
    index_filename = os.path.basename(index_file_path)
    base_filename = index_filename.replace("_index.txt", ".txt")
    text_file_path = os.path.join(base_dir, base_filename)
    return text_file_path


def read_text_file(text_file_path):
    with open(text_file_path, "r", encoding="utf-8") as f:
        text = f.read()
    return text


def is_blacklisted(text, blacklist_emails):
    text_lower = text.lower()
    for email in blacklist_emails:
        if email.lower() in text_lower:
            return True
    return False


def remove_common_phrases(text):
    doc = nlp(text)
    matches = matcher(doc)
    spans = []

    for match_id, start, end in matches:
        span = doc[start:end]
        spans.append(span)

    # Sort spans in reverse order to replace from the end to avoid messing up indices
    spans = sorted(spans, key=lambda span: span.start_char, reverse=True)

    for span in spans:
        text = text[: span.start_char] + "[REDACTED_PHRASE]" + text[span.end_char :]  # noqa: E203

    return text


def anonymize_text(text):
    doc = nlp(text)
    anonymized_text = "".join(
        "[REDACTED]" if token.ent_type_ in ["PERSON", "GPE", "LOC", "ORG"] else token.text + token.whitespace_
        for token in doc
    )
    return anonymized_text


def process_index_files(index_files_chunk, chunk_number, output_dir, blacklist_emails):
    data_list = []
    for index_file in index_files_chunk:
        try:
            data = parse_index_file(index_file)
            if not is_expected_format(data):
                continue
            text_file = get_text_file_path(index_file)
            if os.path.exists(text_file):
                text = read_text_file(text_file)
                # Step 1: Remove common phrases
                text = remove_common_phrases(text)
                # Step 2: Check for blacklisted emails
                is_blacklist = is_blacklisted(text, blacklist_emails)
                data["is_blacklist"] = is_blacklist
                # Step 3: Anonymize text
                anonymized_text = anonymize_text(text)
                data["text"] = anonymized_text
            else:
                data["text"] = ""
                data["is_blacklist"] = False
            data_list.append(data)
        except Exception as e:
            print(f"Error processing {index_file}: {e}")
    df = pd.DataFrame(data_list)
    # Save dataframe to pickle in new subfolder
    final_output_dir = os.path.join(output_dir, "final_dataframes")
    os.makedirs(final_output_dir, exist_ok=True)
    pickle_file = os.path.join(final_output_dir, f"dataframe_chunk_{chunk_number}.pkl")
    df.to_pickle(pickle_file)
    print(f"Chunk {chunk_number} processed and saved to {pickle_file}")


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]  # noqa: E203


def main():
    zip_dir = "simulated_zip_files"  # Directory where zip files are stored
    output_dir = "processed_data"  # Output directory
    month = "2023-10"
    unzip_dir = os.path.join(output_dir, "unzipped_files")
    os.makedirs(unzip_dir, exist_ok=True)

    # Define blacklist emails
    blacklist_emails = set(
        [
            "blacklisted@example.com",
            "spamuser@example.org",
            # Add more emails as needed
        ]
    )

    # Step 1: Unzip files
    unzip_files(zip_dir, unzip_dir, month)

    # Step 2: Find index files
    root_dir = os.path.join(unzip_dir, month)
    index_files = find_index_files(root_dir)
    print(f"Found {len(index_files)} index files.")

    # Step 3: Process index files in chunks
    chunk_size = 100  # Adjust based on available memory
    for chunk_number, index_files_chunk in enumerate(chunks(index_files, chunk_size)):
        process_index_files(index_files_chunk, chunk_number, output_dir, blacklist_emails)

    # Optional: Delete old dataframes if needed
    # intermediate_pickle_files = glob(os.path.join(output_dir, "dataframe_chunk_*.pkl"))
    # for file_path in intermediate_pickle_files:
    #     os.remove(file_path)
    # print('Old intermediate dataframes deleted.')


if __name__ == "__main__":
    main()
