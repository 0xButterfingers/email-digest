"""Service for generating PDF reports from digest summaries."""

import logging
import re
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional

from fpdf import FPDF

logger = logging.getLogger(__name__)

_UNICODE_MAP = str.maketrans({
    "\u2014": "-",
    "\u2013": "-",
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2022": "*",
    "\u2026": "...",
    "\u00b7": ".",
    "\u2122": "(TM)",
    "\u00ae": "(R)",
    "\u00a9": "(C)",
    "\u00a0": " ",
})

_CATEGORY_ORDER = ["Macro", "FX", "Bonds", "Others"]


def _s(text: str) -> str:
    """Sanitize text to latin-1 safe characters."""
    text = text.translate(_UNICODE_MAP)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _extract_sender_name(sender: str) -> str:
    """Extract display name from 'Name <email>' format."""
    match = re.match(r"^(.+?)\s*<[^>]+>$", sender)
    if match:
        return match.group(1).strip()
    return sender


class DigestPDF(FPDF):
    def __init__(self, digest_name: str, run_date: str, email_count: int = 0):
        super().__init__()
        self.digest_name = _s(digest_name)
        self.run_date = _s(run_date)
        self.email_count = email_count

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(26, 58, 92)
        self.cell(0, 8, self.digest_name, align="L")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, self.run_date, align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(26, 58, 92)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, f"Page {self.page_no()} | Email Digest Summarizer", align="C")


class PdfService:
    def generate(
        self,
        items: List[Dict],
        emails: List[Dict],
        archive_urls: Dict[str, str],
        digest_name: str,
        archive_base_url: str,
        images: Optional[list] = None,
    ) -> bytes:
        try:
            run_date = datetime.now().strftime("%d %B %Y, %H:%M SGT")
            pdf = DigestPDF(digest_name=digest_name, run_date=run_date, email_count=len(emails))
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

            # Title block
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_text_color(26, 58, 92)
            pdf.cell(0, 10, _s(digest_name), align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(100, 100, 100)
            subtitle = f"{run_date}  |  {len(emails)} emails scanned"
            pdf.cell(0, 6, _s(subtitle), align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)
            pdf.set_draw_color(26, 58, 92)
            pdf.set_line_width(0.5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(6)

            items, footnotes = self._build_footnotes(items, emails, archive_urls, archive_base_url)

            # Pre-create internal link targets for each footnote (destination set later)
            footnote_links = {}
            for fn in footnotes:
                footnote_links[fn["num"]] = pdf.add_link()

            self._render_body(pdf, items, emails, footnote_links)

            if footnotes:
                self._render_footnotes(pdf, footnotes, footnote_links)

            if images:
                self._render_images(pdf, images)

            buf = BytesIO()
            pdf.output(buf)
            logger.info(f"PDF generated successfully ({buf.tell()} bytes)")
            return buf.getvalue()

        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise

    def _build_footnotes(self, items, emails, archive_urls, archive_base_url):
        seen = {}
        footnotes = []
        counter = 1
        for item in items:
            idx = item.get("source_email_index", 0)
            if idx not in seen:
                if idx < len(emails):
                    email = emails[idx]
                    gid = email.get("gmail_message_id") or email.get("id", "")
                    url_path = archive_urls.get(gid, f"/{gid}/")
                    url = archive_base_url + url_path
                    seen[idx] = counter
                    footnotes.append({
                        "num": counter,
                        "sender": email.get("sender", "Unknown"),
                        "subject": email.get("subject", "(No Subject)"),
                        "date": email.get("date", ""),
                        "url": url,
                    })
                    counter += 1
                else:
                    seen[idx] = 0
            item["footnote_num"] = seen[idx]
        return items, footnotes

    def _render_body(self, pdf, items, emails=None, footnote_links=None):
        emails = emails or []
        footnote_links = footnote_links or {}

        by_category = {}
        for item in items:
            cat = item.get("category", "Others")
            by_category.setdefault(cat, []).append(item)

        for category in _CATEGORY_ORDER:
            cat_items = by_category.get(category)
            if not cat_items:
                continue

            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(26, 58, 92)
            pdf.cell(0, 8, _s(category.upper()), new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(200, 200, 200)
            pdf.set_line_width(0.3)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)

            for item in cat_items:
                pdf.set_x(pdf.l_margin)
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(20, 20, 20)
                pdf.multi_cell(0, 6, _s(item.get("headline", "")))

                pdf.set_x(pdf.l_margin)
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(50, 50, 50)
                pdf.multi_cell(0, 5, _s(item.get("body", "")))

                footnote_num = item.get("footnote_num", 0)
                idx = item.get("source_email_index", 0)
                sender_name = "Unknown"
                if idx < len(emails):
                    sender_name = _extract_sender_name(emails[idx].get("sender", "Unknown"))

                pdf.set_x(pdf.l_margin)
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(120, 120, 120)
                if footnote_num > 0 and footnote_num in footnote_links:
                    # Render "Source: SenderName " then clickable "[n]"
                    source_prefix = f"Source: {sender_name} "
                    pdf.cell(pdf.get_string_width(_s(source_prefix)), 5, _s(source_prefix))
                    # Clickable footnote reference
                    pdf.set_text_color(26, 58, 92)
                    link_text = f"[{footnote_num}]"
                    link_w = pdf.get_string_width(_s(link_text))
                    link_y = pdf.get_y()
                    link_x = pdf.get_x()
                    pdf.cell(link_w, 5, _s(link_text), new_x="LMARGIN", new_y="NEXT")
                    pdf.link(link_x, link_y, link_w, 5, footnote_links[footnote_num])
                else:
                    source_text = f"Source: {sender_name}"
                    pdf.multi_cell(0, 5, _s(source_text))
                pdf.ln(4)

    def _render_footnotes(self, pdf, footnotes, footnote_links=None):
        footnote_links = footnote_links or {}
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(26, 58, 92)
        pdf.cell(0, 8, "SOURCES", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(200, 200, 200)
        pdf.set_line_width(0.3)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

        for fn in footnotes:
            num = fn["num"]
            sender_name = _extract_sender_name(fn["sender"])
            subject = fn["subject"]
            date = fn["date"]
            url = fn["url"]

            # Set the link destination so clicking [n] in the body jumps here
            if num in footnote_links:
                pdf.set_link(footnote_links[num], y=pdf.get_y(), page=pdf.page_no())

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(26, 58, 92)
            pdf.cell(12, 5, _s(f"[{num}]"))

            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(50, 50, 50)
            detail = f'{sender_name} - "{subject}" - {date}'
            pdf.multi_cell(0, 5, _s(detail))

            pdf.set_x(22)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(26, 58, 92)
            link_y = pdf.get_y()
            url_text = _s(url)
            url_width = pdf.get_string_width(url_text)
            pdf.cell(url_width, 4, url_text, new_x="LMARGIN", new_y="NEXT")
            pdf.link(22, link_y, url_width, 4, url)
            pdf.ln(4)

    def _render_images(self, pdf, images):
        import tempfile
        import os
        from PIL import Image as PilImage

        pdf.add_page()
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(26, 58, 92)
        pdf.cell(0, 8, "Charts & Figures", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(200, 200, 200)
        pdf.set_line_width(0.3)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

        MAX_WIDTH = 180
        MAX_HEIGHT = 120
        tmp_files = []
        try:
            for img_data in images:
                try:
                    pil_img = PilImage.open(BytesIO(img_data["data"]))
                    if pil_img.mode not in ("RGB", "L"):
                        pil_img = pil_img.convert("RGB")
                    w_px, h_px = pil_img.size
                    dpi = 96
                    w_mm = w_px * 25.4 / dpi
                    h_mm = h_px * 25.4 / dpi
                    scale = min(MAX_WIDTH / w_mm, MAX_HEIGHT / h_mm, 1.0)
                    w_mm *= scale
                    h_mm *= scale
                    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
                    pil_img.save(tmp, format="JPEG", quality=85)
                    tmp.close()
                    tmp_files.append(tmp.name)
                    if pdf.get_y() + h_mm + 12 > pdf.h - pdf.b_margin:
                        pdf.add_page()
                    pdf.image(tmp.name, x=10, w=w_mm, h=h_mm)
                    pdf.ln(2)
                    caption = _s(img_data.get("filename", "Chart"))
                    pdf.set_font("Helvetica", "I", 8)
                    pdf.set_text_color(120, 120, 120)
                    pdf.cell(0, 5, caption, new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(4)
                except Exception as e:
                    logger.error(f"Failed to render image {img_data.get('filename')}: {e}")
                    continue
        finally:
            for path in tmp_files:
                try:
                    os.unlink(path)
                except Exception:
                    pass
