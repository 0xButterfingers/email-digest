import base64, logging, os, re
from pathlib import Path
from typing import Any, Dict, List, Optional
from html import escape

logger = logging.getLogger(__name__)
ARCHIVE_DIR = Path("/app/email-archive")

def _extract_html_body(payload):
    mime_type = payload.get("mimeType", "")
    if "data" in payload.get("body", {}):
        raw = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
        if mime_type == "text/html": return raw
        if mime_type == "text/plain": return "<pre>" + escape(raw) + "</pre>"
        return ""
    parts = payload.get("parts", [])
    if mime_type == "multipart/alternative":
        html = next((p for p in parts if p.get("mimeType") == "text/html"), None)
        plain = next((p for p in parts if p.get("mimeType") == "text/plain"), None)
        for c in [html, plain]:
            if c:
                r = _extract_html_body(c)
                if r: return r
        return ""
    for part in parts:
        r = _extract_html_body(part)
        if r: return r
    return ""


def _collect_attachments(payload):
    atts = []
    def collect(p):
        body = p.get("body", {})
        aid = body.get("attachmentId")
        if aid:
            fn = p.get("filename") or "attachment_" + aid[:8]
            atts.append({"attachment_id": aid, "filename": fn,
                        "mime_type": p.get("mimeType", "application/octet-stream"),
                        "size": body.get("size", 0)})
        for part in p.get("parts", []): collect(part)
    collect(payload)
    return atts


def _build_html(ed, att_fns):
    subj = escape(ed.get("subject", "(No Subject)"))
    sender = escape(ed.get("sender", "Unknown"))
    date = escape(ed.get("date", ""))
    body = ed.get("html_body", "")
    if not body:
        plain = ed.get("body", "")
        body = "<pre>" + escape(plain) + "</pre>" if plain else "<p><em>No content</em></p>"
    att_html = ""
    if att_fns:
        links = "".join('<li><a href="attachments/' + escape(fn) + '">' + escape(fn) + '</a></li>' for fn in att_fns)
        att_html = '<div style="background:#fff;padding:20px;border-radius:8px;margin-top:20px"><h3 style="margin-top:0;color:#1a73e8">Attachments</h3><ul style="list-style:none;padding:0">' + links + '</ul></div>'
    return '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>' + subj + '</title><style>body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;max-width:900px;margin:0 auto;padding:20px;background:#f5f5f5;color:#333}.hdr{background:#fff;padding:20px;border-radius:8px;margin-bottom:20px;border-left:4px solid #1a73e8}.hdr h1{margin:0 0 10px;font-size:1.3em;color:#1a73e8}.meta{color:#666;font-size:.9em}.meta span{display:block;margin-bottom:4px}.bc{background:#fff;padding:20px;border-radius:8px;overflow-x:auto}.ft{text-align:center;margin-top:20px;color:#999;font-size:.8em}</style></head><body><div class="hdr"><h1>' + subj + '</h1><div class="meta"><span><b>From:</b> ' + sender + '</span><span><b>Date:</b> ' + date + '</span></div></div><div class="bc">' + body + '</div>' + att_html + '<div class="ft">Email Archive</div></body></html>'


class EmailArchiveService:
    def __init__(self):
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    def archive_email(self, email_data, raw_payload, service=None):
        gid = email_data.get("gmail_message_id", "")
        if not gid:
            logger.warning("No gmail_message_id, skipping archive")
            return None
        edir = ARCHIVE_DIR / gid
        adir = edir / "attachments"
        try:
            edir.mkdir(parents=True, exist_ok=True)
            html_body = _extract_html_body(raw_payload)
            ed = {**email_data, "html_body": html_body}
            saved = []
            if service:
                parts = _collect_attachments(raw_payload)
                if parts:
                    adir.mkdir(parents=True, exist_ok=True)
                for att in parts:
                    try:
                        resp = service.users().messages().attachments().get(
                            userId="me", messageId=gid, id=att["attachment_id"]).execute()
                        data = base64.urlsafe_b64decode(resp["data"])
                        safe = re.sub(r"[^\w.\-]", "_", att["filename"]) or "att_" + att["attachment_id"][:8]
                        (adir / safe).write_bytes(data)
                        saved.append(safe)
                        logger.info("Saved attachment %s (%d bytes)", safe, len(data))
                    except Exception as e:
                        logger.error("Failed attachment %s: %s", att["filename"], e)
            (edir / "index.html").write_text(_build_html(ed, saved), encoding="utf-8")
            logger.info("Archived email %s (%d attachments)", gid, len(saved))
            return "/" + gid + "/"
        except Exception as e:
            logger.error("Failed to archive %s: %s", gid, e)
            return None

    def archive_emails(self, emails, raw_payloads, service=None):
        urls = {}
        for ed in emails:
            gid = ed.get("gmail_message_id", "")
            p = raw_payloads.get(gid)
            if p:
                u = self.archive_email(ed, p, service)
                if u:
                    urls[gid] = u
        return urls
