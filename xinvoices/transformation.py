import logging
import os

from saxoncee import PySaxonProcessor

# from weasyprint import HTML

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def _determine_stylesheet(xml_path, xsl_dir):
    """
    Determine the appropriate XSLT stylesheet for the given XML file based on its root element.
    """
    with open(xml_path, "r", encoding="utf-8") as f:
        for _ in range(10):
            line = f.readline()
            if "CrossIndustryInvoice" in line:
                return os.path.join(xsl_dir, "cii-xr.xsl")
            elif "Invoice" in line:
                return os.path.join(xsl_dir, "ubl-invoice-xr.xsl")
            elif "CreditNote" in line:
                return os.path.join(xsl_dir, "ubl-creditnote-xr.xsl")

    logging.error(f"Could not determine the root element of '{xml_path}'")
    raise ValueError(f"Could not determine the root element of '{xml_path}'")


def _compile_and_transform(processor, stylesheet_path, source_file, output_file, params):
    """
    Compiles an XSLT stylesheet and transforms an XML file.

    :param processor: PySaxonProcessor object for handling the transformation.
    :param stylesheet_path: Path to the XSLT stylesheet.
    :param source_file: Path to the input XML file.
    :param output_file: Path to the output file.
    :param params: Dictionary of parameters to pass to the XSLT stylesheet.
    """
    logging.info(f"Compiling XSLT stylesheet: {stylesheet_path}")
    xslt_executable = processor.compile_stylesheet(stylesheet_file=stylesheet_path)

    # Set parameters if provided
    if params:
        for key, value in params.items():
            # Convert value to PyXdmValue before setting it
            xdm_value = processor.make_string_value(value)
            xslt_executable.set_parameter(key, xdm_value)
            logging.debug(f"Set parameter for transformation: {key} = {value}")

    logging.info(f"Transforming '{source_file}' to '{output_file}' using XSLT.")
    xslt_executable.transform_to_file(source_file=source_file, output_file=output_file)
    logging.info(f"Transformation for {stylesheet_path} completed successfully.")


def transform_xml(xml_dir, html_dir, xsl_dir, params=None):
    """
    Transforms XML files in a specified directory to HTML using a two-step XSLT process.

    :param xml_dir: Directory containing input XML files.
    :param html_dir: Directory where output HTML files will be saved.
    :param xsl_dir: Directory containing XSLT stylesheets.
    :param params: (Optional) Dictionary of parameters to pass to the XSLT stylesheets.
    """
    # Initialize the Saxon/C Processor
    with PySaxonProcessor(license=False) as proc:
        logging.info(f"Saxon/C Processor Version: {proc.version}")

        xslt_processor = proc.new_xslt30_processor()

        # Ensure the output directories exist
        os.makedirs(html_dir, exist_ok=True)
        intermediate_dir = os.path.join(html_dir, os.pardir, "xr")
        os.makedirs(intermediate_dir, exist_ok=True)
        logging.info(f"Output directories ensured: {html_dir}, {intermediate_dir}")

        # Iterate over each XML file in the input directory
        for filename in os.listdir(xml_dir):
            if filename.lower().endswith(".xml"):
                xml_path = os.path.join(xml_dir, filename)
                logging.info(f"Processing file: {xml_path}")

                stylesheet_filename = _determine_stylesheet(xml_path, xsl_dir)

                # Intermediate XML filename
                intermediate_path = os.path.join(intermediate_dir, f"{filename[:-4]}-xr.xml")

                # Step 1: Transform to intermediate XR format
                _compile_and_transform(xslt_processor, stylesheet_filename, xml_path, intermediate_path, params)

                # Step 2: Transform to HTML
                second_xsl = os.path.join(xsl_dir, "xrechnung-html.xsl")
                html_filename = f"{filename[:-4]}.html"
                html_path = os.path.join(html_dir, html_filename)
                _compile_and_transform(xslt_processor, second_xsl, intermediate_path, html_path, params)


# def convert_html_to_pdf(html_dir, pdf_dir):
#     """
#     Converts HTML files in a specified directory to PDF using WeasyPrint.

#     :param html_dir: Directory containing input HTML files.
#     :param pdf_dir: Directory where output PDF files will be saved.
#     """
#     # Ensure the output directory exists
#     os.makedirs(pdf_dir, exist_ok=True)
#     logging.info(f"PDF output directory ensured: {pdf_dir}")

#     # Iterate over each HTML file in the input directory
#     for filename in os.listdir(html_dir):
#         if filename.lower().endswith(".html"):
#             html_path = os.path.join(html_dir, filename)
#             pdf_filename = f"{filename[:-5]}.pdf"  # Replace .html with .pdf
#             pdf_path = os.path.join(pdf_dir, pdf_filename)

#             logging.info(f"Converting '{html_path}' to PDF at '{pdf_path}'")
#             HTML(html_path).write_pdf(pdf_path)
#             logging.info(f"Converted '{filename}' to '{pdf_filename}'.")


if __name__ == "__main__":
    xml_dir = "/home/simon/scripts/xinvoices/test_instances/positive"
    html_dir = "output/html"
    pdf_dir = "output/pdf"
    xsl_dir = "/home/simon/scripts/xinvoices/xsl"
    # xsl_path = "/home/simon/scripts/xinvoices/xsl/simple.xsl"

    # Define XSLT parameters if needed
    params = {"lang": "de", "invoiceline-layout": "tabular"}

    print("Transforming XML to HTML using Saxon/C and saxoncee...")
    transform_xml(xml_dir, html_dir, xsl_dir)

    print("Converting HTML to PDF using WeasyPrint...")
    convert_html_to_pdf(html_dir, pdf_dir)

    print("Transformation and PDF generation complete.")
