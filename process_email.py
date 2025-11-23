import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime, parseaddr
from bs4 import BeautifulSoup
import os
import re
import mimetypes
import requests
import datetime
import hashlib
import shutil
import json

# --- CONFIGURATION ---
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_PASSWORD = os.environ["GMAIL_PASSWORD"]
TARGET_LABEL = "Github/archive-newsletters"
OUTPUT_FOLDER = "docs"
BATCH_SIZE = 20  # Nombre max d'emails à traiter par exécution

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

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
            soup = BeautifulSoup(f, 'lxml')
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

def generate_index():
    print("Génération du sommaire...")
    if not os.path.exists(OUTPUT_FOLDER):
        return
        
    subfolders = [f.path for f in os.scandir(OUTPUT_FOLDER) if f.is_dir() and not f.name.startswith('.')]
    pages_data = []
    
    for folder in subfolders:
        folder_name = os.path.basename(folder)
        index_file_path = os.path.join(folder, "index.html")
        if not os.path.exists(index_file_path): continue

        full_title, date_rec_str, sender, date_arch_str = get_page_metadata(index_file_path)
        
        pages_data.append({
            "folder": folder_name,
            "title": full_title,
            "sender": sender,
            "date_rec": format_date_fr(date_rec_str),
            "date_arch": format_date_fr(date_arch_str),
            "sort_key": date_rec_str
        })

    pages_data.sort(key=lambda x: x["sort_key"], reverse=True)

    links_html = ""
    for page in pages_data:
        links_html += f'''
        <li class="news-item">
            <a href="{page['folder']}/index.html" class="item-link">
                <div class="info-col">
                    <span class="sender">{page['sender']}</span>
                    <span class="title">{page['title']}</span>
                </div>
                <div class="date-col">
                    <span class="date" title="Date de réception">📩 {page['date_rec']}</span>
                    <span class="date-arch" title="Date d'archivage">🗄️ {page['date_arch']}</span>
                </div>
            </a>
        </li>
        '''

    current_year = datetime.datetime.now().year

    index_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Archives Newsletters - Benoît Prentout</title>
        <meta name="robots" content="noindex, nofollow">
        <style>
            :root {{
                --bg-body: #f6f9fc; --bg-card: #ffffff; --text-main: #333333; --text-muted: #666666; --text-light: #888888;
                --border-color: #eaeaea; --accent-color: #0070f3; --hover-bg: #f8f9fa; --input-bg: #fcfcfc; --shadow: rgba(0,0,0,0.05);
                --toggle-icon: "🌙";
            }}
            [data-theme="dark"] {{
                --bg-body: #121212; --bg-card: #1e1e1e; --text-main: #e0e0e0; --text-muted: #a0a0a0; --text-light: #666666;
                --border-color: #333333; --accent-color: #4da3ff; --hover-bg: #252525; --input-bg: #252525; --shadow: rgba(0,0,0,0.3);
                --toggle-icon: "☀️";
            }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: var(--bg-body); color: var(--text-main); margin: 0; padding: 20px; display: flex; flex-direction: column; min-height: 100vh; box-sizing: border-box; transition: background-color 0.3s, color 0.3s; }}
            .container {{ max-width: 800px; width: 100%; margin: 0 auto; background: var(--bg-card); padding: 40px; border-radius: 12px; box-shadow: 0 4px 12px var(--shadow); flex: 1; position: relative; }}
            .header-row {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; border-bottom: 2px solid var(--border-color); padding-bottom: 20px; }}
            h1 {{ text-align: center; color: var(--text-main); margin: 0; font-size: 1.8rem; flex-grow: 1; }}
            
            #theme-toggle {{ background: none; border: 1px solid var(--border-color); border-radius: 50%; width: 40px; height: 40px; cursor: pointer; font-size: 1.2rem; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }}
            #theme-toggle:hover {{ background-color: var(--hover-bg); border-color: var(--accent-color); }}
            #theme-toggle::after {{ content: var(--toggle-icon); }}
            
            #searchInput {{ width: 100%; padding: 12px 20px; margin-bottom: 25px; box-sizing: border-box; border: 2px solid var(--border-color); border-radius: 8px; font-size: 16px; background-color: var(--input-bg); color: var(--text-main); transition: border-color 0.3s; }}
            #searchInput:focus {{ border-color: var(--accent-color); outline: none; }}
            
            ul {{ list-style: none; padding: 0; margin: 0; border: 1px solid var(--border-color); border-radius: 8px; overflow: hidden; }}
            li {{ border-bottom: 1px solid var(--border-color); margin: 0; }}
            li:last-child {{ border-bottom: none; }}
            
            a.item-link {{ display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; background: var(--bg-card); text-decoration: none; color: var(--text-main); transition: background 0.1s ease; }}
            a.item-link:hover {{ background-color: var(--hover-bg); }}
            
            .info-col {{ display: flex; flex-direction: column; flex: 1; min-width: 0; margin-right: 15px; }}
            .sender {{ font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-light); margin-bottom: 4px; font-weight: 600; }}
            .title {{ font-weight: 500; font-size: 1rem; color: var(--text-main); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
            
            .date-col {{ display: flex; flex-direction: column; align-items: flex-end; flex-shrink: 0; margin-left: 10px; }}
            .date {{ font-size: 0.85rem; color: var(--text-muted); white-space: nowrap; font-variant-numeric: tabular-nums; }}
            .date-arch {{ font-size: 0.7rem; color: var(--text-light); white-space: nowrap; font-variant-numeric: tabular-nums; margin-top: 3px; }}
            
            /* Pagination Styles */
            .pagination {{ display: flex; justify-content: center; gap: 8px; margin-top: 25px; flex-wrap: wrap; }}
            .page-btn {{ background: var(--bg-card); border: 1px solid var(--border-color); color: var(--text-main); padding: 8px 12px; border-radius: 6px; cursor: pointer; font-size: 0.9rem; transition: all 0.2s; }}
            .page-btn:hover {{ background: var(--hover-bg); border-color: var(--accent-color); }}
            .page-btn.active {{ background: var(--accent-color); color: white; border-color: var(--accent-color); }}
            .page-btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
            
            footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--border-color); text-align: center; color: var(--text-muted); font-size: 0.85rem; }}
            .copyright a {{ color: inherit; text-decoration: none; border-bottom: 1px dotted var(--text-muted); transition: color 0.2s; }}
            .copyright a:hover {{ color: var(--accent-color); border-bottom-color: var(--accent-color); }}
            details {{ margin-top: 15px; cursor: pointer; }}
            details p {{ background: var(--hover-bg); padding: 10px; border-radius: 4px; text-align: left; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header-row">
                <div style="width: 40px;"></div>
                <h1>📬 Archives Newsletters</h1>
                <button id="theme-toggle" title="Changer le thème"></button>
            </div>
            <input type="text" id="searchInput" onkeyup="filterList()" placeholder="Rechercher par titre, expéditeur ou date...">
            <ul id="newsList">
                {links_html}
            </ul>
            <div id="pagination" class="pagination"></div>
            <footer>
                <p class="copyright">&copy; {current_year} <a href="https://github.com/benoit-prentout" target="_blank">Benoît Prentout</a>.</p>
                <details>
                    <summary>Mentions Légales</summary>
                    <p style="margin-top:10px;"><strong>Éditeur :</strong> Benoît Prentout<br><strong>Hébergement :</strong> GitHub Inc.<br>Ce site est une archive personnelle.</p>
                </details>
            </footer>
        </div>
        <script>
        const toggleBtn = document.getElementById('theme-toggle');
        const root = document.documentElement;
        const savedTheme = localStorage.getItem('theme');
        const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        if (savedTheme === 'dark' || (!savedTheme && systemDark)) {{ root.setAttribute('data-theme', 'dark'); }}
        
        toggleBtn.addEventListener('click', () => {{
            const currentTheme = root.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            root.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        }});

        // --- PAGINATION & SEARCH LOGIC ---
        const itemsPerPage = 10;
        let currentPage = 1;
        const list = document.getElementById("newsList");
        const allItems = Array.from(list.getElementsByClassName('news-item'));
        const paginationContainer = document.getElementById('pagination');

        function showPage(page) {{
            currentPage = page;
            const start = (page - 1) * itemsPerPage;
            const end = start + itemsPerPage;
            
            allItems.forEach((item, index) => {{
                if (index >= start && index < end) {{
                    item.style.display = "";
                }} else {{
                    item.style.display = "none";
                }}
            }});
            renderPaginationControls();
            window.scrollTo(0, 0);
        }}

        function renderPaginationControls() {{
            const totalPages = Math.ceil(allItems.length / itemsPerPage);
            paginationContainer.innerHTML = '';
            
            if (totalPages <= 1) return;

            const prevBtn = document.createElement('button');
            prevBtn.className = 'page-btn';
            prevBtn.innerHTML = '&laquo;';
            prevBtn.disabled = currentPage === 1;
            prevBtn.onclick = () => showPage(currentPage - 1);
            paginationContainer.appendChild(prevBtn);

            let startPage = Math.max(1, currentPage - 2);
            let endPage = Math.min(totalPages, currentPage + 2);
            
            if (startPage > 1) {{
                const firstPage = document.createElement('button');
                firstPage.className = 'page-btn';
                firstPage.innerText = '1';
                firstPage.onclick = () => showPage(1);
                paginationContainer.appendChild(firstPage);
                if (startPage > 2) paginationContainer.appendChild(document.createTextNode('...'));
            }}

            for (let i = startPage; i <= endPage; i++) {{
                const btn = document.createElement('button');
                btn.className = `page-btn ${{i === currentPage ? 'active' : ''}}`;
                btn.innerText = i;
                btn.onclick = () => showPage(i);
                paginationContainer.appendChild(btn);
            }}

            if (endPage < totalPages) {{
                if (endPage < totalPages - 1) paginationContainer.appendChild(document.createTextNode('...'));
                const lastPage = document.createElement('button');
                lastPage.className = 'page-btn';
                lastPage.innerText = totalPages;
                lastPage.onclick = () => showPage(totalPages);
                paginationContainer.appendChild(lastPage);
            }}

            const nextBtn = document.createElement('button');
            nextBtn.className = 'page-btn';
            nextBtn.innerHTML = '&raquo;';
            nextBtn.disabled = currentPage === totalPages;
            nextBtn.onclick = () => showPage(currentPage + 1);
            paginationContainer.appendChild(nextBtn);
        }}

        function filterList() {{
            const input = document.getElementById('searchInput');
            const filter = input.value.toUpperCase();
            
            if (filter === "") {{
                paginationContainer.style.display = "flex";
                showPage(1);
            }} else {{
                paginationContainer.style.display = "none";
                allItems.forEach(item => {{
                    const text = item.textContent || item.innerText;
                    if (text.toUpperCase().indexOf(filter) > -1) {{
                        item.style.display = "";
                    }} else {{
                        item.style.display = "none";
                    }}
                }});
            }}
        }}

        showPage(1);
        </script>
    </body>
    </html>
    """
    with open(f"{OUTPUT_FOLDER}/index.html", "w", encoding='utf-8') as f:
        f.write(index_content)

def process_emails():
    try:
        if not os.path.exists(OUTPUT_FOLDER):
            os.makedirs(OUTPUT_FOLDER)

        print("Connexion au serveur Gmail...")
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASSWORD)
        
        rv, data = mail.select(f'"{TARGET_LABEL}"')
        if rv != 'OK':
            print(f"ERREUR: Impossible de trouver le libellé '{TARGET_LABEL}'.")
            return

        status, messages = mail.search(None, 'ALL')
        if messages[0]:
            email_ids = messages[0].split()
            print(f"{len(email_ids)} emails trouvés au total.")

            # --- PHASE 1: SCAN ET NETTOYAGE ---
            print("Analyse des emails valides (Synchronisation)...")
            valid_folder_ids = set()
            email_map = {}

            for num in email_ids:
                try:
                    status, msg_data = mail.fetch(num, '(BODY.PEEK[HEADER.FIELDS (SUBJECT)])')
                    msg_header = email.message_from_bytes(msg_data[0][1])
                    raw_subject = get_decoded_email_subject(msg_header)
                    subject = clean_subject_prefixes(raw_subject)
                    f_id = get_deterministic_id(subject)
                    valid_folder_ids.add(f_id)
                    email_map[f_id] = num
                except Exception as e:
                    print(f"Erreur lecture header {num}: {e}")

            local_folders = set([f.name for f in os.scandir(OUTPUT_FOLDER) if f.is_dir() and not f.name.startswith('.')])
            folders_to_delete = local_folders - valid_folder_ids
            
            if folders_to_delete:
                print(f"🗑️ Suppression de {len(folders_to_delete)} dossiers obsolètes...")
                for f_id in folders_to_delete:
                    path_to_remove = os.path.join(OUTPUT_FOLDER, f_id)
                    try:
                        shutil.rmtree(path_to_remove)
                        print(f"   - Supprimé: {f_id}")
                    except Exception as e:
                        print(f"   - Erreur suppression {f_id}: {e}")
            
            # --- PHASE 2: TÉLÉCHARGEMENT INCRÉMENTAL ---
            folders_to_download = valid_folder_ids - local_folders
            print(f"📥 {len(folders_to_download)} nouveaux emails à télécharger.")
            
            folders_to_process_now = list(folders_to_download)[:BATCH_SIZE]
            
            if folders_to_process_now:
                print(f"🚀 Traitement du lot de {len(folders_to_process_now)} emails...")
                
                for f_id in folders_to_process_now:
                    num = email_map[f_id]
                    try:
                        status, msg_data = mail.fetch(num, '(RFC822)')
                        msg = email.message_from_bytes(msg_data[0][1])
                        
                        raw_subject = get_decoded_email_subject(msg)
                        subject = clean_subject_prefixes(raw_subject)
                        sender_name = get_clean_sender(msg)
                        email_date_str = get_email_date(msg)
                        
                        newsletter_path = os.path.join(OUTPUT_FOLDER, f_id)
                        os.makedirs(newsletter_path, exist_ok=True)
                        
                        print(f"   -> Téléchargement : {subject[:30]}...")

                        html_content = ""
                        for part in msg.walk():
                            if part.get_content_type() == "text/html":
                                payload = part.get_payload(decode=True)
                                charset = part.get_content_charset() or 'utf-8'
                                html_content = payload.decode(charset, errors="ignore")
                                break
                        if not html_content and not msg.is_multipart():
                            payload = msg.get_payload(decode=True)
                            charset = msg.get_content_charset() or 'utf-8'
                            html_content = payload.decode(charset, errors="ignore")
                        
                        if not html_content: continue

                        soup = BeautifulSoup(html_content, "lxml")
                        for s in soup(["script", "iframe", "object"]): s.extract()

                        # Nettoyage Forward
                        split_keywords = ["Forwarded message", "Message transféré"]
                        found_split = False
                        for div in soup.find_all("div"):
                            text = div.get_text()
                            if any(k in text for k in split_keywords) and "-----" in text:
                                real_content = []
                                for sibling in div.next_siblings: real_content.append(sibling)
                                if soup.body:
                                    soup.body.clear()
                                    for item in real_content:
                                        if item: soup.body.append(item)
                                found_split = True
                                break
                        if not found_split:
                            quote = soup.find(class_="gmail_quote")
                            if quote:
                                soup.body.clear()
                                soup.body.append(quote)
                                for attr in soup.find_all(class_="gmail_attr"): attr.decompose()

                        if not soup.body:
                            new_body = soup.new_tag("body")
                            new_body.extend(soup.contents)
                            soup.append(new_body)

                        # Link Extraction
                        extracted_links = []
                        for a_tag in soup.find_all('a', href=True):
                            text = a_tag.get_text(strip=True)
                            if not text:
                                img_tag = a_tag.find('img')
                                if img_tag and img_tag.get('alt'):
                                    text = f"[Image: {img_tag.get('alt')}]"
                                else:
                                    text = "[Lien image/vide]"
                            extracted_links.append({
                                'text': text[:60] + "..." if len(text) > 60 else text, 
                                'url': a_tag['href']
                            })
                        
                        links_html_list = ""
                        for l in extracted_links:
                            links_html_list += f'<li><a href="{l["url"]}" target="_blank" rel="noopener noreferrer"><span class="link-text">{l["text"]}</span><span class="link-url">{l["url"]}</span></a></li>'

                        # Correction Largeur Tables
                        for table in soup.find_all("table"):
                            if table.get("style"):
                                table["style"] = re.sub(r'width:\s*([6-9]\d{2}|\d{4,})px', 'width: 100%', table["style"], flags=re.IGNORECASE)
                            if table.get("width") and table["width"].isdigit():
                                if int(table["width"]) > 600: table["width"] = "100%"

                        # Images
                        img_counter = 0
                        for img in soup.find_all("img"):
                            src = img.get("src")
                            if not src or src.startswith("data:") or src.startswith("cid:"): continue
                            try:
                                if src.startswith("//"): src = "https:" + src
                                response = requests.get(src, headers=HEADERS, timeout=5)
                                if response.status_code == 200:
                                    content_type = response.headers.get('content-type', '')
                                    if 'image' not in content_type: continue
                                    ext = mimetypes.guess_extension(content_type) or ".jpg"
                                    img_name = f"img_{img_counter}{ext}"
                                    img_path = os.path.join(newsletter_path, img_name)
                                    with open(img_path, "wb") as f: f.write(response.content)
                                    img['src'] = img_name
                                    img['loading'] = 'lazy'
                                    if img.has_attr('srcset'): del img['srcset']
                                    img_counter += 1
                            except Exception: pass

                        # GENERATE VIEWER
                        safe_html = json.dumps(str(soup))
                        nb_links = len(extracted_links)
                        
                        viewer_content = f"""
                        <!DOCTYPE html>
                        <html lang="fr">
                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <meta name="creation_date" content="{email_date_str}">
                            <meta name="sender" content="{sender_name}">
                            <meta name="archiving_date" content="{datetime.datetime.now().strftime('%Y-%m-%d')}">
                            <title>{subject}</title>
                            <style>
                                /* Main & Reset */
                                body {{ margin: 0; padding: 0; background: #eef2f5; font-family: system-ui, -apple-system, sans-serif; overflow: hidden; }}
                                
                                /* Header */
                                .header {{ position: fixed; top: 0; left: 0; right: 0; height: 60px; background: white; border-bottom: 1px solid #ddd; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; z-index: 100; box-shadow: 0 2px 5px rgba(0,0,0,0.02); }}
                                .title {{ font-size: 16px; font-weight: 600; color: #333; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-right: 20px; }}
                                .controls {{ display: flex; gap: 10px; flex-shrink: 0; }}
                                .btn {{ padding: 6px 12px; border: 1px solid #ccc; background: #f9f9f9; border-radius: 6px; cursor: pointer; font-size: 13px; display: flex; align-items: center; gap: 5px; transition: all 0.2s; }}
                                .btn:hover {{ background: #eee; }}
                                .btn.active {{ background: #0070f3; color: white; border-color: #0070f3; }}
                                
                                /* Main View Area */
                                .main-view {{ margin-top: 60px; height: calc(100vh - 60px); display: flex; justify-content: center; align-items: center; background: #eef2f5; overflow: hidden; }}
                                
                                /* Iframe Wrapper - Desktop Default */
                                .iframe-wrapper {{ 
                                    width: 1200px; 
                                    max-width: 95%;
                                    height: 90%;
                                    transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1); 
                                    background: white; 
                                    box-shadow: 0 5px 30px rgba(0,0,0,0.1); 
                                    border-radius: 8px;
                                }}
                                
                                iframe {{ width: 100%; height: 100%; border: none; display: block; border-radius: inherit; }}
                                
                                /* Mobile Mode */
                                body.mobile-mode .iframe-wrapper {{ 
                                    width: 375px; 
                                    height: 812px; 
                                    max-height: 90vh;
                                    border-radius: 40px; 
                                    border: 12px solid #333; 
                                    box-shadow: 0 20px 50px rgba(0,0,0,0.2);
                                }}
                                
                                /* Links Sidebar */
                                .links-panel {{ position: fixed; top: 60px; right: -400px; width: 350px; height: calc(100vh - 60px); background: #ffffff; box-shadow: -2px 0 10px rgba(0,0,0,0.1); z-index: 90; transition: right 0.3s ease; padding: 20px; overflow-y: auto; box-sizing: border-box; }}
                                .links-panel.open {{ right: 0; }}
                                .links-panel h3 {{ margin-top: 0; font-size: 16px; color: #333; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                                .links-panel ul {{ list-style: none; padding: 0; }}
                                .links-panel li {{ margin-bottom: 10px; border-bottom: 1px solid #f5f5f5; padding-bottom: 8px; }}
                                .links-panel a {{ text-decoration: none; color: inherit; display: block; word-break: break-all; }}
                                .links-panel a:hover .link-text {{ text-decoration: underline; }}
                                .links-panel .link-text {{ font-weight: 600; font-size: 13px; color: #0070f3; display: block; margin-bottom: 2px; }}
                                .links-panel .link-url {{ font-size: 11px; color: #888; display: block; }}
                                .links-panel .close-btn {{ position: absolute; top: 15px; right: 15px; background: none; border: none; font-size: 20px; cursor: pointer; color: #666; }}

                                /* Dark Mode */
                                body.dark-mode .main-view {{ background: #121212; }}
                                body.dark-mode .header {{ background: #1e1e1e; border-bottom-color: #333; }}
                                body.dark-mode .title {{ color: #e0e0e0; }}
                                body.dark-mode .btn {{ background: #2c2c2c; border-color: #444; color: #ccc; }}
                                body.dark-mode .btn.active {{ background: #0070f3; color: white; }}
                                body.dark-mode iframe {{ filter: invert(1) hue-rotate(180deg); }}
                                
                                body.dark-mode .links-panel {{ background: #1e1e1e; border-left: 1px solid #333; box-shadow: -2px 0 10px rgba(0,0,0,0.5); }}
                                body.dark-mode .links-panel h3 {{ color: #e0e0e0; border-bottom-color: #333; }}
                                body.dark-mode .links-panel li {{ border-bottom-color: #333; }}
                                body.dark-mode .links-panel .link-text {{ color: #4da3ff; }}
                                body.dark-mode .links-panel .link-url {{ color: #aaa; }}
                                body.dark-mode .links-panel .close-btn {{ color: #e0e0e0; }}
                            </style>
                        </head>
                        <body>
                            <header class="header">
                                <div class="title">{subject}</div>
                                <div class="controls">
                                    <button id="btn-links" class="btn" onclick="toggleLinks()"><span>🔗</span> Liens ({nb_links})</button>
                                    <button id="btn-mobile" class="btn" onclick="toggleMobile()"><span>📱</span> Mobile</button>
                                    <button id="btn-dark" class="btn" onclick="toggleDark()"><span>🌙</span> Sombre</button>
                                </div>
                            </header>
                            
                            <div class="main-view">
                                <div class="iframe-wrapper">
                                    <iframe id="emailFrame"></iframe>
                                </div>
                            </div>
                            
                            <div id="links-panel" class="links-panel">
                                <h3>Liens extraits ({nb_links})</h3>
                                <button class="close-btn" onclick="toggleLinks()">×</button>
                                <ul>{links_html_list}</ul>
                            </div>

                            <script>
                                const emailContent = {safe_html};
                                const frame = document.getElementById('emailFrame');
                                
                                frame.contentDocument.open();
                                frame.contentDocument.write(emailContent);
                                frame.contentDocument.close();
                                
                                const style = frame.contentDocument.createElement('style');
                                style.textContent = 'body {{ margin: 0; overflow-x: hidden; }} img {{ max-width: 100%; height: auto; }}';
                                frame.contentDocument.head.appendChild(style);

                                function toggleMobile() {{
                                    document.body.classList.toggle('mobile-mode');
                                    document.getElementById('btn-mobile').classList.toggle('active');
                                }}
                                function toggleDark() {{
                                    document.body.classList.toggle('dark-mode');
                                    document.getElementById('btn-dark').classList.toggle('active');
                                }}
                                function toggleLinks() {{
                                    document.getElementById('links-panel').classList.toggle('open');
                                    document.getElementById('btn-links').classList.toggle('active');
                                }}
                            </script>
                        </body>
                        </html>
                        """
                        
                        with open(os.path.join(newsletter_path, "index.html"), "w", encoding='utf-8') as f:
                            f.write(viewer_content)

                    except Exception as e:
                        print(f"Erreur traitement {f_id}: {e}")

            generate_index()
            print("Terminé.")
        else:
            print("Aucun email trouvé.")
        mail.close()
        mail.logout()
    except Exception as e:
        print(f"Erreur critique: {e}")

if __name__ == "__main__":
    process_emails()
