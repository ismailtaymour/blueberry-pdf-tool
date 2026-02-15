import streamlit as st
from fpdf import FPDF
from bs4 import BeautifulSoup
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

# --- 2. PDF ENGINE WITH CONDENSED LAYOUT ---
class PDF(FPDF):
    def __init__(self, subtitle_text=""):
        super().__init__()
        self.subtitle_text = subtitle_text

    def header(self):
        # CONDENSED HEADER (Height reduced from 45 to 32)
        self.set_fill_color(44, 62, 80)
        self.rect(0, 0, 210, 32, 'F')
        
        self.set_font('Arial', 'B', 18) # Reduced from 22
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 6)
        self.cell(0, 8, 'BlueberryAI - EGX30 Market Intelligence', 0, 1, 'C')
        
        self.set_font('Arial', '', 9) # Reduced from 10
        self.set_xy(10, 14)
        self.cell(0, 5, 'AI-Generated Market Analysis | For Informational Purposes Only', 0, 1, 'C')
        
        self.set_font('Arial', '', 8) # Reduced from 9
        self.set_text_color(200, 200, 200)
        self.set_draw_color(100, 110, 120)
        self.line(40, 21, 170, 21) 
        self.set_xy(10, 23)
        self.cell(0, 5, self.subtitle_text, 0, 1, 'C')
        self.ln(5) # Reduced margin below header

    def footer(self):
        self.set_y(-15) # Shorter footer
        self.set_fill_color(52, 73, 94) 
        self.rect(0, 282, 210, 15, 'F')
        self.set_font('Arial', '', 7.5)
        self.set_text_color(200, 200, 200)
        self.cell(0, 8, f'Blueberry AI Trader | Technical Analysis System | Page {self.page_no()}', 0, 0, 'C')

    def check_page_break(self, height_needed):
        if self.get_y() + height_needed > 278:
            self.add_page()

    def reset_state(self):
        self.set_left_margin(10)
        self.set_right_margin(10)
        self.set_x(10)
        self.set_font('Arial', '', 8.5)
        self.set_text_color(51, 51, 51)

    def section_header(self, title, new_page=True):
        self.reset_state()
        
        # STRICT NEW PAGE LOGIC: Add page if requested AND we aren't already at the top
        if new_page and self.get_y() > 40:
            self.add_page()
        elif self.get_y() > 265: 
            self.add_page()
            
        self.ln(2)
        # Blue left border
        self.set_fill_color(52, 152, 219)
        self.rect(10, self.get_y(), 2, 8, 'F')
        
        self.set_x(15)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(44, 62, 80)
        self.cell(0, 8, title, 0, 1, 'L')
        self.ln(3)

    def alert_box(self, title, text):
        self.reset_state()
        self.set_font('Arial', '', 9)
        lines = len(self.multi_cell(180, 4.5, text, split_only=True))
        h_needed = (lines * 4.5) + 12 
        
        self.check_page_break(h_needed)
        start_y = self.get_y()
        
        self.set_fill_color(255, 235, 238)
        self.set_draw_color(231, 76, 60)
        self.set_line_width(0.5)
        self.rect(10, start_y, 190, h_needed, 'DF')
        
        self.set_xy(15, start_y + 3)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(192, 57, 43)
        self.cell(0, 6, title, 0, 1, 'L')
        
        self.set_xy(15, start_y + 9)
        self.set_font('Arial', '', 9)
        self.set_text_color(60, 0, 0)
        self.multi_cell(180, 4.5, text, align='L')
        
        self.set_y(start_y + h_needed + 3)
        self.set_line_width(0.2)

    def draw_index_card(self, title, metrics):
        self.reset_state()
        h_needed = 12 + (len(metrics) * 6) + 4
        self.check_page_break(h_needed)
        
        start_y = self.get_y()
        self.set_fill_color(240, 244, 248) 
        self.set_draw_color(220, 225, 230)
        self.rect(10, start_y, 190, h_needed, 'DF')
        
        self.set_xy(15, start_y + 3)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(44, 62, 80)
        self.cell(0, 6, title, 0, 1, 'L')
        
        self.set_draw_color(52, 152, 219)
        self.set_line_width(0.5)
        self.line(15, self.get_y(), 195, self.get_y())
        self.set_line_width(0.2)
        
        curr_y = self.get_y() + 3
        self.set_draw_color(220, 220, 220)
        
        for lbl, val, trend in metrics:
            self.set_xy(15, curr_y)
            self.set_text_color(85, 85, 85)
            self.set_font('Arial', 'B', 8.5)
            self.cell(80, 5, lbl, 0, 0, 'L')
            
            if trend == 'bull': self.set_text_color(39, 174, 96)
            elif trend == 'bear': self.set_text_color(231, 76, 60)
            else: self.set_text_color(44, 62, 80)
            
            self.cell(95, 5, val, 0, 1, 'R')
            curr_y += 6
            self.line(15, curr_y-1, 195, curr_y-1)
            
        self.set_y(start_y + h_needed + 4)

    def draw_risk_score(self, risk_box_soup):
        self.reset_state()
        title = safe_get_text(risk_box_soup.find('h3')) or "Risk Assessment"
        p_tags = risk_box_soup.find_all('p')
        texts = [safe_get_text(p) for p in p_tags if safe_get_text(p)]
        if not texts: return
        
        h_needed = 15 + (len(texts) * 6) + 10
        self.check_page_break(h_needed)
        
        start_y = self.get_y()
        self.set_fill_color(217, 60, 43) 
        self.rect(10, start_y, 190, h_needed, 'F')
        
        self.set_xy(15, start_y + 4)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(255, 255, 255)
        self.cell(0, 6, title, 0, 1, 'L')
        self.set_draw_color(255, 255, 255)
        self.line(15, self.get_y(), 195, self.get_y())
        
        curr_y = self.get_y() + 4
        for i, txt in enumerate(texts):
            self.set_xy(15, curr_y)
            if "Risk Score" in txt or "Recommended" in txt or "Allocation" in txt:
                self.set_font('Arial', 'B', 11)
            else:
                self.set_font('Arial', '', 9)
            self.multi_cell(180, 5, txt, align='C')
            curr_y = self.get_y() + 1
            
        self.set_y(start_y + h_needed + 4)

    def draw_market_assessment(self, assess_soup):
        self.reset_state()
        title = safe_get_text(assess_soup.find('h3'))
        p_tags = assess_soup.find_all('p')
        
        h_needed = 14
        self.set_font('Arial', '', 9)
        for p in p_tags:
            h_needed += len(self.multi_cell(180, 4.5, safe_get_text(p), split_only=True)) * 4.5 + 3
            
        self.check_page_break(h_needed)
        start_y = self.get_y()
        
        self.set_fill_color(109, 102, 204) 
        self.rect(10, start_y, 190, h_needed, 'F')
        
        self.set_xy(15, start_y + 4)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(255, 255, 255)
        self.cell(0, 6, title, 0, 1, 'L')
        self.set_draw_color(255, 255, 255)
        self.line(15, self.get_y(), 195, self.get_y())
        
        curr_y = self.get_y() + 4
        self.set_font('Arial', '', 9)
        for p in p_tags:
            self.set_xy(15, curr_y)
            self.multi_cell(180, 4.5, safe_get_text(p), align='L')
            curr_y = self.get_y() + 3
            
        self.set_y(start_y + h_needed + 4)

    def draw_setup_card(self, card_soup):
        self.reset_state()
        
        # EXTRACT DATA
        ticker = safe_get_text(card_soup.find(class_='ticker'))
        name_el = card_soup.find(class_='company-name') or card_soup.find('div', style=lambda v: v and 'color: #666' in v)
        name = safe_get_text(name_el) if name_el else ""
        if ticker in name: name = name.replace(ticker, "").strip(" -|")
        
        badge_el = card_soup.find(class_='setup-type')
        badge_txt = safe_get_text(badge_el)
        
        badge_r, badge_g, badge_b = 109, 102, 204 # Default
        if badge_el and badge_el.has_attr('style'):
            style = badge_el['style'].lower()
            if '27ae60' in style or 'green' in style: badge_r, badge_g, badge_b = 39, 174, 96
            elif 'e74c3c' in style or 'c0392b' in style or 'red' in style: badge_r, badge_g, badge_b = 231, 76, 60
        
        details_ps = card_soup.find(class_='technical-details').find_all('p') if card_soup.find(class_='technical-details') else []
        params_boxes = card_soup.find_all(class_='param-box')
        rationale_el = card_soup.find(class_='rationale')
        confidence_el = card_soup.find(class_=lambda c: c and 'confidence' in c)
        
        # HEIGHT CALCULATION
        self.set_font('Arial', '', 8.5)
        h_details = sum([len(self.multi_cell(180, 4.5, safe_get_text(p), split_only=True)) * 4.5 + 2 for p in details_ps])
        h_params = (math.ceil(len(params_boxes) / 3) * 14 + 10) if params_boxes else 0
        h_rationale = (len(self.multi_cell(180, 4.5, safe_get_text(rationale_el), split_only=True)) * 4.5 + 6) if rationale_el else 0
        
        total_height = 14 + (h_details + 6 if h_details else 0) + h_params + h_rationale + (10 if confidence_el else 0) + 4
        self.check_page_break(total_height)
        start_y = self.get_y()
        
        # DRAW CARD
        self.set_fill_color(255, 255, 255)
        self.set_draw_color(236, 240, 241)
        self.rect(10, start_y, 190, total_height, 'DF')
        
        # HEADER
        self.set_xy(15, start_y + 4)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(44, 62, 80)
        self.cell(30, 6, ticker, 0, 0, 'L')
        self.set_font('Arial', '', 9)
        self.set_text_color(102, 102, 102)
        self.cell(90, 6, name, 0, 0, 'L')
        
        self.set_fill_color(badge_r, badge_g, badge_b)
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 7)
        self.cell(60, 6, badge_txt, 0, 1, 'C', fill=True)
        
        self.set_draw_color(236, 240, 241)
        self.line(15, self.get_y() + 2, 195, self.get_y() + 2)
        
        curr_y = self.get_y() + 4
        
        # DETAILS
        if details_ps:
            self.set_fill_color(248, 249, 250)
            self.rect(15, curr_y, 180, h_details + 4, 'F')
            curr_y += 2
            self.set_text_color(60, 60, 60)
            self.set_font('Arial', '', 8.5)
            for p in details_ps:
                self.set_xy(18, curr_y)
                self.multi_cell(174, 4.5, safe_get_text(p), align='L')
                curr_y = self.get_y() + 2
            curr_y += 2

        # PARAMS
        if params_boxes:
            self.set_fill_color(253, 235, 245) # Light pink
            self.rect(15, curr_y, 180, h_params - 3, 'F')
            
            box_width = 56
            gap = 4
            grid_y = curr_y + 3
            
            for i, box in enumerate(params_boxes):
                row = i // 3
                col = i % 3
                x = 18 + (col * (box_width + gap))
                y = grid_y + (row * 14)
                
                self.set_fill_color(255, 255, 255)
                self.rect(x, y, box_width, 12, 'F')
                
                lbl = safe_get_text(box.find(class_='param-label'))
                val_el = box.find(class_='param-value')
                val = safe_get_text(val_el)
                
                val_r, val_g, val_b = 44, 62, 80
                if val_el and val_el.has_attr('style'):
                    st = val_el['style'].lower()
                    if '27ae60' in st or 'green' in st: val_r, val_g, val_b = 39, 174, 96
                    elif 'e74c3c' in st or 'red' in st: val_r, val_g, val_b = 231, 76, 60
                    elif 'f39c12' in st or 'orange' in st: val_r, val_g, val_b = 243, 156, 18
                
                self.set_xy(x, y + 1)
                self.set_font('Arial', '', 6.5)
                self.set_text_color(102, 102, 102)
                self.cell(box_width, 4, lbl.upper(), 0, 1, 'C')
                
                self.set_xy(x, y + 5)
                self.set_font('Arial', 'B', 9)
                self.set_text_color(val_r, val_g, val_b)
                self.cell(box_width, 6, val, 0, 1, 'C')
                
            curr_y += h_params - 1

        # RATIONALE
        if rationale_el:
            self.set_fill_color(232, 244, 248) 
            self.rect(15, curr_y, 180, h_rationale - 2, 'F')
            self.set_fill_color(52, 152, 219)
            self.rect(15, curr_y, 2, h_rationale - 2, 'F') 
            
            self.set_xy(20, curr_y + 2)
            self.set_font('Arial', 'I', 8.5)
            self.set_text_color(52, 73, 94) 
            self.multi_cell(170, 4.5, safe_get_text(rationale_el), align='L')
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
            self.set_font('Arial', 'B', 7.5)
            
            self.set_xy(15, curr_y)
            w_txt = self.get_string_width(txt) + 8
            self.rect(15, curr_y, w_txt, 6, 'F')
            self.cell(w_txt, 6, txt, 0, 1, 'C')

        self.set_y(start_y + total_height + 4)

    def draw_watchlist(self, watchlist_soup):
        self.reset_state()
        intro_p = watchlist_soup.find('p')
        if intro_p:
            self.set_font('Arial', 'B', 9)
            self.set_text_color(52, 73, 94)
            self.multi_cell(190, 5, safe_get_text(intro_p), align='L')
            self.ln(3)

        items = watchlist_soup.find_all(class_='watchlist-item')
        if not items: return

        for item in items:
            h4 = item.find('h4')
            title = safe_get_text(h4)
            ps = item.find_all('p')
            
            self.set_font('Arial', '', 8.5)
            h_needed = 8
            for p in ps:
                h_needed += len(self.multi_cell(175, 4.5, safe_get_text(p), split_only=True)) * 4.5 + 1.5
                
            self.check_page_break(h_needed + 4)
            start_y = self.get_y()
            
            self.set_fill_color(255, 236, 210)
            self.rect(10, start_y, 190, h_needed + 4, 'F')
            self.set_fill_color(255, 255, 255)
            self.rect(15, start_y + 2, 180, h_needed, 'F')
            self.set_fill_color(230, 126, 34) 
            self.rect(15, start_y + 2, 3, h_needed, 'F')
            
            curr_y = start_y + 4
            self.set_xy(22, curr_y)
            self.set_font('Arial', 'B', 10)
            self.set_text_color(44, 62, 80)
            self.cell(0, 5, title, 0, 1, 'L')
            
            curr_y += 6
            self.set_font('Arial', '', 8.5)
            self.set_text_color(51, 51, 51)
            for p in ps:
                self.set_xy(22, curr_y)
                self.multi_cell(170, 4.5, safe_get_text(p), align='L')
                curr_y = self.get_y() + 1.5
                
            self.set_y(start_y + h_needed + 6)

    def draw_notice_box(self, box_soup):
        self.reset_state()
        txt = safe_get_text(box_soup)
        lines = len(self.multi_cell(180, 4.5, txt, split_only=True))
        h_needed = (lines * 4.5) + 6
        self.check_page_break(h_needed)
        
        self.set_fill_color(248, 215, 218)
        self.set_text_color(114, 28, 36)
        self.rect(10, self.get_y(), 190, h_needed, 'F')
        self.set_xy(15, self.get_y() + 3)
        self.set_font('Arial', 'B', 8.5)
        self.multi_cell(180, 4.5, txt, align='L')
        self.ln(5)

    def draw_disclaimer(self, disc_soup):
        self.reset_state()
        title = safe_get_text(disc_soup.find('h3')) or "Disclaimer"
        ps = disc_soup.find_all('p')
        
        h_needed = 12
        self.set_font('Arial', '', 7.5)
        for p in ps: h_needed += len(self.multi_cell(180, 3.5, safe_get_text(p), split_only=True)) * 3.5 + 2
        self.check_page_break(h_needed)
        
        start_y = self.get_y()
        self.set_fill_color(255, 243, 205) 
        self.set_draw_color(255, 193, 7) 
        self.set_line_width(0.5)
        self.rect(10, start_y, 190, h_needed, 'DF')
        
        self.set_xy(15, start_y + 3)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(133, 100, 4) 
        self.cell(0, 5, title, 0, 1, 'L')
        
        curr_y = start_y + 9
        self.set_font('Arial', '', 7.5)
        for p in ps:
            self.set_xy(15, curr_y)
            self.multi_cell(180, 3.5, safe_get_text(p), align='L')
            curr_y = self.get_y() + 2
            
        self.set_y(start_y + h_needed + 5)

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
        pdf.section_header("Index Technical Status", new_page=True)
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
            pdf.draw_risk_score(risk_box)

    # 2. MARKET TREND
    tab_market = soup.find(id='tab-market')
    if tab_market:
        pdf.section_header("Market Trend Assessment", new_page=True)
        for assess in tab_market.find_all(class_='market-assessment'):
            pdf.draw_market_assessment(assess)

    # 3. TOP OPPORTUNITIES
    tab_buy = soup.find(id='tab-buy')
    if tab_buy:
        pdf.section_header("Top Accumulation Opportunities", new_page=True)
        intro_p = tab_buy.find('p', style=lambda s: s and 'background' in s)
        if intro_p:
            pdf.reset_state()
            pdf.set_fill_color(232, 244, 248)
            txt = safe_get_text(intro_p)
            h = len(pdf.multi_cell(180, 4.5, txt, split_only=True)) * 4.5 + 6
            pdf.check_page_break(h)
            pdf.rect(10, pdf.get_y(), 190, h, 'F')
            pdf.set_xy(15, pdf.get_y() + 3)
            pdf.set_font('Arial', '', 9)
            pdf.multi_cell(180, 4.5, txt, align='L')
            pdf.ln(5)
            
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
            h = len(pdf.multi_cell(180, 4.5, txt, split_only=True)) * 4.5 + 6
            pdf.check_page_break(h)
            pdf.rect(10, pdf.get_y(), 190, h, 'F')
            pdf.set_xy(15, pdf.get_y() + 3)
            pdf.set_font('Arial', '', 9)
            pdf.multi_cell(180, 4.5, txt, align='L')
            pdf.ln(5)
            
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
            pdf.draw_watchlist(wl_container)

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
