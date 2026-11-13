# youtube-infocard-text
# 🎬 YouTube Info Cards Extractor

A lightweight, terminal-based Python script that pulls **Info Cards** (those little pop-up cards in the top-right corner of YouTube videos) along with their exact timestamps and teaser text.

Most tools for doing this rely on heavy browser automation or desktop GUI libraries like `tkinter`, which break or refuse to install on headless Linux setups and **Termux**. I wrote this script to work purely in the terminal using standard HTTP requests and JSON parsing—no GUI dependencies or API keys required.

---

## ✨ What It Does

* **Extracts Video Metadata:** Grabs the video title, channel name, and 11-character video ID.
* **Pulls Info Cards & Timings:** Parses YouTube's internal `ytInitialData` payload to find every info card on the video, showing the exact start/end timestamps (in seconds) and the teaser message.
* **Supports Multiple URL Formats:** Works with standard `youtube.com/watch?v=...` links, shortened `youtu.be/...` links, and embed/nocookie URLs.
* **Headless & Termux Ready:** Zero GUI dependencies (`tkinter`-free) and no YouTube Data API key needed.

---

## 📋 Requirements

* **Python 3.10+** (uses union type hints like `str | None`)
* **`requests`** library

Install the dependency via `pip`:

```bash
pip install requests
```

---

## 🚀 How to Use It

### Option 1: Pass the URL directly as an argument
```bash
python yt_cards.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Option 2: Run interactively
Just run the script without arguments and paste the link when prompted:
```bash
python yt_cards.py
```

---

## 💻 Example Output

```text
YouTube Info Cards Extractor
----------------------------------------

Fetching data for: dQw4w9WgXcQ ...

Title  : Example Tech Review Video
Channel: Tech Creator
ID     : dQw4w9WgXcQ

Found 2 info card(s):

  Card #1  @ 45s → 52s
     → Check out our previous benchmark test

  Card #2  @ 190s → 198s
     → Full battery test breakdown
```

---

## ⚙️ How It Works Under the Hood

1. **ID Parsing:** Strips out the 11-character video ID regardless of extra tracking parameters (`&si=...`, `&t=...`, etc.).
2. **Page Fetch:** Sends a standard browser `User-Agent` GET request to the watch page.
3. **Balanced Brace JSON Extraction:** Instead of fragile regex hacks that break on nested brackets, it scans through the page HTML starting at `ytInitialData` and tracks `{` and `}` depth (ignoring brackets inside strings) to extract clean, valid JSON.
4. **Card Rendering:** Walks `cardCollectionRenderer` to pull out `simpleCardTeaserRenderer` text and converts `cueRanges` millisecond timestamps into readable seconds.
