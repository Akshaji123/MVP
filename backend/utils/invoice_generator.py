from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
import os

class InvoiceGenerator:
    def __init__(self, output_dir="/app/invoices"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        
    def generate_invoice(self, invoice_data: dict) -> str:
        """Generate PDF invoice and return file path"""
        filename = f"invoice_{invoice_data['invoice_number']}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        # Company Header
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#4338ca'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        story.append(Paragraph("HiringReferrals", header_style))
        story.append(Paragraph("AI-Powered Recruitment Platform", self.styles['Normal']))
        story.append(Spacer(1, 0.5*inch))
        
        # Invoice Title
        title_style = ParagraphStyle(
            'InvoiceTitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=colors.black,
            spaceAfter=20
        )
        story.append(Paragraph(f"INVOICE #{invoice_data['invoice_number']}", title_style))
        
        # Invoice Details Table
        details_data = [
            ['Invoice Date:', invoice_data['issue_date'], 'Due Date:', invoice_data['due_date']],
            ['Bill To:', invoice_data['company_name'], 'Status:', invoice_data['status'].upper()],
        ]
        
        details_table = Table(details_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
        details_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.grey),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(details_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Line Items
        items_data = [['Description', 'Quantity', 'Rate', 'Amount']]
        currency_symbol = invoice_data.get('currency_symbol', invoice_data['currency'])
        
        for item in invoice_data['items']:
            items_data.append([
                item['description'],
                str(item['quantity']),
                f"{currency_symbol} {item['rate']:.2f}",
                f"{currency_symbol} {item['amount']:.2f}"
            ])
        
        # Add totals
        items_data.append(['', '', 'Subtotal:', f"{currency_symbol} {invoice_data['amount']:.2f}"])
        items_data.append(['', '', 'Tax:', f"{currency_symbol} {invoice_data['tax_amount']:.2f}"])
        items_data.append(['', '', 'Total:', f"{currency_symbol} {invoice_data['total_amount']:.2f}"])
        
        items_table = Table(items_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4338ca')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -4), colors.beige),
            ('GRID', (0, 0), (-1, -4), 1, colors.black),
            ('FONTNAME', (2, -3), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (2, -1), (-1, -1), 12),
            ('BACKGROUND', (2, -1), (-1, -1), colors.HexColor('#a3e635')),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Notes
        if invoice_data.get('notes'):
            story.append(Paragraph("<b>Notes:</b>", self.styles['Normal']))
            story.append(Paragraph(invoice_data['notes'], self.styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # Payment Terms
        story.append(Paragraph("<b>Payment Terms:</b>", self.styles['Normal']))
        story.append(Paragraph(invoice_data['payment_terms'], self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        return filepath
