import streamlit as st
from fpdf import FPDF
from bs4 import BeautifulSoup
import tempfile

# --- 1. ROBUST TEXT SANITIZATION ---
def clean_text(text):
    if not text: return ""
    # Standardize quotes and dashes
    replacements = {
        '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '-', '\u2026': '...', '\u00A0': ' '
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    # Force encode to Latin-1 compatible (strips emojis/weird chars that crash PDF)
    return text.encode('latin-1', 'ignore').decode('latin-1')

def safe_get_text(element, default=""):
    if element and hasattr(element, 'get_text'):
        return element.get_text(strip=True)
    return default

# --- 2. PDF ENGINE ---
class PDF(FPDF):
    def header(self):
        self.set_fill_color(30, 60, 114)
        self.rect(0, 0, 210, 45, 'F')
        self.set_font('Arial', 'B', 22)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 10)
        self.cell(0, 10, clean_text('BlueberryAI - EGX30 Market Intelligence'), 0, 1, 'C')
        
        self.set_font('Arial', '', 10)
        self.set_xy(10, 22)
        self.cell(0, 5, clean_text('AI-Generated Technical Analysis | For Informational Purposes Only'), 0, 1, 'C')
        
        self.set_font('Arial', '', 9)
        self.set_text_color(200, 200, 200)
        self.cell(0, 8, clean_text('Report Generated: Feb 1, 2026 | EGX 30 Level: 47,662 | Cairo Time: 18:45 EET'), 0, 1, 'C')
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, clean_text(f'BlueBerry AI Trader | Page {self.page_no()}'), 0, 0, 'C')

    def check_page_break(self, height_needed):
        if self.get_y() + height_needed > 270:
            self.add_page()

    def section_header(self, title):
        self.check_page_break(20)
        self.ln(5)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(44, 62, 80)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 10, f"  {clean_text(title)}", 0, 1, 'L', fill=True)
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
        self.cell(0, 5, clean_text(title), 0, 1)
        self.set_xy(15, start_y + 12)
        self.set_font('Arial', '', 10)
        self.set_text_color(60, 0, 0)
        self.multi_cell(180, 5, clean_text(text))
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
        self.cell(25, 8, f" {clean_text(ticker)}", 0, 0, 'L', fill=True)
        self.set_text_color(80, 80, 80)
        self.set_font('Arial', '', 10)
        self.cell(100, 8, f"  {clean_text(name)}", 0, 0, 'L')
        self.set_fill_color(*badge_fill)
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 8)
        self.cell(65, 8, clean_text(setup_type), 0, 1, 'C', fill=True)
        self.ln(2)

        self.set_text_color(0, 0, 0)
        self.set_font('Arial', '', 9)
        for line in details:
            self.multi_cell(0, 5, clean_text(line))
            self.ln(1)

        if table_data:
            self.ln(2)
            self.set_font('Arial', 'B', 8)
            self.set_fill_color(245, 245, 245)
            self.set_draw_color(200, 200, 200)
            col_width = 190 / len(table_data)
            for key in table_data.keys():
                self.cell(col_width, 6, clean_text(key), 1, 0, 'C', fill=True)
            self.ln()
            self.set_font('Arial', '', 9)
            for val in table_data.values():
                self.cell(col_width, 8, clean_text(str(val)), 1, 0, 'C')
            self.ln(10)

        if rationale:
            self.set_fill_color(245, 248, 250)
            self.rect(10, self.get_y(), 190, 15, 'F')
            self.set_xy(12, self.get_y()+2)
            self.set_font('Arial', 'I', 9)
            self.multi_cell(186, 5, f"Rationale: {clean_text(rationale)}")
        
        if confidence:
            self.ln(2)
            self.set_font('Arial', 'B', 9)
            if "HIGH" in confidence: self.set_text_color(39, 174, 96)
            elif "MEDIUM" in confidence: self.set_text_color(243, 156, 18)
            else: self.set_text_color(192, 57, 43)
            self.cell(0, 5, clean_text(confidence), 0, 1, 'R')
        self.ln(5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def disclaimer_box(self, title, text):
        self.check_page_break(35)
        self.ln(5)
        self.set_fill_color(255, 250, 240) # Light Yellow
        self.set_draw_color(243, 156, 18)
        self.set_line_width(0.5)
        
        start_y = self.get_y()
        self.rect(10, start_y, 190, 30, 'DF')
        
        self.set_xy(15, start_y + 4)
        self.set_font('Arial', 'B', 10)
        self.set_text_color(160, 100, 0)
        self.cell(0, 5, clean_text(title), 0, 1)
        
        self.set_xy(15, start_y + 10)
        self.set_font('Arial', '', 8)
        self.multi_cell(180, 4, clean_text(text))
        self.ln(5)

# --- 3. ROBUST HTML PARSER (HEURISTIC MODE) ---
def parse_and_generate_pdf(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # --- 1. ALERT BOX (Heuristic Search) ---
    # Find any div that has 'alert-box' class OR contains "EXTREME CAUTION"
    alert = soup.find(class_='alert-box')
    if not alert:
        # Fallback: Find h3 with caution text and get its parent
        caution_header = soup.find(lambda tag: tag.name == 'h3' and 'CAUTION' in tag.get_text())
        if caution_header:
            alert = caution_header.parent

    if alert:
        title = safe_get_text(alert.find('h3'))
        text = safe_get_text(alert.find('p'))
        if title or text:
            pdf.alert_box(title, text)

    # --- 2. INDEX STATUS (Heuristic Search) ---
    index_card = soup.find(class_='index-card')
    if not index_card:
        # Fallback: Find label "Current Level" and get the container
        lbl = soup.find(class_='metric-label', string=lambda t: t and 'Current Level' in t)
        if lbl:
             # Go up 3 levels (row -> container -> card) approx
             index_card = lbl.find_parent(class_=lambda x: x and 'card' in x if x else False)

    if index_card:
        pdf.section_header("Index Technical Status")
        rows = index_card.find_all(class_='metric-row')
        pdf.set_font('Arial', '', 9)
        pdf.set_fill_color(250, 250, 250)
        for i in range(0, len(rows), 2):
            label1 = safe_get_text(rows[i].find(class_='metric-label'))
            val1 = safe_get_text(rows[i].find(class_='metric-value'))
            pdf.cell(35, 7, clean_text(label1), 1, 0, 'L', fill=True)
            pdf.cell(60, 7, clean_text(val1), 1, 0, 'L')
            
            if i + 1 < len(rows):
                label2 = safe_get_text(rows[i+1].find(class_='metric-label'))
                val2 = safe_get_text(rows[i+1].find(class_='metric-value'))
                pdf.cell(35, 7, clean_text(label2), 1, 0, 'L', fill=True)
                pdf.cell(60, 7, clean_text(val2), 1, 1, 'L')
            else:
                pdf.ln()

    # --- 3. MARKET ASSESSMENT ---
    assess = soup.find(class_='market-assessment')
    if assess:
        pdf.section_header("Market Trend Assessment")
        for tag in assess.find_all(['h3', 'p']):
            if tag.name == 'h3':
                pdf.ln(3)
                pdf.set_font('Arial', 'B', 10)
                pdf.set_text_color(44, 62, 80)
                pdf.cell(0, 6, clean_text(safe_get_text(tag)), 0, 1)
            else:
                pdf.set_font('Arial', '', 9)
                pdf.set_text_color(0, 0, 0)
                pdf.multi_cell(0, 5, clean_text(safe_get_text(tag)))
                pdf.ln(2)

    # --- 4. CARDS (BUY & SELL) - Ticker-Based Discovery ---
    # Primary Search: class="setup-card"
    cards = soup.find_all(class_='setup-card')
    
    # Fallback: If no cards found via class, look for all 'ticker' elements
    if not cards:
        tickers = soup.find_all(class_='ticker')
        # Get the unique parents of these tickers (assuming parent is the card)
        cards = list(set([t.find_parent('div').find_parent('div') for t in tickers if t.find_parent('div')]))
        # Filter out Nones
        cards = [c for c in cards if c]

    buys = []
    sells = []

    for card in cards:
        setup_type_el = card.find(class_='setup-type')
        is_sell = False
        setup_text = ""
        
        if setup_type_el:
            setup_text = safe_get_text(setup_type_el)
            classes = setup_type_el.get('class', [])
            text_lower = setup_text.lower()
            if 'setup-type-exit' in classes or 'exit' in text_lower or 'reduce' in text_lower:
                is_sell = True
        
        # Safe extractions
        ticker_el = card.find(class_='ticker')
        name_el = card.find(class_='company-name')
        
        if not ticker_el: continue # Skip if malformed

        card_data = {
            'ticker': safe_get_text(ticker_el),
            'name': safe_get_text(name_el),
            'setup': setup_text,
            'details': [safe_get_text(p) for p in card.find(class_='technical-details').find_all('p')] if card.find(class_='technical-details') else [],
            'table': {},
            'rationale': safe_get_text(card.find(class_='rationale')).replace("Rationale:", "").strip(),
            'conf': safe_get_text(card.find(class_='confidence')),
            'mode': 'sell' if is_sell else 'buy'
        }
        
        params = card.find(class_='trade-params')
        if params:
            for box in params.find_all(class_='param-box'):
                lbl = safe_get_text(box.find(class_='param-label'))
                val = safe_get_text(box.find(class_='param-value'))
                if lbl: card_data['table'][lbl] = val

        if is_sell: sells.append(card_data)
        else: buys.append(card_data)

    if buys:
        pdf.section_header("Top Buy Opportunities")
        for c in buys:
            pdf.content_card(c['ticker'], c['name'], c['setup'], c['details'], 
                             c['table'], c['rationale'], c['conf'], mode='buy')

    if sells:
        pdf.section_header("Reduce/Exit Recommendations")
        for c in sells:
            pdf.content_card(c['ticker'], c['name'], c['setup'], c['details'], 
                             c['table'], c['rationale'], c['conf'], mode='sell')

    # --- 5. WATCHLIST ---
    wl_items = soup.find_all(class_='watchlist-item')
    if wl_items:
        pdf.section_header("Watchlist - Additional Opportunities")
        for item in wl_items:
            pdf.check_page_break(35)
            pdf.set_fill_color(255, 248, 240)
            pdf.rect(10, pdf.get_y(), 190, 30, 'F')
            pdf.set_xy(15, pdf.get_y() + 5)
            
            h4 = safe_get_text(item.find('h4'))
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 5, clean_text(h4), 0, 1)
            
            ps = item.find_all('p')
            pdf.set_font('Arial', '', 9)
            for p in ps:
                pdf.cell(0, 5, clean_text(safe_get_text(p)), 0, 1)
            pdf.ln(5)

    # --- 6. NOTES ---
    notes_div = soup.find(class_='market-notes')
    if notes_div:
        pdf.add_page()
        pdf.section_header("Technical Market Notes")
        lis = notes_div.find_all('li')
        pdf.set_font('Arial', '', 9)
        for li in lis:
            pdf.cell(5, 5, chr(149), 0, 0)
            pdf.multi_cell(0, 5, clean_text(safe_get_text(li)))
            pdf.ln(2)
            
    # --- 7. DISCLAIMER ---
    disclaimer = soup.find(class_='disclaimer')
    if disclaimer:
        pdf.ln(5)
        title = safe_get_text(disclaimer.find('h4'))
        if not title: title = "Important Disclaimer"
        
        # Get all paragraph text
        text_content = ""
        for p in disclaimer.find_all('p'):
            text_content += safe_get_text(p) + " "
            
        pdf.disclaimer_box(title, text_content)

    return pdf

# --- 4. STREAMLIT INTERFACE ---
st.set_page_config(page_title="BlueberryAI Formatter", layout="centered")
st.title("📄 BlueberryAI PDF Generator")
st.write("Upload your HTML report to generate the formatted PDF.")

uploaded_file = st.file_uploader("Choose HTML file", type="html")

if uploaded_file is not None:
    if st.button("Generate PDF"):
        with st.spinner("Parsing and Formatting..."):
            try:
                # Try multiple decodings to handle file variations
                bytes_data = uploaded_file.getvalue()
                try:
                    html_content = bytes_data.decode("utf-8")
                except UnicodeDecodeError:
                    try:
                        html_content = bytes_data.decode("latin-1")
                    except:
                        html_content = bytes_data.decode("cp1252", errors="ignore")
                
                pdf = parse_and_generate_pdf(html_content)
                
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
