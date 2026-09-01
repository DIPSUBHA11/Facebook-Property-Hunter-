/**
 * Facebook Property Hunter — Popup Script
 * Handles UI interactions and keyword management
 */

// ============================================================================
// DOM Elements
// ============================================================================

const keywordInput = document.getElementById('keywordInput');
const saveBtn = document.getElementById('saveBtn');
const scanBtn = document.getElementById('scanBtn');
const stopBtn = document.getElementById('stopBtn');
const clearBtn = document.getElementById('clearBtn');
const keywordCount = document.getElementById('keywordCount');
const statusMessage = document.getElementById('statusMessage');
const resultsSection = document.getElementById('resultsSection');
const resultsList = document.getElementById('resultsList');
const resultCount = document.getElementById('resultCount');
const loadingIndicator = document.getElementById('loadingIndicator');
const emptyState = document.getElementById('emptyState');
const modeAnyBtn = document.getElementById('modeAny');
const modeAllBtn = document.getElementById('modeAll');
const modeHint = document.getElementById('modeHint');

let isScanning = false;
let matchMode = 'any'; // 'any' (OR) | 'all' (AND)

/**
 * Initialize popup on load
 */
document.addEventListener('DOMContentLoaded', () => {
    loadStoredKeywords();
    loadStoredMode();
    restoreScanState();
    attachEventListeners();
    attachStorageListener();
});

// ============================================================================
// Event Listeners
// ============================================================================

/**
 * Attach event listeners to buttons
 */
function attachEventListeners() {
    saveBtn.addEventListener('click', handleSaveKeywords);
    scanBtn.addEventListener('click', handleScanPage);
    stopBtn.addEventListener('click', handleStopScan);
    clearBtn.addEventListener('click', handleClearKeywords);
    modeAnyBtn.addEventListener('click', () => setMatchMode('any'));
    modeAllBtn.addEventListener('click', () => setMatchMode('all'));
}

/**
 * Load persisted match mode.
 */
function loadStoredMode() {
    chrome.storage.local.get('matchMode', (data) => {
        const mode = data.matchMode === 'all' ? 'all' : 'any';
        applyMatchMode(mode, /* persist */ false);
    });
}

/**
 * Change match mode, persist it, and update the UI.
 */
function setMatchMode(mode) {
    applyMatchMode(mode, /* persist */ true);
}

function applyMatchMode(mode, persist) {
    matchMode = mode === 'all' ? 'all' : 'any';

    modeAnyBtn.classList.toggle('is-active', matchMode === 'any');
    modeAllBtn.classList.toggle('is-active', matchMode === 'all');
    modeAnyBtn.setAttribute('aria-selected', matchMode === 'any' ? 'true' : 'false');
    modeAllBtn.setAttribute('aria-selected', matchMode === 'all' ? 'true' : 'false');

    if (modeHint) {
        if (matchMode === 'all') {
            modeHint.innerHTML = 'One keyword per line or comma-separated. <strong>All</strong>: match posts containing every keyword.';
        } else {
            modeHint.innerHTML = 'One keyword per line or comma-separated. <strong>Any</strong>: match posts containing at least one keyword.';
        }
    }

    if (persist) {
        chrome.storage.local.set({ matchMode });
    }
}

/**
 * Watch chrome.storage for live scan progress and state changes.
 */
function attachStorageListener() {
    chrome.storage.onChanged.addListener((changes, area) => {
        if (area !== 'local') return;

        if (changes.scanState) {
            setScanningUI(changes.scanState.newValue === 'scanning');
        }

        if (changes.savedResults) {
            chrome.storage.local.get(['keywords', 'scanState'], (data) => {
                const posts = changes.savedResults.newValue || [];
                const scanning = data.scanState === 'scanning';
                displayResults(posts, data.keywords || [], scanning);
            });
        }
    });
}

/**
 * Restore UI state on popup open — spinner if a scan is in progress, results if any.
 */
function restoreScanState() {
    chrome.storage.local.get(['savedResults', 'keywords', 'scanState'], (data) => {
        const posts = data.savedResults || [];
        const keywords = data.keywords || [];
        const scanning = data.scanState === 'scanning';
        setScanningUI(scanning);
        if (posts.length > 0) {
            displayResults(posts, keywords, scanning);
        }
    });
}

/**
 * Toggle UI between idle and scanning states.
 */
function setScanningUI(scanning) {
    isScanning = scanning;
    if (scanning) {
        loadingIndicator.classList.remove('hidden');
        scanBtn.classList.add('hidden');
        stopBtn.classList.remove('hidden');
        saveBtn.disabled = true;
        clearBtn.disabled = true;
    } else {
        loadingIndicator.classList.add('hidden');
        scanBtn.classList.remove('hidden');
        stopBtn.classList.add('hidden');
        saveBtn.disabled = false;
        clearBtn.disabled = false;
    }
}

/**
 * Handle Save Keywords button click
 */
function handleSaveKeywords() {
    const rawKeywords = keywordInput.value;
    const keywords = parseKeywords(rawKeywords);

    if (keywords.length === 0) {
        showStatusMessage('Please enter at least one keyword.', 'error');
        return;
    }

    // Save to Chrome Storage
    chrome.storage.local.set({ keywords }, () => {
        showStatusMessage('Keywords saved successfully!', 'success');
        updateKeywordCount(keywords);
        clearResults();
    });
}

/**
 * Handle Hunt Now button click. The content script drives the scroll and streams
 * results into chrome.storage; our storage listener renders them live.
 */
async function handleScanPage() {
    const { keywords = [] } = await chrome.storage.local.get('keywords');

    if (keywords.length === 0) {
        showStatusMessage('Please add at least one keyword.', 'error');
        return;
    }

    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab || !tab.url || !tab.url.includes('facebook.com')) {
        showStatusMessage('Please open Facebook in the active tab first.', 'error');
        return;
    }

    setScanningUI(true);
    clearResults();
    showStatusMessage('Hunting for matches — you can watch results appear below.', 'info');

    chrome.tabs.sendMessage(tab.id, { type: 'SCAN_PAGE', keywords, mode: matchMode }, (response) => {
        if (chrome.runtime.lastError) {
            console.error('Chrome error:', chrome.runtime.lastError);
            setScanningUI(false);
            showStatusMessage(
                'Could not reach the Facebook page. Refresh the tab and try again.',
                'error'
            );
            return;
        }

        if (!response) return; // storage listener already reflects state

        if (response.success) {
            const reason = response.reason || '';
            const count = response.posts ? response.posts.length : 0;
            if (reason === 'stopped') {
                showStatusMessage(`Stopped. ${count} match${count === 1 ? '' : 'es'} found.`, 'info');
            } else if (count === 0) {
                showStatusMessage('Scan complete. No matching posts found.', 'info');
            } else {
                showStatusMessage(`Scan complete. ${count} match${count === 1 ? '' : 'es'} found.`, 'success');
            }
        } else {
            showStatusMessage(
                response.error || 'Unable to scan this page. Refresh Facebook and try again.',
                'error'
            );
        }
    });
}

/**
 * Handle Stop button click — asks the content script to end the current scan.
 * Also flips scanState locally so the UI recovers even if the content script
 * is stale (e.g. Facebook tab wasn't refreshed after reloading the extension)
 * and never receives the STOP_SCAN message.
 */
async function handleStopScan() {
    stopBtn.disabled = true;
    showStatusMessage('Stopping scan…', 'info');

    // 1) Immediately mark idle so the spinner disappears even if step 2 fails.
    //    Update the UI synchronously; the storage.onChanged listener would get
    //    there eventually but there's a small delay before it fires.
    setScanningUI(false);
    chrome.storage.local.set({ scanState: 'idle' });

    // 2) Best-effort: tell the content script to abort its scroll loop.
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tab) {
            chrome.tabs.sendMessage(tab.id, { type: 'STOP_SCAN' }, () => {
                if (chrome.runtime.lastError) {
                    console.warn(
                        '[Property Hunter] STOP_SCAN could not reach the content script — ' +
                        'the Facebook tab may still be running an old scroll loop. ' +
                        'Refresh the Facebook tab to fully stop it.',
                        chrome.runtime.lastError.message
                    );
                    showStatusMessage(
                        'Stopped. If the page keeps scrolling, refresh the Facebook tab.',
                        'info'
                    );
                }
            });
        }
    } finally {
        setTimeout(() => { stopBtn.disabled = false; }, 500);
    }
}

/**
 * Handle Clear Keywords button click
 */
function handleClearKeywords() {
    if (confirm('Are you sure you want to clear all keywords and results?')) {
        chrome.storage.local.set({ keywords: [], savedResults: [] }, () => {
            keywordInput.value = '';
            updateKeywordCount([]);
            clearResults();
            showStatusMessage('Keywords and results cleared.', 'info');
        });
    }
}

// ============================================================================
// Keyword Management
// ============================================================================

/**
 * Parse raw keyword input into normalized array
 * @param {string} rawInput - Raw textarea input
 * @returns {string[]} Normalized keywords array
 */
function parseKeywords(rawInput) {
    return rawInput
        .split(/[\n,]+/)
        .map(keyword => keyword.trim())
        .filter(keyword => keyword.length > 0)
        .filter((keyword, index, array) => array.indexOf(keyword) === index); // Remove duplicates
}

/**
 * Load stored keywords from Chrome Storage
 */
function loadStoredKeywords() {
    chrome.storage.local.get('keywords', (data) => {
        const keywords = data.keywords || [];
        
        // Populate textarea
        keywordInput.value = keywords.join('\n');
        
        // Update count
        updateKeywordCount(keywords);
    });
}

/**
 * Update keyword count display
 * @param {string[]} keywords - Array of keywords
 */
function updateKeywordCount(keywords) {
    if (keywords.length === 0) {
        keywordCount.textContent = 'No keywords';
        keywordCount.className = 'pill pill-muted';
    } else {
        keywordCount.textContent = `${keywords.length} saved`;
        keywordCount.className = 'pill pill-active';
    }
}

// ============================================================================
// Results Display
// ============================================================================

/**
 * Display scan results in popup.
 * @param {Object[]} posts - Matching posts (may be empty)
 * @param {string[]} keywords - Original keywords searched
 * @param {boolean} scanning - True if a scan is currently running
 */
function displayResults(posts, keywords, scanning = false) {
    const count = posts.length;

    if (count === 0) {
        resultCount.textContent = scanning ? 'searching…' : '0 posts';
        resultsList.innerHTML = '';

        if (scanning) {
            // Hide empty-state during scan; results will stream in.
            if (emptyState) emptyState.classList.add('hidden');
            resultsSection.classList.add('hidden');
        } else {
            if (emptyState) emptyState.classList.remove('hidden');
            resultsSection.classList.remove('hidden');
        }
        return;
    }

    resultCount.textContent = `${count} post${count !== 1 ? 's' : ''}${scanning ? ' · live' : ''}`;

    resultsList.innerHTML = '';
    if (emptyState) emptyState.classList.add('hidden');

    posts.forEach((post, index) => {
        const postElement = createPostElement(post, index);
        resultsList.appendChild(postElement);
    });

    resultsSection.classList.remove('hidden');
}

/**
 * Create HTML element for a matching post
 * @param {Object} post - Post object with text, matchedKeywords, url
 * @param {number} index - Post index
 * @returns {HTMLElement} Post element
 */
function createPostElement(post, index) {
    const postDiv = document.createElement('div');
    postDiv.className = 'post-result';

    // Matched keywords
    const keywordsHtml = post.matchedKeywords
        .map(keyword => `<span class="matched-keyword">${escapeHtml(keyword)}</span>`)
        .join(' ');

    // Post text (truncate if too long)
    const displayText = post.text.length > 200 
        ? post.text.substring(0, 200) + '...' 
        : post.text;

    postDiv.innerHTML = `
        <div class="post-header">
            <div class="matched-keywords">${keywordsHtml}</div>
            <span class="post-number">#${index + 1}</span>
        </div>
        <p class="post-text">${escapeHtml(displayText)}</p>
        <a href="${escapeHtml(post.url)}" target="_blank" rel="noopener noreferrer" class="open-button">View on Facebook</a>
    `;

    return postDiv;
}

/**
 * Clear results display
 */
function clearResults() {
    resultsList.innerHTML = '';
    resultsSection.classList.add('hidden');
    if (emptyState) emptyState.classList.add('hidden');
}

// ============================================================================
// Status Messages
// ============================================================================

/**
 * Show status message
 * @param {string} message - Message text
 * @param {string} type - Message type: 'success', 'error', 'info', 'clear'
 */
function showStatusMessage(message, type) {
    if (type === 'clear') {
        statusMessage.textContent = '';
        statusMessage.className = 'status-message';
        return;
    }

    statusMessage.textContent = message;
    statusMessage.className = `status-message status-${type}`;

    // Auto-clear success and info messages after 4 seconds
    if (type === 'success' || type === 'info') {
        setTimeout(() => {
            statusMessage.textContent = '';
            statusMessage.className = 'status-message';
        }, 4000);
    }
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Escape HTML special characters to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
