import streamlit as st
from fpdf import FPDF
from bs4 import BeautifulSoup
import tempfile
import re

# --- 1. CLEANING ---
def clean_text(text):
    if not text: return ""
    replacements = {
        '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '-', '\u2026': '...', '\u00A0': ' '
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode('latin-1', 'ignore').decode('latin-1')

def safe_get_text(element):
    if not element: return ""
    return element.get_text(" ", strip=True)

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
        head_fill = (231, 76, 60) if mode == 'sell' else (52, 152, 219)
        badge_fill = (192, 57, 43) if mode == 'sell' else (46, 204, 113)

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
        self.set_fill_color(255, 250, 240)
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

# --- 3. BOTTOM-UP PARSER ---
def parse_and_generate_pdf(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # 1. ALERT BOX (Heuristic)
    alert = None
    # Look for the specific text "EXTREME CAUTION" or the class
    caution_txt = soup.find(string=re.compile("EXTREME CAUTION"))
    if caution_txt:
        # Walk up to find the container
        alert = caution_txt.find_parent(class_='alert-box') or caution_txt.find_parent('div')

    if alert:
        title = safe_get_text(alert.find(['h3','h4','strong']))
        text = safe_get_text(alert.find('p'))
        pdf.alert_box(title, text)

    # 2. INDEX STATUS (Heuristic: "Current Level" text)
    idx_label = soup.find(string=re.compile("Current Level"))
    if idx_label:
        # The container is usually a few levels up
        idx_card = idx_label.find_parent(class_='index-card') or idx_label.find_parent('div').find_parent('div')
        
        pdf.section_header("Index Technical Status")
        pdf.set_font('Arial', '', 9)
        pdf.set_fill_color(250, 250, 250)
        
        rows = idx_card.find_all(class_='metric-row')
        for i in range(0, len(rows), 2):
            l1 = safe_get_text(rows[i].find(class_='metric-label'))
            v1 = safe_get_text(rows[i].find(class_='metric-value'))
            pdf.cell(35, 7, clean_text(l1), 1, 0, 'L', fill=True)
            pdf.cell(60, 7, clean_text(v1), 1, 0, 'L')
            
            if i + 1 < len(rows):
                l2 = safe_get_text(rows[i+1].find(class_='metric-label'))
                v2 = safe_get_text(rows[i+1].find(class_='metric-value'))
                pdf.cell(35, 7, clean_text(l2), 1, 0, 'L', fill=True)
                pdf.cell(60, 7, clean_text(v2), 1, 1, 'L')
            else:
                pdf.ln()

    # 3. MARKET ASSESSMENT (Heuristic: Header)
    assess_header = soup.find(lambda t: t.name in ['h2','h3'] and 'Market Trend Assessment' in safe_get_text(t))
    if assess_header:
        pdf.section_header("Market Trend Assessment")
        content = assess_header.find_next_sibling('div') or assess_header.parent.find(class_='market-assessment')
        if content:
            for tag in content.find_all(['h3', 'p']):
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

    # 4. CARDS (The Fix: Find Params -> Find Parent -> Find Ticker)
    # This works even if Ticker and Params are separated by Tabs structure
    
    # Find all "Entry Range" labels. These are anchors for every card.
    entry_labels = soup.find_all(string=re.compile("Entry Range"))
    
    buys = []
    sells = []
    seen_tickers = set()

    for label in entry_labels:
        # 1. Find the Params Container
        params_div = label.find_parent(class_='trade-params') or label.find_parent('div').find_parent('div')
        if not params_div: continue
        
        # 2. Find the Card Container (Climb up until we find a Ticker or Company Name)
        card = params_div
        ticker_el = None
        
        # Climb up max 6 levels to find a common ancestor with the ticker
        for _ in range(6):
            if not card.parent: break
            card = card.parent
            # Check if this parent contains a ticker class
            ticker_el = card.find(class_='ticker')
            if ticker_el: break
            
        if not ticker_el: continue # Orphaned table, skip
        
        ticker_text = safe_get_text(ticker_el)
        if ticker_text in seen_tickers: continue
        seen_tickers.add(ticker_text)

        # 3. Now we have the Card and the Ticker. Extract everything.
        name = safe_get_text(card.find(class_='company-name'))
        setup_el = card.find(class_='setup-type')
        setup = safe_get_text(setup_el)
        
        mode = 'buy'
        if setup_el:
            classes = setup_el.get('class', [])
            if 'exit' in setup.lower() or 'reduce' in setup.lower() or 'sell' in setup.lower() or 'setup-type-exit' in classes:
                mode = 'sell'
                
        # Details
        details_div = card.find(class_='technical-details')
        details = [safe_get_text(p) for p in details_div.find_all('p')] if details_div else []
        
        # Table (Use the params_div we found at start)
        table = {}
        for box in params_div.find_all(class_='param-box'):
            lbl = safe_get_text(box.find(class_='param-label'))
            val = safe_get_text(box.find(class_='param-value'))
            if lbl: table[lbl] = val

        # Rationale & Confidence
        rationale_div = card.find(class_='rationale')
        rationale = safe_get_text(rationale_div).replace("Rationale:", "").strip() if rationale_div else ""
        
        conf_div = card.find(class_='confidence')
        conf = safe_get_text(conf_div) if conf_div else ""

        data = {'t': ticker_text, 'n': name, 's': setup, 'd': details, 'tb': table, 'r': rationale, 'c': conf, 'm': mode}
        if mode == 'sell': sells.append(data)
        else: buys.append(data)

    if buys:
        pdf.section_header("Top Buy Opportunities")
        for c in buys:
            pdf.content_card(c['t'], c['n'], c['s'], c['d'], c['tb'], c['r'], c['c'], c['m'])
            
    if sells:
        pdf.section_header("Reduce/Exit Recommendations")
        for c in sells:
            pdf.content_card(c['t'], c['n'], c['s'], c['d'], c['tb'], c['r'], c['c'], c['m'])

    # 5. WATCHLIST
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

    # 6. NOTES
    notes_header = soup.find(lambda t: t.name in ['h2','h3'] and 'Technical Market Notes' in safe_get_text(t))
    if notes_header:
        notes_div = notes_header.find_next_sibling('div') or soup.find(class_='market-notes')
        if notes_div:
            pdf.add_page()
            pdf.section_header("Technical Market Notes")
            for li in notes_div.find_all('li'):
                pdf.cell(5, 5, chr(149), 0, 0)
                pdf.multi_cell(0, 5, clean_text(safe_get_text(li)))
                pdf.ln(2)

    # 7. DISCLAIMER
    disc = soup.find(class_='disclaimer')
    if disc:
        title = safe_get_text(disc.find('h4')) or "Important Disclaimer"
        text = safe_get_text(disc).replace(title, "").strip()
        pdf.disclaimer_box(title, text)

    return pdf

# --- 4. STREAMLIT ---
st.set_page_config(page_title="BlueberryAI Formatter", layout="centered")
st.title("📄 BlueberryAI PDF Generator")
st.write("Upload your HTML report to generate the formatted PDF.")

uploaded_file = st.file_uploader("Choose HTML file", type="html")

if uploaded_file is not None:
    if st.button("Generate PDF"):
        with st.spinner("Parsing and Formatting..."):
            try:
                bytes_data = uploaded_file.getvalue()
                try:
                    html_content = bytes_data.decode("utf-8")
                except:
                    html_content = bytes_data.decode("latin-1", errors="ignore")
                
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
