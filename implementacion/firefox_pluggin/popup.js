document.addEventListener('DOMContentLoaded', function () {
  const resultElement = document.getElementById('result');
  const statusIcon = document.getElementById('statusIcon');
  const analyzeButton = document.getElementById('analyzeButton');

  function updateResult(data) {
    if (data.malicious) {
      statusIcon.innerHTML = '<i class="fas fa-exclamation-circle malicious"></i>';
      resultElement.innerText = `La url ${data.url} es maliciosa con una probabilidad del ${data.probability.toFixed(2)}% de ser maliciosa. `;
    } else {
      statusIcon.innerHTML = '<i class="fas fa-check-circle benign"></i>';
      resultElement.innerText = `La url ${data.url} es benigna con una probabilidad del ${data.probability.toFixed(2)}% de ser maliciosa.`;
    }
  }

  // Obtener la información del análisis desde el storage
  chrome.storage.local.get(['analyzedData'], (result) => {
    const data = result.analyzedData;
    if (data) {
      updateResult(data);
    } else {
      resultElement.innerText = 'No analysis data available.';
    }
  });

  analyzeButton.addEventListener('click', function () {
    chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
      const currentTab = tabs[0];
      console.log('Manual analysis for URL:', currentTab.url);

      fetch('http://localhost:5000/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: currentTab.url })
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
          }
          return response.json();
        })
        .then((data) => {
          console.log('Response Data:', data);
          const analysisData = { ...data, analysisType: 'manual' };
          updateResult(analysisData);
          chrome.storage.local.set({ analyzedData: analysisData });
        })
        .catch((error) => {
          console.error('Error:', error);
          resultElement.innerText = 'Error analyzing the URL. Please try again.';
        });
    });
  });
});
