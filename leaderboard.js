async function fetchTableData() {
  try {
    let qResponse = await fetch("/api/questions");
    let puzzelsLijst = await qResponse.json();
    let totaalPuzzels = puzzelsLijst.length;

    let response = await fetch("/api/deelnemers");
    let personen = await response.json();

    let table = document.getElementById("leaderboard-body");
    table.innerHTML = "";

    personen.forEach(p => {
      let puntenVal = p.score;
      let opgelostVal = p.opgelost;
      let naamVal = p.naam;

      let percentage = totaalPuzzels > 0 
        ? Math.min(100, Math.max(0, ((opgelostVal / totaalPuzzels) * 100))).toFixed(1) 
        : 0;

      let voortgangHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <div class="progress-bar-container">
                <div class="progress-bar-fill" style="width: ${percentage}%;"></div>
            </div>
            <span>${percentage}%</span>
        </div>
      `;

      table.innerHTML += "<tr>" +
        "<td>" + naamVal + "</td>" +
        "<td>" + puntenVal + "</td>" +
        "<td>" + opgelostVal + " / " + totaalPuzzels + "</td>" +
        "<td>" + voortgangHTML + "</td>" +
      "</tr>";
    });

    sortTable();
  } catch (error) {
    console.error("Fout bij ophalen van gegevens:", error);
  }
}

function sortTable() {
  var table, rows, switching, i, x, y, shouldSwitch;
  table = document.getElementById("leaderboard-body");
  switching = true;

  while (switching) {
    switching = false;
    rows = table.rows;

    for (i = 0; i < (rows.length - 1); i++) {
      shouldSwitch = false;
      
      // Kolom 1 = Punten, Kolom 2 = Opgeloste puzzels (breuk zoals "5 / 12")
      let puntenX = parseInt(rows[i].getElementsByTagName("TD")[1].innerText);
      let puntenY = parseInt(rows[i + 1].getElementsByTagName("TD")[1].innerText);

      let opgelostX = parseInt(rows[i].getElementsByTagName("TD")[2].innerText.split("/")[0]);
      let opgelostY = parseInt(rows[i + 1].getElementsByTagName("TD")[2].innerText.split("/")[0]);

      // Sorteer op punten (hoogste eerst)
      if (puntenX < puntenY) {
        shouldSwitch = true;
      } 
      // Tiebreaker: als punten gelijk zijn, sorteer op aantal opgeloste puzzels
      else if (puntenX === puntenY && opgelostX < opgelostY) {
        shouldSwitch = true;
      }

      if (shouldSwitch) {
        rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
        switching = true;
      }
    }
  }
}

fetchTableData();