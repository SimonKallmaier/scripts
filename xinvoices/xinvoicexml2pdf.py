import datetime
import os
import xml.etree.ElementTree as ET

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Define constants
PAGE_WIDTH, PAGE_HEIGHT = A4
FONT_NAME = "Helvetica"
FONT_SIZE_NORMAL = 11
FONT_SIZE_SMALL = 9
CURRENCY = "EUR"
ICCPROFILE_FILE = "sRGB2014.icc"
XMP_METADATA_FILE = "ZUGFeRD2_extension_schema.xmp"
XML_INPUT_FILE = os.path.join("xinvoices", "zugferd_invoice.xml")
PDF_OUTPUT_FILE = os.path.join("xinvoices", "zugferd_invoice.pdf")

# Static data: Company information (seller)
company_info = {
    "name": "Kraxi GmbH",
    "street": "Flugzeugallee 17",
    "postcode": "12345",
    "city": "Papierfeld",
    "country": "Deutschland",
    "country_code": "DE",
    "phone": "(0123) 4567",
    "fax": "(0123) 4568",
    "email": "info@kraxi.com",
    "url": "www.kraxi.com",
    "vat_id": "DE123456789",
    "director": "GF Paul Kraxi",
    "company_registration": "München HRB 999999",
    "bank_name": "Postbank München",
    "iban": "IBAN DE28700100809999999999",
}

# Define namespaces for parsing XML
NAMESPACES = {
    "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
    "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
    "udt": "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100",
}


class MyCanvas(canvas.Canvas):
    """
    Custom canvas class to set PDF/A-3b compliance, load ICC profile, set output intents, and embed XML invoice data.
    """

    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        # Load ICC profile
        with open(ICCPROFILE_FILE, "rb") as f:
            icc_profile = f.read()
        # Set output intent
        self.setPageResources(outputProfile=icc_profile)
        self.setOutputIntents(
            pdfa=True, outputConditionIdentifier="Custom", outputCondition="sRGB", destOutputProfile=icc_profile
        )
        # Load XMP metadata
        with open(XMP_METADATA_FILE, "rb") as f:
            xmp_metadata = f.read()
        self.xmpMetadata = xmp_metadata

    def save(self):
        """
        Override the save method to embed the XML invoice file into the PDF as an attachment with
        AFRelationship 'Alternative'.
        """
        # Embed the XML invoice file
        with open(XML_INPUT_FILE, "rb") as f:
            xml_data = f.read()
        # Embed the XML file with AFRelationship='Alternative'
        self.embedFile(
            filename=XML_INPUT_FILE,
            data=xml_data,
            mimeType="text/xml",
            description="Rechnungsdaten im ZUGFeRD-XML-Format",
            afrelationship="Alternative",
        )
        canvas.Canvas.save(self)


def parse_zugferd_invoice(xml_file):
    """
    Parse the ZUGFeRD XML invoice file and extract necessary invoice data.

    Args:
        xml_file (str): Path to the ZUGFeRD XML file.

    Returns:
        dict: A dictionary containing invoice data including buyer_info, invoice_number, invoice_date,
              articles, totals, vat_percent, and due_date_days.
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Extract invoice number
    invoice_number = root.find(".//ram:ID", NAMESPACES).text

    # Extract invoice date
    issue_date_str = root.find(".//ram:IssueDateTime/udt:DateTimeString", NAMESPACES).text
    issue_date = datetime.datetime.strptime(issue_date_str, "%Y%m%d")

    # Extract buyer information
    buyer_info = extract_buyer_info(root)

    # Extract articles
    articles = extract_articles(root)

    # Extract totals
    total_net, total_tax, total_gross = extract_totals(root)

    # Extract VAT percent
    vat_percent = extract_vat_percent(root)

    # Extract payment due date and calculate due_date_days
    due_date_days = calculate_due_date_days(root, issue_date)

    return {
        "buyer_info": buyer_info,
        "invoice_number": invoice_number,
        "invoice_date": issue_date,
        "articles": articles,
        "total_net": total_net,
        "total_tax": total_tax,
        "total_gross": total_gross,
        "vat_percent": vat_percent,
        "due_date_days": due_date_days,
    }


def extract_buyer_info(root):
    """
    Extract buyer information from the XML root element.

    Args:
        root (xml.etree.ElementTree.Element): Root element of the XML tree.

    Returns:
        dict: Dictionary containing buyer information.
    """
    buyer_element = root.find(".//ram:BuyerTradeParty", NAMESPACES)
    buyer_info = {
        "name": buyer_element.find("ram:Name", NAMESPACES).text,
        "street": buyer_element.find(".//ram:LineOne", NAMESPACES).text,
        "postcode": buyer_element.find(".//ram:PostcodeCode", NAMESPACES).text,
        "city": buyer_element.find(".//ram:CityName", NAMESPACES).text,
        "country": "Deutschland",  # Assuming country name, adjust as necessary
    }
    return buyer_info


def extract_articles(root):
    """
    Extract article line items from the XML root element.

    Args:
        root (xml.etree.ElementTree.Element): Root element of the XML tree.

    Returns:
        list: List of dictionaries containing article data.
    """
    articles = []
    for idx, line_item in enumerate(root.findall(".//ram:IncludedSupplyChainTradeLineItem", NAMESPACES), start=1):
        name = line_item.find(".//ram:Name", NAMESPACES).text
        quantity = float(line_item.find(".//ram:BilledQuantity", NAMESPACES).text)
        price = float(line_item.find(".//ram:ChargeAmount", NAMESPACES).text)
        amount = float(line_item.find(".//ram:LineTotalAmount", NAMESPACES).text)
        articles.append(
            {
                "position": idx,
                "name": name,
                "quantity": quantity,
                "price": price,
                "amount": amount,
            }
        )
    return articles


def extract_totals(root):
    """
    Extract total amounts from the XML root element.

    Args:
        root (xml.etree.ElementTree.Element): Root element of the XML tree.

    Returns:
        tuple: Total net amount, total tax amount, total gross amount.
    """
    totals_element = root.find(".//ram:SpecifiedTradeSettlementHeaderMonetarySummation", NAMESPACES)
    total_net = float(totals_element.find("ram:LineTotalAmount", NAMESPACES).text)
    total_tax = float(totals_element.find("ram:TaxTotalAmount", NAMESPACES).text)
    total_gross = float(totals_element.find("ram:GrandTotalAmount", NAMESPACES).text)
    return total_net, total_tax, total_gross


def extract_vat_percent(root):
    """
    Extract VAT percentage from the XML root element.

    Args:
        root (xml.etree.ElementTree.Element): Root element of the XML tree.

    Returns:
        float: VAT percentage.
    """
    vat_element = root.find(".//ram:ApplicableTradeTax", NAMESPACES)
    vat_percent = float(vat_element.find("ram:RateApplicablePercent", NAMESPACES).text)
    return vat_percent


def calculate_due_date_days(root, issue_date):
    """
    Calculate the number of days until the payment due date.

    Args:
        root (xml.etree.ElementTree.Element): Root element of the XML tree.
        issue_date (datetime.datetime): Invoice issue date.

    Returns:
        int: Number of days until payment is due.
    """
    due_date_str = root.find(".//ram:DueDateDateTime/udt:DateTimeString", NAMESPACES).text
    due_date = datetime.datetime.strptime(due_date_str, "%Y%m%d")
    due_date_days = (due_date - issue_date).days
    return due_date_days


def create_pdf():
    """
    Create the PDF invoice by building the document content and writing to a file.
    """
    # Parse dynamic data from ZUGFeRD XML
    invoice_data = parse_zugferd_invoice(XML_INPUT_FILE)

    # Create PDF document
    doc = SimpleDocTemplate(
        PDF_OUTPUT_FILE, pagesize=A4, canvasmaker=MyCanvas, title="ZUGFeRD Invoice", author=company_info["name"]
    )

    # Set up styles
    normal_style, small_style = get_styles()

    # Build the document content
    story = []

    # Add content sections
    add_seller_address(story, small_style)
    add_buyer_address(story, normal_style, invoice_data["buyer_info"])
    add_invoice_details(story, normal_style, invoice_data)
    add_articles_table(story, invoice_data["articles"], normal_style)
    add_totals_table(story, invoice_data, normal_style)
    add_payment_terms(story, normal_style, invoice_data["due_date_days"])
    add_company_footer(story, small_style)

    # Build the PDF document
    doc.build(story)


def get_styles():
    """
    Set up the paragraph styles used in the document.

    Returns:
        tuple: normal_style, small_style
    """
    stylesheet = getSampleStyleSheet()
    normal_style = stylesheet["Normal"]
    normal_style.fontName = FONT_NAME
    normal_style.fontSize = FONT_SIZE_NORMAL
    normal_style.leading = 14

    small_style = stylesheet["Normal"]
    small_style.fontName = FONT_NAME
    small_style.fontSize = FONT_SIZE_SMALL
    small_style.leading = 12

    return normal_style, small_style


def add_seller_address(story, style):
    """
    Add the seller's address to the story.

    Args:
        story (list): The story list to which the content is added.
        style (ParagraphStyle): The paragraph style to be used.
    """
    seller_address = f"""{company_info['name']}<br/>
    {company_info['street']}<br/>
    {company_info['postcode']} {company_info['city']}<br/>
    {company_info['country']}<br/>
    Tel. {company_info['phone']}<br/>
    Fax {company_info['fax']}<br/>
    {company_info['email']}<br/>
    {company_info['url']}"""
    p_seller_address = Paragraph(seller_address, style)
    story.append(p_seller_address)
    story.append(Spacer(1, 20))


def add_buyer_address(story, style, buyer_info):
    """
    Add the buyer's address to the story.

    Args:
        story (list): The story list to which the content is added.
        style (ParagraphStyle): The paragraph style to be used.
        buyer_info (dict): Dictionary containing buyer information.
    """
    buyer_address = f"""{buyer_info['name']}<br/>
    {buyer_info.get('person_name', '')}<br/>
    {buyer_info['street']}<br/>
    {buyer_info['postcode']} {buyer_info['city']}<br/>
    {buyer_info['country']}"""
    p_buyer_address = Paragraph(buyer_address, style)
    story.append(p_buyer_address)
    story.append(Spacer(1, 20))


def add_invoice_details(story, style, invoice_data):
    """
    Add the invoice details to the story.

    Args:
        story (list): The story list to which the content is added.
        style (ParagraphStyle): The paragraph style to be used.
        invoice_data (dict): Dictionary containing invoice data.
    """
    date_str = invoice_data["invoice_date"].strftime("%d.%m.%Y")

    invoice_details = [
        ["Rechnungsnummer:", invoice_data["invoice_number"]],
        ["Liefer- und Rechnungsdatum:", date_str],
        ["Beträge in", CURRENCY],
    ]

    t_invoice_details = Table(invoice_details, colWidths=[150, 200])

    t_invoice_details.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONT", (0, 0), (-1, -1), FONT_NAME, FONT_SIZE_NORMAL),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    story.append(t_invoice_details)
    story.append(Spacer(1, 20))


def add_articles_table(story, articles, style):
    """
    Add the table of articles to the story.

    Args:
        story (list): The story list to which the content is added.
        articles (list): List of articles to be included in the table.
        style (ParagraphStyle): The paragraph style to be used.
    """
    headers = ["Pos.", "Artikelbeschreibung", "Menge", "Preis", "Betrag"]
    table_data = [headers]

    for article in articles:
        position = article["position"]
        name = article["name"]
        quantity = article["quantity"]
        price = article["price"]
        amount = article["amount"]
        row = [str(position), name, f"{quantity:.2f}", f"{price:.2f}", f"{amount:.2f}"]
        table_data.append(row)

    t_items = Table(table_data, colWidths=[40, 200, 60, 60, 60])

    t_items.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("FONT", (0, 0), (-1, -1), FONT_NAME, FONT_SIZE_NORMAL),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("ALIGN", (0, 1), (0, -1), "RIGHT"),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    story.append(t_items)
    story.append(Spacer(1, 20))


def add_totals_table(story, invoice_data, style):
    """
    Add the totals table to the story.

    Args:
        story (list): The story list to which the content is added.
        invoice_data (dict): Dictionary containing invoice totals and VAT percent.
        style (ParagraphStyle): The paragraph style to be used.
    """
    total_net = invoice_data["total_net"]
    total_tax = invoice_data["total_tax"]
    total_gross = invoice_data["total_gross"]
    vat_percent = invoice_data["vat_percent"]

    total_data = [
        ["Rechnungssumme netto", "", "", "", f"{total_net:.2f}"],
        [f"zuzüglich {vat_percent:.2f}% MwSt.", "", "", "", f"{total_tax:.2f}"],
        ["Rechnungssumme brutto", "", "", "", f"{total_gross:.2f}"],
    ]

    t_totals = Table(total_data, colWidths=[360, 60])

    t_totals.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, -1), FONT_NAME, FONT_SIZE_NORMAL),
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    story.append(t_totals)
    story.append(Spacer(1, 20))


def add_payment_terms(story, style, due_date_days):
    """
    Add the payment terms to the story.

    Args:
        story (list): The story list to which the content is added.
        style (ParagraphStyle): The paragraph style to be used.
        due_date_days (int): Number of days until payment is due.
    """
    payment_terms = (
        f"Zahlbar innerhalb von {due_date_days} Tagen netto auf unser Konto. "
        f"Bitte geben Sie dabei die Rechnungsnummer an. Skontoabzüge "
        f"werden nicht akzeptiert."
    )
    p_payment_terms = Paragraph(payment_terms, style)
    story.append(p_payment_terms)
    story.append(Spacer(1, 20))


def add_company_footer(story, style):
    """
    Add the company footer to the story.

    Args:
        story (list): The story list to which the content is added.
        style (ParagraphStyle): The paragraph style to be used.
    """
    footer_text = (
        f"{company_info['name']} • Sitz der Gesellschaft • USt-IdNr • {company_info['bank_name']}<br/>"
        f"{company_info['director']} • {company_info['company_registration']} • {company_info['vat_id']} • {company_info['iban']}"
    )
    p_footer = Paragraph(footer_text, style)
    story.append(p_footer)


if __name__ == "__main__":
    create_pdf()
