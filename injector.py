import os
import re
from datetime import datetime
from bs4 import BeautifulSoup

# Configuration
DOCS_DIR = "docs"
OUTPUT_FILE = os.path.join(DOCS_DIR, "index.html")

# Template for the main index page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Newsletter Archive</title>
    <meta name="description" content="Personal Newsletter Archive">
    <style>
        :root {{
            --bg-color: #f8f9fa;
            --card-bg: #ffffff;
            --text-main: #2c3e50;
            --text-sec: #7f8c8d;
            --accent: #2980b9;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 40px 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header {{ text-align: center; margin-bottom: 50px; }}
        h1 {{ font-size: 2.5rem; margin-bottom: 15px; color: var(--text-main); }}
        .search-container {{ max-width: 500px; margin: 0 auto; position: relative; }}
        input[type="text"] {{
            width: 100%; padding: 15px 20px; border-radius: 30px;
            border: 1px solid #e1e8ed; font-size: 16px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05); transition: all 0.2s;
            box-sizing: border-box;
        }}
        input[type="text"]:focus {{ outline: none; box-shadow: 0 4px 12px rgba(41, 128, 185, 0.2); border-color: var(--accent); }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 25px;
            margin-top: 40px;
        }}
        .card {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 25px;
            text-decoration: none;
            color: inherit;
            transition: transform 0.2s, box-shadow 0.2s;
            border: 1px solid #eee;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .card:hover {{ transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.08); border-color: var(--accent); }}
        .card-date {{ font-size: 0.85rem; color: var(--text-sec); margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px; }}
        .card-title {{ font-size: 1.2rem; font-weight: 600; line-height: 1.4; margin-bottom: 15px; }}
        .card-snippet {{ font-size: 0.95rem; color: #555; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }}
        .empty-state {{ text-align: center; color: var(--text-sec); margin-top: 50px; display: none; }}
        footer {{ margin-top: 60px; text-align: center; font-size: 0.9rem; color: var(--text-sec); border-top: 1px solid #eee; padding-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📬 Newsletter Archive</h1>
            <div class="search-container">
                <input type="text" id="searchInput" placeholder="Search by title or date..." onkeyup="filterContent()">
            </div>
        </header>

        <div class="grid" id="newsletterGrid">
            {content}
        </div>
        <p id="noResults" class="empty-state">No newsletters found matching your search.</p>
        
        <footer>
            <p>Archive generated daily. Content property of respective authors.</p>
        </footer>
    </div>

    <script>
        function filterContent() {{
            const input = document.getElementById('searchInput');
            const filter = input.value.toLowerCase();
            const cards = document.getElementsByClassName('card');
            let hasVisible = false;

            for (let i = 0; i < cards.length; i++) {{
                const title = cards[i].querySelector('.card-title').innerText.toLowerCase();
                const date = cards[i].querySelector('.card-date').innerText.toLowerCase();
                
                if (title.includes(filter) || date.includes(filter)) {{
                    cards[i].style.display = "";
                    hasVisible = true;
                }} else {{
                    cards[i].style.display = "none";
                }}
            }}
            document.getElementById('noResults').style.display = hasVisible ? "none" : "block";
        }}
    </script>
</body>
</html>
"""

def get_newsletter_data():
    newsletters = []
    
    # Walk through docs directory
    if not os.path.exists(DOCS_DIR):
        print("No docs directory found.")
        return []

    for item in os.listdir(DOCS_DIR):
        folder_path = os.path.join(DOCS_DIR, item)
        if os.path.isdir(folder_path):
            index_path = os.path.join(folder_path, "index.html")
            if os.path.exists(index_path):
                try:
                    with open(index_path, 'r', encoding='utf-8') as f:
                        soup = BeautifulSoup(f, 'html.parser')
                        
                        # Extract Title
                        title = soup.title.string if soup.title else "Untitled Newsletter"
                        
                        # Extract Date (Look for meta tag or date pattern in title/filename)
                        # Fallback to file modification time if no date found
                        date_str = ""
                        date_meta = soup.find("meta", {"name": "date"})
                        if date_meta:
                            date_str = date_meta['content']
                        else:
                            # Try to parse date from file stats
                            mtime = os.path.getmtime(index_path)
                            date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')

                        newsletters.append({
                            'title': title,
                            'date': date_str,
                            'path': f"./{item}/index.html"
                        })
                except Exception as e:
                    print(f"Error processing {item}: {e}")

    # Sort by date descending (newest first)
    newsletters.sort(key=lambda x: x['date'], reverse=True)
    return newsletters

def generate_index():
    data = get_newsletter_data()
    cards_html = ""
    
    for item in data:
        card = f"""
        <a href="{item['path']}" class="card">
            <div>
                <div class="card-date">{item['date']}</div>
                <div class="card-title">{item['title']}</div>
            </div>
            <div class="card-snippet">Click to read full newsletter...</div>
        </a>
        """
        cards_html += card

    full_html = HTML_TEMPLATE.format(content=cards_html)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(full_html)
    
    print(f"Successfully generated index.html with {len(data)} newsletters.")

if __name__ == "__main__":
    generate_index()
