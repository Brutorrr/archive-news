# 📬 Newsletter Archiver

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/release/python-390/)
[![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-orange)](https://pages.github.com/)

An automated DevOps solution that captures incoming newsletters from Gmail, processes them, and archives them as a static website hosted on GitHub Pages.

Designed to preserve content fidelity, download remote images locally, and provide a persistent, searchable archive accessible via a web browser.

---

## 🚀 Features

* **Automated Ingestion:** Connects to Gmail via IMAP to fetch specific unread emails (filtered by label).
* **Content Processing:**
    * Parses HTML content using `BeautifulSoup`.
    * Sanitizes dangerous scripts (XSS protection).
    * **Local Image Caching:** Automatically downloads remote images to ensure archives remain viewable even if the original source deletes them.
* **Static Site Generation:**
    * Generates individual HTML pages for each newsletter.
    * Auto-generates a clean, responsive `index.html` (Table of Contents) with dates and titles.
* **CI/CD Pipeline:** Fully automated via **GitHub Actions** (runs on a schedule).
* **Free Hosting:** Deploys automatically to **GitHub Pages**.

---

## 🛠️ Tech Stack

* **Language:** Python 3.9
* **Libraries:**
    * `imaplib` & `email`: For email server interaction.
    * `BeautifulSoup4`: For HTML parsing and DOM manipulation.
    * `Requests`: For downloading assets.
* **Automation:** GitHub Actions (CRON scheduler).
* **Hosting:** GitHub Pages.

---

## ⚙️ Architecture

```mermaid
graph LR
A[Gmail (Label: Netlify-News)] -- IMAP --> B(Python Script via GitHub Actions)
B -- Extract HTML & Download Images --> C[Process & Sanitize]
C -- Commit changes --> D[GitHub Repository (/docs)]
D -- Auto Deploy --> E[GitHub Pages Website]
