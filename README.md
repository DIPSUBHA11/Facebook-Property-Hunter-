# Facebook-Property-Hunter-


# Facebook Property Hunter

A Chrome extension that turns Facebook's endless feed into a targeted search tool for property hunters. Enter your keywords (locality, BHK, budget, whatever), open a Facebook group or timeline, and hit **Hunt Now** — the extension auto-scrolls the page, expands truncated posts, and streams matching listings into the popup as they're found. Click **Open Post** to jump straight to the source thread.

## Highlights

- **Auto-scroll** — scrolls the Facebook feed (window, `role="feed"`, and inner scroll containers) until the page stops loading new posts or you hit **Stop**.
- **Live results** — matches stream into the popup as they're discovered, backed by `chrome.storage.local` so closing the popup mid-scan doesn't lose progress.
- **AND / OR match modes** — segmented toggle to require *every* keyword (AND) or *any one* (OR). Persisted across sessions.
- **"See more" expansion** — clicks every truncated-post expander before matching, so keywords hidden below the fold still get picked up. The longest captured version of each post wins.
- **Native-feeling UI** — Meta blue → sky → aqua header, rounded popup, tuned for long browsing sessions on top of Facebook.
- **No accounts, no API** — everything runs locally in your browser. The extension only reads DOM content of the tab you're already looking at.

## Install

1. Clone the repo.
2. Open `chrome://extensions`, enable **Developer mode**, click **Load unpacked**, and select the `chrome-extension/` folder.
3. Pin the extension, open Facebook, click the icon.

## Use

1. Paste keywords in the textarea (one per line or comma-separated).
2. Hit **Save**.
3. Choose **Any** (OR) or **All** (AND).
4. Open the Facebook feed / group you want to hunt.
5. Click **Hunt Now** and watch matches roll in. Hit **Stop** any time.
