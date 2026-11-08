async function fetchOverviewData() {
  try {
    let response = await fetch("/api/questions");
    let questions = await response.json();

    // Sorteer de puzzels op populariteit (meeste oplossers bovenaan)
    questions.sort((a, b) => {
      if (b.aantal !== a.aantal) {
        return b.aantal - a.aantal;
      }
      return a.nummer - b.nummer; // Als het gelijk is op puzzelnummer
    });

    let table = document.getElementById("overview-body");
    table.innerHTML = "";

    questions.forEach(q => {
      let voortgangHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <div class="progress-bar-container">
                <div class="progress-bar-fill" style="width: ${q.percentage}%;"></div>
            </div>
            <span>${q.percentage}% (${q.aantal})</span>
        </div>
      `;

      table.innerHTML += "<tr>" +
        "<td><strong>" + q.number + "</strong></td>" +
        "<td>" + voortgangHTML + "</td>" +
        "<td>" + q.people + "</td>" +
      "</tr>";
    });
    
  } catch (error) {
    console.error("Fout bij ophalen van gegevens:", error);
  }
}

fetchOverviewData();