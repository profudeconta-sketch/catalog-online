// Adăugați acest cod în proiectul Google Apps Script EXISTENT.
// Nu înlocuiți și nu modificați funcția doGet(e) existentă.
// Script Properties: PARENT_LOGIN_HISTORY_API_KEY = valoare aleatorie secretă.
// Folosiți aceeași valoare în Streamlit Secrets, fără a o salva în GitHub.

function doPost(e) {
  try {
    var body = JSON.parse((e && e.postData && e.postData.contents) || "{}");
    var expected = PropertiesService.getScriptProperties().getProperty("PARENT_LOGIN_HISTORY_API_KEY");
    if (!expected || typeof body.key !== "string" || body.key !== expected || body.action !== "history") {
      return ContentService.createTextOutput(JSON.stringify({status: "forbidden"}))
        .setMimeType(ContentService.MimeType.JSON);
    }

    var ss = SpreadsheetApp.openById("1kFMG5hW2vErnEDWqX4civzMWcEhhnuqXGSRdQxbJ4fk");
    var sheet = ss.getSheets()[0];
    var lastRow = sheet.getLastRow();
    var count = Math.min(lastRow, 10000);
    var startRow = lastRow - count + 1;
    var values = count > 0 ? sheet.getRange(startRow, 1, count, 3).getDisplayValues() : [];
    var rows = [];
    for (var i = values.length - 1; i >= 0; i--) {
      var r = values[i];
      // Ignoră un eventual antet, dar nu modifică foaia.
      if (r[0] === "Data și ora" && r[1] === "Elev") continue;
      if (!r[0] && !r[1]) continue;
      rows.push({data_ora: r[0], elev: r[1], matricol: r[2]});
    }
    return ContentService.createTextOutput(JSON.stringify({status: "ok", rows: rows}))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    // Nu divulgăm erori interne sau date din foaia de calcul către apelant.
    return ContentService.createTextOutput(JSON.stringify({status: "error"}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
