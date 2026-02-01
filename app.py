import streamlit as st
from fpdf import FPDF
from bs4 import BeautifulSoup
import tempfile
import re

# --- 1. TEXT CLEANING ---
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

# --- 2. PDF CLASS ---
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
        # Colors
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

# --- 3. FINGERPRINT PARSER (The Key Logic) ---
def find_container_by_keywords(soup, keywords, tag_type=None):
    """Finds the smallest container holding all keywords."""
    matches = []
    # Search all divs or specific tags
    tags = soup.find_all(tag_type) if tag_type else soup.find_all(['div', 'table', 'section'])
    
    for tag in tags:
        text = safe_get_text(tag)
        if all(k in text for k in keywords):
            matches.append(tag)
    
    # Filter to find "leaf" containers (matches that don't contain other matches)
    # This prevents selecting the entire <body> as a match
    leaf_matches = []
    for m in matches:
        is_parent = False
        for other in matches:
            if m != other and m in other.parents:
                is_parent = True # This 'other' is inside 'm', so 'm' is too big
                break
        # Logic inversion: we want the containers that ARE parents of text, but NOT parents of other containers
        # Actually simplest way: Pick matches with shortest text length
        leaf_matches.append(m)
        
    # Sort by length of text to find the most specific containers
    leaf_matches.sort(key=lambda x: len(safe_get_text(x)))
    
    # Remove duplicates (nested containers often share text)
    unique_matches = []
    seen_text = set()
    for m in leaf_matches:
        t = safe_get_text(m)[:50] # Check first 50 chars signature
        if t not in seen_text:
            unique_matches.append(m)
            seen_text.add(t)
            
    return unique_matches

def parse_and_generate_pdf(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # --- 1. ALERT BOX ---
    # Fingerprint: "EXTREME" and "CAUTION"
    alerts = find_container_by_keywords(soup, ["EXTREME", "CAUTION"])
    if alerts:
        a = alerts[0] # Take the most specific one
        pdf.alert_box("EXTREME CAUTION REQUIRED", safe_get_text(a))

    # --- 2. INDEX STATUS ---
    # Fingerprint: "Current Level" and "Distance"
    indexes = find_container_by_keywords(soup, ["Current Level", "Distance"])
    if indexes:
        container = indexes[0]
        pdf.section_header("Index Technical Status")
        pdf.set_font('Arial', '', 9)
        pdf.set_fill_color(250, 250, 250)
        
        # Try to find rows (divs or trs) inside
        rows = container.find_all(['div', 'tr'])
        valid_rows = [r for r in rows if len(safe_get_text(r)) < 100 and ":" in safe_get_text(r)]
        
        # Dedup rows
        seen = set()
        clean_rows = []
        for r in valid_rows:
            if safe_get_text(r) not in seen:
                clean_rows.append(r)
                seen.add(safe_get_text(r))

        for i in range(0, len(clean_rows), 2):
            t1 = safe_get_text(clean_rows[i]).split(":", 1)
            l1, v1 = (t1[0], t1[1]) if len(t1)>1 else (t1[0], "")
            
            pdf.cell(35, 7, clean_text(l1), 1, 0, 'L', fill=True)
            pdf.cell(60, 7, clean_text(v1), 1, 0, 'L')
            
            if i + 1 < len(clean_rows):
                t2 = safe_get_text(clean_rows[i+1]).split(":", 1)
                l2, v2 = (t2[0], t2[1]) if len(t2)>1 else (t2[0], "")
                pdf.cell(35, 7, clean_text(l2), 1, 0, 'L', fill=True)
                pdf.cell(60, 7, clean_text(v2), 1, 1, 'L')
            else:
                pdf.ln()

    # --- 3. MARKET ASSESSMENT ---
    # Fingerprint: Header text
    assess_header = soup.find(lambda t: t.name in ['h2', 'h3'] and 'Market Trend Assessment' in safe_get_text(t))
    if assess_header:
        pdf.section_header("Market Trend Assessment")
        # Grab text from the parent container of the header
        parent = assess_header.parent
        # Get paragraphs
        for p in parent.find_all('p'):
            if len(safe_get_text(p)) > 20: # Filter out empty trash
                pdf.set_font('Arial', '', 9)
                pdf.multi_cell(0, 5, clean_text(safe_get_text(p)))
                pdf.ln(2)

    # --- 4. CARDS (BUY & SELL) ---
    # Fingerprint: "Entry" AND "Target" AND "Stop"
    # This identifies the Trade Params box. We go up to find the Card.
    param_boxes = find_container_by_keywords(soup, ["Entry", "Target", "Stop"])
    
    buys = []
    sells = []

    for box in param_boxes:
        # box is likely the params container. Go up to find the Card.
        card = box.parent
        # Validation: A card usually has a Ticker (uppercase, short)
        # Scan for Ticker
        text = safe_get_text(card)
        if len(text) > 1000: continue # We grabbed too big a container
        
        # Determine Mode
        mode = 'buy'
        if 'Exit' in text or 'Reduce' in text or 'Sell' in text:
            mode = 'sell'
            
        # Extract Ticker (Naive regex: look for 3-5 uppercase letters at start of lines)
        ticker_match = re.search(r'\b[A-Z]{3,5}\b', text)
        ticker = ticker_match.group(0) if ticker_match else "STOCK"
        
        # Extract Name (Line after ticker?)
        name_match = re.search(r'\b[A-Z]{3,5}\b\s+([A-Za-z ]+)', text)
        name = name_match.group(1) if name_match else "Company Name"
        
        # Extract Params
        table = {}
        # Parse text for "Entry: 10.50" patterns
        for key in ["Entry", "Target", "Stop", "Risk/Reward", "Current", "Action"]:
             # Regex to find "Entry" followed by numbers/text until newline
             m = re.search(f"{key}[:\s]+([0-9\.\- a-zA-Z]+)", text)
             if m: table[key] = m.group(1).strip()

        # Extract Rationale
        rationale = ""
        if "Rationale" in text:
            rationale = text.split("Rationale")[-1].split("Confidence")[0].strip(": -")
            
        conf = ""
        if "Confidence" in text:
            conf = "Confidence" + text.split("Confidence")[-1].split("\n")[0]

        card_data = {
            'ticker': ticker, 'name': name, 'setup': mode.upper(),
            'details': [], # Hard to parse unstructured details cleanly without classes
            'table': table, 'rationale': rationale, 'conf': conf
        }

        if mode == 'sell': sells.append(card_data)
        else: buys.append(card_data)

    if buys:
        pdf.section_header("Top Buy Opportunities")
        for c in buys:
            pdf.content_card(c['ticker'], c['name'], c['setup'], c['details'], c['table'], c['rationale'], c['conf'], mode='buy')

    if sells:
        pdf.section_header("Reduce/Exit Recommendations")
        for c in sells:
            pdf.content_card(c['ticker'], c['name'], c['setup'], c['details'], c['table'], c['rationale'], c['conf'], mode='sell')

    # --- 5. WATCHLIST ---
    # Fingerprint: "Trigger" AND "Parameters"
    wl_items = find_container_by_keywords(soup, ["Trigger", "Parameters"])
    if wl_items:
        pdf.section_header("Watchlist")
        for item in wl_items:
            t = safe_get_text(item)
            if len(t) > 500: continue
            
            pdf.check_page_break(35)
            pdf.set_fill_color(255, 248, 240)
            pdf.rect(10, pdf.get_y(), 190, 30, 'F')
            pdf.set_xy(15, pdf.get_y() + 5)
            
            # Extract Title (First line)
            lines = [l for l in t.split('\n') if l.strip()]
            if lines:
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(0, 5, clean_text(lines[0]), 0, 1)
                pdf.set_font('Arial', '', 9)
                for l in lines[1:]:
                    pdf.cell(0, 5, clean_text(l), 0, 1)
                pdf.ln(5)

    # --- 6. NOTES ---
    notes_header = soup.find(lambda t: t.name in ['h2','h3'] and 'Technical Market Notes' in safe_get_text(t))
    if notes_header:
        pdf.add_page()
        pdf.section_header("Technical Market Notes")
        # Try to find list items nearby
        container = notes_header.parent
        lis = container.find_all('li')
        for li in lis:
            pdf.cell(5, 5, chr(149), 0, 0)
            pdf.multi_cell(0, 5, clean_text(safe_get_text(li)))
            pdf.ln(2)

    # --- 7. DISCLAIMER ---
    # Fingerprint: "Disclaimer" and "Risk"
    disc = find_container_by_keywords(soup, ["Disclaimer", "Risk"])
    if disc:
        d = disc[0] # Smallest match
        pdf.disclaimer_box("Important Disclaimer", safe_get_text(d))

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
