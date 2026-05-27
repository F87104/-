import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const repoRoot = "/Users/asamifujita/Documents/Codex/2026-05-21/fx-ai";
const outputDir = `${repoRoot}/outputs/wavebox_forward_validation`;
const outputPath = `${outputDir}/wavebox_forward_validation_tracker.xlsx`;
const renderDir = `${outputDir}/renders`;

const workbook = Workbook.create();
const dashboard = workbook.worksheets.add("Dashboard");
const log = workbook.worksheets.add("Log");
const rules = workbook.worksheets.add("Rules");
const backtest = workbook.worksheets.add("Backtest Summary");

function setValues(sheet, address, values) {
  sheet.getRange(address).values = values;
}

function setFormulas(sheet, address, formulas) {
  sheet.getRange(address).formulas = formulas;
}

function styleTitle(range) {
  range.format.font.bold = true;
  range.format.font.size = 16;
  range.format.font.color = "#FFFFFF";
  range.format.fill.color = "#1F4E78";
}

function styleSection(range) {
  range.format.font.bold = true;
  range.format.font.color = "#FFFFFF";
  range.format.fill.color = "#5B9BD5";
}

function styleHeader(range) {
  range.format.font.bold = true;
  range.format.font.color = "#FFFFFF";
  range.format.fill.color = "#305496";
  range.format.wrapText = true;
}

function styleInputHeader(range) {
  range.format.font.bold = true;
  range.format.font.color = "#FFFFFF";
  range.format.fill.color = "#70AD47";
  range.format.wrapText = true;
}

function setWidths(sheet, widths) {
  for (const [col, px] of Object.entries(widths)) {
    sheet.getRange(`${col}:${col}`).format.columnWidthPx = px;
  }
}

function setNumberFormat(sheet, address, format) {
  sheet.getRange(address).setNumberFormat(format);
}

// Dashboard
setValues(dashboard, "A1:K1", [["USDJPY H1 WaveBox Forward Validation", "", "", "", "", "", "", "", "", "", ""]]);
styleTitle(dashboard.getRange("A1:K1"));
setValues(dashboard, "A2:K2", [["Record GO A+ / GO A / SELECT A exactly as signaled. Judge the method by forward evidence, not by memory.", "", "", "", "", "", "", "", "", "", ""]]);

setValues(dashboard, "A4:B11", [
  ["Metric", "Value"],
  ["Closed trades", ""],
  ["Win rate", ""],
  ["Total R", ""],
  ["Average R", ""],
  ["Profit factor", ""],
  ["Max single loss R", ""],
  ["Open trades", ""],
]);
styleHeader(dashboard.getRange("A4:B4"));
setFormulas(dashboard, "B5:B11", [
  ['=COUNT(Log!$R$2:$R$501)'],
  ['=IFERROR(COUNTIF(Log!$S$2:$S$501,"WIN")/B5,"")'],
  ['=SUM(Log!$R$2:$R$501)'],
  ['=IFERROR(AVERAGE(Log!$R$2:$R$501),"")'],
  ['=IFERROR(SUMIF(Log!$R$2:$R$501,">0",Log!$R$2:$R$501)/ABS(SUMIF(Log!$R$2:$R$501,"<0",Log!$R$2:$R$501)),"")'],
  ['=IFERROR(MIN(Log!$R$2:$R$501),"")'],
  ['=COUNTIF(Log!$AF$2:$AF$501,"OPEN")'],
]);
setNumberFormat(dashboard, "B6", "0.00%");
setNumberFormat(dashboard, "B7:B10", "0.00");

setValues(dashboard, "D4:J4", [["Action", "Trades", "Wins", "Win rate", "Total R", "Avg R", "PF"]]);
styleHeader(dashboard.getRange("D4:J4"));
setValues(dashboard, "D5:D9", [["GO A+"], ["GO A"], ["SELECT A"], ["OBS B"], ["SKIP"]]);
setFormulas(dashboard, "E5:J9", [
  ['=COUNTIF(Log!$G$2:$G$501,D5)', '=COUNTIFS(Log!$G$2:$G$501,D5,Log!$S$2:$S$501,"WIN")', '=IFERROR(F5/E5,"")', '=SUMIF(Log!$G$2:$G$501,D5,Log!$R$2:$R$501)', '=IFERROR(AVERAGEIF(Log!$G$2:$G$501,D5,Log!$R$2:$R$501),"")', '=IFERROR(SUMIFS(Log!$R$2:$R$501,Log!$G$2:$G$501,D5,Log!$R$2:$R$501,">0")/ABS(SUMIFS(Log!$R$2:$R$501,Log!$G$2:$G$501,D5,Log!$R$2:$R$501,"<0")),"")'],
  ['=COUNTIF(Log!$G$2:$G$501,D6)', '=COUNTIFS(Log!$G$2:$G$501,D6,Log!$S$2:$S$501,"WIN")', '=IFERROR(F6/E6,"")', '=SUMIF(Log!$G$2:$G$501,D6,Log!$R$2:$R$501)', '=IFERROR(AVERAGEIF(Log!$G$2:$G$501,D6,Log!$R$2:$R$501),"")', '=IFERROR(SUMIFS(Log!$R$2:$R$501,Log!$G$2:$G$501,D6,Log!$R$2:$R$501,">0")/ABS(SUMIFS(Log!$R$2:$R$501,Log!$G$2:$G$501,D6,Log!$R$2:$R$501,"<0")),"")'],
  ['=COUNTIF(Log!$G$2:$G$501,D7)', '=COUNTIFS(Log!$G$2:$G$501,D7,Log!$S$2:$S$501,"WIN")', '=IFERROR(F7/E7,"")', '=SUMIF(Log!$G$2:$G$501,D7,Log!$R$2:$R$501)', '=IFERROR(AVERAGEIF(Log!$G$2:$G$501,D7,Log!$R$2:$R$501),"")', '=IFERROR(SUMIFS(Log!$R$2:$R$501,Log!$G$2:$G$501,D7,Log!$R$2:$R$501,">0")/ABS(SUMIFS(Log!$R$2:$R$501,Log!$G$2:$G$501,D7,Log!$R$2:$R$501,"<0")),"")'],
  ['=COUNTIF(Log!$G$2:$G$501,D8)', '=COUNTIFS(Log!$G$2:$G$501,D8,Log!$S$2:$S$501,"WIN")', '=IFERROR(F8/E8,"")', '=SUMIF(Log!$G$2:$G$501,D8,Log!$R$2:$R$501)', '=IFERROR(AVERAGEIF(Log!$G$2:$G$501,D8,Log!$R$2:$R$501),"")', '=IFERROR(SUMIFS(Log!$R$2:$R$501,Log!$G$2:$G$501,D8,Log!$R$2:$R$501,">0")/ABS(SUMIFS(Log!$R$2:$R$501,Log!$G$2:$G$501,D8,Log!$R$2:$R$501,"<0")),"")'],
  ['=COUNTIF(Log!$G$2:$G$501,D9)', '=COUNTIFS(Log!$G$2:$G$501,D9,Log!$S$2:$S$501,"WIN")', '=IFERROR(F9/E9,"")', '=SUMIF(Log!$G$2:$G$501,D9,Log!$R$2:$R$501)', '=IFERROR(AVERAGEIF(Log!$G$2:$G$501,D9,Log!$R$2:$R$501),"")', '=IFERROR(SUMIFS(Log!$R$2:$R$501,Log!$G$2:$G$501,D9,Log!$R$2:$R$501,">0")/ABS(SUMIFS(Log!$R$2:$R$501,Log!$G$2:$G$501,D9,Log!$R$2:$R$501,"<0")),"")'],
]);
setNumberFormat(dashboard, "G5:G9", "0.00%");
setNumberFormat(dashboard, "H5:J9", "0.00");

setValues(dashboard, "A14:J18", [
  ["Gate", "Minimum", "Current", "Status", "", "Stop rule", "Trigger", "Action", "", ""],
  ["GO A+ / GO A", 20, "", "", "", "Loss streak", 3, "Pause", "", ""],
  ["GO A+ / GO A", 30, "", "", "", "Monthly DD", "-3R", "Month stop", "", ""],
  ["SELECT A", 10, "", "", "", "Data mismatch", "Any", "Fix first", "", ""],
  ["OBS B", 20, "", "", "", "Spread/news", "Abnormal", "Skip", "", ""],
]);
styleSection(dashboard.getRange("A14:J14"));
setFormulas(dashboard, "C15:D18", [
  ['=COUNTIFS(Log!$G$2:$G$501,"GO A+")+COUNTIFS(Log!$G$2:$G$501,"GO A")', '=IF(C15>=B15,"OK","WAIT")'],
  ['=COUNTIFS(Log!$G$2:$G$501,"GO A+")+COUNTIFS(Log!$G$2:$G$501,"GO A")', '=IF(C16>=B16,"OK","WAIT")'],
  ['=COUNTIF(Log!$G$2:$G$501,"SELECT A")', '=IF(C17>=B17,"ENOUGH","WAIT")'],
  ['=COUNTIF(Log!$G$2:$G$501,"OBS B")', '=IF(C18>=B18,"ENOUGH","WAIT")'],
]);

dashboard.freezePanes.freezeRows(4);
setWidths(dashboard, { A: 180, B: 115, C: 90, D: 115, E: 80, F: 120, G: 95, H: 105, I: 90, J: 80, K: 50 });

// Log
const headers = [
  "No", "Logged Date", "Symbol", "TF", "Mode", "Rank", "Action", "Direction",
  "Signal Time", "Entry Time", "Entry", "Stop", "Target", "Exit Time", "Exit",
  "Exit Reason", "Planned RR", "Result R", "Outcome", "H4 State", "Retrace %",
  "Box Position", "Break Quality", "Phase", "W1 ATR", "W1 Speed", "Box ATR",
  "Chase ATR", "Body Ratio", "Screenshot / TV Link", "Decision Note", "Post Review"
];
setValues(log, "A1:AF1", [headers]);
styleInputHeader(log.getRange("A1:AF1"));
const idFormulas = [];
const outcomeFormulas = [];
const statusFormulas = [];
for (let row = 2; row <= 501; row += 1) {
  idFormulas.push([`=IF($B${row}="","",ROW()-1)`]);
  outcomeFormulas.push([`=IF($R${row}="","",IF($R${row}>0,"WIN",IF($R${row}<0,"LOSS","BE")))`]);
  statusFormulas.push([`=IF($B${row}="","",IF($R${row}="","OPEN","CLOSED"))`]);
}
setFormulas(log, "A2:A501", idFormulas);
setFormulas(log, "S2:S501", outcomeFormulas);
setFormulas(log, "AF2:AF501", statusFormulas);
log.freezePanes.freezeRows(1);
setWidths(log, {
  A: 45, B: 105, C: 80, D: 60, E: 95, F: 60, G: 95, H: 80,
  I: 135, J: 135, K: 80, L: 80, M: 80, N: 135, O: 80, P: 90,
  Q: 80, R: 80, S: 80, T: 90, U: 85, V: 100, W: 110, X: 100,
  Y: 75, Z: 80, AA: 75, AB: 80, AC: 85, AD: 180, AE: 260, AF: 95,
});
setNumberFormat(log, "B:B", "yyyy-mm-dd");
setNumberFormat(log, "I:J", "yyyy-mm-dd hh:mm");
setNumberFormat(log, "N:N", "yyyy-mm-dd hh:mm");
setNumberFormat(log, "K:M", "0.000");
setNumberFormat(log, "O:O", "0.000");
setNumberFormat(log, "Q:R", "0.00");
setNumberFormat(log, "U:U", "0.00%");
setNumberFormat(log, "Y:AC", "0.00");

// Rules
setValues(rules, "A1:E1", [["WaveBox Forward Validation Rules", "", "", "", ""]]);
styleTitle(rules.getRange("A1:E1"));
setValues(rules, "A3:E8", [
  ["Action", "Use", "Default lot", "Meaning", "Manual check"],
  ["GO A+", "Trade candidate", "Normal small", "A+ shallow retrace. Highest priority.", "No major news/spread issue"],
  ["GO A", "Trade candidate", "Normal small", "Clean A: box not late, break strong/ok, phase early/normal.", "Confirm chart looks like pullback stagnation then rebreak"],
  ["SELECT A", "Usually wait", "None / micro", "A but one quality axis is weak.", "Only trade if visual context is exceptional"],
  ["OBS B", "Observe", "None / micro", "Strict B only.", "Record to decide later"],
  ["SKIP", "No trade", "None", "Expansion B or weak relaxed signal.", "No exception unless rule is redesigned"],
]);
styleHeader(rules.getRange("A3:E3"));
setValues(rules, "A11:D17", [
  ["Field", "Allowed values", "Source", "Notes"],
  ["Mode", "Strict / Balanced / Expansion88", "Pine 1波剪定 + rule settings", "Strict remains baseline"],
  ["Rank", "A+ / A / B", "Pine", "A+ overrides H4 state"],
  ["Action", "GO A+ / GO A / SELECT A / OBS B / SKIP", "Pine", "Primary execution decision"],
  ["Box Position", "bottom / low-mid / mid-high / late", "Pine quality axis", "Late box is less desirable"],
  ["Break Quality", "strong / ok / weak/wick", "Pine quality axis", "Weak/wick needs visual caution"],
  ["Phase", "early/normal / late/chase", "Pine quality axis", "Late/chase means stretched move"],
]);
styleHeader(rules.getRange("A11:D11"));
setWidths(rules, { A: 120, B: 210, C: 170, D: 320, E: 220 });

// Backtest summary
setValues(backtest, "A1:H1", [["Backtest Reference", "", "", "", "", "", "", ""]]);
styleTitle(backtest.getRange("A1:H1"));
setValues(backtest, "A3:H11", [
  ["Mode / Rule", "Trades", "Win rate", "Total R", "Avg R", "PF", "Max DD R", "Use"],
  ["Strict all", 69, 0.6522, 41.47, 0.601, 2.69, 3.13, "Baseline"],
  ["Balanced all", 73, 0.6438, 42.31, 0.580, 2.59, 3.13, "Candidate"],
  ["Expansion88 all", 88, 0.6136, 44.28, 0.503, 2.27, 4.17, "Research only"],
  ["Strict A+ or clean A", 38, 0.6842, 26.09, 0.687, 3.15, 4.18, "Main forward set"],
  ["Balanced A+ or clean A", 39, 0.6923, 27.56, 0.707, 3.27, 4.18, "Main expansion set"],
  ["Expansion88 A+ or clean A", 47, 0.6809, 31.80, 0.677, 3.09, 4.77, "Only A+/clean A"],
  ["Expansion88 B only", 28, 0.5357, 8.50, 0.304, 1.63, 3.36, "Skip"],
  ["Strict B only", 21, 0.6190, 10.78, 0.514, 2.30, 2.11, "Observe"],
]);
styleHeader(backtest.getRange("A3:H3"));
setNumberFormat(backtest, "C4:C11", "0.00%");
setNumberFormat(backtest, "D4:G11", "0.00");
setWidths(backtest, { A: 210, B: 80, C: 90, D: 90, E: 90, F: 80, G: 90, H: 150 });

// Lightweight visual polish
for (const sheet of [dashboard, log, rules, backtest]) {
  sheet.showGridLines = false;
  sheet.getRange("A1:AF501").format.verticalAlignment = "Top";
}
log.getRange("AE2:AE501").format.wrapText = true;
rules.getRange("D:E").format.wrapText = true;

await workbook.recalculate();

await fs.mkdir(renderDir, { recursive: true });
const dashboardPreview = await workbook.render({ sheetName: "Dashboard", range: "A1:K18", scale: 1.5 });
await fs.writeFile(`${renderDir}/dashboard.png`, Buffer.from(await dashboardPreview.arrayBuffer()));
const logPreview = await workbook.render({ sheetName: "Log", range: "A1:AF15", scale: 1.2 });
await fs.writeFile(`${renderDir}/log.png`, Buffer.from(await logPreview.arrayBuffer()));

const dashboardInspect = await workbook.inspect({
  kind: "table",
  range: "Dashboard!A1:J18",
  include: "values,formulas",
  tableMaxRows: 20,
  tableMaxCols: 12,
});
console.log(dashboardInspect.ndjson);

const errorScan = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "formula error scan",
});
console.log(errorScan.ndjson);

await fs.mkdir(outputDir, { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(`Saved ${outputPath}`);
