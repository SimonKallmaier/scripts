import os

from saxoncee import PySaxonProcessor


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
        print(f"Saxon/C Processor Version: {proc.version}")

        xslt_processor = proc.new_xslt30_processor()

        # Ensure the output directories exist
        os.makedirs(html_dir, exist_ok=True)
        intermediate_dir = os.path.join(html_dir, "intermediate")
        os.makedirs(intermediate_dir, exist_ok=True)
        print(f"Output directories ensured: {html_dir}, {intermediate_dir}")

        # Iterate over each XML file in the input directory
        for filename in os.listdir(xml_dir):
            if filename.lower().endswith("uncefact.xml"):
                xml_path = os.path.join(xml_dir, filename)
                print(f"Processing file: {xml_path}")

                # Determine if the file is an invoice or credit note
                is_invoice = False
                is_credit_note = False

                # Read the first few lines to determine the root element
                with open(xml_path, "r", encoding="utf-8") as f:
                    for _ in range(10):
                        line = f.readline()
                        if "Invoice" in line:
                            is_invoice = True
                            break
                        elif "CreditNote" in line:
                            is_credit_note = True
                            break

                if not is_invoice and not is_credit_note:
                    print(f"Skipping '{filename}': Not an invoice or credit note.")
                    continue

                # TODO: use the correct stylesheet for CII
                # Choose the appropriate XSLT stylesheet for the first transformation
                if is_invoice:
                    first_xsl = os.path.join(xsl_dir, "ubl-invoice-xr.xsl")
                    first_xsl = os.path.join(xsl_dir, "cii-xr.xsl")
                    print(f"Identified as Invoice. Using stylesheet: {first_xsl}")
                elif is_credit_note:
                    first_xsl = os.path.join(xsl_dir, "ubl-creditnote-xr.xsl")
                    print(f"Identified as Credit Note. Using stylesheet: {first_xsl}")
                else:
                    print(f"Skipping '{filename}': Unknown document type.")
                    continue

                # Intermediate XML filename
                intermediate_filename = filename[:-4] + "-xr.xml"
                intermediate_path = os.path.join(intermediate_dir, intermediate_filename)

                # First Transformation: UBL XML to XR format
                xslt_executable = xslt_processor.compile_stylesheet(stylesheet_file=first_xsl)
                print(f"Compiled first XSLT stylesheet: {first_xsl}")

                if params:
                    for key, value in params.items():
                        xslt_executable.set_parameter(key, value)
                        print(f"Set parameter for first transformation: {key} = {value}")

                print(f"Transforming '{xml_path}' to intermediate XR format at '{intermediate_path}'")
                xslt_executable.transform_to_file(source_file=xml_path, output_file=intermediate_path)
                print(f"Transformed '{filename}' to intermediate XR format.")

                # Second Transformation: XR XML to HTML
                second_xsl = os.path.join(xsl_dir, "xrechnung-html.xsl")
                html_filename = filename[:-4] + ".html"
                html_path = os.path.join(html_dir, html_filename)

                xslt_executable = xslt_processor.compile_stylesheet(stylesheet_file=second_xsl)
                print(f"Compiled second XSLT stylesheet: {second_xsl}")

                if params:
                    for key, value in params.items():
                        xslt_executable.set_parameter(key, value)
                        print(f"Set parameter for second transformation: {key} = {value}")

                print(f"Transforming intermediate XR format at '{intermediate_path}' to HTML at '{html_path}'")
                xslt_executable.transform_to_file(source_file=intermediate_path, output_file=html_path)
                print(f"Transformed intermediate XR format to '{html_filename}'.")


def convert_html_to_pdf(html_dir, pdf_dir):
    """
    Converts HTML files in a specified directory to PDF using WeasyPrint.

    :param html_dir: Directory containing input HTML files.
    :param pdf_dir: Directory where output PDF files will be saved.
    """
    from weasyprint import HTML

    # Ensure the output directory exists
    os.makedirs(pdf_dir, exist_ok=True)
    print(f"PDF output directory ensured: {pdf_dir}")

    # Iterate over each HTML file in the input directory
    for filename in os.listdir(html_dir):
        if filename.lower().endswith(".html"):
            html_path = os.path.join(html_dir, filename)
            pdf_filename = filename[:-5] + ".pdf"  # Replace .html with .pdf
            pdf_path = os.path.join(pdf_dir, pdf_filename)

            print(f"Converting '{html_path}' to PDF at '{pdf_path}'")
            HTML(html_path).write_pdf(pdf_path)
            print(f"Converted '{filename}' to '{pdf_filename}'.")
