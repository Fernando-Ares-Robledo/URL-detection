document.getElementById("analyzeBtn").addEventListener("click", function() {
  var url = document.getElementById("urlInput").value;
  analyzeURL(url);
});

function analyzeURL(url) {
  fetch(`http://your-streamlit-server-address/?url=${encodeURIComponent(url)}`)
    .then(response => response.json())
    .then(data => {
      displayResults(data);
    })
    .catch(error => {
      console.error("Error analyzing URL:", error);
      document.getElementById("result").innerText = "Error analyzing URL.";
    });
}

function displayResults(data) {
  var resultDiv = document.getElementById("result");
  resultDiv.innerHTML = "";
  for (var key in data) {
    if (data.hasOwnProperty(key)) {
      var p = document.createElement("p");
      p.innerHTML = `<strong>${key}:</strong> ${data[key]}`;
      resultDiv.appendChild(p);
    }
  }
}
