# LinkedIn Post Exporter — Chrome Extension

A Chrome extension that scrapes LinkedIn posts from your activity feed and sends them to the backend API.

## 🚀 Features

- **Batch Scraping**: Sends posts in chunks (configurable batch size).
- **Auto-Retry**: Handles network hiccups gracefully.
- **Configurable API**: Point to any backend URL via `config.js`.

## 🛠️ Installation

1.  **Open Chrome Extensions**:
    Go to `chrome://extensions/` in your browser.

2.  **Enable Developer Mode**:
    Toggle the switch in the top right corner.

3.  **Load Unpacked**:
    Click "Load unpacked" and select this `chrome-extension` directory.

4.  **Configure API**:
    Edit `config.js` if your backend is not running on `http://localhost:8000`.

## 📖 Usage

1.  Navigate to your LinkedIn "All Activity" or "Posts" page.
2.  Click the extension icon in the toolbar.
3.  Click **"Scrape Posts"**.
4.  Wait for the confirmation message.
5.  Check the backend logs for received data.
