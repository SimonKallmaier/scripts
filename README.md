
# Transforming XML to PDF

As we cannot directly make use of the provided resources linked from the ['Bundesministerium'](https://www.e-rechnung-bund.de/faq/xrechnung/#:~:text=XRechnung%20ist%20ein%20Standard%20f%C3%BCr,die%20Weiterverarbeitung%20durch%20unterschiedliche%20Softwaresysteme.), we rely on an alternative solution using Python.

## ADR
We decided to use saxonica, although commercial license, as this is the only python library robustly handling xsl version 2.0 and above. Moreoever, we rely on xsl stylesheets provided by[XRechnung Visualization](https://github.com/itplr-kosit/xrechnung-visualization) to have a robust implementation that is able to visualize the incoming data. Python is required as described above.

The code will be both provisioned via a streamlit dashboard as well as via an executable file.

## XSL Stylesheet usage
### Understanding the XSL Stylesheets and Two-Level Process

XSLT (eXtensible Stylesheet Language Transformations) is a language for transforming XML documents into different formats, such as HTML or other XML formats. In this project, the XSLT stylesheets are crucial for interpreting and formatting the XML data according to the XRechnung visualization requirements. The key XSL stylesheets involved are:

`ubl-invoice-xr.xsl`, `ubl-creditnote-xr.xsl`, and `cii-xr.xsl`: These stylesheets are used to transform XML files in different formats (UBL Invoice, CreditNote, or CrossIndustryInvoice (CII)) into an intermediate XR XML format.

`xrechnung-html.xsl`: This stylesheet is used to convert the intermediate XR XML into HTML format, which is a human-readable representation of the invoice or credit note. The output HTML is styled and structured to provide a clear, understandable view of the invoice data.

These stylesheets are provided by the XRechnung Visualization GitHub repository, which is designed to ensure that the output follows the XRechnung standards for German electronic invoicing.

### The Two-Level Transformation Process

The transformation from XML to HTML occurs in two distinct levels aligning on the java implementation.

**Level 1**: XML to Intermediate XR XML

By transforming the original XML into this intermediate format, we ensure consistency in the next step of rendering the document into HTML. This step also helps to abstract the specific details of the original XML formats, simplifying the process of applying visual styles.

**:Level 2**:: Intermediate XR XML to HTML

The intermediate XML provides a clean starting point for this final transformation, allowing the XSLT stylesheet to focus on the visual presentation rather than worrying about the complexities of the original UBL or CII format.


## Code

This script transforms XML invoices into HTML and then converts the HTML files to PDF.

1. **Logging Configuration**: Sets up logging to display information and error messages.
2. **determine_stylesheet**: Determines the appropriate XSLT stylesheet based on the root element of the XML file.
3. **compile_and_transform**: Compiles an XSLT stylesheet and transforms an XML file to another format.
4. **transform_xml**: Transforms XML files in a specified directory to HTML using a two-step XSLT process.
5. **convert_html_to_pdf**: Converts HTML files in a specified directory to PDF using WeasyPrint.

**Main Execution**:
- Defines directories for XML input, HTML output, PDF output, and XSLT stylesheets.
- Defines optional XSLT parameters.
- Transforms XML files to HTML.
- Converts the resulting HTML files to PDF.

# References
For more details on the transformations and XML/XSLT stylesheets, refer to the following resources:

- [XRechnung Testsuite](https://github.com/itplr-kosit/xrechnung-testsuite/tree/master) GitHub Repository: Provides sample invoices and the test environment.
- [XRechnung Visualization](https://github.com/itplr-kosit/xrechnung-visualization) GitHub Repository: Provides visualization stylesheets for transforming XR XML to HTML and PDF.
- [Saxonica License](https://www.saxonica.com/shop/shop.xml#!/Individual-licenses/c/905991).
- [Saxonica Python API](https://www.saxonica.com/saxon-c/doc12/html/saxonc.html#PySaxonProcessor).

# Licences

The xsl stylesheets are published under the Apache 2.0 licence (see [here](https://github.com/itplr-kosit/xrechnung-visualization/blob/master/LICENSE)), which allow commercial use. 

In contrast, the saxonica usage reqiures a single payment per year. Needs to be discussed with supervisors.

