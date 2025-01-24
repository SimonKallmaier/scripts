import enum
import pickle
import random
import string

import pandas as pd


# Define enums
class DocumentType(enum.Enum):
    INVOICE = "INVOICE"
    RECEIPT = "RECEIPT"
    STATE = "STATE"


class InputChannel(enum.Enum):
    EMAIL = "EMAIL"
    UPLOAD = "UPLOAD"
    API = "API"


class AutoUpload(enum.Enum):
    TRUE = "True"
    FALSE = "False"


columns_interest = ["DocumentType", "clean_text"]
extraction_columns = ["Number1", "Number2", "Number3"]
categorical_columns = ["InputChannel", "Autoclass"]
identifier = ["Batch_ID", "Document_ID"]


if __name__ == "__main__":
    # Define column names

    # Number of sample rows
    num_rows = 1000

    # Function to generate random numbers of a specific length
    def generate_number(length):
        return "".join(random.choices(string.digits, k=length))

    # Generate identifiers
    batch_ids = [f"BATCH_{i:04d}" for i in range(1, num_rows + 1)]
    document_ids = [f"DOC_{i:06d}" for i in range(1, num_rows + 1)]

    # Generate categorical data
    document_types = [random.choice(list(DocumentType)).value for _ in range(num_rows)]
    input_channels = [random.choice(list(InputChannel)).value for _ in range(num_rows)]
    autoclasses = [random.choice(list(AutoUpload)).value for _ in range(num_rows)]

    # Generate extraction numbers with a 70% chance of having a number, else None
    number1 = [generate_number(5) if random.random() > 0.3 else None for _ in range(num_rows)]
    number2 = [generate_number(7) if random.random() > 0.3 else None for _ in range(num_rows)]
    number3 = [generate_number(10) if random.random() > 0.3 else None for _ in range(num_rows)]

    # Generate clean_text, including numbers with a 50% chance if they exist
    clean_text = []
    for i in range(num_rows):
        text = "This is a sample document."
        if number1[i] and random.random() > 0.5:
            text += f" Number1: {number1[i]}."
        if number2[i] and random.random() > 0.5:
            text += f" Number2: {number2[i]}."
        if number3[i] and random.random() > 0.5:
            text += f" Number3: {number3[i]}."
        clean_text.append(text)

    # Create the DataFrame
    data = {
        "Batch_ID": batch_ids,
        "Document_ID": document_ids,
        "DocumentType": document_types,
        "clean_text": clean_text,
        "Number1": number1,
        "Number2": number2,
        "Number3": number3,
        "InputChannel": input_channels,
        "Autoclass": autoclasses,
    }

    df = pd.DataFrame(data)

    # Display the first few rows of the DataFrame
    print(df.head())

    # Store the DataFrame in a pickle file
    pickle_filename = "dummy_dataframe.pkl"
    with open(pickle_filename, "wb") as f:
        pickle.dump(df, f)

    print(f"\nDataFrame successfully saved to {pickle_filename}")
