import streamlit as st
from fpdf import FPDF
from bs4 import BeautifulSoup
import tempfile
import re

# --- 1. CLEANING FUNCTIONS ---
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
        
        if mode == 'sell':
            head_fill = (231, 76, 60) # Red
            badge_fill = (192, 57, 43)
        elif mode == 'open':
            head_fill = (46, 204, 113) # Green
            badge_fill = (39, 174, 96)
        else: # buy
            head_fill = (52, 152, 219) # Blue
            badge_fill = (41, 128, 185)

        # Header
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

        # Details
        self.set_text_color(0, 0, 0)
        self.set_font('Arial', '', 9)
        for line in details:
            self.multi_cell(0, 5, clean_text(line))
            self.ln(1)

        # Table
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

        # Rationale
        if rationale:
            self.set_fill_color(245, 248, 250)
            self.rect(10, self.get_y(), 190, 15, 'F')
            self.set_xy(12, self.get_y()+2)
            self.set_font('Arial', 'I', 9)
            self.multi_cell(186, 5, f"Rationale: {clean_text(rationale)}")
        
        # Confidence
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

# --- 3. HYBRID PARSER ---
def parse_and_generate_pdf(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # --- 1. DETECT HTML TYPE ---
    # Is this the Fancy List style or the Simple Tabbed style?
    has_setup_cards = len(soup.find_all(class_='setup-card')) > 0
    
    # --- 2. COMMON ELEMENTS (Alerts & Index) ---
    # Alerts
    alert = soup.find(class_='alert-box') or soup.find(string=re.compile("EXTREME CAUTION"))
    if alert:
        if not hasattr(alert, 'find'): alert = alert.parent
        if alert:
            # Try to find header inside or use generic
            head = alert.find(['h3', 'h4', 'strong'])
            title = safe_get_text(head) if head else "MARKET ALERT"
            text = safe_get_text(alert.find('p')) or safe_get_text(alert)
            # Cleanup text if it contains the title
            text = text.replace(title, "").strip()
            pdf.alert_box(title, text)

    # Index Status
    idx_anchor = soup.find(string=re.compile("Current Level"))
    if idx_anchor:
        # Find container (works for both layouts)
        idx_card = idx_anchor.find_parent(class_='index-card') or idx_anchor.find_parent(class_='card') or idx_anchor.find_parent('div').find_parent('div')
        
        pdf.section_header("Index Technical Status")
        pdf.set_font('Arial', '', 9)
        pdf.set_fill_color(250, 250, 250)
        
        # Try finding row divs first
        rows = idx_card.find_all(class_='metric-row')
        if not rows:
            # Fallback for Tabbed Style: look for div.metric
            rows = idx_card.find_all(class_='metric')
        
        for i in range(0, len(rows), 2):
            # Extract Label/Value pairs
            if rows[i].find(class_='metric-label'): # Style A
                l1 = safe_get_text(rows[i].find(class_='metric-label'))
                v1 = safe_get_text(rows[i].find(class_='metric-value'))
            else: # Style B (Tabbed)
                spans = rows[i].find_all('span')
                l1 = safe_get_text(spans[0]) if len(spans)>0 else ""
                v1 = safe_get_text(spans[1]) if len(spans)>1 else ""

            pdf.cell(35, 7, clean_text(l1), 1, 0, 'L', fill=True)
            pdf.cell(60, 7, clean_text(v1), 1, 0, 'L')
            
            if i+1 < len(rows):
                if rows[i+1].find(class_='metric-label'): # Style A
                    l2 = safe_get_text(rows[i+1].find(class_='metric-label'))
                    v2 = safe_get_text(rows[i+1].find(class_='metric-value'))
                else: # Style B
                    spans = rows[i+1].find_all('span')
                    l2 = safe_get_text(spans[0]) if len(spans)>0 else ""
                    v2 = safe_get_text(spans[1]) if len(spans)>1 else ""
                pdf.cell(35, 7, clean_text(l2), 1, 0, 'L', fill=True)
                pdf.cell(60, 7, clean_text(v2), 1, 1, 'L')
            else:
                pdf.ln()

    # Market Trend
    assess_header = soup.find(lambda t: t.name in ['h2', 'h3'] and 'Market Trend' in safe_get_text(t))
    if assess_header:
        pdf.section_header("Market Trend Assessment")
        # Find content container
        content = assess_header.find_next_sibling('div') or assess_header.parent.find(class_='market-assessment')
        if content:
            # Extract paragraphs
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

    # --- 3. EXTRACT STOCKS (HYBRID LOGIC) ---
    
    cards_data = [] # List of dicts
    
    if has_setup_cards:
        # === SCHEMA A: "LIST" STYLE ===
        for card in soup.find_all(class_='setup-card'):
            ticker = safe_get_text(card.find(class_='ticker'))
            name = safe_get_text(card.find(class_='company-name'))
            setup_el = card.find(class_='setup-type')
            setup = safe_get_text(setup_el)
            
            # Mode detection
            mode = 'buy'
            if setup_el and ('exit' in setup.lower() or 'reduce' in setup.lower() or 'sell' in setup.lower()):
                mode = 'sell'
            
            # Table
            table = {}
            if card.find(class_='trade-params'):
                for b in card.find(class_='trade-params').find_all(class_='param-box'):
                    lbl = safe_get_text(b.find(class_='param-label'))
                    val = safe_get_text(b.find(class_='param-value'))
                    if lbl: table[lbl] = val
            
            # Details
            details = [safe_get_text(p) for p in card.find(class_='technical-details').find_all('p')] if card.find(class_='technical-details') else []
            rationale = safe_get_text(card.find(class_='rationale')).replace("Rationale:", "").strip()
            conf = safe_get_text(card.find(class_='confidence'))
            
            cards_data.append({'t': ticker, 'n': name, 's': setup, 'd': details, 'tb': table, 'r': rationale, 'c': conf, 'm': mode})
            
    else:
        # === SCHEMA B: "TABBED" STYLE ===
        # In this style, cards are generic divs inside tab-contents
        # We must iterate by SECTIONS to know if it's Buy/Sell/Open
        
        # 1. Find all tab-content divs
        tabs = soup.find_all(class_='tab-content')
        for tab in tabs:
            tab_id = tab.get('id', '').lower()
            
            # Determine mode based on tab ID
            mode = 'buy'
            if 'sell' in tab_id or 'reduce' in tab_id: mode = 'sell'
            elif 'open' in tab_id or 'pos' in tab_id: mode = 'open'
            elif 'watch' in tab_id: continue # Handle watch later
            elif 'index' in tab_id or 'market' in tab_id or 'notes' in tab_id: continue
            
            # Find cards in this tab
            cards = tab.find_all(class_='card')
            for card in cards:
                # Extract Header (Ticker - Name)
                header = card.find('h3')
                if not header: continue
                
                header_text = safe_get_text(header)
                parts = header_text.split('-', 1)
                ticker = parts[0].strip()
                name = parts[1].strip() if len(parts) > 1 else ""
                
                # Extract Details & Table
                # In tabbed view, params are mixed in <p> tags like "Entry: 10.00"
                details = []
                table = {}
                setup = "Technical Setup" # Default
                
                for p in card.find_all('p'):
                    txt = safe_get_text(p)
                    # Check if this P tag is a parameter key/value
                    if ':' in txt and len(txt) < 100:
                        key, val = txt.split(':', 1)
                        key = key.strip().lower()
                        val = val.strip()
                        
                        # Map keys to table or details
                        if any(k in key for k in ['entry', 'target', 'stop', 'r:r', 'current', 'action', 'decision']):
                            table[key.title()] = val
                        elif 'setup' in key:
                            setup = val
                            details.append(f"Setup: {val}")
                        elif 'momentum' in key or 'volume' in key:
                            details.append(txt)
                        else:
                            details.append(txt)
                    else:
                        details.append(txt)
                
                cards_data.append({'t': ticker, 'n': name, 's': setup, 'd': details, 'tb': table, 'r': "", 'c': "", 'm': mode})

    # --- 4. RENDER CARDS ---
    opens = [c for c in cards_data if c['m'] == 'open']
    buys = [c for c in cards_data if c['m'] == 'buy']
    sells = [c for c in cards_data if c['m'] == 'sell']
    
    if opens:
        pdf.section_header("Open Positions Management")
        for c in opens: pdf.content_card(c['t'], c['n'], c['s'], c['d'], c['tb'], c['r'], c['c'], mode='open')
        
    if buys:
        pdf.section_header("Top Buy Opportunities")
        for c in buys: pdf.content_card(c['t'], c['n'], c['s'], c['d'], c['tb'], c['r'], c['c'], mode='buy')
        
    if sells:
        pdf.section_header("Reduce/Exit Recommendations")
        for c in sells: pdf.content_card(c['t'], c['n'], c['s'], c['d'], c['tb'], c['r'], c['c'], mode='sell')

    # --- 5. WATCHLIST ---
    # Try finding class 'watchlist' (List style) or id 'watch' (Tabbed style)
    wl_section = soup.find(class_='watchlist') or soup.find(id='watch')
    if wl_section:
        pdf.section_header("Watchlist - Additional Opportunities")
        # List style items
        items = wl_section.find_all(class_='watchlist-item')
        if not items:
            # Tabbed style items are just cards inside 'watch' tab
            items = wl_section.find_all(class_='card')
            
        for item in items:
            pdf.check_page_break(35)
            pdf.set_fill_color(255, 248, 240)
            pdf.rect(10, pdf.get_y(), 190, 30, 'F')
            pdf.set_xy(15, pdf.get_y() + 5)
            
            # Title
            h = item.find(['h3', 'h4'])
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 5, clean_text(safe_get_text(h)), 0, 1)
            
            # Content
            pdf.set_font('Arial', '', 9)
            for p in item.find_all('p'):
                pdf.cell(0, 5, clean_text(safe_get_text(p)), 0, 1)
            pdf.ln(5)

    # --- 6. NOTES ---
    notes_header = soup.find(lambda t: t.name in ['h2','h3'] and 'Notes' in safe_get_text(t))
    if notes_header:
        # Find container (List style uses div, Tabbed uses div with ul inside)
        container = notes_header.find_next_sibling('div') or notes_header.parent
        lis = container.find_all('li')
        if lis:
            pdf.add_page()
            pdf.section_header("Technical Market Notes")
            for li in lis:
                pdf.cell(5, 5, chr(149), 0, 0)
                pdf.multi_cell(0, 5, clean_text(safe_get_text(li)))
                pdf.ln(2)

    # --- 7. DISCLAIMER ---
    disc = soup.find(class_='disclaimer')
    if disc:
        title = safe_get_text(disc.find(['h3', 'h4'])) or "Important Disclaimer"
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
                try: html_content = bytes_data.decode("utf-8")
                except: html_content = bytes_data.decode("latin-1", errors="ignore")
                
                pdf = parse_and_generate_pdf(html_content)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    pdf.output(tmp.name)
                    with open(tmp.name, "rb") as f: pdf_bytes = f.read()
                
                st.success("PDF Generated Successfully!")
                st.download_button("📥 Download Styled PDF", pdf_bytes, "BlueberryAI_Market_Report.pdf", "application/pdf")
            except Exception as e:
                st.error(f"Error processing file: {e}")
