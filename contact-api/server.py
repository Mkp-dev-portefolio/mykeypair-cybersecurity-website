#!/usr/bin/env python3
"""MyKeyPair Contact Form Handler — sends Telegram notifications."""

import hashlib
import json
import os
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
SUBMISSIONS_FILE = os.environ.get('SUBMISSIONS_FILE', '/var/www/mykeypair-data/submissions.json')
ALLOWED_ORIGINS = ['https://staging.mykeypair.be', 'https://mykeypair.be', 'https://www.mykeypair.be', 'https://crypto.mykeypair.be']
CONSENT_LOG = os.environ.get('CONSENT_LOG', '/var/www/mykeypair-data/cookie-consents.json')
VISITOR_LOG = os.environ.get('VISITOR_LOG', '/var/www/mykeypair-data/visitors.jsonl')
PORT = 8900
# Optional lead fields accepted from landing-page forms (stored under 'lead', never required).
LEAD_EXTRA_FIELDS = ['company', 'role', 'platform', 'volume', 'challenge', 'context', 'page',
                     'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term']


def send_telegram(text):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    data = urllib.parse.urlencode({
        'chat_id': TELEGRAM_CHAT_ID,
        'text': text,
        'parse_mode': 'HTML'
    }).encode()
    try:
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f'Telegram send failed: {e}')


def save_submission(entry):
    os.makedirs(os.path.dirname(SUBMISSIONS_FILE), exist_ok=True)
    submissions = []
    if os.path.exists(SUBMISSIONS_FILE):
        with open(SUBMISSIONS_FILE, 'r') as f:
            submissions = json.load(f)
    submissions.append(entry)
    with open(SUBMISSIONS_FILE, 'w') as f:
        json.dump(submissions, f, indent=2)


ANALYTICS_FILE = os.environ.get('ANALYTICS_FILE', '/var/www/mykeypair-data/analytics.jsonl')

def save_analytics_event(event):
    os.makedirs(os.path.dirname(ANALYTICS_FILE), exist_ok=True)
    with open(ANALYTICS_FILE, 'a') as f:
        f.write(json.dumps(event) + '\n')


def save_visitor_event(event):
    """Append a visitor event to the JSONL visitor log."""
    os.makedirs(os.path.dirname(VISITOR_LOG), exist_ok=True)
    with open(VISITOR_LOG, 'a') as f:
        f.write(json.dumps(event) + '\n')


def hash_ip(ip):
    """Stable SHA-256 hash of IP (first 16 hex chars) for correlation without storing raw IP."""
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


class ContactHandler(BaseHTTPRequestHandler):

    def _get_real_ip(self):
        """Extract real client IP from proxy headers or socket."""
        forwarded = self.headers.get('X-Forwarded-For', '')
        if forwarded:
            return forwarded.split(',')[0].strip()
        real_ip = self.headers.get('X-Real-IP', '')
        if real_ip:
            return real_ip.strip()
        return self.client_address[0]

    def _get_visitor_fingerprint(self):
        """Collect all available server-side visitor metadata."""
        real_ip = self._get_real_ip()
        return {
            'ip_hash': hash_ip(real_ip),
            'user_agent': str(self.headers.get('User-Agent', ''))[:300],
            'accept_language': str(self.headers.get('Accept-Language', ''))[:100],
            'referer': str(self.headers.get('Referer', ''))[:300],
            'origin': str(self.headers.get('Origin', ''))[:100],
            'sec_ch_ua': str(self.headers.get('Sec-Ch-Ua', ''))[:200],
            'sec_ch_ua_platform': str(self.headers.get('Sec-Ch-Ua-Platform', ''))[:30],
            'sec_ch_ua_mobile': str(self.headers.get('Sec-Ch-Ua-Mobile', ''))[:5],
            'connection': str(self.headers.get('Connection', ''))[:20],
        }

    def do_OPTIONS(self):
        origin = self.headers.get('Origin', '')
        self.send_response(204)
        if origin in ALLOWED_ORIGINS:
            self.send_header('Access-Control-Allow-Origin', origin)
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()

    def do_POST(self):
        origin = self.headers.get('Origin', '')
        content_length = int(self.headers.get('Content-Length', 0))

        if content_length > 10000:
            self.send_error(413, 'Payload too large')
            return

        body = self.rfile.read(content_length)
        content_type = self.headers.get('Content-Type', '')

        try:
            if 'application/json' in content_type:
                data = json.loads(body)
            elif 'application/x-www-form-urlencoded' in content_type:
                data = dict(urllib.parse.parse_qsl(body.decode()))
            else:
                self.send_error(415, 'Unsupported content type')
                return
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_error(400, 'Invalid request body')
            return

        # Route: Analytics event
        if self.path == '/analytics':
            self._handle_analytics(data, origin)
            return

        # Route: Cookie consent logging
        if self.path == '/consent':
            self._handle_consent(data, origin)
            return

        name = str(data.get('name', '')).strip()[:200]
        email = str(data.get('email', '')).strip()[:200]
        subject = str(data.get('subject', '')).strip()[:200]
        message = str(data.get('message', '')).strip()[:2000]

        if not name or not email or not message:
            self.send_error(400, 'Missing required fields')
            return

        # Honeypot check
        if data.get('_gotcha', ''):
            self.send_response(200)
            self.end_headers()
            return

        timestamp = datetime.now(timezone.utc).isoformat()
        fingerprint = self._get_visitor_fingerprint()

        # Optional structured lead fields (landing pages). Unknown keys are ignored, values truncated.
        extra = {}
        for key in LEAD_EXTRA_FIELDS:
            value = str(data.get(key, '')).strip()
            if value:
                extra[key] = value[:300]

        entry = {
            'timestamp': timestamp,
            'name': name,
            'email': email,
            'subject': subject,
            'message': message,
            **({'lead': extra} if extra else {}),
            **fingerprint
        }

        save_submission(entry)

        # Also log to visitor log for cross-referencing
        save_visitor_event({
            'ts': timestamp,
            'event': 'contact_form',
            'name': name,
            'email': email,
            **fingerprint
        })

        telegram_text = (
            f'<b>New Contact Form Submission</b>\n'
            f'━━━━━━━━━━━━━━━━━━━━\n'
            f'<b>Name:</b> {name}\n'
            f'<b>Email:</b> {email}\n'
            f'<b>Subject:</b> {subject}\n'
            f'<b>Message:</b>\n{message}\n'
            + (f'<b>Company:</b> {extra.get("company", "")} · <b>Role:</b> {extra.get("role", "")}\n' if extra else '')
            + (f'<b>Campaign:</b> {extra.get("utm_campaign", "")} / {extra.get("utm_source", "")} / {extra.get("utm_medium", "")}\n' if extra.get('utm_campaign') or extra.get('utm_source') else '')
            + f'━━━━━━━━━━━━━━━━━━━━\n'
            f'<b>IP:</b> {fingerprint["ip_hash"]}\n'
            f'<b>UA:</b> {fingerprint["user_agent"][:80]}\n'
            f'<b>Lang:</b> {fingerprint["accept_language"][:30]}\n'
            f'<b>Platform:</b> {fingerprint["sec_ch_ua_platform"]}\n'
            f'<i>{timestamp}</i>'
        )
        send_telegram(telegram_text)

        self.send_response(200)
        if origin in ALLOWED_ORIGINS:
            self.send_header('Access-Control-Allow-Origin', origin)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'ok': True, 'message': 'Message received'}).encode())

    def _handle_analytics(self, data, origin):
        """Log analytics event."""
        allowed_events = {'pageview', 'page_exit', 'outbound_click', 'cta_click',
                         'service_interest', 'scroll_depth', 'form_submit', 'feedback'}

        event_type = str(data.get('event', ''))[:30]
        if event_type not in allowed_events:
            self.send_response(400)
            self.end_headers()
            return

        fingerprint = self._get_visitor_fingerprint()
        event = {
            'ts': datetime.now(timezone.utc).isoformat(),
            'event': event_type,
            'session': str(data.get('session', ''))[:30],
            'page': str(data.get('page', ''))[:200],
            'referrer': str(data.get('referrer', ''))[:100],
            'device': str(data.get('device', ''))[:10],
            'screen': str(data.get('screen', ''))[:15],
            'lang': str(data.get('lang', ''))[:10],
            'ip_hash': fingerprint['ip_hash'],
            'ua': fingerprint['user_agent'][:100],
        }
        
        # Add event-specific fields
        if event_type == 'page_exit':
            event['duration_sec'] = min(int(data.get('duration_sec', 0)), 3600)
        elif event_type in ('outbound_click', 'cta_click'):
            event['url'] = str(data.get('url', ''))[:200]
            event['text'] = str(data.get('text', ''))[:50]
        elif event_type == 'service_interest':
            event['service'] = str(data.get('service', ''))[:30]
        elif event_type == 'scroll_depth':
            event['depth'] = min(int(data.get('depth', 0)), 100)
        elif event_type == 'form_submit':
            event['subject'] = str(data.get('subject', ''))[:30]
        elif event_type == 'feedback':
            event['source'] = str(data.get('source', ''))[:20]
            event['looking_for'] = str(data.get('looking_for', ''))[:30]
            event['rating'] = min(int(data.get('rating', 0)), 5)
            event['comment'] = str(data.get('comment', ''))[:500]

        save_analytics_event(event)

        self.send_response(200)
        if origin in ALLOWED_ORIGINS:
            self.send_header('Access-Control-Allow-Origin', origin)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'ok': True}).encode())

    def _handle_consent(self, data, origin):
        """Log cookie consent for GDPR proof."""
        fingerprint = self._get_visitor_fingerprint()
        consent = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'ip_hash': fingerprint['ip_hash'],
            'user_agent': fingerprint['user_agent'],
            'accept_language': fingerprint['accept_language'],
            'sec_ch_ua_platform': fingerprint['sec_ch_ua_platform'],
            'essential': True,
            'analytics': bool(data.get('analytics', False)),
            'marketing': bool(data.get('marketing', False)),
            'action': str(data.get('action', 'unknown'))[:20],  # 'accept_all' or 'essential_only'
            'version': str(data.get('version', '1'))[:5],
        }

        # Append to consent log
        os.makedirs(os.path.dirname(CONSENT_LOG), exist_ok=True)
        entries = []
        if os.path.exists(CONSENT_LOG):
            try:
                with open(CONSENT_LOG, 'r') as f:
                    entries = json.load(f)
            except:
                entries = []
        entries.append(consent)
        # Keep last 10,000 entries (prevent unlimited growth)
        entries = entries[-10000:]
        with open(CONSENT_LOG, 'w') as f:
            json.dump(entries, f, indent=2)

        self.send_response(200)
        if origin in ALLOWED_ORIGINS:
            self.send_header('Access-Control-Allow-Origin', origin)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'ok': True}).encode())

    def log_message(self, format, *args):
        print(f'[{datetime.now(timezone.utc).isoformat()}] {args[0]}')


if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', PORT), ContactHandler)
    print(f'Contact form handler running on 127.0.0.1:{PORT}')
    server.serve_forever()
