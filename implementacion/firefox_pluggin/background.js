const RECENTLY_ANALYZED_URLS_KEY = 'recentlyAnalyzedUrls';
const ANALYSIS_THRESHOLD_MS = 5 * 60 * 1000; // 5 minutos

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url && !tab.url.startsWith('moz-extension://')) {
    shouldAnalyzeUrl(tab.url)
      .then((shouldAnalyze) => {
        if (shouldAnalyze) {
          analyzeUrl(tab.url, 'automatic');
        }
      })
      .catch((error) => {
        console.error('Error checking if URL should be analyzed:', error);
      });
  }
});

function shouldAnalyzeUrl(url) {
  return new Promise((resolve, reject) => {
    chrome.storage.local.get([RECENTLY_ANALYZED_URLS_KEY], (result) => {
      const recentlyAnalyzedUrls = result[RECENTLY_ANALYZED_URLS_KEY] || {};
      const now = Date.now();

      if (recentlyAnalyzedUrls[url] && now - recentlyAnalyzedUrls[url] < ANALYSIS_THRESHOLD_MS) {
        resolve(false);
      } else {
        recentlyAnalyzedUrls[url] = now;
        chrome.storage.local.set({ [RECENTLY_ANALYZED_URLS_KEY]: recentlyAnalyzedUrls }, () => {
          resolve(true);
        });
      }
    });
  });
}

function analyzeUrl(url, analysisType) {
  fetch('http://localhost:5000/predict', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ url })
  })
  .then((response) => {
    if (!response.ok) {
      throw new Error('Network response was not ok ' + response.statusText);
    }
    return response.json();
  })
  .then((data) => {
    console.log(
      `The URL ${data.url} is ${data.malicious ? 'malicious' : 'benign'} with a probability of ${data.probability.toFixed(
        2
      )}% of being malicious.`
    );
    chrome.action.setBadgeText({ text: data.malicious ? '!' : '' });

    chrome.windows.create({
      url: chrome.runtime.getURL('popup.html'),
      type: 'popup',
      width: 400,
      height: 300
    }, (win) => {

      chrome.storage.local.set({ analyzedData: { ...data, analysisType } });
    });
  })
  .catch((error) => {
    console.error('Error analyzing the URL:', error);
  });
}
