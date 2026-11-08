async function fetchTableData() {
  try {
    // get people with api route
    let response = await fetch("/api/deelnemers");
    let person = await response.json();

    // clear leaderboard before filling
    let table = document.getElementById("leaderboard-body");
    table.innerHTML;

    let totaalPuzzels = 12;

    person.forEach(p => {
      let scoreVal = p.score;
      let naamVal = p.naam;

      // visualise the completion percentage
      let percentage = Math.min(100, Math.max(0, ((scoreVal / totaalPuzzels) * 100))).toFixed(1);

      let voortgangHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <div class="progress-bar-container">
                <div class="progress-bar-fill" style="width: ${percentage}%;"></div>
            </div>
        </div>
      `;

      table.innerHTML += "<tr>" +
        "<td>" + naamVal + "</td>" +
        "<td>" + scoreVal + " / " + totaalPuzzels + "</td>" +
        "<td>" + voortgangHTML + "</td>" +
        "<td>" + percentage + "%</td>" +
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
    // assume you dont switch in the first place
    switching = false;
    rows = table.rows;

    // Loop through all the table rows
    for (i = 0; i < (rows.length - 1); i++) {
      // helper for if statement below to execute a switch
      shouldSwitch = false;
      // get the info from the current row and the next of the amount of puzzles solved
      x = rows[i].getElementsByTagName("TD")[1];
      y = rows[i + 1].getElementsByTagName("TD")[1];

      let scoreX = parseInt(x.innerHTML.split("/")[0]);
      let scoreY = parseInt(y.innerHTML.split("/")[0]);
  
      if (scoreX < scoreY) {
        shouldSwitch = true;
        break;
      }
    }
    if (shouldSwitch) {
      // If a switch has been marked, make the switch and mark that a switch has been done
      rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
      switching = true;
    }
  }
}

fetchTableData();