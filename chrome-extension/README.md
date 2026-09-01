# Facebook Tracker - Chrome Extension MVP

A minimal Chrome Extension that helps you find Facebook posts matching your keywords.

## Features

- ✅ **Keyword Management**: Add, save, and manage keywords locally
- ✅ **Post Scanning**: Scan current Facebook page for matching posts
- ✅ **Case-Insensitive Matching**: Find keywords regardless of case
- ✅ **Deduplication**: Show each post only once
- ✅ **Direct Post Links**: Open posts directly from the extension
- ✅ **Privacy-First**: All data stored locally, no backend required
- ✅ **No Bypassing**: Respects Facebook's access controls and DOM protections

## Installation

### Step 1: Open Chrome Extensions Page
1. Open **Google Chrome**
2. Go to `chrome://extensions/` in the address bar
3. Press Enter

### Step 2: Enable Developer Mode
- Toggle the **Developer mode** switch in the top-right corner

### Step 3: Load the Extension
1. Click **Load unpacked**
2. Navigate to the `chrome-extension` folder in this project
3. Select and open it
4. The extension should now appear in your Chrome toolbar

### Step 4: Use the Extension
1. Visit any Facebook page
2. Click the **Facebook Tracker** icon in your Chrome toolbar
3. Enter keywords (one per line):
   - `Kharadi`
   - `Tingre Nagar`
   - `Pune flat`
   - `1BHK`
4. Click **Save Keywords**
5. Click **Scan Current Page**
6. View matching posts and click **Open Post** to visit them

## Project Structure

```
chrome-extension/
├── manifest.json       # Extension configuration (Manifest V3)
├── popup.html          # Popup UI
├── popup.js            # Popup logic and event handling
├── content.js          # Facebook page scanning logic
├── style.css           # Styling
└── README.md           # This file
```

## How It Works

### 1. **manifest.json**
- Defines the extension as Manifest V3
- Declares content script for Facebook pages
- Requests minimal permissions: `storage` and `tabs`
- Specifies the popup interface

### 2. **popup.html & popup.js**
- Provides the user interface for entering keywords
- Manages keyword storage using Chrome Storage API
- Sends "Scan" messages to the content script
- Displays results from the scan

### 3. **content.js**
- Runs on Facebook pages only
- Detects posts currently visible/loaded
- Extracts text and URLs from posts
- Matches posts against keywords (case-insensitive)
- Returns deduplicated results

### 4. **style.css**
- Responsive, clean UI
- Dark mode compatible
- Matches Facebook's color scheme

## Usage Guide

### Adding Keywords

1. Click the **Facebook Tracker** icon
2. In the text area, enter keywords (one per line)
3. Click **Save Keywords**
4. The count displays how many keywords you've saved

Example:
```
Kharadi
Tingre Nagar
Keshav Nagar
Pune flat
1BHK
2BHK
```

### Scanning a Page

1. Open any Facebook page (group, profile, etc.)
2. Click the **Facebook Tracker** icon
3. Click **Scan Current Page**
4. Wait for results to load
5. View matching posts with highlighted keywords

### Opening a Post

1. Click **Open Post** on any matching post
2. Facebook opens the post in a new tab

### Clearing Keywords

1. Click **Clear Keywords**
2. Confirm the action
3. All keywords are removed

## Keyword Matching

Matching is **case-insensitive** and uses **substring matching**.

### Examples

Keyword: `Kharadi`

Will match:
- "Looking for a flat in Kharadi"
- "KHARADI 1bhk available"
- "kharadi rent required"
- "apartment near kharadi"

## Limitations (MVP)

### What This Extension Does
- ✅ Scan posts visible on the current Facebook page
- ✅ Match keywords case-insensitively
- ✅ Store keywords locally
- ✅ Deduplicate results
- ✅ Respect Facebook's privacy and access controls

### What This Extension Does NOT Do (Yet)
- ❌ Automatic background scanning
- ❌ Notifications or alerts
- ❌ Database or backend storage
- ❌ Cross-page scanning
- ❌ Private message or group bypass
- ❌ Bypass CAPTCHAs or rate limits
- ❌ Account automation or login

### Facebook DOM Limitations

Facebook's website structure changes frequently. The extension uses:
- Multiple CSS selectors to find posts
- Fallback strategies if selectors change
- Text extraction from various post structures

If the extension stops finding posts after a Facebook update:
1. Open `chrome://extensions`
2. Click the **Reload** button next to Facebook Tracker
3. Try scanning again

If posts still aren't found, the DOM selectors may need updating. Open an issue or contact the developer.

## Development

### Reloading After Changes

After editing any file:
1. Go to `chrome://extensions`
2. Click the **Reload** button next to Facebook Tracker
3. Refresh your Facebook page
4. Test the extension

### Debugging

#### View Console Logs
1. Right-click the Facebook Tracker icon
2. Select **Inspect popup**
3. Go to the **Console** tab
4. Look for debug messages

#### Inspect Content Script
1. Open Facebook
2. Right-click on the page → **Inspect**
3. Go to the **Console** tab
4. Messages from content.js appear here

### Key Functions

**popup.js**
- `handleSaveKeywords()` - Save keywords to storage
- `handleScanPage()` - Send scan message to content script
- `parseKeywords()` - Normalize keyword input
- `displayResults()` - Show matching posts

**content.js**
- `findFacebookPosts()` - Detect post elements on page
- `findMatchingKeywords()` - Match keywords in text
- `deduplicatePosts()` - Remove duplicate posts
- `extractPostUrl()` - Get post URL

## Privacy & Security

- **Local Storage Only**: All keywords stored in Chrome's local storage, never sent to servers
- **No Data Collection**: Extension doesn't collect or track user data
- **No Login Required**: Doesn't require Facebook credentials
- **No Scraping**: Respects Facebook's DOM protections
- **No Bypass**: Doesn't bypass private groups, CAPTCHAs, or access controls

## Permissions Explained

- **`storage`**: Saves keywords locally in the extension's storage
- **`tabs`**: Detects when you click "Scan" to know which Facebook page you're on
- **`https://www.facebook.com/*`**: Allows the content script to run on Facebook pages

## Troubleshooting

### "Please open Facebook first"
- You're on a non-Facebook page
- **Fix**: Navigate to Facebook and try again

### "Please add at least one keyword"
- No keywords are saved
- **Fix**: Enter keywords and click Save Keywords

### "No matching posts found"
- Your keywords don't match any visible posts
- **Fix**: Try different keywords or scroll the page to load more posts

### "Unable to scan this page"
- The content script didn't load or Facebook's structure changed
- **Fix**: 
  1. Refresh the Facebook page
  2. Reload the extension (`chrome://extensions` → Reload button)
  3. Try again

### Posts aren't showing
- Facebook's DOM structure may have changed
- **Fix**:
  1. Reload the extension
  2. Check the browser console for errors
  3. Try with different keywords

## Future Enhancements (Not in MVP)

- [ ] Auto-refresh scanning
- [ ] Email notifications
- [ ] Bookmark matching posts
- [ ] Search history
- [ ] Advanced keyword matching (regex, exact match, etc.)
- [ ] Multiple keyword sets/profiles
- [ ] Dark mode toggle
- [ ] Export results as CSV

## License

This project is open source and available under the MIT License.

## Support

For issues or suggestions, please check:
1. That you're on a Facebook page
2. That at least one keyword is configured
3. That you've refreshed the page and reloaded the extension

---

**Version**: 1.0.0  
**Last Updated**: August 2026
