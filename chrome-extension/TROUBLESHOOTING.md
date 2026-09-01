## 🔧 Troubleshooting: "Unable to scan this page"

This error means the content script isn't communicating with the popup. Follow these steps:

---

## ✅ Step 1: Verify Extension is Loaded

1. Go to `chrome://extensions/`
2. Find "Facebook Tracker"
3. Make sure it says **Enabled** (toggle should be ON)
4. Note the ID shown (e.g., `ilcjhdidghljpmglplheamcoccffpela`)

---

## ✅ Step 2: Verify Content Script is Running on Facebook

1. **Open Facebook** in a tab
2. **Don't** go to the extension popup yet
3. Right-click on the Facebook page
4. Click **Inspect** (or press F12)
5. Go to the **Console** tab
6. Look for messages starting with ✅ or 📨

### You should see:
```
✅ Facebook Tracker content script loaded at 2:30:45 PM
📍 Current URL: https://www.facebook.com/...
📨 Registering message listener...
✅ Message listener registered successfully
```

**If you don't see these messages:**
- Refresh the Facebook page (Cmd+R or F5)
- Wait 2-3 seconds for page to fully load
- Check console again
- If still nothing, the content script isn't loading

---

## ✅ Step 3: Test Connection

If content script loaded (you saw the messages):

1. **Don't close console**
2. Click the extension icon
3. Add keyword: `the`
4. Click **Save Keywords**
5. Click **Scan Current Page**
6. **Watch the console** for these messages:

```
📨 Message received: SCAN_PAGE from chrome-extension://...
🔍 SCAN_PAGE request received
🔍 Scan request received with keywords: ["the"]
⏳ Starting infinite scroll until keywords found...
```

**If you see these messages:** ✅ Extension is working! (Just needs post detection fix)

**If you DON'T see these messages:** ❌ Content script isn't receiving messages

---

## 🐛 If Content Script Didn't Load

### Fix #1: Hard Reload the Extension
1. Go to `chrome://extensions/`
2. Find Facebook Tracker
3. Click the **Reload** button
4. Go back to Facebook
5. **Hard refresh Facebook**: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
6. Wait 3 seconds
7. Check console again

### Fix #2: Clear Cache
1. Fully close Facebook tab
2. Go to `chrome://extensions/`
3. Click **Reload** on Facebook Tracker
4. Open Facebook in a NEW tab
5. Wait for page to load
6. Check console

### Fix #3: Reinstall Extension
1. Go to `chrome://extensions/`
2. Click the trash icon to remove Facebook Tracker
3. Click **Load unpacked**
4. Select the extension folder again
5. Go to Facebook
6. Check console

---

## 🔍 Still Not Working?

Tell me:
1. ✅ Does Facebook Tracker show as "Enabled" in `chrome://extensions/`?
2. ✅ Do you see "content script loaded" in console?
3. ✅ Do you see message listener registered?
4. ✅ Do you see "Message received: SCAN_PAGE"?
5. 🔴 Any RED error messages in console?

Share any red error messages you see!

---

## 📝 Quick Checklist

- [ ] Extension is enabled in chrome://extensions
- [ ] Facebook page fully loaded
- [ ] Console shows "content script loaded"
- [ ] Console shows "Message listener registered"
- [ ] Tried clicking Scan (check console for SCAN_PAGE message)
- [ ] Tried hard refresh (Cmd+Shift+R)
- [ ] Tried reloading extension

---

## 💡 Pro Tip: Developer Console

The **console** is your best friend:
1. Right-click Facebook → Inspect
2. Click **Console** tab
3. Keep it open while testing
4. Look for ✅ (success), 📨 (messages), ❌ (errors)
5. Red text = errors to report

All troubleshooting info will be in the console!
