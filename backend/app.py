from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import smtplib
from email.message import EmailMessage
import time
import os
import socket
import io
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt
import matplotlib
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from PIL import Image as PILImage
import tempfile
from datetime import datetime

# Use non-interactive backend for matplotlib
matplotlib.use('Agg')

print("="*50)
print("WEBANALYZER BACKEND STARTING UP")
print("="*50)

# Get the parent directory (project root) - handle both local and Railway
APP_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(APP_DIR, '..')

# Ensure frontend dir exists and use absolute path
if not os.path.exists(FRONTEND_DIR):
    FRONTEND_DIR = APP_DIR  # Fallback to app directory
else:
    FRONTEND_DIR = os.path.abspath(FRONTEND_DIR)

print(f"APP_DIR: {APP_DIR}")
print(f"FRONTEND_DIR: {FRONTEND_DIR}")
print(f"Static files exist: {os.path.exists(os.path.join(FRONTEND_DIR, 'index.html'))}")

try:
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
    # Configure CORS explicitly
    CORS(app, 
         origins="*",
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
         supports_credentials=False)
    print("✓ Flask app initialized successfully")
except Exception as e:
    print(f"✗ Error initializing Flask app: {e}")
    raise

# Executor for background tasks (email sending)
executor = ThreadPoolExecutor(max_workers=2)

REPORTS_DIR = os.path.join(os.path.dirname(__file__), 'reports')
if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)
    print(f"✓ Created reports directory: {REPORTS_DIR}")
else:
    print(f"✓ Reports directory exists: {REPORTS_DIR}")

LOGO_PATH = os.path.abspath(os.path.join(APP_DIR, '..', 'WebAnalayzer_logo.png'))
print(f"LOGO_PATH: {LOGO_PATH}, exists: {os.path.exists(LOGO_PATH)}")
print("="*50)

# ==== DEBUG ENDPOINTS ====
@app.route("/", methods=["GET"])
def root():
    return jsonify({"message": "WebAnalyzer API is running", "status": "ok"})

@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({"status": "ok", "service": "WebAnalyzer"})

# ========================

# 1. SEO ANALYSIS FUNCTION
def seo_analysis(url):
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        print(f"Analyzing SEO for: {url}")
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.title.string if soup.title else "Missing"

        meta_desc = soup.find("meta", attrs={"name": "description"})
        meta_status = "Present" if meta_desc else "Missing"

        h1_tags = soup.find_all("h1")
        h1_count = len(h1_tags)

        images = soup.find_all("img")
        images_without_alt = 0
        for img in images:
            if not img.get("alt"):
                images_without_alt += 1

        print(f"SEO analysis complete for {url}")
        return {
            "url": url,
            "title": title,
            "meta_description": meta_status,
            "h1_count": h1_count,
            "images_without_alt": images_without_alt,
            "total_images": len(images)
        }
    except Exception as e:
        print(f"SEO Analysis Error: {str(e)}")
        raise Exception(f"SEO Analysis failed: {str(e)}")

# 2. PERFORMANCE ANALYSIS
def performance_analysis(url):
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        print(f"Analyzing Performance for: {url}")
        start_time = time.time()
        response = requests.get(url, timeout=10)
        response_time = (time.time() - start_time) * 1000
        
        # Response time score (lower is better)
        score = max(10, min(100, int(100 - (response_time / 10))))
        
        print(f"Performance analysis complete for {url} (Response time: {response_time:.2f}ms, Score: {score})")
        return {
            "score": score,
            "response_time": response_time,
            "status_code": response.status_code
        }
    except Exception as e:
        print(f"Performance Analysis Error: {str(e)}")
        return {
            "score": 50,
            "response_time": 0,
            "status_code": 0
        }

# 3. REPORT GENERATION (Text)
def generate_report(seo, performance):
    report = f"""
AI WEBSITE ANALYSIS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

WEBSITE ANALYZED: {seo['url']}

SEO ANALYSIS:
- Title Tag: {seo['title']}
- Meta Description: {seo['meta_description']}
- Number of H1 Tags: {seo['h1_count']}
- Total Images: {seo['total_images']}
- Images without ALT text: {seo['images_without_alt']}

PERFORMANCE ANALYSIS:
- Website Performance Score: {performance['score']}/100
- Response Time: {performance['response_time']:.2f}ms
- Status Code: {performance['status_code']}

RECOMMENDATIONS:
- Add meta description if missing
- Use only one H1 tag per page
- Add ALT text to all images for better SEO
- Optimize images to improve loading speed
- Ensure response time is under 3000ms for better user experience
"""
    return report

# 4. EMAIL SENDING FUNCTION WITH PDF ATTACHMENT
def send_email(user_email, report, pdf_path):
    try:
        sender_email = "harshavardhankatta5@gmail.com"
        app_password = "jfvr czuu iwrr acyf"

        msg = EmailMessage()
        msg.set_content(report)
        msg["Subject"] = "AI Website Growth Analysis Report"
        msg["From"] = sender_email
        msg["To"] = user_email

        # Attach PDF
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as attachment:
                msg.add_attachment(attachment.read(), maintype='application', subtype='pdf', filename='analysis_report.pdf')
            print(f"PDF attached to email")

        print(f"Sending email to: {user_email}")
        # Set socket timeout to prevent hanging
        socket.setdefaulttimeout(10)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)
        
        print(f"Email sent successfully to: {user_email}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"Email Auth Error: {str(e)}")
        print("Note: Email not sent due to authentication error, but PDF was generated")
        return False
    except socket.timeout as e:
        print(f"Email Timeout Error: {str(e)}")
        print("Note: Email sending timed out, but PDF was generated")
        return False
    except Exception as e:
        print(f"Email Sending Error: {str(e)}")
        print("Note: Email failed but PDF analysis was completed")
        return False

# 5. PDF GENERATION WITH CHARTS
# 5. GENERATE SMART RECOMMENDATIONS BASED ON ANALYSIS
def generate_recommendations(seo, performance):
    recommendations = []
    
    # SEO Recommendations
    if seo['meta_description'] == 'Missing':
        recommendations.append("✓ Add meta description to home page (recommended 150-160 characters)")
    else:
        recommendations.append("✓ Meta description present - ensure it's compelling and keyword-rich")
    
    if seo['h1_count'] > 1:
        recommendations.append("✓ Use only ONE H1 tag per page for better SEO hierarchy")
    elif seo['h1_count'] == 0:
        recommendations.append("✓ Add an H1 tag to your main pages for better SEO")
    
    if seo['images_without_alt'] > 0:
        recommendations.append(f"✓ Add ALT text to {seo['images_without_alt']} images for accessibility and SEO")
    
    if seo['title'] == 'Missing':
        recommendations.append("✓ Add a descriptive title tag (optimal: 50-60 characters)")
    
    # Performance Recommendations
    if performance['score'] < 60:
        recommendations.append("✓ Website performance is slow - consider image optimization and caching")
    elif performance['score'] < 80:
        recommendations.append("✓ Optimize assets to improve page load speed")
    
    if performance['response_time'] > 3000:
        recommendations.append("✓ Response time exceeds 3 seconds - implement CDN for faster delivery")
    elif performance['response_time'] > 2000:
        recommendations.append("✓ Reduce server response time through database optimization and caching")
    
    # Content Recommendations
    recommendations.append("✓ Create descriptive, unique titles for each page (50-60 chars)")
    recommendations.append("✓ Write engaging meta descriptions with target keywords (150-160 chars)")
    recommendations.append("✓ Use internal linking to improve crawlability and user navigation")
    recommendations.append("✓ Optimize images (compress, use modern formats like WebP)")
    recommendations.append("✓ Implement lazy loading for images below the fold")
    
    # Technical Recommendations
    recommendations.append("✓ Enable GZIP compression to reduce file transfer sizes")
    recommendations.append("✓ Minify CSS and JavaScript files to reduce load times")
    recommendations.append("✓ Use browser caching to improve repeat visitor load times")
    recommendations.append("✓ Implement structured data (Schema.org) for better rich snippets")
    recommendations.append("✓ Ensure mobile responsiveness across all devices")
    recommendations.append("✓ Implement SSL/HTTPS for secure data transmission")
    
    # UX Recommendations
    recommendations.append("✓ Ensure clear navigation hierarchy on all pages")
    recommendations.append("✓ Use readable fonts (minimum 16px for body text)")
    recommendations.append("✓ Implement a clear call-to-action (CTA) strategy")
    recommendations.append("✓ Design mobile-first experience for growing mobile traffic")
    recommendations.append("✓ Reduce bounce rate with engaging above-the-fold content")
    
    return recommendations

def generate_pdf_report(seo, performance, user_email):
    try:
        print("Generating PDF report...")
        
        # Sanitize email for filename
        sanitized_email = ''.join([c if c.isalnum() else '_' for c in user_email])
        # Create temporary file (include email to help lookup)
        pdf_path = os.path.join(REPORTS_DIR, f"report_{sanitized_email}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        
        # Create PDF with better margins
        doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                               rightMargin=0.6*inch,
                               leftMargin=0.6*inch,
                               topMargin=0.6*inch,
                               bottomMargin=0.6*inch)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles - more professional
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#ffffff'),
            spaceAfter=6,
            spaceBefore=6,
            alignment=TA_CENTER
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#404040'),
            spaceAfter=2,
            spaceBefore=2,
            alignment=TA_CENTER
        )
        
        section_heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#ffffff'),
            spaceAfter=8,
            spaceBefore=8,
            leftIndent=6
        )
        
        # Header with Logo and Title
        header_table_data = []
        if os.path.exists(LOGO_PATH):
            try:
                img = Image(LOGO_PATH, width=1*inch, height=1*inch)
                header_table_data.append([img, Paragraph("AI Website Analysis Report", title_style)])
            except:
                header_table_data.append([Paragraph("AI Website Analysis Report", title_style)])
        else:
            header_table_data.append([Paragraph("AI Website Analysis Report", title_style)])
        
        header_table = Table(header_table_data, colWidths=[1.2*inch, 5.3*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1a73e8')),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 0.15*inch))
        
        # Website Info Section
        info_data = [
            ['Website URL:', seo['url']],
            ['Analysis Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Recipient:', user_email]
        ]
        
        info_table = Table(info_data, colWidths=[1.5*inch, 4.84*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f5f5')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 0.15*inch))
        
        # SEO Analysis Section Header
        seo_header = Table([['SEO ANALYSIS']], colWidths=[6.34*inch])
        seo_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1a73e8')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGNMENT', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(seo_header)
        
        # SEO Metrics Table - Compact
        seo_data = [
            ['Metric', 'Status', 'Recommendation'],
            ['Title Tag', seo['title'][:30], 'Use descriptive, unique titles'],
            ['Meta Description', seo['meta_description'], 'Add compelling description (160 chars)'],
            ['H1 Tags', str(seo['h1_count']), 'Use only 1 H1 per page'],
            ['Total Images', str(seo['total_images']), 'Optimize image sizes'],
            ['Images without ALT', str(seo['images_without_alt']), 'Add ALT text to all images'],
        ]
        
        seo_table = Table(seo_data, colWidths=[1.5*inch, 1.5*inch, 3.34*inch])
        seo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34a853')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#000000')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f0f7f0')])
        ]))
        
        elements.append(seo_table)
        elements.append(Spacer(1, 0.1*inch))
        
        # SEO Chart
        seo_chart_path = create_seo_chart(seo)
        if seo_chart_path:
            img = Image(seo_chart_path, width=6.34*inch, height=2.5*inch)
            elements.append(img)
        
        elements.append(Spacer(1, 0.15*inch))
        
        # Performance Analysis Section Header
        perf_header = Table([['PERFORMANCE ANALYSIS']], colWidths=[6.34*inch])
        perf_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ea4335')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGNMENT', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(perf_header)
        
        # Performance Metrics Table - Compact
        perf_data = [
            ['Metric', 'Value', 'Status'],
            ['Performance Score', f"{performance['score']}/100", 'Good' if performance['score'] >= 80 else 'Fair' if performance['score'] >= 60 else 'Needs Work'],
            ['Response Time', f"{performance['response_time']:.0f}ms", 'Fast' if performance['response_time'] < 1000 else 'Slow'],
            ['HTTP Status', str(performance['status_code']), 'OK' if performance['status_code'] == 200 else 'Check']
        ]
        
        perf_table = Table(perf_data, colWidths=[2*inch, 1.5*inch, 2.84*inch])
        perf_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fbbc04')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#000000')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#000000')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#fffef0')])
        ]))
        
        elements.append(perf_table)
        elements.append(Spacer(1, 0.1*inch))
        
        # Performance Chart
        perf_chart_path = create_performance_chart(performance)
        if perf_chart_path:
            img = Image(perf_chart_path, width=6.34*inch, height=3*inch)
            elements.append(img)
        
        elements.append(PageBreak())
        
        # Recommendations Section
        rec_header = Table([['COMPREHENSIVE RECOMMENDATIONS']], colWidths=[6.34*inch])
        rec_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#5f6368')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGNMENT', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(rec_header)
        elements.append(Spacer(1, 0.08*inch))
        
        # Generate recommendations based on analysis
        recommendations = generate_recommendations(seo, performance)
        
        # Split recommendations into categories
        categories = {
            'SEO & Content': [],
            'User Experience': [],
            'Performance': [],
            'Technical': []
        }
        
        for rec in recommendations:
            if any(keyword in rec for keyword in ['SEO', 'keyword', 'title', 'meta', 'description', 'H1', 'heading', 'content', 'link']):
                categories['SEO & Content'].append(rec)
            elif any(keyword in rec for keyword in ['UX', 'user', 'mobile', 'responsive', 'navigation', 'accessibility']):
                categories['User Experience'].append(rec)
            elif any(keyword in rec for keyword in ['performance', 'speed', 'load', 'optimize', 'compress', 'cache', 'CDN']):
                categories['Performance'].append(rec)
            else:
                categories['Technical'].append(rec)
        
        # Recommendations table
        rec_rows = [['Category', 'Recommendation']]
        for category, recs in categories.items():
            for i, rec in enumerate(recs):
                if i == 0:
                    rec_rows.append([category, rec])
                else:
                    rec_rows.append(['', rec])
        
        rec_table = Table(rec_rows, colWidths=[1.5*inch, 4.84*inch])
        rec_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5f6368')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f9f9f9')])
        ]))
        
        elements.append(rec_table)
        
        # Footer
        elements.append(Spacer(1, 0.2*inch))
        footer_text = Paragraph(
            "<i>This report was generated by WebAnalyzer AI. Follow these recommendations to improve your website's performance and SEO.</i>",
            ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#666666'),
                alignment=TA_CENTER
            )
        )
        elements.append(footer_text)
        
        # Build PDF
        doc.build(elements)
        print(f"PDF report generated: {pdf_path}")
        return pdf_path
        
    except Exception as e:
        print(f"PDF Generation Error: {str(e)}")
        raise Exception(f"PDF generation failed: {str(e)}")


def generate_and_send_pdf(seo, performance, user_email, text_report):
    try:
        pdf_path = generate_pdf_report(seo, performance, user_email)
        send_email(user_email, text_report, pdf_path)
    except Exception as e:
        print(f"Background PDF generation/send failed: {str(e)}")

# 6. CHART GENERATION FUNCTIONS
def create_seo_chart(seo):
    try:
        print("Creating SEO chart...")
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
        fig.patch.set_facecolor('white')
        
        # Bar chart for images
        categories = ['Total Images', 'With ALT', 'Without ALT']
        values = [seo['total_images'], seo['total_images'] - seo['images_without_alt'], seo['images_without_alt']]
        colors_list = ['#1a73e8', '#34a853', '#ea4335']
        
        ax1.bar(categories, values, color=colors_list)
        ax1.set_ylabel('Count')
        ax1.set_title('Image ALT Tag Analysis')
        ax1.grid(axis='y', alpha=0.3)
        
        # Pie chart for meta tags
        meta_status = [1 if seo['meta_description'] == 'Present' else 0, 1 if seo['meta_description'] == 'Missing' else 0]
        meta_labels = [seo['meta_description'], 'Not ' + seo['meta_description']]
        meta_colors = ['#34a853', '#ea4335']
        
        if meta_status[0] > 0:
            ax2.pie([1], labels=['Meta Description Present'], colors=['#34a853'], autopct='%1.0f%%', startangle=90)
        else:
            ax2.pie([1], labels=['Meta Description Missing'], colors=['#ea4335'], autopct='%1.0f%%', startangle=90)
        
        ax2.set_title('Meta Description Status')
        
        plt.tight_layout()
        
        chart_path = os.path.join(REPORTS_DIR, 'seo_chart.png')
        plt.savefig(chart_path, dpi=100, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return chart_path
    except Exception as e:
        print(f"SEO Chart Error: {str(e)}")
        return None

def create_performance_chart(performance):
    try:
        print("Creating performance chart...")
        fig, ax = plt.subplots(figsize=(8, 6))
        fig.patch.set_facecolor('white')
        
        score = performance['score']
        colors_list = []
        
        if score >= 80:
            colors_list = ['#34a853', '#e8e8e8']
        elif score >= 60:
            colors_list = ['#fbbc04', '#e8e8e8']
        else:
            colors_list = ['#ea4335', '#e8e8e8']
        
        # Create pie chart for performance score
        sizes = [score, 100 - score]
        labels = [f'Score: {score}/100', f'Remaining: {100-score}']
        explode = (0.05, 0)
        
        wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
                                           colors=colors_list, shadow=True, startangle=90)
        
        ax.set_title(f'Website Performance Score\nResponse Time: {performance["response_time"]:.2f}ms', fontsize=14, fontweight='bold')
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(12)
        
        plt.tight_layout()
        
        chart_path = os.path.join(REPORTS_DIR, 'performance_chart.png')
        plt.savefig(chart_path, dpi=100, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return chart_path
    except Exception as e:
        print(f"Performance Chart Error: {str(e)}")
        return None

# HEALTH CHECK
@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for Railway"""
    return jsonify({"status": "ok", "message": "WebAnalyzer backend is running"})

@app.route("/test-analyze", methods=["POST"])
def test_analyze():
    """Test endpoint that doesn't require email"""
    try:
        print("=== Test Analyze request received ===")
        data = request.json
        url = data.get("url")
        email = data.get("email", "test@example.com")
        
        if not url:
            return jsonify({"error": "URL is required"}), 400

        print(f"Test URL: {url}")
        
        print("Starting SEO analysis...")
        seo_result = seo_analysis(url)
        
        print("Starting performance analysis...")
        performance_score = performance_analysis(url)
        
        print("=== Test request completed successfully ===")
        return jsonify({
            "message": "Analysis successful",
            "seo": seo_result,
            "performance": performance_score
        })
    except Exception as e:
        error_msg = str(e)
        print(f"TEST ERROR: {error_msg}")
        return jsonify({"error": error_msg}), 500

# 7. API ENDPOINT
@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        print("=== Analyze request received ===")
        data = request.json
        url = data.get("url")
        email = data.get("email")
        
        if not url or not email:
            return jsonify({"error": "URL and email are required"}), 400

        print(f"URL: {url}, Email: {email}")
        
        print("Starting SEO analysis...")
        seo_result = seo_analysis(url)
        
        print("Starting performance analysis...")
        performance_score = performance_analysis(url)
        
        print("Generating text report...")
        text_report = generate_report(seo_result, performance_score)
        
        print("Queueing quick text email (no attachment) to send immediately in background...")
        # Send a quick text-only email immediately so user receives something fast
        executor.submit(send_email, email, text_report, None)

        print("Queueing PDF generation and attachment send in background...")
        # Generate PDF and send as a follow-up email in background
        executor.submit(generate_and_send_pdf, seo_result, performance_score, email, text_report)

        print("=== Request accepted and background tasks queued ===")
        return jsonify({"message": "Analysis started. A quick summary email will arrive shortly; full PDF will follow when ready."})
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: {error_msg}")
        return jsonify({"error": error_msg}), 500


# SERVE FRONTEND
@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)


@app.route('/download-latest')
def download_latest():
    email = request.args.get('email')
    if not email:
        return jsonify({"error": "email query parameter is required"}), 400

    sanitized_email = ''.join([c if c.isalnum() else '_' for c in email])
    try:
        files = [f for f in os.listdir(REPORTS_DIR) if sanitized_email in f and f.lower().endswith('.pdf')]
        if not files:
            return jsonify({"error": "No report found for this email yet"}), 404
        latest = max(files, key=lambda f: os.path.getmtime(os.path.join(REPORTS_DIR, f)))
        return send_from_directory(REPORTS_DIR, latest, as_attachment=True)
    except Exception as e:
        print(f"Download latest error: {str(e)}")
        return jsonify({"error": "Failed to retrieve report"}), 500


# RUN SERVER
if __name__ == "__main__":
    try:
        port = int(os.environ.get('PORT', 5000))
        print(f"\n{'='*50}")
        print(f"Starting Flask app on port {port}")
        print(f"{'='*50}\n")
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        raise

# For gunicorn
if __name__ != "__main__":
    print("✓ App loaded for gunicorn")

