import re

common_phrases = [
    "Sehr geehrte Damen und Herren",
    "Mit freundlichen Grüßen",
    "Beste Grüße",
    "Liebe Kolleginnen und Kollegen",
    # Add more phrases as needed
]
# Compile regex patterns for emails and phone numbers
email_pattern = re.compile(r"\b[\w.-]+?@[\w.-]+\.\w+?\b")
phone_pattern = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?|\(\d{1,4}\)\s?)?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b")

regex_substitutions = [
    ("EMAIL_PATTERN", email_pattern),
    ("PHONE_PATTERN", phone_pattern),
]
