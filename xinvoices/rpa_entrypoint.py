import argparse
import logging
import os

from transformation import convert_html_to_pdf, transform_xml


def parse_arguments():
    """
    Parses command-line arguments for the RPA entry point script.
    """
    parser = argparse.ArgumentParser(
        description="Transform a single XML to HTML and then to PDF using Saxon/C and WeasyPrint."
    )
    parser.add_argument("--xml-file", required=True, help="Path to the input XML file")
    parser.add_argument("--html-file", required=True, help="Path to the output HTML file")
    parser.add_argument("--pdf-file", required=True, help="Path to the output PDF file")
    parser.add_argument("--xsl-dir", required=True, help="Directory containing XSLT stylesheets")
    parser.add_argument("--lang", default="de", help="Language parameter for the transformation (default: de)")
    parser.add_argument(
        "--invoiceline-layout", default="tabular", help="Invoice line layout parameter (default: tabular)"
    )
    return parser.parse_args()


def main():
    """
    Main function to handle the transformation process for RPA bot.
    """
    # Parse the input arguments
    args = parse_arguments()

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Extract arguments
    xml_file = args.xml_file
    html_file = args.html_file
    pdf_file = args.pdf_file
    xsl_dir = args.xsl_dir
    params = {"lang": args.lang, "invoiceline-layout": args.invoiceline_layout}

    # Validate input XML file
    if not os.path.isfile(xml_file):
        logging.error(f"Input XML file '{xml_file}' does not exist.")
        return

    # Validate XSL directory
    if not os.path.exists(xsl_dir):
        logging.error(f"XSL directory '{xsl_dir}' does not exist.")
        return

    # Perform the XML to HTML transformation
    logging.info("Starting XML to HTML transformation...")
    transform_xml(xml_file, html_file, xsl_dir, params)
    logging.info("XML to HTML transformation completed.")

    # Convert HTML to PDF
    logging.info("Starting HTML to PDF conversion...")
    convert_html_to_pdf(html_file, pdf_file)
    logging.info("HTML to PDF conversion completed.")


if __name__ == "__main__":
    main()
    # python rpa_entrypoint.py --xml-file path/to/input.xml --html-file path/to/output.html --pdf-file path/to/output.pdf --xsl-dir path/to/xslt-directory
