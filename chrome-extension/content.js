var currentScan = null; // { stop: boolean } while a scan is running

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'SCAN_PAGE') {
        handleScanRequest(request.keywords, request.mode || 'any', sendResponse);
        return true;
    }
    if (request.type === 'STOP_SCAN') {
        if (currentScan) currentScan.stop = true;
        sendResponse({ ok: true });
        return false;
    }
});

function handleScanRequest(keywords, mode, sendResponse) {
    // If a scan is already running, cancel it first
    if (currentScan) currentScan.stop = true;

    // Reset saved state and mark as scanning so the popup can show live progress
    try {
        chrome.storage.local.set({ scanState: 'scanning', savedResults: [] });
    } catch (e) {}

    scrollUntilFoundOrTimeout(keywords, 120000, mode)
        .then((result) => {
            try {
                chrome.storage.local.set({ scanState: 'idle', savedResults: result.posts });
            } catch (e) {}
            sendResponse({ success: true, posts: result.posts, reason: result.reason });
        })
        .catch((error) => {
            try {
                chrome.storage.local.set({ scanState: 'idle' });
            } catch (e) {}
            sendResponse({ success: false, error: error.message });
        });
}

function scrollUntilFoundOrTimeout(keywords, maxTimeout, mode) {
    var matchMode = mode === 'all' ? 'all' : 'any';
    return new Promise((resolve) => {
        var scan = { stop: false };
        currentScan = scan;

        var scrollCount = 0;
        var noGrowCount = 0;
        var lastHeight = getPageHeight();
        var startTime = Date.now();
        var collected = Object.create(null); // dedupe map: key -> post
        var collectedVersion = 0;
        var lastPublishedVersion = -1;

        function tick() {
            if (scan.stop) return finish('stopped');

            var elapsed = Date.now() - startTime;

            if (elapsed > maxTimeout) {
                console.log('⏱️ Timeout reached after ' + scrollCount + ' scrolls');
                return finish('timeout');
            }

            var beforeHeight = getPageHeight();
            doScroll();
            scrollCount++;

            // Click all "See more" buttons to expand hidden post text
            clickAllSeeMore();

            setTimeout(function() {
                if (scan.stop) return finish('stopped');

                // Collect matches on every tick — don't stop at the first find
                collectMatches();
                publishProgress();

                var afterHeight = getPageHeight();
                var grew = afterHeight > beforeHeight + 20;

                console.log(
                    '📜 Scroll ' + scrollCount +
                    ' | height ' + beforeHeight + ' → ' + afterHeight +
                    ' | matches so far: ' + Object.keys(collected).length +
                    ' (' + (elapsed / 1000).toFixed(1) + 's)'
                );

                if (grew) {
                    noGrowCount = 0;
                    lastHeight = afterHeight;
                } else {
                    noGrowCount++;
                    // Nudge — sometimes Facebook needs a small upward scroll to trigger
                    // the intersection observer that loads the next page.
                    doNudge();
                }

                // If the page has stopped growing for several ticks AND we already
                // have some matches, we're done. Otherwise keep trying until timeout.
                if (noGrowCount >= 6 && Object.keys(collected).length > 0) {
                    return finish('end-of-feed-with-matches');
                }
                if (noGrowCount >= 12) {
                    return finish('end-of-feed');
                }

                tick();
            }, 1500);
        }

        function collectMatches() {
            var posts = getPagePosts();
            var matched = matchPosts(posts, keywords, matchMode);
            var changed = false;
            for (var i = 0; i < matched.length; i++) {
                var m = matched[i];
                var key = (m.url && m.url !== window.location.href)
                    ? m.url
                    : m.text.substring(0, 80);

                // Keep the longest version — once "See more" has been clicked,
                // the expanded text replaces the earlier truncated capture.
                var existing = collected[key];
                if (!existing || m.text.length > existing.text.length) {
                    collected[key] = m;
                    changed = true;
                }
            }
            if (changed) collectedVersion++;
        }

        function currentPostsArray() {
            var results = [];
            for (var k in collected) results.push(collected[k]);
            return results;
        }

        function publishProgress() {
            if (collectedVersion === lastPublishedVersion) return; // nothing new
            lastPublishedVersion = collectedVersion;
            try {
                chrome.storage.local.set({ savedResults: currentPostsArray() });
            } catch (e) {}
        }

        function finish(reason) {
            if (currentScan === scan) currentScan = null;
            collectMatches();
            var results = currentPostsArray();
            console.log('🏁 Finish: ' + reason + ' | total matches: ' + results.length);
            resolve({ posts: results, scrollCount: scrollCount, reason: reason });
        }

        tick();
    });
}

/**
 * Total scrollable height across all likely containers.
 */
function getPageHeight() {
    var h = 0;
    if (document.scrollingElement) h = Math.max(h, document.scrollingElement.scrollHeight);
    if (document.documentElement) h = Math.max(h, document.documentElement.scrollHeight);
    if (document.body) h = Math.max(h, document.body.scrollHeight);

    var feed = document.querySelector('[role="feed"]');
    if (feed) h = Math.max(h, feed.scrollHeight);

    // Facebook sometimes wraps the feed in a scrollable main
    var main = document.querySelector('div[role="main"]');
    if (main) h = Math.max(h, main.scrollHeight);

    return h;
}

/**
 * Scroll every plausible container to the bottom.
 * Facebook may put the scrollbar on window, documentElement, an inner div, or role="feed".
 */
function doScroll() {
    var target = getPageHeight();

    // Window / document scroll
    try { window.scrollTo(0, target); } catch (e) {}
    try { if (document.scrollingElement) document.scrollingElement.scrollTop = target; } catch (e) {}
    try { if (document.documentElement) document.documentElement.scrollTop = target; } catch (e) {}
    try { if (document.body) document.body.scrollTop = target; } catch (e) {}

    // Scroll the last item of the feed into view — most reliable on modern Facebook
    var feed = document.querySelector('[role="feed"]');
    if (feed) {
        try { feed.scrollTop = feed.scrollHeight; } catch (e) {}
        var last = feed.lastElementChild;
        if (last && last.scrollIntoView) {
            try { last.scrollIntoView({ block: 'end', behavior: 'auto' }); } catch (e) {}
        }
    }

    // Any explicitly scrollable div under main that has overflow set
    var scrollers = document.querySelectorAll('div[role="main"] [style*="overflow"]');
    for (var i = 0; i < scrollers.length; i++) {
        try { scrollers[i].scrollTop = scrollers[i].scrollHeight; } catch (e) {}
    }
}

/**
 * Small upward nudge, then back down — helps kick Facebook's lazy-loader
 * when the page appears stuck at the bottom.
 */
function doNudge() {
    try { window.scrollBy(0, -400); } catch (e) {}
    var feed = document.querySelector('[role="feed"]');
    if (feed) {
        try { feed.scrollTop = Math.max(0, feed.scrollTop - 400); } catch (e) {}
    }
    setTimeout(function() {
        doScroll();
    }, 150);
}

/**
 * Return true if this element's visible text is a "See more" style expander.
 * Handles: "See more", "See More", "Show more", "See more…", "…more", "… more",
 * "...more", "more". Guards against catching arbitrary body text by requiring
 * the trimmed label to be short.
 */
function isSeeMoreLabel(el) {
    var t = (el.innerText || el.textContent || '').trim();
    if (!t) return false;
    if (t.length > 25) return false; // real post text is longer

    var lower = t.toLowerCase();
    if (lower === 'see more' || lower === 'show more') return true;
    if (lower === 'see more…' || lower === 'see more...') return true;
    if (lower === '…more' || lower === '… more') return true;
    if (lower === '...more' || lower === '... more') return true;
    if (lower === 'more') return true;
    return false;
}

/**
 * Return true if the element is a UI action we should NOT click (translation,
 * comment expander, "See less", etc.).
 */
function isSeeMoreExcluded(el) {
    var t = (el.innerText || el.textContent || '').trim().toLowerCase();
    if (!t) return true;
    if (t.indexOf('see translation') !== -1) return true;
    if (t.indexOf('see less') !== -1) return true;
    if (t.indexOf('view previous') !== -1) return true;
    if (t.indexOf('view more comments') !== -1) return true;
    if (t.indexOf('most relevant') !== -1) return true;
    return false;
}

function clickAllSeeMore() {
    var clicked = 0;

    // 1) Any role="button" whose label reads as a "See more" expander.
    var buttons = document.querySelectorAll('[role="button"]');
    for (var i = 0; i < buttons.length; i++) {
        var b = buttons[i];
        if (b.dataset && b.dataset.__seeMoreClicked) continue;
        if (isSeeMoreExcluded(b)) continue;
        if (!isSeeMoreLabel(b)) continue;

        try {
            b.click();
            if (b.dataset) b.dataset.__seeMoreClicked = '1';
            clicked++;
        } catch (e) {}
    }

    // 2) Inline spans / anchors embedded in a post's text block (dir="auto").
    //    Facebook sometimes renders "…more" as a plain span inside the truncated
    //    text rather than as a proper role="button".
    var inlines = document.querySelectorAll('div[dir="auto"] span, div[dir="auto"] a, span[dir="auto"] span');
    for (var j = 0; j < inlines.length; j++) {
        var el = inlines[j];
        if (el.dataset && el.dataset.__seeMoreClicked) continue;
        if (isSeeMoreExcluded(el)) continue;
        if (!isSeeMoreLabel(el)) continue;

        try {
            el.click();
            if (el.dataset) el.dataset.__seeMoreClicked = '1';
            clicked++;
        } catch (e) {}
    }

    if (clicked > 0) {
        console.log('👆 Expanded ' + clicked + ' "See more" element(s)');
    }
    return clicked;
}
function getPagePosts() {
    var posts = [];
    var seenTexts = new Set();

    // Facebook uses dir="auto" for all user-generated text content
    var textNodes = document.querySelectorAll('div[dir="auto"], span[dir="auto"]');

    for (var i = 0; i < textNodes.length; i++) {
        var node = textNodes[i];
        var text = (node.innerText || '').trim();

        // Only keep substantial text (real post content, not UI buttons)
        if (text.length >= 20 && text.length <= 20000) {
            // Skip common UI patterns
            if (isUIText(text)) continue;

            // Deduplicate
            var key = text.substring(0, 100);
            if (seenTexts.has(key)) continue;
            seenTexts.add(key);

            var url = findNearestPostUrl(node);
            posts.push({ text: text, url: url });
        }
    }

    console.log('🔎 Found ' + posts.length + ' text blocks on page');
    return posts;
}

function isUIText(text) {
    var t = text.trim();
    if (t.length > 100) return false; // Long text is probably a post
    var uiWords = [
        'Like', 'Comment', 'Share', 'Save', 'Delete', 'Edit', 'Report', 'Hide',
        'Log Out', 'Log In', 'Sign Up', 'Settings', 'Privacy', 'Terms',
        'Marketplace', 'Watch', 'Gaming', 'Groups', 'Events',
        'Notifications', 'Messages', 'Menu', 'Search Facebook',
        'Write a comment', 'Create a story', 'See more', 'See less'
    ];
    for (var i = 0; i < uiWords.length; i++) {
        if (t === uiWords[i]) return true;
    }
    return false;
}

function findNearestPostUrl(node) {
    var current = node;
    for (var i = 0; i < 15; i++) {
        if (!current || !current.parentElement) break;
        current = current.parentElement;

        var links = current.querySelectorAll('a[href]');
        for (var j = 0; j < links.length; j++) {
            var href = links[j].getAttribute('href') || '';
            
            // Skip empty or javascript links
            if (!href || href === '#' || href.indexOf('javascript:') === 0) continue;

            // Check for post-like URLs
            if (
                href.indexOf('/posts/') !== -1 ||
                href.indexOf('/permalink/') !== -1 ||
                href.indexOf('/photo/') !== -1 ||
                href.indexOf('/photos/') !== -1 ||
                href.indexOf('/videos/') !== -1 ||
                href.indexOf('/reel/') !== -1 ||
                href.indexOf('/watch/') !== -1 ||
                href.indexOf('story_fbid') !== -1 ||
                href.indexOf('pfbid') !== -1 ||
                href.indexOf('/groups/') !== -1 && href.match(/\/\d{5,}/)
            ) {
                if (href.charAt(0) === '/') {
                    return 'https://www.facebook.com' + href;
                }
                return href;
            }

            // Facebook timestamp links (e.g. "2h ago", "August 12") always point to the post
            var ariaLabel = links[j].getAttribute('aria-label') || '';
            var linkText = (links[j].innerText || '').trim();
            var isTimestamp = linkText.match(/^\d+\s*(h|m|d|w|hr|min|sec|hour|minute|day|week|month|year)/i) ||
                             linkText.match(/^(January|February|March|April|May|June|July|August|September|October|November|December)/i) ||
                             linkText.match(/^\d+\s+(August|September|October)/i) ||
                             linkText.match(/^(Yesterday|Just now)/i) ||
                             ariaLabel.match(/\d+\s*(hour|minute|day|week|month|year)/i);

            if (isTimestamp && href.indexOf('facebook.com') !== -1) {
                if (href.charAt(0) === '/') {
                    return 'https://www.facebook.com' + href;
                }
                return href;
            }
        }
    }
    return window.location.href;
}

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

function matchPosts(posts, keywords, mode) {
    var isAll = mode === 'all';
    var results = [];
    for (var i = 0; i < posts.length; i++) {
        var matched = findMatchingKeywords(posts[i].text, keywords);
        var qualifies = isAll
            ? (matched.length === keywords.length && keywords.length > 0)
            : (matched.length > 0);
        if (qualifies) {
            results.push({
                text: posts[i].text.substring(0, 500),
                matchedKeywords: matched,
                url: posts[i].url
            });
        }
    }
    return results;
}

function deduplicatePosts(posts) {
    var seen = new Set();
    var unique = [];
    for (var i = 0; i < posts.length; i++) {
        var key = posts[i].url !== window.location.href ? posts[i].url : posts[i].text.substring(0, 80);
        if (!seen.has(key)) {
            seen.add(key);
            unique.push(posts[i]);
        }
    }
    return unique;
}
