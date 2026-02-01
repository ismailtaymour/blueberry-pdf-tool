import streamlit as st
from fpdf import FPDF
from bs4 import BeautifulSoup
import tempfile

# --- 1. PDF GENERATION ENGINE (Fixed Formatting) ---
class PDF(FPDF):
    def header(self):
        self.set_fill_color(30, 60, 114) # Deep Blue
        self.rect(0, 0, 210, 45, 'F')
        self.set_font('Arial', 'B', 22)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 10)
        self.cell(0, 10, 'BlueberryAI - EGX30 Market Intelligence', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.set_xy(10, 22)
        self.cell(0, 5, 'AI-Generated Technical Analysis | For Informational Purposes Only', 0, 1, 'C')
        self.set_font('Arial', '', 9)
        self.set_text_color(200, 200, 200)
        self.cell(0, 8, 'Report Generated: Feb 1, 2026 | EGX 30 Level: 47,662 | Cairo Time: 18:45 EET', 0, 1, 'C')
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'BlueBerry AI Trader | Page {self.page_no()}', 0, 0, 'C')

    def check_page_break(self, height_needed):
        if self.get_y() + height_needed > 270:
            self.add_page()

    def section_header(self, title):
        self.check_page_break(20)
        self.ln(5)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(44, 62, 80)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 10, f"  {title}", 0, 1, 'L', fill=True)
        self.ln(3)

    def alert_box(self, title, text):
        self.check_page_break(40)
        self.set_fill_color(255, 235, 238)
        self.set_draw_color(231, 76, 60)
        self.set_line_width(0.5)
        start_y = self.get_y()
        self.rect(10, start_y, 190, 35, 'DF')
        self.set_xy(15, start_y + 5)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(192, 57, 43)
        self.cell(0, 5, title, 0, 1)
        self.set_xy(15, start_y + 12)
        self.set_font('Arial', '', 10)
        self.set_text_color(60, 0, 0)
        self.multi_cell(180, 5, text)
        self.ln(5)
        self.set_line_width(0.2)

    def content_card(self, ticker, name, setup_type, details, table_data, rationale, confidence, mode='buy'):
        self.check_page_break(80)
        if mode == 'buy':
            head_fill, badge_fill = (52, 152, 219), (46, 204, 113)
        else:
            head_fill, badge_fill = (231, 76, 60), (192, 57, 43)

        self.set_fill_color(*head_fill)
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 12)
        self.cell(25, 8, f" {ticker}", 0, 0, 'L', fill=True)
        self.set_text_color(80, 80, 80)
        self.set_font('Arial', '', 10)
        self.cell(100, 8, f"  {name}", 0, 0, 'L')
        self.set_fill_color(*badge_fill)
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 8)
        self.cell(65, 8, setup_type, 0, 1, 'C', fill=True)
        self.ln(2)

        self.set_text_color(0, 0, 0)
        self.set_font('Arial', '', 9)
        for line in details:
            self.multi_cell(0, 5, line)
            self.ln(1)

        if table_data:
            self.ln(2)
            self.set_font('Arial', 'B', 8)
            self.set_fill_color(245, 245, 245)
            self.set_draw_color(200, 200, 200)
            col_width = 190 / len(table_data)
            for key in table_data.keys():
                self.cell(col_width, 6, key, 1, 0, 'C', fill=True)
            self.ln()
            self.set_font('Arial', '', 9)
            for val in table_data.values():
                self.cell(col_width, 8, str(val), 1, 0, 'C')
            self.ln(10)

        if rationale:
            self.set_fill_color(245, 248, 250)
            self.rect(10, self.get_y(), 190, 15, 'F')
            self.set_xy(12, self.get_y()+2)
            self.set_font('Arial', 'I', 9)
            self.multi_cell(186, 5, f"Rationale: {rationale}")
        
        if confidence:
            self.ln(2)
            self.set_font('Arial', 'B', 9)
            if "HIGH" in confidence: self.set_text_color(39, 174, 96)
            elif "MEDIUM" in confidence: self.set_text_color(243, 156, 18)
            else: self.set_text_color(192, 57, 43)
            self.cell(0, 5, confidence, 0, 1, 'R')
        self.ln(5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

# --- 2. HTML PARSER ---
def parse_and_generate_pdf(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # 1. Alert Box
    alert = soup.find(class_='alert-box')
    if alert:
        title = alert.find('h3').get_text(strip=True)
        text = alert.find('p').get_text(strip=True)
        pdf.alert_box(title, text)

    # 2. Index Status
    pdf.section_header("Index Technical Status")
    index_card = soup.find(class_='index-card')
    if index_card:
        rows = index_card.find_all(class_='metric-row')
        pdf.set_font('Arial', '', 9)
        pdf.set_fill_color(250, 250, 250)
        # Process in pairs for 2-column layout
        for i in range(0, len(rows), 2):
            label1 = rows[i].find(class_='metric-label').get_text(strip=True)
            val1 = rows[i].find(class_='metric-value').get_text(strip=True)
            pdf.cell(35, 7, label1, 1, 0, 'L', fill=True)
            pdf.cell(60, 7, val1, 1, 0, 'L')
            
            if i + 1 < len(rows):
                label2 = rows[i+1].find(class_='metric-label').get_text(strip=True)
                val2 = rows[i+1].find(class_='metric-value').get_text(strip=True)
                pdf.cell(35, 7, label2, 1, 0, 'L', fill=True)
                pdf.cell(60, 7, val2, 1, 1, 'L')
            else:
                pdf.ln()

    # 3. Market Assessment
    pdf.section_header("Market Trend Assessment")
    assess = soup.find(class_='market-assessment')
    if assess:
        for tag in assess.find_all(['h3', 'p']):
            if tag.name == 'h3':
                pdf.ln(3)
                pdf.set_font('Arial', 'B', 10)
                pdf.set_text_color(44, 62, 80)
                pdf.cell(0, 6, tag.get_text(strip=True), 0, 1)
            else:
                pdf.set_font('Arial', '', 9)
                pdf.set_text_color(0, 0, 0)
                pdf.multi_cell(0, 5, tag.get_text(strip=True))
                pdf.ln(2)

    # 4. Process Cards (Buy/Sell)
    sections = soup.find_all(class_='section')
    for section in sections:
        title = section.find(class_='section-title')
        if not title: continue
        title_text = title.get_text(strip=True)
        
        # Skip sections we already handled
        if "Index" in title_text or "Assessment" in title_text or "Watchlist" in title_text or "Notes" in title_text:
            continue
            
        pdf.section_header(title_text)
        mode = 'sell' if "Reduce" in title_text or "Sell" in title_text else 'buy'
        
        cards = section.find_all(class_='setup-card')
        for card in cards:
            ticker = card.find(class_='ticker').get_text(strip=True)
            name = card.find(class_='company-name').get_text(strip=True)
            setup = card.find(class_='setup-type').get_text(strip=True)
            
            # Extract details paragraphs
            details_div = card.find(class_='technical-details')
            details = [p.get_text(strip=True) for p in details_div.find_all('p')] if details_div else []
            
            # Extract Table
            table_data = {}
            params = card.find(class_='trade-params')
            if params:
                boxes = params.find_all(class_='param-box')
                for box in boxes:
                    lbl = box.find(class_='param-label').get_text(strip=True)
                    val = box.find(class_='param-value').get_text(strip=True)
                    table_data[lbl] = val
            
            # Rationale
            rationale_div = card.find(class_='rationale')
            rationale = rationale_div.get_text(strip=True).replace("Rationale:", "").strip() if rationale_div else ""
            
            # Confidence
            conf_span = card.find(class_='confidence')
            conf = conf_span.get_text(strip=True) if conf_span else ""
            
            pdf.content_card(ticker, name, setup, details, table_data, rationale, conf, mode)

    # 5. Watchlist
    pdf.section_header("Watchlist - Additional Opportunities")
    wl = soup.find(class_='watchlist')
    if wl:
        items = wl.find_all(class_='watchlist-item')
        for item in items:
            pdf.check_page_break(35)
            pdf.set_fill_color(255, 248, 240)
            pdf.rect(10, pdf.get_y(), 190, 30, 'F')
            pdf.set_xy(15, pdf.get_y() + 5)
            
            h4 = item.find('h4').get_text(strip=True)
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 5, h4, 0, 1)
            
            ps = item.find_all('p')
            pdf.set_font('Arial', '', 9)
            for p in ps:
                pdf.cell(0, 5, p.get_text(strip=True), 0, 1)
            pdf.ln(5)

    # 6. Notes
    pdf.add_page()
    pdf.section_header("Technical Market Notes")
    notes_div = soup.find(class_='market-notes')
    if notes_div:
        lis = notes_div.find_all('li')
        pdf.set_font('Arial', '', 9)
        for li in lis:
            pdf.cell(5, 5, chr(149), 0, 0)
            pdf.multi_cell(0, 5, li.get_text(strip=True))
            pdf.ln(2)

    return pdf

# --- 3. STREAMLIT INTERFACE ---
st.set_page_config(page_title="BlueberryAI Formatter", layout="centered")
st.title("📄 BlueberryAI PDF Generator")
st.write("Upload your HTML report to generate the formatted PDF.")

uploaded_file = st.file_uploader("Choose HTML file", type="html")

if uploaded_file is not None:
    if st.button("Generate PDF"):
        with st.spinner("Parsing and Formatting..."):
            try:
                html_content = uploaded_file.getvalue().decode("utf-8")
                pdf = parse_and_generate_pdf(html_content)
                
                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    pdf.output(tmp.name)
                    with open(tmp.name, "rb") as f:
                        pdf_bytes = f.read()
                
                st.success("PDF Generated Successfully!")
                st.download_button(
                    label="📥 Download Styled PDF",
                    data=pdf_bytes,
                    file_name="BlueberryAI_Market_Report.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error processing file: {e}")
