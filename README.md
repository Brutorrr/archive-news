# 📬 Newsletter Archiver

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/release/python-390/)
[![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-orange)](https://pages.github.com/)
[![Actions Status](https://github.com/benoit-prentout/archive-news/workflows/Check%20Newsletter/badge.svg)](https://github.com/benoit-prentout/archive-news/actions)

An automated DevOps solution that captures incoming newsletters from Gmail, sanitizes them (removing forward history), and archives them as a static website hosted on GitHub Pages.

**🔗 [Accéder à l'archive en ligne / Access Online Archive](https://benoit-prentout.github.io/archive-news/)**

---

## 🚀 Features

* **Smart Ingestion:** Fetches emails from Gmail via IMAP using a specific alias/filter strategy.
* **Advanced Processing:**
    * **Sanitization:** Automatically removes "Forward" headers (`Fwd:`, `Tr:`) and quoted history to preserve only the original content.
    * **Structure:** Organizes each newsletter in its own dedicated folder with a deterministic ID.
    * **Metadata:** Extracts the *original* email date (not the archiving date) for accurate timeline sorting.
* **Asset Management:** Downloads remote images locally to ensure long-term preservation and privacy.
* **Static Site Generation:** Auto-generates a responsive `index.html` with a clean footer and legal notices.
* **CI/CD Pipeline:** Runs automatically every 30 minutes via GitHub Actions.

---

## 🛠️ Tech Stack

* **Core:** ![Python](https://img.shields.io/badge/Python-3.9-3776AB?style=flat&logo=python&logoColor=white)
* **Libraries:** `BeautifulSoup4` (Parsing), `imaplib` (Email), `Requests` (Assets).
* **Automation:** ![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat&logo=github-actions&logoColor=white)
* **Hosting:** ![GitHub Pages](https://img.shields.io/badge/GitHub_Pages-222222?style=flat&logo=github&logoColor=white)

---

## ⚙️ Architecture

```mermaid
graph LR
    A["Gmail (Alias + Filter)"] -- "IMAP Fetch" --> B("Python Script (GitHub Actions)")
    B -- "Extract HTML & Clean History" --> C["Sanitize & Download Images"]
    C -- "Commit Changes" --> D["GitHub Repository (/docs)"]
    D -- "Auto Deploy" --> E["GitHub Pages Website"]
