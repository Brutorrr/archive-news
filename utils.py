import os
import re
import hashlib
import datetime
from email.header import decode_header
from email.utils import parsedate_to_datetime, parseaddr
from bs4 import BeautifulSoup

def clean_subject_prefixes(subject):
    if not subject: return "Sans titre"
    pattern = r'^\s*\[?(?:Fwd|Fw|Tr|Re|Aw|Wg)\s*:\s*\]?\s*'
    cleaned = subject
    while re.match(pattern, cleaned, re.IGNORECASE):
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()

def get_deterministic_id(subject):
    if not subject: subject = "sans_titre"
    hash_object = hashlib.sha256(subject.encode('utf-8', errors='ignore'))
    return hash_object.hexdigest()[:12]

def get_email_date(msg):
    try:
        date_header = msg["Date"]
        if date_header:
            dt = parsedate_to_datetime(date_header)
            return dt.strftime('%Y-%m-%d')
    except Exception:
        pass
    return datetime.datetime.now().strftime('%Y-%m-%d')

def get_clean_sender(msg):
    try:
        from_header = msg["From"]
        if not from_header: return "Inconnu"
        decoded_header = ""
        for part, encoding in decode_header(from_header):
            if isinstance(part, bytes):
                decoded_header += part.decode(encoding or "utf-8", errors="ignore")
            else:
                decoded_header += str(part)
        realname, email_addr = parseaddr(decoded_header)
        sender = realname if realname else email_addr
        return sender.strip() if sender else "Expéditeur Inconnu"
    except:
        return "Expéditeur Inconnu"

def get_decoded_email_subject(msg):
    subject_header = msg["Subject"]
    if not subject_header: return "Sans Titre"
    decoded_list = decode_header(subject_header)
    full_subject = ""
    for part, encoding in decoded_list:
        if isinstance(part, bytes):
            full_subject += part.decode(encoding or "utf-8", errors="ignore")
        else:
            full_subject += str(part)
    return full_subject.strip()

def get_page_metadata(filepath):
    title = "Sans titre"
    date_str = None
    archiving_date_str = None
    sender = "Expéditeur Inconnu"
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
            
            meta_date = soup.find("meta", attrs={"name": "creation_date"})
            if meta_date and meta_date.get("content"):
                date_str = meta_date["content"]
            
            meta_arch = soup.find("meta", attrs={"name": "archiving_date"})
            if meta_arch and meta_arch.get("content"):
                archiving_date_str = meta_arch["content"]
                
            meta_sender = soup.find("meta", attrs={"name": "sender"})
            if meta_sender and meta_sender.get("content"):
                sender = meta_sender["content"]
    except Exception:
        pass

    if not date_str:
        try:
            timestamp = os.path.getmtime(filepath)
            date_str = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        except:
            date_str = datetime.datetime.now().strftime('%Y-%m-%d')
            
    if not archiving_date_str:
        archiving_date_str = date_str

    return title, date_str, sender, archiving_date_str

def format_date_fr(date_iso):
    try:
        dt = datetime.datetime.strptime(date_iso, '%Y-%m-%d')
        return dt.strftime('%d/%m/%Y')
    except:
        return date_iso
