import os
import random
import string
import zipfile


def generate_random_string(length):
    """Generate a random string of fixed length."""
    return "".join(random.choices(string.ascii_uppercase, k=length))


def generate_random_name():
    """Generate a random full name."""
    first_names = ["Max", "Erika", "Hans", "Anna", "Peter", "Laura", "Karl", "Sophie"]
    last_names = ["Mustermann", "Musterfrau", "Schmidt", "Schneider", "Fischer", "Weber"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"


def generate_random_email(name):
    """Generate a random email address based on a name."""
    domains = ["example.com", "mail.com", "test.org"]
    email_name = name.lower().replace(" ", ".")
    return f"{email_name}@{random.choice(domains)}"


def generate_random_date():
    """Generate a random date."""
    years = ["2022", "2023", "2024"]
    months = [
        "Januar",
        "Februar",
        "März",
        "April",
        "Mai",
        "Juni",
        "Juli",
        "August",
        "September",
        "Oktober",
        "November",
        "Dezember",
    ]
    days = [str(day) for day in range(1, 29)]  # Keep it simple with days 1-28
    return f"{random.choice(days)}. {random.choice(months)} {random.choice(years)}"


def generate_random_phone():
    """Generate a random phone number."""
    return f"+49 {random.randint(1000, 9999)} {random.randint(100000, 999999)}"


def create_simulated_zip_files(base_zip_dir, month, num_zip_files=3, documents_per_zip=10, pages_per_document=5):
    """
    Create simulated ZIP files with the specified structure and dummy data.

    Parameters:
    - base_zip_dir (str): Directory where ZIP files will be stored.
    - month (str): Month identifier (e.g., '2023-10').
    - num_zip_files (int): Number of ZIP files to create.
    - documents_per_zip (int): Number of documents per ZIP file.
    - pages_per_document (int): Number of pages per document.
    """
    os.makedirs(base_zip_dir, exist_ok=True)

    for zip_num in range(1, num_zip_files + 1):
        zip_name = f"sample_data_{zip_num}.zip"
        zip_path = os.path.join(base_zip_dir, zip_name)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for doc_num in range(1, documents_per_zip + 1):
                BatchID = f"Batch_{zip_num:03d}"
                DocumentID = f"Doc_{doc_num:05d}"

                # Create directory structure inside ZIP
                dir_path = f"{BatchID}/{DocumentID}/"

                # Generate base filename
                base_filename = generate_random_string(7)  # e.g., 'ABCDEFG'

                # Generate random personal data
                name = generate_random_name()
                email = generate_random_email(name)
                date = generate_random_date()
                phone = generate_random_phone()

                # Include common phrases
                common_phrase_intro = random.choice(
                    [
                        "Sehr geehrte Damen und Herren",
                        "Liebe Kolleginnen und Kollegen",
                        "Guten Tag",
                    ]
                )
                common_phrase_outro = random.choice(
                    [
                        "Mit freundlichen Grüßen",
                        "Beste Grüße",
                        "Hochachtungsvoll",
                    ]
                )

                # Create text file content with personal data and common phrases
                ocr_text = f"""{common_phrase_intro},

Mein Name ist {name} und ich wohne in Berlin. Sie können mich unter {email} oder {phone} erreichen.
Heute ist der {date}.

{common_phrase_outro},
{name}
"""

                index_content = (
                    "zipname",
                    "filename",
                    "{BatchID}",
                    BatchID,
                    "{DocumentID}",
                    DocumentID,
                    "docType",
                    "bill",
                    "{pageCount}",
                    str(pages_per_document),
                )
                index_content_str = ",".join(['"' + i + '"' for i in index_content])

                # Define file paths within the ZIP
                ocr_file_path = os.path.join(dir_path, f"{base_filename}.txt")
                index_file_path = os.path.join(dir_path, f"{base_filename}_index.txt")

                # Write OCR text file
                zipf.writestr(ocr_file_path, ocr_text)

                # Write index file
                zipf.writestr(index_file_path, index_content_str)

        print(f"Created simulated ZIP file: {zip_path}")


def main():
    # Configuration
    base_zip_dir = "simulated_zip_files"  # Directory to store simulated ZIP files
    month = "2023-10"  # Specify the month
    num_zip_files = 3  # Number of ZIP files to create
    documents_per_zip = 500  # Number of documents per ZIP file
    pages_per_document = 5  # Number of pages per document

    create_simulated_zip_files(
        base_zip_dir=base_zip_dir,
        month=month,
        num_zip_files=num_zip_files,
        documents_per_zip=documents_per_zip,
        pages_per_document=pages_per_document,
    )

    print("Simulation data creation complete.")


if __name__ == "__main__":
    main()
