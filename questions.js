async function fetchOverviewData() {
  try {
    let response = await fetch("/api/questions");
    let questions = await response.json();

    let table = document.getElementById("overview-body");
    table.innerHTML = "";

    questions.forEach(q => {
      // Completion bar
      let voortgangHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <div class="progress-bar-container">
                <div class="progress-bar-fill" style="width: ${q.percentage}%;"></div>
            </div>
            <span>${q.percentage}% (${q.aantal})</span>
        </div>
      `;

      // Update html table
      table.innerHTML += "<tr>" +
        "<td><strong>" + q.number + "</strong></td>" +
        "<td>" + q.punten + " pt</td>" +
        "<td>" + voortgangHTML + "</td>" +
        "<td>" + q.people + "</td>" +
      "</tr>";
    });
    
  } catch (error) {
    console.error("Fout bij ophalen van gegevens:", error);
  }
}

fetchOverviewData();