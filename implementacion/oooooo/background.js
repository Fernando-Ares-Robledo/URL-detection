chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action == "analyzeUrl") {
    fetch("http://localhost:8501/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ url: request.url })
    })
      .then(response => response.json())
      .then(data => sendResponse(data))
      .catch(error => console.error("Error:", error));
    return true;  // Will respond asynchronously.
  }
});
