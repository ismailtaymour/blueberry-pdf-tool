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
    # Nuke non-breaking spaces that break FPDF text wrapping
    text = text.replace('\xa0', ' ').replace('\u00A0', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    replacements = {
        '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '-', '\u2026': '...', '📊': '', 
        '📈': '', '🎯': '', '💼': '', '⚠️': '', '👀': '', '📝': '',
        '•': '-', '\u2022': '-' 
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode('latin-1', 'ignore').decode('latin-1').strip()

def safe_get_text(element):
    if not element: return ""
    return clean_text(element.get_text(" ", strip=True))

def hex_to_rgb(hex_color):
    hex_color = hex_color.replace(' ', '').lstrip('#')
    if len(hex_color) == 3: hex_color = ''.join([c*2 for c in hex_color])
    if len(hex_color) == 6: return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return (44, 62, 80)

# --- 2. COMPACT PDF ENGINE ---
class PDF(FPDF):
    def __init__(self, subtitle_text=""):
        super().__init__()
        self.subtitle_text = subtitle_text

    def header(self):
        # Expanded header height to safely accommodate multi-line subtitles
        self.set_fill_color(44, 62, 80)
        self.rect(0, 0, 210, 36, 'F') 
        
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
        # Multi-cell wrapper prevents off-page bleeding
        self.multi_cell(190, 4.2, self.subtitle_text, align='C')
        
        # Lock cursor safely below the expanded header
        self.set_y(38)

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
            self.set_y(38)

    def reset_state(self):
        self.set_left_margin(8) 
        self.set_right_margin(8)
        self.set_x(8)
        self.set_text_color(0, 0, 0)

    def section_header(self, title, new_page=False):
        self.reset_state()
        if new_page and self.get_y() > 45: 
            self.add_page()
            self.set_y(38)
        elif self.get_y() > 260: 
            self.add_page()
            self.set_y(38)
            
        self.ln(3)
        color = (155, 89, 182) if "Dashboard" in title else (52, 152, 219)
        self.set_fill_color(*color)
        self.rect(8, self.get_y(), 1.5, 6, 'F') 
        
        self.set_x(12)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(44, 62, 80)
        self.cell(0, 6, title, 0, 1, 'L')
        self.ln(2)

    def draw_notice_box(self, text, style='neutral'):
        self.reset_state()
        self.set_font('Arial', '', 8.5)
        lines = len(self.multi_cell(186, 4.2, text, split_only=True))
        h_needed = (lines * 4.2) + 6 
        
        self.check_page_break(h_needed)
        start_y = self.get_y()
        
        if 'warning' in style or 'Distribute' in text or 'Note:' in text:
            self.set_fill_color(248, 215, 218)
            self.set_text_color(114, 28, 36)
        else:
            self.set_fill_color(244, 246, 247)
            self.set_text_color(85, 85, 85)
            
        self.rect(8, start_y, 194, h_needed, 'DF')
        
        self.set_xy(12, start_y + 3)
        if 'warning' in style: self.set_font('Arial', 'B', 8.5)
        self.multi_cell(186, 4.2, text, align='L')
        self.set_y(start_y + h_needed + 3)

    def draw_dashboard_card(self, soup):
        self.reset_state()
        
        h_tag = soup.find(['h3', 'h2'])
        title_text = safe_get_text(h_tag) if h_tag else "Internal Market Map"
        
        top_items = []
        dash_row = soup.find(class_='dash-row')
        if dash_row:
            boxes = dash_row.find_all(class_='dash-box')
            for b in boxes:
                lbl = safe_get_text(b.find(class_='dash-label'))
                val_node = b.find(class_='dash-value')
                val = safe_get_text(val_node)
                color = (44, 62, 80)
                if val_node and val_node.has_attr('style'):
                    match = re.search(r'color:\s*(#[0-9a-fA-F]{3,6})', val_node['style'].replace(' ', ''))
                    if match: color = hex_to_rgb(match.group(1))
                top_items.append({'label': lbl, 'val': val, 'color': color})
                
        bottom_items = []
        count_row = soup.find(class_='count-row')
        if count_row:
            boxes = count_row.find_all(['div'], class_='count-box')
            for b in boxes:
                bottom_items.append({
                    'label': safe_get_text(b.find(class_='dash-label')),
                    'val': safe_get_text(b.find(class_='dash-value'))
                })
                    
        rat_node = soup.find(class_=['interp', 'rationale'])
        rat_txt = safe_get_text(rat_node)
        
        note_p = soup.find('p', string=lambda s: s and 'Note:' in s)
        note_txt = safe_get_text(note_p)

        self.set_font('Arial', '', 8.5)
        h_rat = (len(self.multi_cell(180, 4.2, rat_txt, split_only=True)) * 4.2 + 4) if rat_txt else 0
        h_note = (len(self.multi_cell(186, 4.2, note_txt, split_only=True)) * 4.2 + 2) if note_txt else 0
        
        h_needed = 16
        if top_items: h_needed += 15
        if bottom_items: h_needed += 17
        if h_rat: h_needed += h_rat + 3
        if h_note: h_needed += h_note + 4
        
        self.check_page_break(h_needed)
        start_y = self.get_y()
        
        self.set_fill_color(247, 243, 255)
        self.set_draw_color(230, 220, 245)
        self.rect(8, start_y, 194, h_needed, 'DF')
        
        self.set_xy(12, start_y + 4)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(91, 44, 131) 
        self.cell(0, 6, title_text, 0, 1, 'L')
        self.set_draw_color(155, 89, 182)
        self.line(12, self.get_y(), 198, self.get_y())
        
        curr_y = self.get_y() + 4
        
        if top_items:
            cols = len(top_items)
            box_w = min(44, (186 - (cols-1)*3) / cols) if cols > 0 else 44
            gap = (186 - (box_w * cols)) / (cols - 1) if cols > 1 else 0
            for i, item in enumerate(top_items):
                x = 12 + i * (box_w + gap)
                self.set_fill_color(255, 255, 255)
                self.rect(x, curr_y, box_w, 11, 'F')
                
                self.set_xy(x, curr_y + 1.5)
                self.set_font('Arial', '', 6)
                self.set_text_color(119, 119, 119)
                self.cell(box_w, 4, item['label'].upper(), 0, 1, 'C')
                
                self.set_xy(x, curr_y + 5.5)
                self.set_font('Arial', 'B', 9)
                self.set_text_color(*item['color'])
                
                if self.get_string_width(item['val']) > box_w - 2:
                    self.set_font('Arial', 'B', 7.5)
                self.cell(box_w, 5, item['val'], 0, 1, 'C')
            curr_y += 15
            
        if bottom_items:
            self.set_fill_color(142, 68, 173) 
            self.rect(12, curr_y, 186, 14, 'F')
            
            cols = len(bottom_items)
            box_w = min(58, (186 - (cols+1)*4) / cols) if cols > 0 else 58
            gap = (186 - (box_w * cols)) / (cols + 1) if cols > 0 else 4
            for i, item in enumerate(bottom_items):
                x = 12 + gap + i * (box_w + gap)
                self.set_fill_color(255, 255, 255)
                self.rect(x, curr_y + 2, box_w, 10, 'F')
                
                self.set_xy(x, curr_y + 3)
                self.set_font('Arial', '', 6)
                self.set_text_color(100, 100, 100)
                self.cell(box_w, 4, item['label'].upper(), 0, 1, 'C')
                
                self.set_xy(x, curr_y + 7)
                self.set_font('Arial', 'B', 9)
                self.set_text_color(44, 62, 80)
                self.cell(box_w, 4, item['val'], 0, 1, 'C')
            curr_y += 17
            
        if rat_txt:
            self.set_fill_color(243, 235, 248) 
            self.rect(12, curr_y, 186, h_rat, 'F')
            self.set_fill_color(155, 89, 182)
            self.rect(12, curr_y, 1.5, h_rat, 'F')
            
            self.set_xy(16, curr_y + 2)
            self.set_font('Arial', '', 8.5)
            self.set_text_color(74, 35, 90)
            
            if 'Interpretation:' in rat_txt:
                self.set_font('Arial', 'B', 8.5)
                w_prefix = self.get_string_width('Interpretation:') + 1
                self.cell(w_prefix, 4.2, 'Interpretation:', 0, 0, 'L')
                self.set_font('Arial', 'I', 8.5)
                self.multi_cell(182 - w_prefix, 4.2, " " + rat_txt.replace('Interpretation:', '').strip(), align='L')
            else:
                self.set_font('Arial', 'I', 8.5)
                self.multi_cell(182, 4.2, rat_txt, align='L')
            curr_y += h_rat + 3
            
        if note_txt:
            self.set_xy(12, curr_y)
            self.set_font('Arial', 'B', 8)
            self.set_text_color(119, 119, 119)
            if 'Note:' in note_txt:
                self.cell(10, 4.2, 'Note:', 0, 0, 'L')
                self.set_font('Arial', '', 8)
                self.multi_cell(175, 4.2, note_txt.replace('Note:', '').strip(), align='L')
            else:
                self.set_font('Arial', '', 8)
                self.multi_cell(186, 4.2, note_txt, align='L')

        self.set_y(start_y + h_needed + 2)

    def draw_index_card(self, soup):
        self.reset_state()
        h_needed = 10
        elements = []
        self.set_font('Arial', '', 8.5)
        
        for child in soup.children:
            if not getattr(child, 'name', None): continue
            
            if child.name == 'h3':
                h_needed += 8
                elements.append(('h3', safe_get_text(child)))
                
            elif child.name == 'p':
                txt = safe_get_text(child)
                if not txt: continue
                lines = len(self.multi_cell(186, 4.2, txt, split_only=True))
                h_needed += (lines * 4.2) + 2
                c_class = child.get('class', [])
                color = (39, 174, 96) if 'trend-bull' in c_class else (231, 76, 60) if 'trend-bear' in c_class else (85, 85, 85)
                elements.append(('p', txt, color, lines))
                
            elif child.name == 'div' and 'metric-row' in child.get('class', []):
                h_needed += 5.5
                lbl = safe_get_text(child.find(class_='metric-label'))
                val_node = child.find(class_='metric-value')
                val = safe_get_text(val_node)
                c_class = val_node.get('class', []) if val_node else []
                color = (39, 174, 96) if 'trend-bull' in c_class else (231, 76, 60) if 'trend-bear' in c_class else (44, 62, 80)
                elements.append(('metric', lbl, val, color))
            
            elif child.name in ['ul', 'ol']:
                for li in child.find_all('li'):
                    txt = "- " + safe_get_text(li)
                    if ':' in txt and txt.index(':') < 20:
                        parts = txt.split(':', 1)
                        self.set_font('Arial', 'B', 8.5)
                        w_pref = self.get_string_width(parts[0] + ':')
                        self.set_font('Arial', '', 8.5)
                        w_avail = 198 - 14 - w_pref
                        lines = len(self.multi_cell(w_avail, 4.2, " " + parts[1].lstrip(), split_only=True))
                    else:
                        lines = len(self.multi_cell(182, 4.2, txt, split_only=True))
                    h_needed += (lines * 4.2) + 2
                    elements.append(('li', txt, lines))
                
        self.check_page_break(h_needed)
        start_y = self.get_y()
        
        self.set_fill_color(240, 244, 248) 
        self.set_draw_color(220, 225, 230)
        self.rect(8, start_y, 194, h_needed, 'DF')
        
        curr_y = start_y + 3
        for el in elements:
            if el[0] == 'h3':
                self.set_xy(12, curr_y)
                self.set_font('Arial', 'B', 11)
                self.set_text_color(44, 62, 80)
                self.cell(0, 5, el[1], 0, 1, 'L')
                self.set_draw_color(52, 152, 219)
                self.line(12, curr_y + 6, 198, curr_y + 6)
                curr_y += 8
            elif el[0] == 'p':
                self.set_xy(12, curr_y)
                self.set_font('Arial', 'B' if 'Strong' in el[1] or 'Bullish' in el[1] else '', 8.5)
                self.set_text_color(*el[2])
                self.multi_cell(186, 4.2, el[1], align='L')
                curr_y = self.get_y() + 2
            elif el[0] == 'metric':
                self.set_xy(12, curr_y)
                self.set_font('Arial', 'B', 8.5)
                self.set_text_color(85, 85, 85)
                self.cell(80, 5, el[1], 0, 0, 'L')
                self.set_text_color(*el[3])
                self.cell(100, 5, el[2], 0, 1, 'R')
                self.set_draw_color(220, 220, 220)
                self.line(12, curr_y + 5, 198, curr_y + 5)
                curr_y += 5.5
            elif el[0] == 'li':
                txt = el[1]
                if re.search(r'\+\d+\.?\d*%', txt): self.set_text_color(39, 174, 96)
                elif re.search(r'-\d+\.?\d*%', txt): self.set_text_color(231, 76, 60)
                else: self.set_text_color(60, 60, 60)
                
                if ':' in txt and txt.index(':') < 15:
                    parts = txt.split(':', 1)
                    prefix = parts[0] + ':'
                    suffix = " " + parts[1].lstrip()
                    self.set_font('Arial', 'B', 8.5)
                    w_prefix = self.get_string_width(prefix)
                    self.set_xy(14, curr_y)
                    self.cell(w_prefix, 4.2, prefix, 0, 0, 'L')
                    orig_margin = self.l_margin
                    self.set_left_margin(14 + w_prefix)
                    self.set_xy(14 + w_prefix, curr_y)
                    self.set_font('Arial', '', 8.5)
                    self.multi_cell(198 - 14 - w_prefix, 4.2, suffix, align='L')
                    self.set_left_margin(orig_margin)
                else:
                    self.set_xy(14, curr_y)
                    self.set_font('Arial', '', 8.5)
                    self.multi_cell(182, 4.2, txt, align='L')
                curr_y = self.get_y() + 2
                
        self.set_y(start_y + h_needed + 3)

    def draw_market_assessment(self, soup):
        self.reset_state()
        title = safe_get_text(soup.find('h3'))
        p_tags = soup.find_all('p')
        
        h_needed = 10
        self.set_font('Arial', '', 8.5)
        for p in p_tags:
            h_needed += len(self.multi_cell(186, 4.2, safe_get_text(p), split_only=True)) * 4.2 + 2
            
        self.check_page_break(h_needed)
        start_y = self.get_y()
        
        self.set_fill_color(109, 102, 204) 
        self.rect(8, start_y, 194, h_needed, 'F')
        
        self.set_xy(12, start_y + 3)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(255, 255, 255)
        self.cell(0, 6, title, 0, 1, 'L')
        self.set_draw_color(255, 255, 255)
        self.line(12, self.get_y(), 198, self.get_y())
        
        curr_y = self.get_y() + 3
        self.set_font('Arial', '', 8.5)
        for p in p_tags:
            self.set_xy(12, curr_y)
            self.multi_cell(186, 4.2, safe_get_text(p), align='L')
            curr_y = self.get_y() + 2
            
        self.set_y(start_y + h_needed + 3)

    def draw_setup_card(self, card_soup, is_watchlist=False):
        self.reset_state()
        
        header = card_soup.find(class_='setup-header')
        if header:
            ticker = safe_get_text(header.find(class_='ticker'))
            badge_el = header.find(class_='setup-type')
            badge_txt = safe_get_text(badge_el)
        else:
            h4 = card_soup.find(['h3', 'h4'])
            title_txt = safe_get_text(h4)
            if "-" in title_txt: ticker = title_txt.split("-", 1)[0].strip()
            else: ticker = title_txt
            badge_el = None
            badge_txt = "WATCHLIST"
        
        name_el = card_soup.find(class_='company-name')
        name = safe_get_text(name_el) if name_el else ""
        if ticker in name: name = name.replace(ticker, "").strip(" -|")
        
        badge_r, badge_g, badge_b = 109, 102, 204 
        if badge_el and badge_el.has_attr('style'):
            st_str = badge_el['style'].lower()
            if '27ae60' in st_str or 'green' in st_str: badge_r, badge_g, badge_b = 39, 174, 96
            elif 'e74c3c' in st_str or 'red' in st_str: badge_r, badge_g, badge_b = 231, 76, 60
            
        if is_watchlist: badge_r, badge_g, badge_b = 230, 126, 34 
        
        is_radar = 'Radar' in ticker or 'Behavioral' in badge_txt
            
        parsed_params = []
        details_texts = []
        extra_texts = []
        
        params_div = card_soup.find(class_='trade-params')
        if params_div:
            for box in params_div.find_all(class_='param-box'):
                lbl = safe_get_text(box.find(class_='param-label'))
                val_node = box.find(class_='param-value')
                val = safe_get_text(val_node)
                color = (44, 62, 80)
                if val_node and val_node.has_attr('style'):
                    st = val_node['style'].lower()
                    if '27ae60' in st or 'green' in st: color = (39, 174, 96)
                    elif 'e74c3c' in st or 'red' in st: color = (231, 76, 60)
                parsed_params.append({'label': lbl, 'val': val, 'color': color})
                
        for child in card_soup.find_all(['p', 'li']):
            if child.find_parent(class_=['trade-params', 'rationale', 'confidence', 'coverage-table']) or child.find_parent('table'): 
                continue
                
            prefix = "- " if child.name == 'li' else ""
            txt = safe_get_text(child)
            if not txt: continue
            
            if ('Parameters:' in txt or '|' in txt) and not params_div:
                if txt.startswith('Parameters:'): _, txt = txt.split(':', 1)
                for part in txt.split('|'):
                    part = part.strip()
                    if 'R:R' in part:
                        parsed_params.append({'label': 'Risk/Reward', 'val': part.replace('R:R', '').strip(), 'color': (44, 62, 80)})
                    elif ' ' in part and any(c.isdigit() for c in part):
                        k, v = part.split(' ', 1)
                        if k[0].isdigit(): val, lbl = k, v
                        else: lbl, val = k, v
                        
                        lbl = lbl.lower()
                        if 'accum' in lbl: label = 'Accumulation'
                        elif 'proj' in lbl: label = 'Projected'
                        elif 'protect' in lbl: label = 'Protective'
                        elif 'entry' in lbl: label = 'Entry'
                        else: label = lbl.title()
                        parsed_params.append({'label': label, 'val': val, 'color': (44, 62, 80)})
                    elif '%' in part: parsed_params.append({'label': 'Allocation', 'val': part, 'color': (44, 62, 80)})
                    else: details_texts.append(prefix + part)
            elif 'Invalidation Cue:' in txt:
                extra_texts.append(txt)
            else:
                details_texts.append(prefix + txt)

        rationale_el = card_soup.find(class_='rationale')
        confidence_el = card_soup.find(class_=lambda c: c and 'confidence' in c)
        
        self.set_font('Arial', '', 8.5)
        
        h_details = 0
        if details_texts:
            h_details += 3
            for t in details_texts:
                if ':' in t and t.index(':') < 40:
                    parts = t.split(':', 1)
                    self.set_font('Arial', 'B', 8.5)
                    w_pref = self.get_string_width(parts[0] + ':') + 1
                    w_avail = 186 - w_pref
                    self.set_font('Arial', '', 8.5)
                    lines = len(self.multi_cell(w_avail, 4.2, " " + parts[1].lstrip(), split_only=True))
                else:
                    lines = len(self.multi_cell(186, 4.2, t, split_only=True))
                h_details += (lines * 4.2) + 2
            h_details += 1.5
            
        h_extras = 0
        if extra_texts:
            h_extras += 1
            for t in extra_texts:
                lines = len(self.multi_cell(186, 4.2, t, split_only=True))
                h_extras += (lines * 4.2) + 1
                
        h_rationale = (len(self.multi_cell(184, 4.2, safe_get_text(rationale_el), split_only=True)) * 4.2 + 4) if rationale_el else 0
        
        params_count = len(parsed_params)
        if params_count == 4: cols, box_w, gap = 2, 90, 4
        elif params_count in [1, 2]: cols, box_w, gap = params_count, 90, 4
        else: cols, box_w, gap = 3, 58, 4
        
        row_heights = []
        rows = math.ceil(params_count / cols) if params_count > 0 else 0
        for r in range(rows):
            max_lines = 1
            for c in range(cols):
                idx = r * cols + c
                if idx < params_count:
                    val_text = parsed_params[idx]['val']
                    self.set_font('Arial', 'B', 8.5)
                    lines = len(self.multi_cell(box_w - 4, 3.8, val_text, split_only=True))
                    if lines > max_lines: max_lines = lines
            row_heights.append(4 + (max_lines * 3.8) + 4) 
            
        h_params = sum(row_heights) + (len(row_heights) * 2) + 4 if params_count > 0 else 0

        # Exact boundary mapping
        total_height = 14 + h_details + h_params + h_rationale + h_extras + (8 if confidence_el else 0) + 4
        self.check_page_break(total_height)
        start_y = self.get_y()
        
        # DRAW BG
        self.set_fill_color(255, 255, 255)
        self.set_draw_color(230, 230, 230)
        self.rect(8, start_y, 194, total_height, 'DF')
        
        # DRAW HEADER
        self.set_xy(12, start_y + 3)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(44, 62, 80)
        self.cell(140, 6, ticker, 0, 1, 'L') 
        
        if name:
            self.set_xy(12, start_y + 9)
            self.set_font('Arial', '', 9)
            self.set_text_color(102, 102, 102)
            self.cell(100, 5, name, 0, 1, 'L')
        
        if badge_txt:
            self.set_font('Arial', 'B', 8)
            w_badge = max(self.get_string_width(badge_txt) + 12, 22)
            self.set_xy(202 - w_badge - 4, start_y + 3) 
            self.set_fill_color(badge_r, badge_g, badge_b)
            self.set_text_color(255, 255, 255)
            self.cell(w_badge, 6, badge_txt, 0, 1, 'C', fill=True)
            
        self.set_draw_color(240, 240, 240)
        self.line(10, start_y + 11, 200, start_y + 11)
        curr_y = start_y + 13
        
        # DRAW DETAILS
        if details_texts:
            self.set_fill_color(248, 249, 250)
            self.rect(10, curr_y, 190, h_details, 'F')
            curr_y += 1.5
            
            for t in details_texts:
                self.set_xy(12, curr_y)
                self.set_font('Arial', '', 8.5)
                
                if is_radar:
                    if re.search(r'\+\d+\.?\d*%', t): self.set_text_color(39, 174, 96)
                    elif re.search(r'-\d+\.?\d*%', t): self.set_text_color(231, 76, 60)
                    else: self.set_text_color(60, 60, 60)
                else:
                    if 'trend-bull' in t or 'Hold' in t or 'Breakout' in t: self.set_text_color(39, 174, 96)
                    elif 'trend-bear' in t or 'Exit' in t or 'Breakdown' in t: self.set_text_color(231, 76, 60)
                    else: self.set_text_color(60, 60, 60)
                
                if ':' in t and t.index(':') < 40:
                    parts = t.split(':', 1)
                    prefix = parts[0] + ':'
                    suffix = " " + parts[1].lstrip()
                    
                    self.set_font('Arial', 'B', 8.5)
                    w_prefix = self.get_string_width(prefix) + 1
                    
                    self.set_xy(12, curr_y)
                    self.cell(w_prefix, 4.2, prefix, 0, 0, 'L')
                    
                    orig_margin = self.l_margin
                    self.set_left_margin(12 + w_prefix)
                    self.set_xy(12 + w_prefix, curr_y)
                    self.set_font('Arial', '', 8.5)
                    
                    self.multi_cell(186 - w_prefix, 4.2, suffix, align='L')
                    self.set_left_margin(orig_margin)
                    curr_y = self.get_y() + 2 
                else:
                    self.set_xy(12, curr_y)
                    self.multi_cell(186, 4.2, t, align='L')
                    curr_y = self.get_y() + 2
                    
            curr_y = start_y + 13 + h_details + 1.5

        # DRAW PARAMS 
        if parsed_params:
            self.set_fill_color(253, 235, 245) 
            self.rect(10, curr_y, 190, h_params, 'F')
            
            start_x = 10 + (190 - ((cols * box_w) + ((cols - 1) * gap))) / 2
            grid_y = curr_y + 3
            
            for r in range(rows):
                row_h = row_heights[r]
                for c in range(cols):
                    idx = r * cols + c
                    if idx >= params_count: break
                    p_data = parsed_params[idx]
                    
                    x = start_x + (c * (box_w + gap))
                    y = grid_y
                    
                    self.set_fill_color(255, 255, 255)
                    self.rect(x, y, box_w, row_h - 2, 'F')
                    
                    self.set_xy(x, y + 1.5)
                    self.set_font('Arial', '', 6.5)
                    self.set_text_color(100, 100, 100)
                    self.cell(box_w, 3, p_data['label'].upper(), 0, 1, 'C')
                    
                    self.set_xy(x + 2, y + 5)
                    self.set_font('Arial', 'B', 8.5)
                    self.set_text_color(*p_data['color'])
                    self.multi_cell(box_w - 4, 3.8, p_data['val'], align='C')
                
                grid_y += row_h + 2
                
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

        # DRAW EXTRAS (Uses strictly get_y() to prevent overlapping Confidence badge)
        if extra_texts:
            curr_y += 1
            self.set_font('Arial', 'B', 8.5)
            self.set_text_color(192, 57, 43) 
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
            
            self.set_xy(12, curr_y + 1)
            w_txt = self.get_string_width(txt) + 8
            self.rect(12, curr_y + 1, w_txt, 6, 'F')
            self.cell(w_txt, 6, txt, 0, 1, 'C')

        self.set_y(start_y + total_height + 4)

    def draw_disclaimer(self, disc_soup):
        self.reset_state()
        title = safe_get_text(disc_soup.find(['h3', 'h4'])) or "Disclaimer"
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
    if date_el:
        for br in date_el.find_all('br'):
            br.replace_with(' | ')
        subtitle = safe_get_text(date_el)
    else:
        subtitle = "Market Report"

    pdf = PDF(subtitle)
    pdf.set_auto_page_break(auto=False) 
    pdf.add_page()

    # Alerts
    alert = soup.find(class_='alert-box')
    if alert:
        title = safe_get_text(alert.find(['h3', 'h4'])) or "ALERT"
        txt = safe_get_text(alert).replace(title, "").strip()
        pdf.draw_notice_box(title + ": " + txt, style='warning')
        alert.attrs['processed'] = True

    # 1. Market Positioning Dashboard Tracker
    dash_card = soup.find('div', class_='dashboard-card')
    if dash_card:
        pdf.section_header("Market Positioning Dashboard (Quantified)", new_page=False)
        pdf.draw_dashboard_card(dash_card)
        dash_card.attrs['processed'] = True
        parent_sec = dash_card.find_parent('div', class_='section')
        if parent_sec: parent_sec.attrs['processed'] = True

    # 2. Main Tabs
    tabs = [
        ('tab-index', "Index Analysis — EGX30", False),
        ('tab-market', "Market Trend (Internal Structure)", False),
        ('tab-buy', "Top Opportunities", True),
        ('tab-open', "Open Positions Management", True),
        ('tab-reduce', "Reduce / Distribute", True),
        ('tab-watchlist', "Watchlist", True),
        ('tab-notes', "Market Notes", True)
    ]

    for tab_id, default_title, force_new_page in tabs:
        tab = soup.find(id=tab_id)
        if not tab: continue
        
        h2 = tab.find('h2')
        title = safe_get_text(h2) if h2 else default_title
        
        pdf.section_header(title, new_page=force_new_page)
        
        processed_ids = set()
        cards_on_page = 0 
        
        for element in tab.find_all(['div', 'p']):
            el_id = id(element)
            if el_id in processed_ids or 'processed' in element.attrs: continue
            
            c_class = element.get('class', [])
            
            if element.name == 'p' and (element.parent == tab or 'section' in element.parent.get('class', [])):
                txt = safe_get_text(element)
                if len(txt) > 5:
                    style = 'warning' if ('reduce' in tab_id or 'Distribute' in txt or 'Note:' in txt) else 'neutral'
                    pdf.draw_notice_box(txt, style=style)
                processed_ids.add(el_id)
                
            elif 'setup-card' in c_class or 'watchlist-item' in c_class:
                
                # STRICT FILTRATION ENGINE
                header = element.find(class_='setup-header')
                if header:
                    ticker_txt = safe_get_text(header.find(class_='ticker')).lower()
                    
                    # Ignore Technical Market Notes & Coverage Summary globally
                    if "technical market notes" in ticker_txt or "coverage summary" in ticker_txt:
                        element.attrs['processed'] = True
                        for child in element.find_all(True): processed_ids.add(id(child))
                        continue
                    
                    # In Market Notes tab, ONLY allow Big Move Radar
                    if tab_id == 'tab-notes' and "big move radar" not in ticker_txt:
                        element.attrs['processed'] = True
                        for child in element.find_all(True): processed_ids.add(id(child))
                        continue

                # Enforce exactly 2 cards per page max
                if cards_on_page >= 2 and tab_id not in ['tab-index', 'tab-market', 'tab-notes']:
                    pdf.add_page()
                    pdf.set_y(38)
                    pdf.set_font('Arial', 'I', 8)
                    pdf.set_text_color(150, 150, 150)
                    pdf.cell(0, 4, f"{title} (Continued)", 0, 1, 'R')
                    pdf.ln(2)
                    cards_on_page = 0
                
                start_page = pdf.page_no()
                pdf.draw_setup_card(element, is_watchlist=('watch' in tab_id or 'watchlist' in c_class))
                end_page = pdf.page_no()
                
                if end_page > start_page: cards_on_page = 1
                else: cards_on_page += 1
                
                for child in element.find_all(True): processed_ids.add(id(child))
                processed_ids.add(el_id)
                
            elif 'index-card' in c_class and 'dashboard-card' not in c_class:
                pdf.draw_index_card(element)
                for child in element.find_all(True): processed_ids.add(id(child))
                processed_ids.add(el_id)
                
            elif 'market-assessment' in c_class:
                pdf.draw_market_assessment(element)
                for child in element.find_all(True): processed_ids.add(id(child))
                processed_ids.add(el_id)

    disclaimer = soup.find(class_='disclaimer')
    if disclaimer:
        pdf.draw_disclaimer(disclaimer)

    return pdf

# --- 4. STREAMLIT APP ---
st.set_page_config(page_title="BlueberryAI Formatter", layout="centered")
st.title("📄 BlueberryAI PDF Generator")
st.write("Upload your HTML report to generate a pixel-perfect styled PDF.")

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
