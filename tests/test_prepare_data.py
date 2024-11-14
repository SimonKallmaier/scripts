import os
import shutil
import tempfile
import unittest

import pandas as pd
import spacy

from preprocessing.prepare_data import (
    anonymize_text,
    chunks,
    get_text_file_path,
    is_blacklisted,
    is_expected_format,
    parse_index_file,
    process_index_files,
    read_text_file,
    remove_common_phrases,
)

nlp = spacy.load("de_core_news_md")


class TestPrepareData(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for file operations
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)
        # Set up test data
        self.index_file_content = (
            '"zipname","filename","{BatchID}","Batch_001","{DocumentID}","Doc_00001","docType","bill","{pageCount}","5"'
        )
        self.text_file_content = (
            "Sehr geehrte Damen und Herren,\n\n"
            "Mein Name ist Max Mustermann und ich wohne in Berlin. "
            "Sie können mich unter max.mustermann@example.com oder +49 1234 567890 erreichen.\n"
            "Heute ist der 15. Oktober 2023.\n\n"
            "Mit freundlichen Grüßen,\n"
            "Max Mustermann"
        )
        self.blacklist_emails = {"blacklisted@example.com"}

    def test_parse_index_file(self):
        # Write index file to temporary directory
        index_file_path = os.path.join(self.test_dir, "test_index.txt")
        with open(index_file_path, "w", encoding="utf-8") as f:
            f.write(self.index_file_content)
        expected_data = {
            "BATCHKLASSE": "zipname",
            "BATCHCONTENT": "filename",
            "{BatchID}": "Batch_001",
            "{DocumentID}": "Doc_00001",
            "docType": "bill",
            "{pageCount}": "5",
        }
        result = parse_index_file(index_file_path)
        self.assertEqual(result, expected_data)

    def test_is_expected_format(self):
        data = {
            "BATCHKLASSE": "zipname",
            "BATCHCONTENT": "filename",
            "{BatchID}": "Batch_001",
            "{DocumentID}": "Doc_00001",
            "docType": "bill",
            "{pageCount}": "5",
        }
        self.assertTrue(is_expected_format(data))
        data_missing = data.copy()
        del data_missing["docType"]
        self.assertFalse(is_expected_format(data_missing))

    def test_get_text_file_path(self):
        index_file_path = "/path/to/file_index.txt"
        expected = "/path/to/file.txt"
        result = get_text_file_path(index_file_path)
        self.assertEqual(result, expected)

    def test_read_text_file(self):
        text_file_path = os.path.join(self.test_dir, "test_text.txt")
        with open(text_file_path, "w", encoding="utf-8") as f:
            f.write(self.text_file_content)
        result = read_text_file(text_file_path)
        self.assertEqual(result, self.text_file_content)

    def test_is_blacklisted(self):
        text = "Contact me at blacklisted@example.com"
        self.assertTrue(is_blacklisted(text, self.blacklist_emails))
        text = "Contact me at allowed@example.com"
        self.assertFalse(is_blacklisted(text, self.blacklist_emails))

    def test_remove_common_phrases(self):
        text = "Sehr geehrte Damen und Herren,\n\n" "Dies ist ein Test.\n\n" "Mit freundlichen Grüßen,\n" "Tester"
        expected = "[REDACTED_PHRASE],\n\n" "Dies ist ein Test.\n\n" "[REDACTED_PHRASE],\n" "Tester"
        result = remove_common_phrases(text)
        self.assertEqual(result, expected)

    def test_anonymize_text(self):
        text = (
            "Mein Name ist Max Mustermann und ich wohne in Berlin. "
            "Sie können mich unter max.mustermann@example.com erreichen."
        )
        result = anonymize_text(text)
        self.assertTrue("Max Mustermann" not in result)

    def test_process_index_files(self):
        # Set up index and text files
        index_file_path = os.path.join(self.test_dir, "test_index.txt")
        text_file_path = os.path.join(self.test_dir, "test.txt")
        with open(index_file_path, "w", encoding="utf-8") as f:
            f.write(self.index_file_content)
        with open(text_file_path, "w", encoding="utf-8") as f:
            f.write(self.text_file_content)
        # Run process_index_files
        output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        index_files_chunk = [index_file_path]
        chunk_number = 0
        process_index_files(index_files_chunk, chunk_number, output_dir, self.blacklist_emails)
        # Check output
        pickle_file = os.path.join(output_dir, "final_dataframes", f"dataframe_chunk_{chunk_number}.pkl")
        self.assertTrue(os.path.exists(pickle_file))
        df = pd.read_pickle(pickle_file)
        self.assertEqual(len(df), 1)

    def test_chunks(self):
        lst = list(range(10))
        chunked = list(chunks(lst, 3))
        expected = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
        self.assertEqual(chunked, expected)


if __name__ == "__main__":
    unittest.main()
