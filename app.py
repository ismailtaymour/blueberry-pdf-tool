import streamlit as st
from fpdf import FPDF
from bs4 import BeautifulSoup, NavigableString
import tempfile
import re
import math

# --- 1. CLEANING FUNCTIONS ---
def clean_text(text):
    if not text: return ""
    replacements = {
        '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '-', '\u2026': '...', '\u00A0': ' ',
        '\t': ' '
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode('latin-1', 'ignore').decode('latin-1').strip()

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
        self.cell(0, 10, clean_text(f'Blueberry AI Trader | Page {self.page_no()}'), 0, 0, 'C')

    def check_page_break(self, height_needed):
        if self.get_y() + height_needed > 270:
            self.add_page()

    def section_header(self, title, new_page=False):
        if new_page:
            self.add_page()
        elif self.get_y() > 250: 
            self.add_page()
            
        self.ln(5)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(44, 62, 80)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 10, f"  {clean_text(title)}", 0, 1, 'L', fill=True)
        self.ln(3)

    def alert_box(self, title, text):
        self.set_font('Arial', '', 10)
        lines = len(self.multi_cell(180, 5, clean_text(text), split_only=True))
        h_needed = (lines * 5) + 20 
        
        self.check_page_break(h_needed)
        
        start_y = self.get_y()
        self.set_fill_color(255, 235, 238)
        self.set_draw_color(231, 76, 60)
        self.set_line_width(0.5)
        self.rect(10, start_y, 190, h_needed, 'DF')
        
        self.set_xy(15, start_y + 5)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(192, 57, 43)
        self.cell(0, 5, clean_text(title), 0, 1)
        
        self.set_xy(15, start_y + 12)
        self.set_font('Arial', '', 10)
        self.set_text_color(60, 0, 0)
        self.multi_cell(180, 5, clean_text(text), align='L')
        
        self.set_y(start_y + h_needed + 5)
        self.set_line_width(0.2)

    def table_row(self, texts, widths, fills, aligns):
        """
        Draws a table row with correct margins to prevent vertical stacking issues.
        """
        line_height = 5
        font_size = 9
        self.set_font('Arial', '', font_size)
        
        # 1. Calculate max height required for this row
        cell_heights = []
        for i, text in enumerate(texts):
            w = widths[i]
            # Simulate wrapping to count lines
            lines = len(self.multi_cell(w - 2, line_height, text, split_only=True))
            h = max(lines * line_height, 8)
            cell_heights.append(h)
            
        row_height = max(cell_heights)
        self.check_page_break(row_height)
        
        # 2. Draw Cells
        y_start = self.get_y()
        x_start = 10 # Page left margin
        original_l_margin = self.l_margin
        
        for i, text in enumerate(texts):
            w = widths[i]
            
            # Draw Background & Border
            self.set_xy(x_start, y_start)
            if fills[i]:
                self.set_fill_color(250, 250, 250)
                self.rect(x_start, y_start, w, row_height, 'FD')
            else:
                self.rect(x_start, y_start, w, row_height, 'D')
                
            # Draw Text (CRITICAL: Set margin so wrapping stays in column)
            self.set_left_margin(x_start) 
            self.set_xy(x_start, y_start + 1.5)
            self.multi_cell(w, line_height, text, 0, aligns[i])
            
            x_start += w
            
        # Restore Margin and move down
        self.set_left_margin(original_l_margin)
        self.set_y(y_start + row_height)

    def content_card(self, ticker, name, setup_type, details, table_data, rationale, confidence, mode='buy'):
        self.check_page_break(80)
        
        if mode == 'sell':
            head_fill, badge_fill = (231, 76, 60), (192, 57, 43)
        elif mode == 'open':
            head_fill, badge_fill = (46, 204, 113), (39, 174, 96)
        else:
            head_fill, badge_fill = (52, 152, 219), (41, 128, 185)

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
        self.set_x(10)
        for line in details:
            self.multi_cell(0, 5, clean_text(line), align='L')
            self.ln(1)

        # Dynamic Table
        if table_data:
            self.ln(2)
            self.set_draw_color(200, 200, 200)
            cols = len(table_data)
            if cols > 0:
                col_width = 190 / cols
                widths = [col_width] * cols
                
                # Headers
                self.set_font('Arial', 'B', 8)
                self.set_fill_color(245, 245, 245)
                self.set_text_color(0,0,0)
                headers = [clean_text(h) for h in table_data.keys()]
                self.table_row(headers, widths, [True]*cols, ['C']*cols)
                
                # Values
                self.set_font('Arial', '', 9)
                values = [clean_text(str(v)) for v in table_data.values()]
                self.table_row(values, widths, [False]*cols, ['C']*cols)
            self.ln(5)

        # Rationale
        if rationale:
            self.set_fill_color(245, 248, 250)
            self.set_font('Arial', 'I', 9)
            
            # Dynamic height
            w_text = 186
            lines = len(self.multi_cell(w_text, 5, f"Rationale: {clean_text(rationale)}", split_only=True))
            h_needed = (lines * 5) + 4
            
            self.rect(10, self.get_y(), 190, h_needed, 'F')
            self.set_xy(12, self.get_y()+2)
            self.multi_cell(186, 5, f"Rationale: {clean_text(rationale)}", align='L')
            self.set_y(self.get_y() + 2)
        
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
        
        self.set_font('Arial', '', 8)
        lines = len(self.multi_cell(180, 4, clean_text(text), split_only=True))
        h_needed = (lines * 4) + 15
        
        start_y = self.get_y()
        self.rect(10, start_y, 190, h_needed, 'DF')
        self.set_xy(15, start_y + 4)
        self.set_font('Arial', 'B', 10)
        self.set_text_color(160, 100, 0)
        self.cell(0, 5, clean_text(title), 0, 1)
        
        self.set_xy(15, start_y + 10)
        self.set_font('Arial', '', 8)
        self.multi_cell(180, 4, clean_text(text), align='L')
        self.ln(5)

# --- 3. PARSER ---
def parse_and_generate_pdf(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # 1. ALERT BOX
    alert_tag = soup.find(class_='alert-box')
    if not alert_tag:
        alert_text = soup.find(string=re.compile("EXTREME CAUTION"))
        if alert_text:
            if isinstance(alert_text, NavigableString):
                alert_tag = alert_text.parent
                if alert_tag.name in ['b', 'strong', 'h3', 'h4', 'span']:
                    alert_tag = alert_tag.parent

    if alert_tag:
        head = alert_tag.find(['h3', 'h4', 'strong'])
        title = safe_get_text(head) if head else "MARKET ALERT"
        text = safe_get_text(alert_tag.find('p')) or safe_get_text(alert_tag)
        text = text.replace(title, "").strip()
        pdf.alert_box(title, text)

    # 2. INDEX STATUS
    idx_header = soup.find(lambda t: t.name in ['h2', 'h3'] and 'Index' in safe_get_text(t) and ('Status' in safe_get_text(t) or 'Analysis' in safe_get_text(t)))
    idx_anchor = soup.find(string=re.compile(r"(Current Level|Level:)"))
    
    idx_card = None
    if idx_header:
        idx_card = idx_header.find_next(class_=['index-card', 'card'])
    elif idx_anchor:
        idx_card = idx_anchor.find_parent(class_=['index-card', 'card']) or idx_anchor.find_parent('div').find_parent('div')

    if idx_card:
        pdf.section_header("Index Technical Status", new_page=False)
        pdf.set_font('Arial', '', 9)
        pdf.set_fill_color(250, 250, 250)
        
        rows = idx_card.find_all(class_='metric-row')
        if not rows: rows = idx_card.find_all(class_='metric')
        
        for i in range(0, len(rows), 2):
            l1, v1, l2, v2 = "", "", "", ""
            if rows[i].find(class_='metric-label'):
                l1 = safe_get_text(rows[i].find(class_='metric-label'))
                v1 = safe_get_text(rows[i].find(class_='metric-value'))
            else:
                spans = rows[i].find_all('span')
                if len(spans) > 0: l1 = safe_get_text(spans[0])
                if len(spans) > 1: v1 = safe_get_text(spans[1])

            texts = [clean_text(l1), clean_text(v1)]
            widths = [35, 60]
            fills = [True, False]
            aligns = ['L', 'L']
            
            if i+1 < len(rows):
                if rows[i+1].find(class_='metric-label'):
                    l2 = safe_get_text(rows[i+1].find(class_='metric-label'))
                    v2 = safe_get_text(rows[i+1].find(class_='metric-value'))
                else:
                    spans = rows[i+1].find_all('span')
                    if len(spans) > 0: l2 = safe_get_text(spans[0])
                    if len(spans) > 1: v2 = safe_get_text(spans[1])
                
                texts.extend([clean_text(l2), clean_text(v2)])
                widths.extend([35, 60])
                fills.extend([True, False])
                aligns.extend(['L', 'L'])
            
            pdf.table_row(texts, widths, fills, aligns)

    # 3. MARKET ASSESSMENT
    assess_header = soup.find(lambda t: t.name in ['h2', 'h3'] and 'Market Trend' in safe_get_text(t))
    if assess_header:
        pdf.section_header("Market Trend Assessment", new_page=False)
        content = assess_header.find_next_sibling('div') or assess_header.parent.find(class_='market-assessment') or assess_header.parent.find(class_='card')
        if content:
            for tag in content.find_all(['h3', 'p']):
                pdf.set_x(10)
                if tag.name == 'h3':
                    pdf.ln(3)
                    pdf.set_font('Arial', 'B', 10)
                    pdf.set_text_color(44, 62, 80)
                    pdf.cell(0, 6, clean_text(safe_get_text(tag)), 0, 1)
                else:
                    pdf.set_font('Arial', '', 9)
                    pdf.set_text_color(0, 0, 0)
                    pdf.multi_cell(0, 5, clean_text(safe_get_text(tag)), align='L')
                    pdf.ln(2)

    # 4. CARD EXTRACTION
    cards_data = []
    
    if soup.find(class_='setup-card'):
        for card in soup.find_all(class_='setup-card'):
            ticker = safe_get_text(card.find(class_='ticker'))
            name = safe_get_text(card.find(class_='company-name'))
            setup_el = card.find(class_='setup-type')
            setup = safe_get_text(setup_el)
            
            mode = 'buy'
            if setup_el and ('exit' in setup.lower() or 'reduce' in setup.lower() or 'sell' in setup.lower()): mode = 'sell'
            if setup_el and ('distribution' in setup.lower()): mode = 'sell'
            
            curr = card.parent
            for _ in range(4):
                if curr:
                    cid = curr.get('id', '').lower()
                    if 'open' in cid or 'pos' in cid: mode = 'open'
                    elif 'reduce' in cid or 'sell' in cid or 'distrib' in cid: mode = 'sell'
                    curr = curr.parent
                else: break

            table = {}
            if card.find(class_='trade-params'):
                for b in card.find(class_='trade-params').find_all(class_='param-box'):
                    lbl = safe_get_text(b.find(class_='param-label'))
                    val = safe_get_text(b.find(class_='param-value'))
                    if lbl: table[lbl] = val
            
            details = [safe_get_text(p) for p in card.find(class_='technical-details').find_all('p')] if card.find(class_='technical-details') else []
            rationale = safe_get_text(card.find(class_='rationale')).replace("Rationale:", "").strip()
            conf = safe_get_text(card.find(class_='confidence'))
            
            cards_data.append({'t': ticker, 'n': name, 's': setup, 'd': details, 'tb': table, 'r': rationale, 'c': conf, 'm': mode})
            
    else:
        tabs = soup.find_all(class_='tab-content')
        for tab in tabs:
            tab_id = tab.get('id', '').lower()
            mode = 'buy'
            if 'sell' in tab_id or 'reduce' in tab_id: mode = 'sell'
            elif 'open' in tab_id: mode = 'open'
            elif 'watch' in tab_id or 'index' in tab_id or 'market' in tab_id or 'notes' in tab_id: continue
            
            cards = tab.find_all(class_='card')
            for card in cards:
                header = card.find('h3')
                if not header: continue
                parts = safe_get_text(header).split('-', 1)
                ticker = parts[0].strip()
                name = parts[1].strip() if len(parts) > 1 else ""
                
                details, table, setup = [], {}, "Technical Setup"
                for p in card.find_all('p'):
                    txt = safe_get_text(p)
                    if ':' in txt and len(txt) < 120:
                        key, val = txt.split(':', 1)
                        key, val = key.strip().lower(), val.strip()
                        if any(k in key for k in ['entry', 'target', 'stop', 'r:r', 'current', 'action', 'decision', 'gain', 'loss']):
                            table[key.title()] = val
                        elif 'setup' in key:
                            setup = val
                            details.append(f"Setup: {val}")
                        else: details.append(txt)
                    else: details.append(txt)
                
                cards_data.append({'t': ticker, 'n': name, 's': setup, 'd': details, 'tb': table, 'r': "", 'c': "", 'm': mode})

    # Render Groups (FORCE NEW PAGE)
    opens = [c for c in cards_data if c['m'] == 'open']
    buys = [c for c in cards_data if c['m'] == 'buy']
    sells = [c for c in cards_data if c['m'] == 'sell']
    
    if opens:
        pdf.section_header("Open Positions Management", new_page=True)
        for c in opens: pdf.content_card(c['t'], c['n'], c['s'], c['d'], c['tb'], c['r'], c['c'], mode='open')
    if buys:
        pdf.section_header("Top Buy Opportunities", new_page=True)
        for c in buys: pdf.content_card(c['t'], c['n'], c['s'], c['d'], c['tb'], c['r'], c['c'], mode='buy')
    if sells:
        pdf.section_header("Reduce/Exit Recommendations", new_page=True)
        for c in sells: pdf.content_card(c['t'], c['n'], c['s'], c['d'], c['tb'], c['r'], c['c'], mode='sell')

    # 5. WATCHLIST
    wl_section = soup.find(class_='watchlist') or soup.find(id='watch')
    if wl_section:
        pdf.section_header("Watchlist - Additional Opportunities", new_page=True)
        items = wl_section.find_all(class_='watchlist-item') or wl_section.find_all(class_='card')
        for item in items:
            pdf.check_page_break(35)
            pdf.set_fill_color(255, 248, 240)
            pdf.rect(10, pdf.get_y(), 190, 30, 'F')
            pdf.set_xy(15, pdf.get_y() + 5)
            h = item.find(['h3', 'h4'])
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 5, clean_text(safe_get_text(h)), 0, 1)
            pdf.set_font('Arial', '', 9)
            pdf.set_x(10)
            for p in item.find_all('p'):
                pdf.set_x(10) 
                pdf.cell(0, 5, clean_text(safe_get_text(p)), 0, 1)
            pdf.ln(5)

    # 6. NOTES
    notes_head = soup.find(lambda t: t.name in ['h2','h3'] and 'Notes' in safe_get_text(t))
    if notes_head:
        container = notes_head.find_next_sibling('div') or notes_head.parent
        lis = container.find_all('li')
        if lis:
            pdf.section_header("Technical Market Notes", new_page=True)
            for li in lis:
                pdf.set_x(10)
                pdf.cell(5, 5, chr(149), 0, 0)
                pdf.multi_cell(0, 5, clean_text(safe_get_text(li)), align='L')
                pdf.ln(2)

    # 7. DISCLAIMER
    disc = soup.find(class_='disclaimer')
    if disc:
        if isinstance(disc, NavigableString):
            disc = disc.parent
        title_tag = disc.find(['h3', 'h4'])
        title = safe_get_text(title_tag) if title_tag else "Important Disclaimer"
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
