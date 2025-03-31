import re
from reportlab.platypus import Paragraph, Table, TableStyle, Spacer
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet

def parse_tone_analysis(text):
    """
    Parses only the Tone Analysis section from the risk analysis text.
    """
    styles = getSampleStyleSheet()
    
    # Extract the Tone Analysis section
    tone_section = re.search(r"\*\*- Tone Analysis:\*\*(.*?)(?=\*\*- Risk Analysis:|$)", text, re.DOTALL)
    if not tone_section:
        return []
    
    tone_section_text = tone_section.group(1).strip()
    
    # Extract Overall Tone
    tone_match = re.search(r"\* \*\*Overall Tone:\*\* (.+?)(?=\n|$)", tone_section_text)
    tone = tone_match.group(1) if tone_match else "Not available"
    
    # Extract Supporting Phrases
    phrases_section = re.search(r"\* \*\*Supporting Phrases:\*\*(.*?)\* \*\*Explanation:", tone_section_text, re.DOTALL)
    phrases_text = ""
    if phrases_section:
        phrases_text = phrases_section.group(1).strip()
        # Convert bullet points to HTML list for better rendering
        phrases_items = re.findall(r"[ \t]*\* (.+?)(?=\n[ \t]*\*|\n\n|$)", phrases_text, re.DOTALL)
        if phrases_items:
            phrases_text = "<ul>" + "".join([f"<li>{item.strip()}</li>" for item in phrases_items]) + "</ul>"
    phrases = Paragraph(phrases_text, styles["Normal"]) if phrases_text else Paragraph("Not available", styles["Normal"])
    
    # Extract Explanation
    explanation_match = re.search(r"\* \*\*Explanation:\*\* (.+?)(?=\n\n|$)", tone_section_text, re.DOTALL)
    explanation = Paragraph(explanation_match.group(1).strip(), styles["Normal"]) if explanation_match else Paragraph("Not available", styles["Normal"])
    
    tone_data = [
        ["Overall Tone", Paragraph(tone, styles["Normal"])],
        ["Supporting Phrases", phrases],
        ["Explanation", explanation]
    ]
    
    return tone_data

def parse_risk_analysis(text):
    """
    Parses only the Risk Analysis section from the risk analysis text.
    """
    styles = getSampleStyleSheet()
    
    # Extract the Risk Analysis section
    risk_section = re.search(r"\*\*- Risk Analysis:\*\*(.*?)(?=\*\*- Timestamped Insights:|$)", text, re.DOTALL)
    if not risk_section:
        return []
    
    risk_section_text = risk_section.group(1).strip()
    risk_data = []
    
    # Find all risk type entries
    risk_entries = re.findall(r"\* \*\*Risk Type:\*\* (.+?)(?=\* \*\*Risk Type:|$)", risk_section_text, re.DOTALL)
    
    for entry in risk_entries:
        # Extract components of each risk
        risk_type = re.search(r"(.+?)(?=\n[ \t]*\* \*\*Supporting Evidence:|$)", entry)
        supporting_evidence = re.search(r"\* \*\*Supporting Evidence:\*\* (.+?)(?=\n[ \t]*\* \*\*Explanation:|$)", entry, re.DOTALL)
        explanation = re.search(r"\* \*\*Explanation:\*\* (.+?)(?=\n[ \t]*\* \*\*Suggested Mitigation:|$)", entry, re.DOTALL)
        mitigation = re.search(r"\* \*\*Suggested Mitigation:\*\* (.+?)(?=\n|$)", entry, re.DOTALL)
        
        # Add the risk entry to our data
        risk_data.append([
            Paragraph(risk_type.group(1).strip() if risk_type else "Not specified", styles["Normal"]),
            Paragraph(supporting_evidence.group(1).strip() if supporting_evidence else "Not specified", styles["Normal"]),
            Paragraph(explanation.group(1).strip() if explanation else "Not specified", styles["Normal"]),
            Paragraph(mitigation.group(1).strip() if mitigation else "Not specified", styles["Normal"])
        ])
    
    return risk_data

def parse_timestamped_insights(text):
    """
    Parses only the Timestamped Insights section from the risk analysis text.
    Specifically designed for the format:
    * **00:00:00:** Description text here.
    """
    styles = getSampleStyleSheet()
    
    # Extract the Timestamped Insights section
    timestamp_section = re.search(r"\*\*- Timestamped Insights:\*\*(.*?)$", text, re.DOTALL)
    if not timestamp_section:
        return []
    
    timestamp_section_text = timestamp_section.group(1).strip()
    timestamp_data = []
    
    # Corrected pattern to match the format: * **00:00:00:** Description text
    pattern = r"\* \*\*(\d{2}:\d{2}:\d{2}):\*\*(.*?)(?=\n\* \*\*|\Z)"
    timestamp_entries = re.findall(pattern, timestamp_section_text, re.DOTALL)
    
    for timestamp, insight in timestamp_entries:
        timestamp_data.append([
            timestamp,
            Paragraph(insight.strip(), styles["Normal"])
        ])
    
    return timestamp_data

def create_timestamped_insights_table(elements, timestamp_data):
    """
    Creates a formatted table just for the timestamp insights
    """
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph("Timestamped Insights", styles["Heading1"]))
    elements.append(Spacer(1, 0.1 * inch))

    if not timestamp_data:
        elements.append(Paragraph("No timestamped insights available.", styles["Normal"]))
        elements.append(Spacer(1, 0.25 * inch))
        return

    # Add headers to data
    headers = [Paragraph("<b>Timestamp</b>", styles["Normal"]), Paragraph("<b>Key Insight</b>", styles["Normal"])]
    full_data = [headers] + timestamp_data

    table = Table(full_data, colWidths=[1 * inch, 5 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 0.25 * inch))

def create_tone_analysis_table(tone_data, elements):
    """
    Creates and adds the Tone Analysis table to the elements list.
    """
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph("Tone Analysis", styles["Heading1"]))
    elements.append(Spacer(1, 0.1 * inch))
    
    if not tone_data:
        elements.append(Paragraph("No tone analysis data available.", styles["Normal"]))
        elements.append(Spacer(1, 0.25 * inch))
        return
    
    # Add headers
    headers = [Paragraph("<b>Category</b>", styles["Normal"]), Paragraph("<b>Details</b>", styles["Normal"])]
    full_data = [headers] + tone_data
    
    # Create table
    table = Table(full_data, colWidths=[1.5 * inch, 4.5 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.25 * inch))

def create_risk_analysis_table(risk_data, elements):
    """
    Creates and adds the Risk Analysis table to the elements list.
    """
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph("Risk Analysis", styles["Heading1"]))
    elements.append(Spacer(1, 0.1 * inch))
    
    if not risk_data:
        elements.append(Paragraph("No risk analysis data available.", styles["Normal"]))
        elements.append(Spacer(1, 0.25 * inch))
        return
    
    # Add headers
    headers = [
        Paragraph("<b>Risk Type</b>", styles["Normal"]),
        Paragraph("<b>Supporting Evidence</b>", styles["Normal"]),
        Paragraph("<b>Explanation</b>", styles["Normal"]),
        Paragraph("<b>Suggested Mitigation</b>", styles["Normal"])
    ]
    full_data = [headers] + risk_data
    
    # Create table with adjusted column widths
    col_widths = [1.2 * inch, 1.6 * inch, 1.8 * inch, 1.4 * inch]
    table = Table(full_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.25 * inch))


# def generate_pdf(result):
#     """
#     Main function to generate the PDF with all three tables.
#     """
#     from io import BytesIO
#     from reportlab.lib.pagesizes import letter
#     from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
#     from reportlab.lib.styles import getSampleStyleSheet
    
#     buffer = BytesIO()
#     doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
#     elements = []
#     styles = getSampleStyleSheet()
    
#     # Add Title
#     elements.append(Paragraph("Risk Analysis Report", styles["Title"]))
#     elements.append(Spacer(1, 0.25 * inch))
    
#     analysis_text = result.get("risk_analysis", "No analysis available.")
    
#     # Parse data for each table
#     tone_data = parse_tone_analysis(analysis_text)
#     risk_data = parse_risk_analysis(analysis_text)
#     timestamp_data = parse_timestamped_insights(analysis_text)
    
#     # Create and add each table to elements
#     create_tone_analysis_table(tone_data, elements)
#     create_risk_analysis_table(risk_data, elements)
#     create_timestamped_insights_table(elements,timestamp_data)
    
#     # Build PDF
#     doc.build(elements)
#     buffer.seek(0)
    
#     pdf_filename = "risk_analysis_report.pdf"
#     with open(pdf_filename, "wb") as f:
#         f.write(buffer.getbuffer())
    
#     print(f"PDF report generated: {pdf_filename}")
#     return pdf_filename
