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

# --- 2. COMPACT PDF ENGINE ---
class PDF(FPDF):
    def __init__(self, subtitle_text=""):
        super().__init__()
        self.subtitle_text = subtitle_text

    def header(self):
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
        
        # CRITICAL FIX: Lock Y cursor below the header to prevent overlap on new pages
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
            # FPDF automatically calls header() which safely resets Y to 30

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
        self.set_fill_color(52, 152, 219)
        self.rect(8, self.get_y(), 1.5, 6, 'F') 
        
        self.set_x(11)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(44, 62, 80)
        self.cell(0, 6, title, 0, 1, 'L')
        self.ln(1.5)

    def alert_box(self, title, text):
        self.reset_state()
        self.set_font('Arial', '', 8.5)
        lines = len(self.multi_cell(186, 4, clean_text(text), split_only=True))
        h_needed = (lines * 4) + 10 
        
        self.check_page_break(h_needed)
        start_y = self.get_y()
        
        self.set_fill_color(255, 235, 238)
        self.set_draw_color(231, 76, 60)
        self.set_line_width(0.3)
        self.rect(8, start_y, 194, h_needed, 'DF')
        
        self.set_xy(11, start_y + 2)
        self.set_font('Arial', 'B', 10)
        self.set_text_color(192, 57, 43)
        self.cell(0, 5, clean_text(title), 0, 1, 'L')
        
        self.set_xy(11, start_y + 7)
        self.set_font('Arial', '', 8.5)
        self.set_text_color(60, 0, 0)
        self.multi_cell(188, 4, clean_text(text), align='L')
        self.set_y(start_y + h_needed + 2)
        self.set_line_width(0.2)

    def draw_index_card(self, title, metrics):
        self.reset_state()
        h_needed = 10 + (len(metrics) * 5) + 3 # Compressed line height
        self.check_page_break(h_needed)
        
        start_y = self.get_y()
        self.set_fill_color(240, 244, 248) 
        self.set_draw_color(220, 225, 230)
        self.rect(8, start_y, 194, h_needed, 'DF')
        
        self.set_xy(12, start_y + 2)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(44, 62, 80)
        self.cell(0, 6, title, 0, 1, 'L')
        
        self.set_draw_color(52, 152, 219)
        self.line(11, self.get_y(), 199, self.get_y())
        
        curr_y = self.get_y() + 2
        self.set_draw_color(220, 220, 220)
        
        for lbl, val, trend in metrics:
            self.set_xy(12, curr_y)
            self.set_text_color(85, 85, 85)
            self.set_font('Arial', 'B', 8)
            self.cell(80, 5, lbl, 0, 0, 'L')
            
            if trend == 'bull': self.set_text_color(39, 174, 96)
            elif trend == 'bear': self.set_text_color(231, 76, 60)
            else: self.set_text_color(44, 62, 80)
            
            self.cell(100, 5, val, 0, 1, 'R')
            curr_y += 5
            self.line(12, curr_y, 198, curr_y)
            
        self.set_y(start_y + h_needed + 2)

    def risk_summary_box(self, risk_data):
        self.reset_state()
        h_needed = 38 
        self.check_page_break(h_needed)
        start_y = self.get_y()
        
        self.set_fill_color(231, 76, 60)
        self.rect(8, start_y, 194, h_needed, 'F')
        
        self.set_xy(8, start_y + 2)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(255, 255, 255)
        self.cell(194, 5, "Risk Assessment", 0, 1, 'C')
        
        self.set_font('Arial', 'B', 12)
        self.cell(194, 5, clean_text(risk_data.get('score', 'Risk Score: N/A')), 0, 1, 'C')
        self.set_font('Arial', '', 9)
        self.cell(194, 4, clean_text(risk_data.get('env', '')), 0, 1, 'C')
        
        # White Box
        box_y = self.get_y() + 3
        self.set_fill_color(255, 255, 255)
        self.rect(12, box_y, 186, 16, 'F')
        
        self.set_xy(12, box_y + 2)
        self.set_text_color(192, 57, 43) 
        self.set_font('Arial', 'B', 9)
        combo_txt = f"{clean_text(risk_data.get('exposure', ''))}  |  {clean_text(risk_data.get('allocation', ''))}"
        self.cell(186, 4, combo_txt, 0, 1, 'C')
        
        self.set_xy(14, box_y + 7)
        self.set_font('Arial', '', 7.5)
        self.set_text_color(100, 100, 100)
        self.multi_cell(182, 3.5, clean_text(risk_data.get('details', '')), align='C')
        
        self.set_y(start_y + h_needed + 2)

    def draw_market_assessment(self, assess_soup):
        self.reset_state()
        title = safe_get_text(assess_soup.find('h3'))
        p_tags = assess_soup.find_all('p')
        
        h_needed = 8
        self.set_font('Arial', '', 8.5)
        for p in p_tags:
            h_needed += len(self.multi_cell(186, 4, safe_get_text(p), split_only=True)) * 4 + 2
            
        self.check_page_break(h_needed)
        start_y = self.get_y()
        
        self.set_fill_color(109, 102, 204) 
        self.rect(8, start_y, 194, h_needed, 'F')
        
        self.set_xy(12, start_y + 2)
        self.set_font('Arial', 'B', 10)
        self.set_text_color(255, 255, 255)
        self.cell(0, 6, title, 0, 1, 'L')
        self.set_draw_color(255, 255, 255)
        self.line(12, self.get_y(), 198, self.get_y())
        
        curr_y = self.get_y() + 2
        self.set_font('Arial', '', 8.5)
        for p in p_tags:
            self.set_xy(12, curr_y)
            self.multi_cell(186, 4, safe_get_text(p), align='L')
            curr_y = self.get_y() + 2
            
        self.set_y(start_y + h_needed + 2)

    def draw_setup_card(self, card_soup, is_watchlist=False):
        self.reset_state()
        
        # EXTRACT DATA
        ticker = safe_get_text(card_soup.find(class_='ticker'))
        name_el = card_soup.find(class_='company-name') or card_soup.find('div', style=lambda v: v and 'color: #666' in v)
        name = safe_get_text(name_el) if name_el else ""
        if ticker in name: name = name.replace(ticker, "").strip(" -|")
        
        badge_el = card_soup.find(class_='setup-type')
        badge_txt = safe_get_text(badge_el)
        
        badge_r, badge_g, badge_b = 109, 102, 204
        if badge_el and badge_el.has_attr('style'):
            style = badge_el['style'].lower()
            if '27ae60' in style or 'green' in style: badge_r, badge_g, badge_b = 39, 174, 96
            elif 'e74c3c' in style or 'c0392b' in style or 'red' in style: badge_r, badge_g, badge_b = 231, 76, 60
        
        if is_watchlist: badge_r, badge_g, badge_b = 230, 126, 34 
        
        details_ps = card_soup.find(class_='technical-details').find_all('p') if card_soup.find(class_='technical-details') else []
        params_boxes = card_soup.find_all(class_='param-box')
        rationale_el = card_soup.find(class_='rationale')
        confidence_el = card_soup.find(class_=lambda c: c and 'confidence' in c)
        
        # PARAMETER GRID CALCULATION (Smart 2x2 vs 3-col)
        params_count = len(params_boxes)
        if params_count == 4:
            col_count = 2
            box_width = 88
            gap = 4
        elif params_count in [1, 2]:
            col_count = params_count
            box_width = 88
            gap = 4
        else:
            col_count = 3
            box_width = 58
            gap = 4
            
        rows_needed = math.ceil(params_count / col_count) if params_count > 0 else 0
        h_params = (rows_needed * 14 + 6) if params_count > 0 else 0 

        # HEIGHT CALCULATION
        self.set_font('Arial', '', 8.5)
        h_details = sum([len(self.multi_cell(186, 4.5, safe_get_text(p), split_only=True)) * 4.5 + 2 for p in details_ps])
        h_rationale = (len(self.multi_cell(184, 4.5, safe_get_text(rationale_el), split_only=True)) * 4.5 + 4) if rationale_el else 0
        
        # Fixed header height = 18
        total_height = 18 + (h_details + 3 if h_details else 0) + h_params + h_rationale + (8 if confidence_el else 0) + 2
        self.check_page_break(total_height)
        start_y = self.get_y()
        
        # DRAW CARD
        self.set_fill_color(255, 255, 255)
        self.set_draw_color(230, 230, 230)
        self.rect(8, start_y, 194, total_height, 'DF')
        
        # HEADER (Stacked text, right-aligned badge)
        self.set_xy(12, start_y + 3)
        self.set_font('Arial', 'B', 13)
        self.set_text_color(44, 62, 80)
        self.cell(100, 6, ticker, 0, 1, 'L')
        
        self.set_xy(12, start_y + 9)
        self.set_font('Arial', '', 9)
        self.set_text_color(102, 102, 102)
        self.cell(100, 5, name, 0, 1, 'L')
        
        # Badge
        self.set_font('Arial', 'B', 9)
        w_badge = self.get_string_width(badge_txt) + 12
        w_badge = max(w_badge, 22)
        self.set_xy(202 - w_badge - 4, start_y + 4) 
        self.set_fill_color(badge_r, badge_g, badge_b)
        self.set_text_color(255, 255, 255)
        self.cell(w_badge, 7, badge_txt, 0, 1, 'C', fill=True)
        
        self.set_draw_color(240, 240, 240)
        self.line(10, start_y + 16, 200, start_y + 16)
        
        curr_y = start_y + 18
        
        # DETAILS
        if details_ps:
            self.set_fill_color(248, 249, 250)
            self.rect(10, curr_y, 190, h_details + 3, 'F')
            curr_y += 1.5
            self.set_text_color(50, 50, 50)
            self.set_font('Arial', '', 8.5)
            for p in details_ps:
                self.set_xy(12, curr_y)
                self.multi_cell(186, 4.5, safe_get_text(p), align='L')
                curr_y = self.get_y() + 2 
            curr_y += 1.5

        # PARAMS GRID
        if params_boxes:
            self.set_fill_color(253, 235, 245) 
            self.rect(10, curr_y, 190, h_params, 'F')
            
            # Center the grid automatically
            grid_width = (col_count * box_width) + ((col_count - 1) * gap)
            start_x = 10 + (190 - grid_width) / 2
            
            grid_y = curr_y + 3
            for i, box in enumerate(params_boxes):
                row = i // col_count
                col = i % col_count
                x = start_x + (col * (box_width + gap))
                y = grid_y + (row * 14)
                
                self.set_fill_color(255, 255, 255)
                self.rect(x, y, box_width, 11, 'F')
                
                lbl = safe_get_text(box.find(class_='param-label'))
                val_el = box.find(class_='param-value')
                val = safe_get_text(val_el)
                
                val_r, val_g, val_b = 44, 62, 80
                if val_el and val_el.has_attr('style'):
                    st = val_el['style'].lower()
                    if '27ae60' in st or 'green' in st: val_r, val_g, val_b = 39, 174, 96
                    elif 'e74c3c' in st or 'red' in st: val_r, val_g, val_b = 231, 76, 60
                    elif 'f39c12' in st or 'orange' in st: val_r, val_g, val_b = 243, 156, 18
                
                self.set_xy(x, y + 1.5)
                self.set_font('Arial', '', 7)
                self.set_text_color(100, 100, 100)
                self.cell(box_width, 4, lbl.upper(), 0, 1, 'C')
                
                self.set_xy(x, y + 5.5)
                self.set_font('Arial', 'B', 9.5)
                self.set_text_color(val_r, val_g, val_b)
                self.cell(box_width, 5, val, 0, 1, 'C')
                
            curr_y += h_params

        # RATIONALE
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

        # CONFIDENCE
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
            
            self.set_xy(12, curr_y + 1)
            w_txt = self.get_string_width(txt) + 6
            self.rect(12, curr_y + 1, w_txt, 6, 'F')
            self.cell(w_txt, 6, txt, 0, 1, 'C')

        self.set_y(start_y + total_height + 2)

    def draw_notice_box(self, box_soup):
        self.reset_state()
        txt = safe_get_text(box_soup)
        lines = len(self.multi_cell(190, 4.5, txt, split_only=True))
        h_needed = (lines * 4.5) + 6
        self.check_page_break(h_needed)
        
        self.set_fill_color(248, 215, 218)
        self.set_text_color(114, 28, 36)
        self.rect(8, self.get_y(), 194, h_needed, 'F')
        self.set_xy(10, self.get_y() + 3)
        self.set_font('Arial', 'B', 8.5)
        self.multi_cell(190, 4.5, txt, align='C') 
        self.ln(3)

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

# --- 3. HTML PARSER ---
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
        pdf.alert_box(title, txt)

    # 1. INDEX ANALYSIS
    tab_index = soup.find(id='tab-index')
    if tab_index:
        pdf.section_header("Index Technical Status", new_page=False) # Keep on Page 1
        idx_card = tab_index.find(class_='index-card')
        if idx_card:
            title = safe_get_text(idx_card.find('h3'))
            metrics = []
            for row in idx_card.find_all(class_='metric-row'):
                lbl = safe_get_text(row.find(class_='metric-label'))
                val_el = row.find(class_='metric-value')
                val = safe_get_text(val_el)
                trend = 'neutral'
                if val_el and val_el.has_attr('class'):
                    c = val_el['class']
                    if 'trend-bull' in c: trend = 'bull'
                    elif 'trend-bear' in c: trend = 'bear'
                metrics.append((lbl, val, trend))
            pdf.draw_index_card(title, metrics)
            
        risk_box = tab_index.find(class_='risk-score-box')
        if risk_box:
            data = {}
            score_p = risk_box.find('p', style=lambda v: v and '1.8em' in v)
            if score_p: data['score'] = safe_get_text(score_p)
            if score_p and score_p.find_next_sibling('p'): data['env'] = safe_get_text(score_p.find_next_sibling('p'))
            inner_box = risk_box.find('div', style=lambda v: v and 'background' in v)
            if inner_box:
                ps = inner_box.find_all('p')
                if len(ps) > 0: data['exposure'] = safe_get_text(ps[0])
                if len(ps) > 1: data['allocation'] = safe_get_text(ps[1])
                if len(ps) > 2: data['details'] = safe_get_text(ps[2])
            if data:
                pdf.risk_summary_box(data)

    # 2. MARKET TREND
    tab_market = soup.find(id='tab-market')
    if tab_market:
        pdf.section_header("Market Trend Assessment", new_page=False) # Keep on Page 1 (will fit seamlessly)
        for assess in tab_market.find_all(class_='market-assessment'):
            pdf.draw_market_assessment(assess)

    # 3. TOP OPPORTUNITIES
    tab_buy = soup.find(id='tab-buy')
    if tab_buy:
        pdf.section_header("Top Accumulation Opportunities", new_page=True) # Forces break to page 2
        intro_p = tab_buy.find('p', style=lambda s: s and 'background' in s)
        if intro_p:
            pdf.reset_state()
            pdf.set_fill_color(232, 244, 248)
            txt = safe_get_text(intro_p)
            h = len(pdf.multi_cell(190, 4.5, txt, split_only=True)) * 4.5 + 4
            pdf.check_page_break(h)
            pdf.rect(8, pdf.get_y(), 194, h, 'F')
            pdf.set_xy(10, pdf.get_y() + 2)
            pdf.set_font('Arial', '', 8.5)
            pdf.multi_cell(190, 4.5, txt, align='L')
            pdf.ln(3)
            
        for card in tab_buy.find_all(class_='setup-card'):
            pdf.draw_setup_card(card)

    # 4. OPEN POSITIONS
    tab_open = soup.find(id='tab-open')
    if tab_open:
        pdf.section_header("Open Positions Management", new_page=True)
        intro_p = tab_open.find('p', style=lambda s: s and 'background' in s)
        if intro_p:
            pdf.reset_state()
            pdf.set_fill_color(232, 244, 248)
            txt = safe_get_text(intro_p)
            h = len(pdf.multi_cell(190, 4.5, txt, split_only=True)) * 4.5 + 4
            pdf.check_page_break(h)
            pdf.rect(8, pdf.get_y(), 194, h, 'F')
            pdf.set_xy(10, pdf.get_y() + 2)
            pdf.set_font('Arial', '', 8.5)
            pdf.multi_cell(190, 4.5, txt, align='L')
            pdf.ln(3)
            
        for card in tab_open.find_all(class_='setup-card'):
            pdf.draw_setup_card(card)

    # 5. REDUCE / DISTRIBUTE
    tab_reduce = soup.find(id='tab-reduce')
    if tab_reduce:
        pdf.section_header("Reduce/Distribution Recommendations", new_page=True)
        intro_p = tab_reduce.find('p', style=lambda s: s and 'color: #721c24' in s)
        if intro_p:
            pdf.draw_notice_box(intro_p)
            
        for card in tab_reduce.find_all(class_='setup-card'):
            pdf.draw_setup_card(card)

    # 6. WATCHLIST
    tab_watch = soup.find(id='tab-watchlist')
    if tab_watch:
        pdf.section_header("Watchlist", new_page=True)
        wl_container = tab_watch.find(class_='watchlist')
        if wl_container:
            intro_p = wl_container.find('p')
            if intro_p:
                pdf.reset_state()
                pdf.set_font('Arial', 'B', 8.5)
                pdf.set_text_color(52, 73, 94)
                pdf.multi_cell(194, 4, safe_get_text(intro_p), align='L')
                pdf.ln(2)

            items = wl_container.find_all(class_='watchlist-item')
            for item in items:
                card_soup_mock = BeautifulSoup('<div class="setup-card"></div>', 'html.parser').div
                
                h4 = item.find('h4')
                title_txt = safe_get_text(h4)
                if "-" in title_txt:
                    tick, name = title_txt.split("-", 1)
                else: tick, name = title_txt, ""
                
                tick_tag = soup.new_tag("div", attrs={"class": "ticker"})
                tick_tag.string = tick.strip()
                name_tag = soup.new_tag("div", attrs={"class": "company-name"})
                name_tag.string = name.strip()
                badge_tag = soup.new_tag("div", attrs={"class": "setup-type"})
                badge_tag.string = "WATCHLIST"
                
                card_soup_mock.append(tick_tag)
                card_soup_mock.append(name_tag)
                card_soup_mock.append(badge_tag)
                
                details_div = soup.new_tag("div", attrs={"class": "technical-details"})
                params_div = soup.new_tag("div", attrs={"class": "trade-params"})
                
                for p in item.find_all('p'):
                    txt = safe_get_text(p)
                    if '|' in txt:
                        if ':' in txt: _, txt = txt.split(':', 1)
                        parts = txt.split('|')
                        for part in parts:
                            part = part.strip()
                            if ' ' in part:
                                k, v = part.split(' ', 1)
                                if k[0].isdigit(): val, lbl = k, v
                                else: lbl, val = k, v
                                
                                lbl = lbl.lower()
                                if 'accum' in lbl: label = 'Accumulation'
                                elif 'proj' in lbl: label = 'Projected'
                                elif 'protect' in lbl: label = 'Protective'
                                else: label = lbl.title()
                                
                                box = soup.new_tag("div", attrs={"class": "param-box"})
                                l = soup.new_tag("div", attrs={"class": "param-label"})
                                l.string = label
                                v_tag = soup.new_tag("div", attrs={"class": "param-value"})
                                v_tag.string = val
                                box.append(l)
                                box.append(v_tag)
                                params_div.append(box)
                            else:
                                new_p = soup.new_tag("p")
                                new_p.string = part
                                details_div.append(new_p)
                    else:
                        new_p = soup.new_tag("p")
                        new_p.string = txt
                        details_div.append(new_p)
                        
                if details_div.contents: card_soup_mock.append(details_div)
                if params_div.contents: card_soup_mock.append(params_div)
                
                pdf.draw_setup_card(card_soup_mock, is_watchlist=True)

    # 7. DISCLAIMER
    disclaimer = soup.find(class_='disclaimer')
    if disclaimer:
        pdf.draw_disclaimer(disclaimer)

    return pdf

# --- 4. STREAMLIT APP ---
st.set_page_config(page_title="BlueberryAI Formatter", layout="centered")
st.title("📄 BlueberryAI PDF Generator")
st.write("Upload your HTML report to generate a pixel-perfect, condensed PDF.")

uploaded_file = st.file_uploader("Choose HTML file", type="html")

if uploaded_file is not None:
    if st.button("Generate PDF"):
        with st.spinner("Parsing and Framing PDF..."):
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
