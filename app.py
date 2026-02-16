import streamlit as st
from fpdf import FPDF
from bs4 import BeautifulSoup, NavigableString
import tempfile
import re
import math

# --- 1. CLEANING FUNCTIONS ---
def clean_text(text):
    if not text: return ""
    text = text.replace('\n', ' ').replace('\t', ' ').replace('\r', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    replacements = {
        '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '-', '\u2026': '...', '\u00A0': ' ',
        '📊': '', '📈': '', '🎯': '', '💼': '', '⚠️': '', '👀': '', '📝': ''
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode('latin-1', 'ignore').decode('latin-1').strip()

def safe_get_text(element):
    if not element: return ""
    return clean_text(element.get_text(" ", strip=True))

# --- 2. UNIVERSAL PDF ENGINE ---
class PDF(FPDF):
    def __init__(self, subtitle_text=""):
        super().__init__()
        self.subtitle_text = subtitle_text

    def header(self):
        # Ultra Compact Header
        self.set_fill_color(44, 62, 80)
        self.rect(0, 0, 210, 26, 'F') 
        
        self.set_font('Arial', 'B', 15) 
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 5)
        self.cell(0, 6, 'BlueberryAI - EGX30 Market Intelligence', 0, 1, 'C')
        
        self.set_font('Arial', '', 8)
        self.set_xy(10, 11)
        self.cell(0, 4, 'AI-Generated Market Analysis | For Informational Purposes Only', 0, 1, 'C')
        
        self.set_draw_color(100, 110, 120)
        self.line(40, 16, 170, 16) 
        
        self.set_font('Arial', '', 7.5)
        self.set_text_color(200, 200, 200)
        self.set_xy(10, 18)
        self.cell(0, 4, self.subtitle_text, 0, 1, 'C')
        
        # Lock cursor safely below header to prevent overlaps
        self.set_y(30)

    def footer(self):
        self.set_y(-12) 
        self.set_fill_color(52, 73, 94) 
        self.rect(0, 285, 210, 12, 'F')
        self.set_font('Arial', '', 7)
        self.set_text_color(200, 200, 200)
        self.cell(0, 8, f'Blueberry AI Trader | Technical Analysis System | Page {self.page_no()}', 0, 0, 'C')

    def check_page_break(self, height_needed):
        if self.get_y() + height_needed > 280:
            self.add_page()

    def reset_state(self):
        self.set_left_margin(8) 
        self.set_right_margin(8)
        self.set_x(8)
        self.set_text_color(0, 0, 0)

    def section_header(self, title, new_page=False):
        self.reset_state()
        if new_page and self.get_y() > 35: 
            self.add_page()
        elif self.get_y() > 260: 
            self.add_page()
            
        self.ln(2)
        # Try to extract icon or color if needed, defaulting to Blue
        color = (52, 152, 219)
        if "Dashboard" in title: color = (155, 89, 182) # Purple for dashboard
        
        self.set_fill_color(*color)
        self.rect(8, self.get_y(), 1.5, 6, 'F') 
        
        self.set_x(11)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(44, 62, 80)
        self.cell(0, 6, clean_text(title), 0, 1, 'L')
        self.ln(1.5)

    def draw_notice_box(self, text, style='neutral'):
        self.reset_state()
        self.set_font('Arial', '', 8.5)
        lines = len(self.multi_cell(186, 4.2, text, split_only=True))
        h_needed = (lines * 4.2) + 6 
        
        self.check_page_break(h_needed)
        start_y = self.get_y()
        
        if 'warning' in style.lower() or 'distribute' in text.lower():
            self.set_fill_color(248, 215, 218)
            self.set_text_color(114, 28, 36)
        else:
            self.set_fill_color(244, 246, 247)
            self.set_text_color(85, 85, 85)
            
        self.rect(8, start_y, 194, h_needed, 'F')
        
        self.set_xy(11, start_y + 3)
        if 'warning' in style.lower(): self.set_font('Arial', 'B', 8.5)
        self.multi_cell(188, 4.2, text, align='L')
        self.set_y(start_y + h_needed + 2)

    def draw_generic_card(self, soup, card_type='index'):
        """Universal parser for Index Cards, Market Assessments, and Dashboard Cards"""
        self.reset_state()
        
        # Color Themes
        if card_type == 'dashboard':
            bg_c, border_c, accent_c = (247, 243, 255), (230, 220, 245), (155, 89, 182)
            text_main, text_sub = (44, 62, 80), (85, 85, 85)
        elif card_type == 'market':
            bg_c, border_c, accent_c = (109, 102, 204), (109, 102, 204), (255, 255, 255)
            text_main, text_sub = (255, 255, 255), (240, 240, 240)
        else: # index
            bg_c, border_c, accent_c = (240, 244, 248), (220, 225, 230), (52, 152, 219)
            text_main, text_sub = (44, 62, 80), (85, 85, 85)
            
        # 1. Component Extraction & Height Calculation
        h_needed = 4
        elements = []
        
        for child in soup.children:
            if not getattr(child, 'name', None): continue
            
            if child.name == 'h3':
                h_needed += 9
                elements.append(('h3', child))
                
            elif child.name == 'p':
                txt = safe_get_text(child)
                if not txt: continue
                lines = len(self.multi_cell(186, 4.2, txt, split_only=True))
                h_needed += (lines * 4.2) + 2.5
                elements.append(('p', child, txt, lines))
                
            elif child.name == 'div' and 'metric-row' in child.get('class', []):
                h_needed += 5.5
                elements.append(('metric', child))
                
            elif child.name == 'div' and ('trade-params' in child.get('class', []) or child.find(class_='param-box')):
                boxes = child.find_all(class_='param-box')
                if boxes:
                    cols = 2 if len(boxes) == 4 else min(4, len(boxes))
                    rows = math.ceil(len(boxes) / cols)
                    is_trade = 'trade-params' in child.get('class', [])
                    block_h = (rows * 12) + (6 if is_trade else 2)
                    h_needed += block_h + 3
                    elements.append(('grid', boxes, cols, is_trade, block_h))
                    
            elif child.name == 'div' and 'rationale' in child.get('class', []):
                txt = safe_get_text(child)
                lines = len(self.multi_cell(182, 4.2, txt, split_only=True))
                block_h = (lines * 4.2) + 5
                h_needed += block_h + 3
                elements.append(('rationale', txt, block_h))
                
        h_needed += 4
        self.check_page_break(h_needed)
        
        # 2. Draw Background
        start_y = self.get_y()
        self.set_fill_color(*bg_c)
        self.set_draw_color(*border_c)
        self.rect(8, start_y, 194, h_needed, 'DF')
        
        # 3. Render Components
        curr_y = start_y + 3
        for el in elements:
            type_ = el[0]
            
            if type_ == 'h3':
                self.set_xy(12, curr_y)
                self.set_font('Arial', 'B', 11)
                self.set_text_color(*text_main)
                self.cell(0, 5, safe_get_text(el[1]), 0, 1, 'L')
                self.set_draw_color(*accent_c)
                self.set_line_width(0.4)
                self.line(11, curr_y + 5.5, 199, curr_y + 5.5)
                self.set_line_width(0.2)
                curr_y += 8
                
            elif type_ == 'p':
                self.set_xy(12, curr_y)
                txt = el[2]
                
                # Dynamic text styling based on content
                if 'trend-bull' in str(el[1]) or 'expanding' in txt.lower(): self.set_text_color(39, 174, 96)
                elif 'trend-bear' in str(el[1]) or 'declining' in txt.lower(): self.set_text_color(231, 76, 60)
                else: self.set_text_color(*text_sub)
                
                if ':' in txt and txt.index(':') < 25:
                    self.set_font('Arial', 'B', 8.5)
                else:
                    self.set_font('Arial', '', 8.5)
                    
                self.multi_cell(186, 4.2, txt, align='L')
                curr_y += (el[3] * 4.2) + 2.5
                
            elif type_ == 'metric':
                lbl = safe_get_text(el[1].find(class_='metric-label'))
                val_node = el[1].find(class_='metric-value')
                val = safe_get_text(val_node)
                
                self.set_xy(12, curr_y)
                self.set_font('Arial', 'B', 8.5)
                self.set_text_color(*text_sub)
                self.cell(80, 5, lbl, 0, 0, 'L')
                
                if val_node and 'trend-bull' in val_node.get('class', []): self.set_text_color(39, 174, 96)
                elif val_node and 'trend-bear' in val_node.get('class', []): self.set_text_color(231, 76, 60)
                else: self.set_text_color(*text_main)
                
                self.cell(100, 5, val, 0, 1, 'R')
                self.set_draw_color(*border_c)
                self.line(12, curr_y + 5, 198, curr_y + 5)
                curr_y += 5.5
                
            elif type_ == 'grid':
                boxes, cols, is_trade, block_h = el[1], el[2], el[3], el[4]
                grid_y = curr_y
                
                if is_trade:
                    if card_type == 'dashboard': self.set_fill_color(142, 68, 173) 
                    else: self.set_fill_color(253, 235, 245) 
                    self.rect(10, curr_y, 190, block_h, 'F')
                    grid_y += 3
                    
                box_width = 88 if cols == 2 else (44 if cols == 4 else 60)
                gap = 3
                start_x = 10 + (190 - ((cols * box_width) + ((cols - 1) * gap))) / 2
                
                for i, box in enumerate(boxes):
                    row = i // cols
                    col = i % cols
                    x = start_x + (col * (box_width + gap))
                    y = grid_y + (row * 12)
                    
                    self.set_fill_color(255, 255, 255)
                    self.rect(x, y, box_width, 10, 'F')
                    
                    lbl = safe_get_text(box.find(class_='param-label'))
                    val_node = box.find(class_='param-value')
                    val = safe_get_text(val_node)
                    
                    self.set_xy(x, y + 1.5)
                    self.set_font('Arial', '', 6.5)
                    self.set_text_color(100, 100, 100)
                    self.cell(box_width, 3, lbl.upper(), 0, 1, 'C')
                    
                    self.set_xy(x, y + 5)
                    self.set_font('Arial', 'B', 9)
                    if val_node and val_node.has_attr('style'):
                        st = val_node['style'].lower()
                        if '27ae60' in st: self.set_text_color(39, 174, 96)
                        elif 'e74c3c' in st: self.set_text_color(231, 76, 60)
                        else: self.set_text_color(*text_main)
                    else:
                        self.set_text_color(*text_main)
                    self.cell(box_width, 4, val, 0, 1, 'C')
                
                curr_y += block_h + 3
                
            elif type_ == 'rationale':
                txt, block_h = el[1], el[2]
                if card_type == 'dashboard': self.set_fill_color(243, 235, 248) 
                else: self.set_fill_color(232, 244, 248)
                    
                self.rect(10, curr_y, 190, block_h, 'F')
                self.set_fill_color(*accent_c)
                self.rect(10, curr_y, 1.5, block_h, 'F')
                
                self.set_xy(14, curr_y + 2)
                self.set_font('Arial', 'I', 8.5)
                self.set_text_color(*text_main)
                self.multi_cell(182, 4.2, txt, align='L')
                curr_y += block_h + 3

        self.set_y(start_y + h_needed)

    def draw_setup_card(self, card_soup):
        """Universal parser for Buy, Open, Reduce, Watchlist, and Notes Cards"""
        self.reset_state()
        
        # 1. HEADER
        header = card_soup.find(class_='setup-header')
        ticker = safe_get_text(header.find(class_='ticker')) if header else ""
        badge_el = header.find(class_='setup-type') if header else None
        badge_txt = safe_get_text(badge_el)
        
        # 2. DETAILS (Supports Paragraphs & Lists)
        details_div = card_soup.find(class_='technical-details')
        details_texts = []
        if details_div:
            for child in details_div.find_all(['p', 'li']):
                prefix = "• " if child.name == 'li' else ""
                txt = safe_get_text(child)
                if txt: details_texts.append(prefix + txt)
                
        # 3. PARAMS
        params_div = card_soup.find(class_='trade-params')
        params_boxes = params_div.find_all(class_='param-box') if params_div else []
        
        # 4. RATIONALE & EXTRAS
        rationale_el = card_soup.find(class_='rationale')
        confidence_el = card_soup.find(class_=lambda c: c and 'confidence' in c)
        
        extra_texts = []
        for child in card_soup.children:
            if getattr(child, 'name', None) == 'p':
                txt = safe_get_text(child)
                if txt: extra_texts.append(txt)

        # HEIGHT CALCULATION
        self.set_font('Arial', '', 8.5)
        h_details = sum([len(self.multi_cell(186, 4.2, t, split_only=True)) * 4.2 + 2 for t in details_texts])
        h_extras = sum([len(self.multi_cell(186, 4.2, t, split_only=True)) * 4.2 + 2 for t in extra_texts])
        h_rationale = (len(self.multi_cell(184, 4.2, safe_get_text(rationale_el), split_only=True)) * 4.2 + 4) if rationale_el else 0
        
        params_count = len(params_boxes)
        if params_count == 4: cols, box_w, gap = 2, 88, 4
        elif params_count in [1, 2]: cols, box_w, gap = params_count, 88, 4
        else: cols, box_w, gap = 3, 58, 4
        h_params = (math.ceil(params_count / cols) * 14 + 6) if params_count > 0 else 0 

        total_height = 14 + (h_details + 3 if h_details else 0) + h_params + h_rationale + (h_extras + 2 if h_extras else 0) + (8 if confidence_el else 0) + 2
        self.check_page_break(total_height)
        start_y = self.get_y()
        
        # DRAW CARD BG
        self.set_fill_color(255, 255, 255)
        self.set_draw_color(230, 230, 230)
        self.rect(8, start_y, 194, total_height, 'DF')
        
        # DRAW HEADER
        self.set_xy(12, start_y + 3)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(44, 62, 80)
        self.cell(100, 6, ticker, 0, 1, 'L')
        
        self.set_font('Arial', 'B', 8)
        w_badge = max(self.get_string_width(badge_txt) + 12, 22)
        self.set_xy(202 - w_badge - 4, start_y + 3) 
        self.set_fill_color(109, 102, 204) # Default Purple
        self.set_text_color(255, 255, 255)
        self.cell(w_badge, 6, badge_txt, 0, 1, 'C', fill=True)
        
        self.set_draw_color(240, 240, 240)
        self.line(10, start_y + 11, 200, start_y + 11)
        curr_y = start_y + 13
        
        # DRAW DETAILS
        if details_texts:
            self.set_fill_color(248, 249, 250)
            self.rect(10, curr_y, 190, h_details + 3, 'F')
            curr_y += 1.5
            
            for t in details_texts:
                self.set_xy(12, curr_y)
                self.set_font('Arial', '', 8.5)
                
                # Smart Coloring
                if 'trend-bull' in t or 'Hold' in t or 'Breakout' in t: self.set_text_color(39, 174, 96)
                elif 'trend-bear' in t or 'Exit' in t or 'Breakdown' in t: self.set_text_color(231, 76, 60)
                else: self.set_text_color(60, 60, 60)
                
                self.multi_cell(186, 4.2, t, align='L')
                curr_y = self.get_y() + 2 
            curr_y += 1.5

        # DRAW PARAMS
        if params_boxes:
            self.set_fill_color(253, 235, 245) 
            self.rect(10, curr_y, 190, h_params, 'F')
            
            start_x = 10 + (190 - ((cols * box_w) + ((cols - 1) * gap))) / 2
            grid_y = curr_y + 3
            
            for i, box in enumerate(params_boxes):
                row = i // cols
                col = i % cols
                x = start_x + (col * (box_w + gap))
                y = grid_y + (row * 14)
                
                self.set_fill_color(255, 255, 255)
                self.rect(x, y, box_w, 11, 'F')
                
                lbl = safe_get_text(box.find(class_='param-label'))
                val_node = box.find(class_='param-value')
                val = safe_get_text(val_node)
                
                self.set_xy(x, y + 1.5)
                self.set_font('Arial', '', 6.5)
                self.set_text_color(100, 100, 100)
                self.cell(box_w, 4, lbl.upper(), 0, 1, 'C')
                
                self.set_xy(x, y + 5.5)
                self.set_font('Arial', 'B', 9.5)
                
                # Inline color parser
                val_r, val_g, val_b = 44, 62, 80
                if val_node and val_node.has_attr('style'):
                    st = val_node['style'].lower()
                    if '27ae60' in st: val_r, val_g, val_b = 39, 174, 96
                    elif 'e74c3c' in st: val_r, val_g, val_b = 231, 76, 60
                self.set_text_color(val_r, val_g, val_b)
                self.cell(box_w, 5, val, 0, 1, 'C')
                
            curr_y += h_params

        # DRAW RATIONALE
        if rationale_el:
            self.set_fill_color(232, 244, 248) 
            self.rect(10, curr_y, 190, h_rationale, 'F')
            self.set_fill_color(52, 152, 219)
            self.rect(10, curr_y, 1.5, h_rationale, 'F') 
            
            self.set_xy(14, curr_y + 2)
            self.set_font('Arial', 'I', 8.5)
            self.set_text_color(52, 73, 94) 
            self.multi_cell(184, 4.2, safe_get_text(rationale_el), align='L')
            curr_y += h_rationale

        # DRAW EXTRAS (e.g. Invalidation Cues)
        if extra_texts:
            curr_y += 1
            self.set_font('Arial', 'B', 8.5)
            self.set_text_color(114, 28, 36) # Dark Red
            for t in extra_texts:
                self.set_xy(12, curr_y)
                self.multi_cell(186, 4.2, t, align='L')
                curr_y = self.get_y() + 1
                
        # DRAW CONFIDENCE
        if confidence_el:
            txt = safe_get_text(confidence_el)
            c_class = confidence_el.get('class', [])
            bg_c, text_c = (248, 249, 250), (44, 62, 80) 
            if any('high' in c for c in c_class): bg_c, text_c = (212, 237, 218), (21, 87, 36)
            elif any('medium' in c for c in c_class): bg_c, text_c = (255, 243, 205), (133, 100, 4)
            elif any('low' in c for c in c_class): bg_c, text_c = (248, 215, 218), (114, 28, 36)
            
            self.set_fill_color(*bg_c)
            self.set_text_color(*text_c)
            self.set_font('Arial', 'B', 8)
            
            self.set_xy(10, curr_y + 1)
            w_txt = self.get_string_width(txt) + 6
            self.rect(10, curr_y + 1, w_txt, 6, 'F')
            self.cell(w_txt, 6, txt, 0, 1, 'C')

        self.set_y(start_y + total_height + 2)

    def draw_disclaimer(self, disc_soup):
        self.reset_state()
        title = safe_get_text(disc_soup.find('h3')) or "Disclaimer"
        ps = disc_soup.find_all('p')
        
        h_needed = 10
        self.set_font('Arial', '', 7)
        for p in ps: h_needed += len(self.multi_cell(190, 3.5, safe_get_text(p), split_only=True)) * 3.5 + 1.5
        self.check_page_break(h_needed)
        
        start_y = self.get_y()
        self.set_fill_color(255, 243, 205) 
        self.set_draw_color(255, 193, 7) 
        self.set_line_width(0.4)
        self.rect(8, start_y, 194, h_needed, 'DF')
        
        self.set_xy(10, start_y + 2)
        self.set_font('Arial', 'B', 8)
        self.set_text_color(133, 100, 4) 
        self.cell(0, 4, title, 0, 1, 'L')
        
        curr_y = start_y + 7
        self.set_font('Arial', '', 7)
        for p in ps:
            self.set_xy(10, curr_y)
            self.multi_cell(190, 3.5, safe_get_text(p), align='L')
            curr_y = self.get_y() + 1.5
            
        self.set_y(start_y + h_needed + 3)

# --- 3. HTML PARSER ORCHESTRATOR ---
def parse_and_generate_pdf(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    date_el = soup.find(class_='date')
    subtitle = safe_get_text(date_el) if date_el else "Market Report"

    pdf = PDF(subtitle)
    pdf.set_auto_page_break(auto=False) 
    pdf.add_page()

    alert = soup.find(class_='alert-box')
    if alert:
        title = safe_get_text(alert.find('h3')) or "ALERT"
        txt = safe_get_text(alert).replace(title, "").strip()
        pdf.draw_notice_box(txt, style='warning')

    # SECTION 0: Dashboard
    dash_head = soup.find(string=re.compile("Market Positioning Dashboard"))
    if dash_head:
        section = dash_head.find_parent(class_='section')
        if section:
            pdf.section_header("Market Positioning Dashboard (Quantified)", new_page=False)
            card = section.find(class_='index-card')
            if card: pdf.draw_generic_card(card, 'dashboard')

    # THE TABS LOOP
    tabs = [
        ('tab-index', "Index Analysis — EGX30", False), # Kept on Page 1
        ('tab-market', "Market Trend (Internal Structure)", False), # Kept on Page 1
        ('tab-buy', "Top Opportunities", True), # Forces Page 2
        ('tab-open', "Open Positions Management", True),
        ('tab-reduce', "Reduce / Distribute", True),
        ('tab-watchlist', "Watchlist", True),
        ('tab-notes', "Market Notes", True)
    ]

    for tab_id, header_title, force_new_page in tabs:
        tab = soup.find(id=tab_id)
        if not tab: continue
        
        pdf.section_header(header_title, new_page=force_new_page)
        
        # Parse Every Child Dynamically
        sections = tab.find_all(class_='section')
        for sec in sections:
            for child in sec.children:
                if not getattr(child, 'name', None): continue
                
                if child.name == 'div':
                    c_class = child.get('class', [])
                    if 'setup-card' in c_class:
                        pdf.draw_setup_card(child)
                    elif 'index-card' in c_class:
                        pdf.draw_generic_card(child, 'index')
                    elif 'market-assessment' in c_class:
                        pdf.draw_generic_card(child, 'market')
                        
                elif child.name == 'p':
                    txt = safe_get_text(child)
                    if len(txt) > 10 and "Note:" in txt or "Reminder:" in txt or "Top 3" in txt:
                        style = 'warning' if 'Distribute' in header_title else 'neutral'
                        pdf.draw_notice_box(txt, style=style)

    # DISCLAIMER
    disclaimer = soup.find(class_='disclaimer')
    if disclaimer:
        pdf.draw_disclaimer(disclaimer)

    return pdf

# --- 4. STREAMLIT APP ---
st.set_page_config(page_title="BlueberryAI Formatter", layout="centered")
st.title("📄 BlueberryAI PDF Generator")
st.write("Upload your HTML report to generate a pixel-perfect, completely dynamic PDF.")

uploaded_file = st.file_uploader("Choose HTML file", type="html")

if uploaded_file is not None:
    if st.button("Generate PDF"):
        with st.spinner("Parsing HTML and Rendering PDF..."):
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
