import logging
import os
import re
import time
import zipfile
from glob import glob
from multiprocessing import Pool, cpu_count
from typing import Dict, Generator, List, Set

import pandas as pd
import spacy
from annonymization import common_phrases, regex_substitutions
from spacy.matcher import Matcher

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s")

nlp = spacy.load("de_core_news_md")

# Initialize the Matcher and EntityRuler
matcher = Matcher(nlp.vocab)

# Create patterns for the Matcher
patterns = [[{"LOWER": token.lower_} for token in nlp(text)] for text in common_phrases]
matcher.add("COMMON_PHRASES", patterns)


def unzip_files(zip_dir: str, output_dir: str, month: str, force: bool = False) -> None:
    """Unzip all files in the given directory."""
    zip_files = glob(os.path.join(zip_dir, "*.zip"))
    for zip_path in zip_files:
        zip_name = os.path.basename(zip_path)
        zip_name_no_ext = os.path.splitext(zip_name)[0]
        extract_dir = os.path.join(output_dir, month, zip_name_no_ext)
        if not force and os.path.exists(extract_dir):
            logging.info(f"Skipping {zip_name} as it already exists in {extract_dir}")
            continue
        os.makedirs(extract_dir, exist_ok=True)
        logging.info(f"Extracting {zip_name} to {extract_dir}")
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
        except zipfile.BadZipFile as e:
            logging.error(f"Error extracting {zip_name}: {e}")
    logging.info("All zip files processed.")


def find_index_files(root_dir: str) -> List[str]:
    """Find all index files in the directory tree."""
    index_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith("_index.txt"):
                index_files.append(os.path.join(dirpath, filename))
    return index_files


def get_batch_id(index_file_path: str) -> str:
    return index_file_path.replace("\n", "").split("\\")[-2]


def get_doc_id(index_file_path: str) -> str:
    return index_file_path.replace("\n", "").split("\\")[-1].split(".")[0]


def parse_index_file(index_file_path: str) -> Dict[str, str]:
    """Parse the index file into a dictionary."""

    try:
        with open(index_file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        items = [item.strip().strip('"') for item in content.split(",")]

        if len(items) % 2 == 0:
            logging.warning(f"Even number ({len(items)}) of items in {index_file_path}. Expected odd number.")

        if items[-1] == "":
            logging.debug(f"Classification index file. Dropping last item: {items[-1]}.")

        else:
            logging.debug(f"Attributes index file. Getting BatchID and DocID from {items[-1]}.")
            batch_id = get_batch_id(items[-1])
            doc_id = get_doc_id(items[-1])

        data = {"BATCHKLASSE": items[0], "BATCHCONTENT": items[1]}

        for i in range(2, len(items[:-1]), 2):  # Skip last item
            key = items[i]
            value = items[i + 1] if i + 1 < len(items) else ""
            data[key] = value

        # batch id and doc id are only part of classiciation index files.
        if "{Batch ID}" not in data:
            data["{Batch ID}"] = batch_id
            data["{Document ID}"] = doc_id

        return data
    except Exception as e:
        logging.error(f"Error parsing index file {index_file_path}: {e}")
        return {}


def is_expected_format(data: Dict[str, str]) -> bool:
    """Check if the data has the expected format."""
    expected_columns = {
        "BATCHKLASSE",
        "BATCHCONTENT",
        "{Batch ID}",
        "{Document ID}",
        "docType",
        "{pageCount}",
    }
    missing_columns = expected_columns - data.keys()
    if missing_columns:
        logging.warning(f"Missing columns: {missing_columns}")
        return False
    return True


def get_text_file_path(index_file_path: str) -> str:
    """Get the corresponding text file path for the index file."""
    base_dir = os.path.dirname(index_file_path)
    index_filename = os.path.basename(index_file_path)
    base_filename = index_filename.replace("_index.txt", ".txt")
    return os.path.join(base_dir, base_filename)


def read_text_file(text_file_path: str) -> str:
    """Read the content of the text file."""
    try:
        with open(text_file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logging.error(f"Error reading text file {text_file_path}: {e}")
        return ""


def is_blacklisted(text: str, blacklist_emails: Set[str]) -> bool:
    """Check if the text contains any blacklisted emails."""
    text_lower = text.lower()
    for email in blacklist_emails:
        if email.lower() in text_lower:
            return True
    return False


def remove_common_phrases(text: str) -> str:
    """Remove common phrases from the text."""
    doc = nlp(text)
    matches = matcher(doc)
    spans = [doc[start:end] for _, start, end in matches]
    spans = spacy.util.filter_spans(spans)

    # Replace matched phrases with [REDACTED_PHRASE]
    for span in spans:
        # Use regex to ensure exact phrase replacement, considering word boundaries
        pattern = re.compile(re.escape(span.text))
        text = pattern.sub("[REDACTED_PHRASE]", text)

    return text


def anonymize_text(text: str) -> str:
    """Anonymize personal data in the text."""
    for pattern_name, pattern in regex_substitutions:
        text = pattern.sub(f"[REDACTED_{pattern_name}]", text)

    doc = nlp(text)
    anonymized_tokens = []
    for token in doc:
        if token.ent_type_ in ["PER", "ORG", "LOC"]:
            anonymized_tokens.append("[REDACTED]")
        else:
            anonymized_tokens.append(token.text_with_ws)
    return "".join(anonymized_tokens)


def process_index_files(
    index_files_chunk: List[str], chunk_number: int, output_dir: str, blacklist_emails: Set[str]
) -> None:
    """Process a chunk of index files."""
    data_list = []
    count_blacklist = 0
    for index_file in index_files_chunk:
        try:
            data = parse_index_file(index_file)
            if not is_expected_format(data):  # log message in function
                continue

            text_file = get_text_file_path(index_file)
            if os.path.exists(text_file):
                text = read_text_file(text_file)

                # Blacklist is a set of email addresses from employees who are not allowed to be mentioned in the text
                is_blacklist = is_blacklisted(text, blacklist_emails)
                if is_blacklist:
                    logging.info(f"Blacklisted email found in {index_file}")
                    count_blacklist += 1
                    continue

                text = remove_common_phrases(text)
                anonymized_text = anonymize_text(text)
                data["text"] = anonymized_text
            else:
                data["text"] = ""
            data_list.append(data)
        except Exception as e:
            logging.error(f"Error processing {index_file}: {e}")

    df = pd.DataFrame(data_list)
    # Save dataframe to pickle in new subfolder
    final_output_dir = os.path.join(output_dir, "final_dataframes")
    os.makedirs(final_output_dir, exist_ok=True)
    pickle_file = os.path.join(final_output_dir, f"dataframe_chunk_{chunk_number}.pkl")
    df.to_pickle(pickle_file)
    logging.info(f"Chunk {chunk_number} processed and saved to {pickle_file}")

    if count_blacklist > 0:
        logging.info(
            f"Found {count_blacklist} blacklisted emails ({count_blacklist/len(index_files_chunk)}%) in this chunk."
        )


def chunks(lst: List[str], n: int) -> Generator[List[str], None, None]:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]  # noqa: E203


def main(multiprocessing=True) -> None:
    zip_dir = "simulated_zip_files"  # Directory where zip files are stored
    output_dir = "processed_data"  # Output directory
    month = "2023-10"
    unzip_dir = os.path.join(output_dir, "unzipped_files")
    os.makedirs(unzip_dir, exist_ok=True)

    # Define blacklist emails
    blacklist_emails = {"blacklisted@example.com", "spamuser@example.org", "max.mustermann@example.com,"}

    # Step 1: Unzip files
    unzip_files(zip_dir, unzip_dir, month)

    # Step 2: Find index files
    root_dir = os.path.join(unzip_dir, month)
    index_files = find_index_files(root_dir)
    logging.info(f"Found {len(index_files)} index files.")

    # Step 3: Process index files in chunks using multiprocessing
    chunk_size = 100  # Adjust based on available memory
    chunks_list = list(chunks(index_files, chunk_size))

    if not multiprocessing:
        logging.info("Processing index files sequentially.")
        for i, chunk in enumerate(chunks_list):
            process_index_files(chunk, i, output_dir, blacklist_emails)
    else:
        logging.info(f"Processing index files in parallel using {cpu_count()} cores")
        with Pool(cpu_count()) as pool:
            pool.starmap(
                process_index_files, [(chunk, i, output_dir, blacklist_emails) for i, chunk in enumerate(chunks_list)]
            )


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    logging.info(f"Script ran for {end_time - start_time:.2f} seconds")
