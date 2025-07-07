# 🕵️‍♂️ SuperPages Business Scraper

A robust Python scraper that extracts business listings from [SuperPages.com](https://www.superpages.com) across multiple U.S. cities and categories. Built using **Playwright**, this tool automates data collection including business name, phone number, address, category, and state.

---

## 📌 Features

- ✅ Multi-city & multi-state scraping
- ✅ Customizable business categories
- ✅ Duplicate filtering
- ✅ Periodic browser restarts for memory efficiency
- ✅ Auto-resume from last page in case of interruption
- ✅ Saves output to `.csv`

---

## ⚙️ Requirements

- Python 3.8+
- [Playwright](https://playwright.dev/python/)
- CSV (standard lib)
- Other standard libraries: `os`, `gc`, `random`, `time`, `signal`, `datetime`

---

## 📦 Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/superpages-business-scraper.git
cd superpages-business-scraper

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Playwright and dependencies
pip install playwright
playwright install
