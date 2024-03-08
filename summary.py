from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import re
from transformers import BartTokenizer, BartForConditionalGeneration
# from pdfminer.high_level import extract_text
import os

# Load pre-trained model and tokenizer
model_name = "facebook/bart-large-cnn"
tokenizer = BartTokenizer.from_pretrained(model_name)
model = BartForConditionalGeneration.from_pretrained(model_name)

# Function to check if a sentence is declarative
def is_declarative(sentence):
    return not sentence.endswith('?')

# Function to extract declarative sentences containing financial keywords
def extract_financial_sentences(text):
    # Define financial-related keywords (at least 60 keywords)
    financial_keywords = ['earnings', 'revenue', 'profit', 'loss', 'cash flow', 'ebitda', 'financial performance', 'pbt', 'pat',
                          'net income', 'operating income', 'gross profit', 'expenditure', 'dividend', 'assets', 'liabilities',
                          'equity', 'interest', 'revenue growth', 'cost of goods sold', 'EBIT', 'EBIT margin', 'depreciation',
                          'amortization', 'working capital', 'current ratio', 'quick ratio', 'return on equity', 'return on assets',
                          'profit margin', 'operating margin', 'gross margin', 'cash conversion cycle', 'inventory turnover',
                          'accounts receivable turnover', 'accounts payable turnover', 'debt to equity ratio', 'interest coverage ratio',
                          'operating cash flow', 'free cash flow', 'capital expenditure', 'return on investment', 'net profit margin',
                          'liquidity ratio', 'solvency ratio', 'inventory days', 'accounts receivable days', 'accounts payable days',
                          'return on capital employed', 'earnings before tax', 'earnings after tax', 'net profit', 'cost of revenue',
                          'interest expense', 'net interest income', 'net interest margin', 'shareholder equity', 'capital adequacy ratio']

    # Use regex to extract sentences containing financial keywords
    sentences = re.findall(r'[^.]*?(?:' + '|'.join(financial_keywords) + ')[^.]*\.', text, re.IGNORECASE)

    # Filter out non-declarative sentences
    declarative_sentences = [sentence.strip() for sentence in sentences if is_declarative(sentence)]

    return declarative_sentences

# Function to generate a PDF with formatted content
def generate_pdf(pdf_path, content, company_name):
    pdf = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()

    # Define a custom style for justified text
    justified_style = ParagraphStyle(
        'JustifiedStyle',
        parent=styles['BodyText'],
        alignment=4,  # 0=Left, 1=Center, 2=Right, 4=Justified
    )

    # Define a custom style for centered heading
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading1'],
        alignment=TA_CENTER,  # Set alignment to center
    )

    # Set up the Story (a list of elements) with justified text
    story = []

    # Add the specified heading with centered alignment
    heading_text = f"{company_name} Transcript Summary"
    heading = Paragraph(heading_text, heading_style)
    story.append(heading)
    story.append(Spacer(1, 12))  # Add some space after heading

    # Aggregate all sentences into paragraphs after every 15 sentences
    sentences_count = 0
    paragraph = ""
    for _, sentences in content:
        for sentence in sentences:
            paragraph += sentence + ' '
            sentences_count += 1
            if sentences_count % 15 == 0:
                # Create a new paragraph after every 15 sentences
                story.append(Paragraph(paragraph, justified_style))
                story.append(Spacer(1, 6))  # Add some space between paragraphs
                paragraph = ""

    # If there are remaining sentences, add them as the last paragraph
    if paragraph:
        story.append(Paragraph(paragraph, justified_style))

    # Build the PDF
    pdf.build(story)
    print("successfully generated pdf")
    print("This is the pdf path i am sending "+ pdf_path)
    return pdf_path

# Function to summarize financial content for each page and generate PDF
def summarize_financial_pages_to_pdf(pdf_path, transcript):
    # Extract company name from the file name
    company_name = os.path.splitext(os.path.basename(pdf_path_transcript))[0]

    # Extract and store declarative sentences containing financial keywords for the entire transcript
    all_financial_sentences = extract_financial_sentences(transcript)

    # Generate PDF content
    generate_pdf(pdf_path, [(1, all_financial_sentences)], company_name)

# Example usage

# pdf_path = "output.pdf"
# pdf_path_transcript = "META-Q1-2023-Earnings-Call-Transcript.pdf"
# transcript_text = extract_text(pdf_path_transcript)
# summarize_financial_pages_to_pdf(pdf_path, transcript_text)
