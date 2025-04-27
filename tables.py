import re
from reportlab.platypus import Paragraph, Table, TableStyle, Spacer
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet

def parse_tone_analysis(text):
    """
    More robust parsing of the Tone Analysis section from the risk analysis text.
    """
    styles = getSampleStyleSheet()
    
    # Extract the Tone Analysis section - more flexible pattern
    tone_section = re.search(r"\*?\*?[-\s]*Tone Analysis:?\*?\*?(.*?)(?=\*?\*?[-\s]*Risk Analysis|\*?\*?[-\s]*Timestamped Insights|$)", 
                          text, re.DOTALL | re.IGNORECASE)
    
    if not tone_section:
        return []
    
    tone_section_text = tone_section.group(1).strip()
    
    # Extract Overall Tone with more flexible pattern
    tone_match = re.search(r"(?:[-\*\s]*|^)(?:Overall Tone:?|Tone:?)\s*\*?\*?\s*([^*\n]+)", tone_section_text, re.IGNORECASE)
    tone = tone_match.group(1).strip() if tone_match else "Not available"
    
    # Extract Supporting Phrases - more flexible pattern
    phrases_section = re.search(r"(?:[-\*\s]*|^)Supporting Phrases:?\*?\*?(.*?)(?:[-\*\s]*Explanation:|\n\n|$)", 
                             tone_section_text, re.DOTALL | re.IGNORECASE)
    
    phrases_text = ""
    if phrases_section:
        phrases_text = phrases_section.group(1).strip()
        # Convert various bullet formats to HTML list
        # This handles asterisks, dashes, or numbers followed by text
        phrases_items = re.findall(r"(?:[-\*•\s]+|\d+[\.\)]\s+)([^-\*•\n]+)(?=\n|$)", phrases_text, re.MULTILINE)
        if phrases_items:
            phrases_text = "<ul>" + "".join([f"<li>{item.strip()}</li>" for item in phrases_items]) + "</ul>"
        else:
            # If no bullet points found, keep the original text
            phrases_text = phrases_section.group(1).strip()
    
    phrases = Paragraph(phrases_text, styles["Normal"]) if phrases_text else Paragraph("Not available", styles["Normal"])
    
    # Extract Explanation - more flexible pattern
    explanation_match = re.search(r"(?:[-\*\s]*|^)Explanation:?\*?\*?\s*([^*].*?)(?=\n\n|\n[-\*]|$)", 
                               tone_section_text, re.DOTALL | re.IGNORECASE)
    
    explanation = (Paragraph(explanation_match.group(1).strip(), styles["Normal"]) 
                  if explanation_match else Paragraph("Not available", styles["Normal"]))
    
    tone_data = [
        ["Overall Tone", Paragraph(tone, styles["Normal"])],
        ["Supporting Phrases", phrases],
        ["Explanation", explanation]
    ]
    
    return tone_data

def parse_risk_analysis(text):
    """
    More robust parsing of the Risk Analysis section.
    """
    styles = getSampleStyleSheet()
    
    # Extract the Risk Analysis section - more flexible pattern
    risk_section = re.search(r"\*?\*?[-\s]*Risk Analysis:?\*?\*?(.*?)(?=\*?\*?[-\s]*Timestamped Insights|\*?\*?[-\s]*Strengths and Opportunities|$)", 
                          text, re.DOTALL | re.IGNORECASE)
    
    if not risk_section:
        return []
    
    risk_section_text = risk_section.group(1).strip()
    risk_data = []
    
    # Find all risk type entries - more flexible pattern
    # This pattern looks for "Risk Type:" followed by any text
    risk_entries = re.findall(r"(?:[-\*\s]*|^)Risk Type:?\s*\*?\*?\s*([^*\n]+)(.*?)(?=(?:[-\*\s]*|^)Risk Type:|$)", 
                           risk_section_text, re.DOTALL | re.IGNORECASE)
    
    for risk_type_match, details in risk_entries:
        risk_type = risk_type_match.strip()
        
        # Extract components with more flexible patterns
        supporting_evidence = re.search(r"(?:[-\*\s]*|^)Supporting Evidence:?\s*\*?\*?\s*(.*?)(?=(?:[-\*\s]*|^)Explanation:|(?:[-\*\s]*|^)Risk Type:|$)", 
                                     details, re.DOTALL | re.IGNORECASE)
                                     
        explanation = re.search(r"(?:[-\*\s]*|^)Explanation:?\s*\*?\*?\s*(.*?)(?=(?:[-\*\s]*|^)Suggested Mitigation:|(?:[-\*\s]*|^)Risk Type:|$)", 
                             details, re.DOTALL | re.IGNORECASE)
                             
        mitigation = re.search(r"(?:[-\*\s]*|^)Suggested Mitigation:?\s*\*?\*?\s*(.*?)(?=$|(?:[-\*\s]*|^)Risk Type:)", 
                            details, re.DOTALL | re.IGNORECASE)
        
        # Add the risk entry to our data
        risk_data.append([
            Paragraph(risk_type, styles["Normal"]),
            Paragraph(supporting_evidence.group(1).strip() if supporting_evidence else "Not specified", styles["Normal"]),
            Paragraph(explanation.group(1).strip() if explanation else "Not specified", styles["Normal"]),
            Paragraph(mitigation.group(1).strip() if mitigation else "Not specified", styles["Normal"])
        ])
    
    return risk_data

def parse_timestamped_insights(text):
    """
    More robust parsing of the Timestamped Insights section.
    """
    styles = getSampleStyleSheet()
    
    # Extract the Timestamped Insights section - more flexible pattern
    timestamp_section = re.search(r"\*?\*?[-\s]*Timestamped Insights:?\*?\*?(.*?)(?=\*?\*?[-\s]*Strengths and Opportunities|$)", 
                               text, re.DOTALL | re.IGNORECASE)
    
    if not timestamp_section:
        return []
    
    timestamp_section_text = timestamp_section.group(1).strip()
    timestamp_data = []
    
    # More flexible pattern for timestamps
    # This handles various formats like "00:00:00:", "* 00:00:00:", "- 00:00:00", etc.
    pattern = r"(?:[-\*\s]*|^)(?:\*\*)?(\d{2}:\d{2}:\d{2})(?:\*\*)?:?\s*(.*?)(?=(?:[-\*\s]*|^)(?:\*\*)?(?:\d{2}:\d{2}:\d{2})|$)"
    timestamp_entries = re.findall(pattern, timestamp_section_text, re.DOTALL)
    
    for timestamp, insight in timestamp_entries:
        # Clean up the insight text
        clean_insight = re.sub(r"^\s*[-\*]\s*", "", insight.strip())
        # Remove any remaining markdown formatting
        clean_insight = re.sub(r"\*\*(.*?)\*\*", r"\1", clean_insight)
        
        timestamp_data.append([
            timestamp,
            Paragraph(clean_insight, styles["Normal"])
        ])
    
    return timestamp_data

def parse_strengths_opportunities(text):
    """
    More robust parsing of the Strengths and Opportunities section.
    """
    styles = getSampleStyleSheet()
    
    # Extract the Strengths and Opportunities section - more flexible pattern
    strengths_section = re.search(r"\*?\*?[-\s]*Strengths and Opportunities:?\*?\*?(.*?)$", 
                               text, re.DOTALL | re.IGNORECASE)
    
    if not strengths_section:
        return []
    
    strengths_section_text = strengths_section.group(1).strip()
    strengths_opportunities_data = []
    
    # More flexible pattern for categories
    # This handles various formats of category entries
    pattern = r"(?:[-\*\s]*|^)Category:?\s*\*?\*?\s*([^*\n]+).*?(?:[-\*\s]*|^)Positive Indicator:?\s*\*?\*?\s*(.*?)(?:[-\*\s]*|^)Strategic Impact:?\s*\*?\*?\s*(.*?)(?=(?:[-\*\s]*|^)Category:|$)"
    
    matches = re.findall(pattern, strengths_section_text, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        category, positive_indicator, strategic_impact = match
        # Clean up and add to data
        strengths_opportunities_data.append([
            category.strip(),
            Paragraph(positive_indicator.strip(), styles["Normal"]),
            Paragraph(strategic_impact.strip(), styles["Normal"])
        ])
    
    return strengths_opportunities_data

def create_timestamped_insights_table(elements, timestamp_data):
    """
    Creates a formatted table for the timestamp insights.
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

def create_strengths_opportunities_table(strengths_opportunities_data, elements):
    """
    Creates and adds the Strengths and Opportunities Matrix table to the elements list.
    """
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph("Strengths and Opportunities Matrix", styles["Heading1"]))
    elements.append(Spacer(1, 0.1 * inch))
    
    if not strengths_opportunities_data:
        elements.append(Paragraph("No strengths and opportunities data available.", styles["Normal"]))
        elements.append(Spacer(1, 0.25 * inch))
        return
    
    # Add headers
    headers = [
        Paragraph("<b>CATEGORY</b>", styles["Normal"]),
        Paragraph("<b>POSITIVE INDICATOR</b>", styles["Normal"]),
        Paragraph("<b>STRATEGIC IMPACT</b>", styles["Normal"])
    ]
    full_data = [headers] + strengths_opportunities_data
    
    # Create table
    table = Table(full_data, colWidths=[2.0 * inch, 3.0 * inch, 3.0 * inch])
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

def process_risk_analysis(risk_analysis_text, elements):
    """
    Main function to process the entire risk analysis text and create all tables.
    """
    # Parse and create all tables
    tone_data = parse_tone_analysis(risk_analysis_text)
    create_tone_analysis_table(tone_data, elements)
    
    risk_data = parse_risk_analysis(risk_analysis_text)
    create_risk_analysis_table(risk_data, elements)
    
    timestamp_data = parse_timestamped_insights(risk_analysis_text)
    create_timestamped_insights_table(elements, timestamp_data)
    
    strengths_opportunities_data = parse_strengths_opportunities(risk_analysis_text)
    create_strengths_opportunities_table(strengths_opportunities_data, elements)
    
    return elements