# Facebook Tracker — Chrome Extension Architecture & Technical Documentation

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture Diagram](#architecture-diagram)
3. [File Structure](#file-structure)
4. [Complete Flow](#complete-flow)
5. [Technical Deep Dive](#technical-deep-dive)
6. [Key Concepts](#key-concepts)
7. [Security & Privacy](#security--privacy)
8. [Data Flow](#data-flow)
9. [Testing Strategy](#testing-strategy)
10. [Interview Q&A](#interview-qa)
11. [Limitations & Future Scope](#limitations--future-scope)

---

## Overview

**Facebook Tracker** is a Chrome Extension (Manifest V3) that helps users find Facebook posts matching specific keywords. It:

- Automatically scrolls the Facebook page
- Expands truncated posts ("See more")
- Scans all visible text for user-defined keywords
- Displays matching posts with direct links
- Persists results in local storage

### Use Case
> A user looking for broker-free house rentals in Pune can set keywords like "pune", "2bhk", "female", "no brokerage" — and the extension will scroll through Facebook groups, find matching posts, and show them with direct links.

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         CHROME BROWSER                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌────────────────────┐                  ┌────────────────────┐   │
│  │     POPUP LAYER     │                  │   CONTENT SCRIPT    │   │
│  │                      │  sendMessage()   │                    │   │
│  │  popup.html          │ ───────────────► │  content.js        │   │
│  │  popup.js            │                  │                    │   │
│  │  style.css           │ ◄─────────────── │  Runs INSIDE       │   │
│  │                      │  sendResponse()  │  facebook.com      │   │
│  └──────────┬───────────┘                  └────────┬───────────┘   │
│             │                                        │              │
│             │  chrome.storage.local                   │              │
│             ▼                                        ▼              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                     CHROME STORAGE API                         │  │
│  │                                                                │  │
│  │  {                                                             │  │
│  │    keywords: ["pune", "2bhk", "female"],                       │  │
│  │    savedResults: [{ text, matchedKeywords, url }, ...]         │  │
│  │  }                                                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                      manifest.json                             │  │
│  │  - Declares permissions (storage, tabs, scripting)             │  │
│  │  - Registers content script for facebook.com                   │  │
│  │  - Defines popup UI                                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
chrome-extension/
├── manifest.json          # Extension configuration
├── popup.html             # Popup UI layout
├── popup.js               # Popup logic & keyword management
├── content.js             # Facebook page scanning logic
├── style.css              # Popup styling
├── ARCHITECTURE.md        # This file
└── README.md              # Installation guide
```

### File Responsibilities

| File | Responsibility | Execution Context |
|------|---------------|-------------------|
| `manifest.json` | Declares permissions, scripts, popup | Chrome engine |
| `popup.html` | UI structure (textarea, buttons, results container) | Extension popup window |
| `popup.js` | Keyword CRUD, messaging, result display, storage | Extension popup window |
| `content.js` | Scrolling, "See more" expansion, text extraction, matching | Inside Facebook tab |
| `style.css` | Visual styling for the popup | Extension popup window |

---

## Complete Flow

### Phase 1: Extension Installation & Injection

```
1. User loads unpacked extension → Chrome reads manifest.json
2. Chrome registers:
   - Content script: content.js → injected on *://*.facebook.com/*
   - Popup: popup.html → shown when extension icon clicked
   - Permissions: storage, tabs, scripting
3. When user navigates to facebook.com:
   - Chrome injects content.js into the page (at document_end)
   - content.js executes immediately
   - Registers chrome.runtime.onMessage listener
   - Logs: "✅ Facebook Tracker content script loaded"
```

### Phase 2: Keyword Configuration

```
1. User clicks extension icon → popup.html opens
2. popup.js fires DOMContentLoaded:
   - loadStoredKeywords() → populates textarea from storage
   - loadStoredResults() → displays previous scan results
3. User types keywords (one per line or comma-separated):
   "pune, 2bhk, female, no brokerage"
4. User clicks "Save Keywords":
   - parseKeywords() splits input by \n and , characters
   - Trims whitespace, removes empty strings, removes duplicates
   - Result: ["pune", "2bhk", "female", "no brokerage"]
   - chrome.storage.local.set({ keywords: [...] })
   - UI shows: "Keywords saved: 4"
```

### Phase 3: Scan Initiation (Popup → Content Script)

```
1. User clicks "Scan Current Page"
2. handleScanPage() executes:
   a. Reads keywords from chrome.storage.local
   b. Validates keywords exist (error if empty)
   c. Gets active tab: chrome.tabs.query({ active: true, currentWindow: true })
   d. Validates tab URL contains "facebook.com" (error if not)
   e. Shows loading spinner + status message
   f. Sends message to content script:
      chrome.tabs.sendMessage(tab.id, { type: 'SCAN_PAGE', keywords }, callback)
   g. Sets 90-second timeout for response
```

### Phase 4: Content Script Scanning (Inside Facebook)

```
1. chrome.runtime.onMessage listener receives { type: 'SCAN_PAGE', keywords }
2. handleScanRequest(keywords, sendResponse) fires
3. scrollUntilFoundOrTimeout(keywords, 60000) starts:

   LOOP (repeats every 2 seconds until match or timeout):
   ┌─────────────────────────────────────────────────────┐
   │ a. window.scrollTo(0, document.body.scrollHeight)    │
   │    → Scrolls page to bottom to trigger lazy loading  │
   │                                                      │
   │ b. clickAllSeeMore()                                 │
   │    → Finds all "See more" buttons and clicks them    │
   │    → Reveals full post text hidden behind truncation  │
   │                                                      │
   │ c. setTimeout(2000) → Wait for new content to load   │
   │                                                      │
   │ d. getPagePosts()                                    │
   │    → querySelectorAll('div[dir="auto"], span[dir="auto"]') │
   │    → Filters text blocks (length 20-5000 chars)      │
   │    → Skips UI text (Like, Comment, Share, etc.)      │
   │    → Deduplicates by first 100 chars                 │
   │    → Finds nearest post URL for each text block      │
   │                                                      │
   │ e. matchPosts(posts, keywords)                       │
   │    → For each post text, check if any keyword exists │
   │    → Case-insensitive substring matching             │
   │    → Returns posts with their matched keywords       │
   │                                                      │
   │ f. IF matches found → STOP loop, return results      │
   │    IF timeout (60s) → STOP loop, return whatever     │
   │    ELSE → continue to next scroll iteration          │
   └─────────────────────────────────────────────────────┘

4. sendResponse({ success: true, posts: [...] })
```

### Phase 5: Results Display & Persistence

```
1. popup.js receives response in callback
2. If successful:
   a. saveResults(posts) → chrome.storage.local.set({ savedResults: posts })
   b. displayResults(posts, keywords):
      - Shows result count badge
      - For each post:
        - Creates HTML element with:
          - Yellow keyword badges (matched keywords)
          - Post text preview (first 200 chars)
          - "Open Post" link (target="_blank")
      - Shows results section
3. Hides loading spinner
```

### Phase 6: Persistence & Clear

```
PERSISTENCE:
- Every time popup opens → loadStoredResults() → shows previous results
- Results survive browser restart (chrome.storage.local is persistent)

CLEAR:
- User clicks "Clear Keywords"
- Confirmation dialog appears
- chrome.storage.local.set({ keywords: [], savedResults: [] })
- UI cleared: textarea empty, results hidden
```

---

## Technical Deep Dive

### 1. manifest.json — Extension Configuration

```json
{
  "manifest_version": 3,
  "name": "Facebook Tracker",
  "version": "1.0.0",
  "description": "Find Facebook posts matching your keywords",
  "permissions": ["storage", "tabs", "scripting"],
  "host_permissions": [
    "https://www.facebook.com/*",
    "https://facebook.com/*"
  ],
  "action": {
    "default_popup": "popup.html",
    "default_title": "Facebook Tracker"
  },
  "content_scripts": [
    {
      "matches": ["https://www.facebook.com/*", "*://*.facebook.com/*"],
      "js": ["content.js"],
      "run_at": "document_end"
    }
  ]
}
```

**Key Fields:**
- `manifest_version: 3` — Required for modern Chrome extensions
- `permissions` — What the extension can access
- `host_permissions` — Which websites content script can run on
- `content_scripts.run_at` — When to inject (after DOM is ready)

---

### 2. popup.js — Popup Logic

**Key Functions:**

| Function | Purpose |
|----------|---------|
| `handleSaveKeywords()` | Parse input → save to storage |
| `handleScanPage()` | Validate → send message to content script |
| `handleClearKeywords()` | Clear storage + UI |
| `parseKeywords(raw)` | Split by `\n` and `,` → trim → dedupe |
| `loadStoredKeywords()` | Read from storage → populate textarea |
| `loadStoredResults()` | Read from storage → display results |
| `saveResults(posts)` | Save scan results to storage |
| `displayResults(posts)` | Render HTML for each matched post |
| `createPostElement(post)` | Build DOM element for one result |
| `showStatusMessage(msg)` | Show info/error/success messages |
| `showLoading(bool)` | Show/hide loading spinner |
| `escapeHtml(text)` | Prevent XSS in displayed text |

---

### 3. content.js — Facebook Page Scanner

**Key Functions:**

| Function | Purpose |
|----------|---------|
| `handleScanRequest(keywords, sendResponse)` | Entry point for scan |
| `scrollUntilFoundOrTimeout(keywords, timeout)` | Infinite scroll loop |
| `clickAllSeeMore()` | Expand truncated posts |
| `getPagePosts()` | Extract text blocks from DOM |
| `isUIText(text)` | Filter out Facebook UI elements |
| `findNearestPostUrl(node)` | Walk DOM to find post permalink |
| `findMatchingKeywords(text, keywords)` | Case-insensitive substring match |
| `matchPosts(posts, keywords)` | Filter posts that match keywords |
| `deduplicatePosts(posts)` | Remove duplicate results |

---

### 4. Post Detection Strategy

```javascript
// Facebook wraps ALL user-generated text in dir="auto" elements
document.querySelectorAll('div[dir="auto"], span[dir="auto"]')
```

**Why `dir="auto"`?**
- Facebook uses this HTML attribute for bidirectional text support (RTL/LTR)
- It's applied to ALL user-generated content
- Unlike class names (`x1yztbdb`), this attribute is stable and semantic
- Won't break when Facebook changes their CSS class obfuscation

---

### 5. "See More" Expansion Logic

```javascript
function clickAllSeeMore() {
    // Strategy 1: div[role="button"] or span[role="button"] with text "See more"
    // Strategy 2: <a> or <span> elements with "See more" text near post content
    // Clicks them programmatically to reveal full post text
}
```

**Why?**
- Facebook truncates posts longer than ~3 lines
- Hidden text may contain our keywords
- Must expand before scanning to avoid false negatives

---

### 6. URL Detection Strategy

```javascript
function findNearestPostUrl(node) {
    // Walk UP the DOM tree (up to 15 parent levels)
    // At each level, search for <a href> links matching:
    //   - /posts/
    //   - /permalink/
    //   - /photo/, /photos/
    //   - /videos/, /reel/, /watch/
    //   - ?story_fbid=
    //   - pfbid (Facebook's new post ID format)
    //   - Group posts with numeric IDs
    //   - Timestamp links (always permalink to post)
    // Fallback: window.location.href (current page)
}
```

---

### 7. Keyword Matching Algorithm

```javascript
function findMatchingKeywords(text, keywords) {
    var textLower = text.toLowerCase();
    var matched = [];
    for (var i = 0; i < keywords.length; i++) {
        if (textLower.indexOf(keywords[i].toLowerCase()) !== -1) {
            matched.push(keywords[i]);
        }
    }
    return matched;
}
```

- **Type:** Case-insensitive substring matching
- **Time Complexity:** O(n × m) where n = text length, m = number of keywords
- **Future:** Can be upgraded to regex, word boundary, or NLP-based matching

---

### 8. Deduplication Strategy

```javascript
function deduplicatePosts(posts) {
    var seen = new Set();
    // Primary key: post URL (if unique)
    // Fallback key: first 80 characters of text
    // Set ensures O(1) lookup for duplicates
}
```

---

### 9. Message Passing (IPC)

```
┌──────────┐  chrome.tabs.sendMessage()  ┌────────────────┐
│  POPUP   │ ─────────────────────────►  │ CONTENT SCRIPT  │
│          │                              │                 │
│          │  sendResponse(data)          │                 │
│          │ ◄─────────────────────────── │                 │
└──────────┘                              └────────────────┘
```

**Critical: `return true` in message listener**
```javascript
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    handleScanRequest(request.keywords, sendResponse);
    return true; // ← REQUIRED for async sendResponse
});
```

Without `return true`, Chrome closes the message channel immediately. Since our scan is async (scroll loop with setTimeout), we need the channel to stay open.

---

### 10. Chrome Storage API

```javascript
// WRITE
chrome.storage.local.set({
    keywords: ["pune", "2bhk", "female"],
    savedResults: [{ text: "...", matchedKeywords: [...], url: "..." }]
});

// READ
chrome.storage.local.get(['keywords', 'savedResults'], (data) => {
    console.log(data.keywords);      // ["pune", "2bhk", "female"]
    console.log(data.savedResults);  // [{...}, {...}]
});
```

**Why chrome.storage.local vs localStorage?**

| Feature | chrome.storage.local | localStorage |
|---------|---------------------|-------------|
| Scope | Extension-wide | Per-origin (facebook.com) |
| Accessible from | Popup + Content Script | Only same origin |
| Storage limit | 10 MB | 5 MB |
| Async | Yes (callback-based) | No (synchronous) |
| Persists | Yes (across sessions) | Yes |

---

## Security & Privacy

| Principle | Implementation |
|-----------|---------------|
| **No credential theft** | Never accesses login forms, cookies, or tokens |
| **No data exfiltration** | All data stays in chrome.storage.local (never sent to server) |
| **Minimal permissions** | Only `storage`, `tabs`, `scripting` — no `cookies`, `webRequest` |
| **User-initiated only** | Only scans when user explicitly clicks "Scan" |
| **No background activity** | No service worker or background script running |
| **Respects access controls** | Only reads DOM content user can already see |
| **No CAPTCHA bypass** | Does not automate login or verification |
| **No private data access** | Cannot access private messages, hidden groups, etc. |
| **XSS prevention** | All displayed text is escaped via `escapeHtml()` |

---

## Data Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  USER INPUT  │     │   STORAGE    │     │  FACEBOOK PAGE   │
└──────┬──────┘     └──────┬───────┘     └────────┬────────┘
       │                    │                       │
       │  "pune, female"    │                       │
       ├───────────────────►│                       │
       │                    │  keywords:            │
       │                    │  ["pune","female"]    │
       │                    │                       │
       │  Click "Scan"      │                       │
       ├────────────────────┼──────────────────────►│
       │                    │                       │ scroll()
       │                    │                       │ clickSeeMore()
       │                    │                       │ getPagePosts()
       │                    │                       │ matchPosts()
       │                    │                       │
       │                    │  savedResults:        │
       │                    │◄──────────────────────┤ return matches
       │                    │  [{text, url,         │
       │                    │    matchedKeywords}]  │
       │                    │                       │
       │  Display results   │                       │
       │◄───────────────────┤                       │
       │                    │                       │
       │  Next popup open   │                       │
       │◄───────────────────┤ load savedResults     │
       │  (results persist) │                       │
       │                    │                       │
       │  Click "Clear"     │                       │
       ├───────────────────►│ keywords: []          │
       │                    │ savedResults: []      │
       │  UI cleared        │                       │
       │◄───────────────────┤                       │
```

---

## Testing Strategy

### Unit Tests (Manual)

| # | Test Case | Input | Expected Result |
|---|-----------|-------|-----------------|
| 1 | No keywords configured | Click Scan with empty textarea | "Please add at least one keyword" |
| 2 | Non-Facebook page | Click Scan on google.com | "Please open Facebook first" |
| 3 | Save keywords (newline) | "pune\nfemale\n2bhk" | Keywords saved: 3 |
| 4 | Save keywords (comma) | "pune, female, 2bhk" | Keywords saved: 3 |
| 5 | Duplicate keywords | "pune\npune\nPUNE" | Keywords saved: 1 (deduplicated) |
| 6 | Scan with common keyword | "the" | Finds multiple posts immediately |
| 7 | Scan with rare keyword | "xyzabc123" | Scrolls 60s, shows "No matching posts" |
| 8 | Scan finds match | "pune" on Pune housing group | Shows results with yellow badges |
| 9 | "See more" posts | Post with truncated text containing keyword | Expanded and matched |
| 10 | Open Post link | Click "Open Post" | Opens Facebook post in new tab |
| 11 | Results persistence | Close popup → reopen | Previous results still visible |
| 12 | Clear all | Click "Clear Keywords" | Keywords + results gone |
| 13 | Infinite scroll | Keyword not on first page | Keeps scrolling until found or timeout |

### Integration Tests

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| 1 | Full flow | Install → Save keywords → Open FB group → Scan → View results → Open post | End-to-end success |
| 2 | Extension reload | Reload extension → Refresh FB → Scan | Works without issues |
| 3 | Multiple scans | Scan once → Scan again with new keywords | New results replace old |
| 4 | Large page | Open FB group with 100+ posts → Scan | Handles without crashing |

---

## Interview Q&A

### Architecture & Design

**Q: What problem does this solve?**
> Helps users find specific posts (like house rentals) on Facebook without manually scrolling through hundreds of posts. Automates keyword-based search with filtering.

**Q: Why a Chrome Extension and not a web app?**
> A Chrome Extension can directly access the Facebook page DOM. A web app would need Facebook API access (restricted/deprecated for scraping) or proxy servers. The extension reads only what the user already has access to — no API keys needed.

**Q: Why Manifest V3 instead of V2?**
> Manifest V2 is deprecated since 2023. V3 is required for new extensions. It introduces: stricter permission model, service workers instead of background pages, better security via declarativeNetRequest, and improved performance.

**Q: Why vanilla JavaScript instead of React/Vue?**
> For an MVP, vanilla JS is simpler — no build step, no bundler, smaller file size, faster load. Extension popups need to open instantly. A framework adds complexity without benefit at this scale.

---

### Technical Implementation

**Q: How does popup communicate with the Facebook page?**
> Chrome's message passing API. `popup.js` calls `chrome.tabs.sendMessage()` to send a message to the content script. `content.js` receives it via `chrome.runtime.onMessage.addListener()` and replies with `sendResponse()`.

**Q: Why `return true` in the message listener?**
> It tells Chrome to keep the message channel open for asynchronous responses. Our scan involves scrolling (async setTimeout loops), so `sendResponse` is called later. Without `return true`, Chrome would close the channel immediately.

**Q: How do you detect Facebook posts in the DOM?**
> We use `document.querySelectorAll('div[dir="auto"], span[dir="auto"]')`. Facebook wraps all user-generated text in elements with `dir="auto"` for bidirectional text support. This is more stable than class names which Facebook obfuscates and changes frequently.

**Q: Why not use Facebook's Graph API?**
> Graph API requires app review, user access tokens, and has strict rate limits. It's meant for app developers, not personal tools. Our approach works with content the user can already see — no auth needed, no rate limits, privacy-compliant.

**Q: How do you handle the "See more" truncation?**
> Before scanning text, we find all elements with `role="button"` containing "See more" text and programmatically `.click()` them. This expands the full post content, ensuring keywords hidden in truncated text are found.

**Q: How does infinite scroll work?**
> A recursive `tick()` function: scroll → wait 2s → scan → if no match, call `tick()` again. Stops when: keywords matched, or 60-second timeout reached. Uses `window.scrollTo(0, document.body.scrollHeight)` to trigger Facebook's lazy loading.

**Q: How do you find the URL for a specific post?**
> Walk UP the DOM tree from the text node (up to 15 parent levels). At each level, look for `<a href>` tags with patterns like `/posts/`, `/permalink/`, `pfbid`, or timestamp links. Timestamp links (e.g., "2h ago") always point to the individual post permalink.

**Q: How is deduplication handled?**
> Using a `Set` with post URL as the unique key. If URL is not specific (falls back to page URL), we use the first 80 characters of text as a fingerprint. Set provides O(1) duplicate checking.

---

### Storage & Persistence

**Q: Why chrome.storage.local instead of localStorage?**
> `localStorage` in a content script belongs to facebook.com (not our extension). `chrome.storage.local` is scoped to the extension, accessible from both popup and content scripts, supports 10MB, and persists across sessions.

**Q: What data do you store?**
> Only two things: `keywords` (array of strings) and `savedResults` (array of matched post objects with text, URL, and matched keywords). No Facebook user data, no credentials, no tracking.

**Q: How do results persist?**
> After every successful scan, results are saved to `chrome.storage.local`. When popup opens, `loadStoredResults()` reads from storage and displays them. Results stay until user clicks "Clear Keywords".

---

### Security & Privacy

**Q: Does this violate Facebook's Terms of Service?**
> This is a gray area. The extension only reads content the user can already see — it doesn't bypass authentication, access private data, or use automated accounts. It's similar to using Ctrl+F on a page, but smarter.

**Q: How do you prevent XSS attacks?**
> All post text displayed in the popup is escaped via `escapeHtml()` which uses `document.createElement('div').textContent = text` to sanitize HTML entities before rendering.

**Q: What permissions does the extension need and why?**
> - `storage`: Save keywords and results locally
> - `tabs`: Know which tab is active and send messages to it
> - `scripting`: Inject content script into Facebook pages
> - `host_permissions` for facebook.com: Allow content script to run

---

### Scalability & Future

**Q: How would you scale this?**
> 1. **Background service worker** — periodic scanning without user clicking
> 2. **Push notifications** — alert when new matching posts found
> 3. **Backend server** — aggregate results, share across devices
> 4. **ML/NLP matching** — understand intent, not just keywords
> 5. **Multi-platform** — support Instagram, Twitter, marketplace sites

**Q: What if Facebook changes their DOM?**
> `dir="auto"` is an HTML standard attribute unlikely to change. But if detection breaks, only `getPagePosts()` needs updating — the rest of the code (matching, scrolling, storage) is decoupled. Modular architecture makes maintenance easy.

**Q: How would you add notifications?**
> Add a background service worker that periodically runs the scan (using `chrome.alarms` API). When new matches are found that weren't in previous results, fire `chrome.notifications.create()` to show a desktop notification.

---

## Limitations & Future Scope

### Current Limitations

| Limitation | Reason |
|-----------|--------|
| Only works on Facebook in the browser | Chrome Extension constraint |
| 60-second timeout per scan | Prevents infinite resource usage |
| Simple substring matching | MVP — not semantic/NLP |
| Depends on `dir="auto"` selector | Could break if Facebook removes it |
| No background scanning | Requires user to click "Scan" |
| No notifications | Not implemented in MVP |
| Single device | No cloud sync |

### Future Enhancements

| Feature | Priority | Complexity |
|---------|----------|-----------|
| Background periodic scanning | High | Medium |
| Desktop notifications | High | Low |
| Regex/advanced matching | Medium | Low |
| Dark mode | Low | Low |
| Export results as CSV | Medium | Low |
| Multi-platform (Instagram, Twitter) | High | High |
| Cloud sync across devices | Medium | High |
| ML-based post classification | Low | High |
| Auto-reply/auto-comment | Low | High (risky) |
| Bookmark/favorite posts | Medium | Low |

---

## Tech Stack Summary

| Technology | Purpose |
|-----------|---------|
| Chrome Extension Manifest V3 | Extension framework |
| Vanilla JavaScript (ES5/ES6) | All application logic |
| HTML5 | Popup UI structure |
| CSS3 | Popup styling & animations |
| Chrome Storage API | Persistent local data |
| Chrome Tabs API | Tab detection & messaging |
| Chrome Scripting API | Content script injection |
| DOM APIs | querySelectorAll, scrollTo, click() |
| Message Passing (IPC) | Popup ↔ Content Script communication |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Aug 2026 | Initial MVP — keyword storage, scanning, results display |
| 1.1.0 | Aug 2026 | Added infinite scroll, "See more" expansion |
| 1.2.0 | Aug 2026 | Added result persistence, comma-separated keywords |
| 1.3.0 | Aug 2026 | Fixed post URL detection (pfbid, timestamps) |

---

*Last Updated: 26 August 2026*
