/*
    Sai Scanner / EA adapter template for Forex Tester Desktop.

    This file is intentionally a wiring template, not a drop-in compiled DLL.
    Forex Tester ships the exact C++/Delphi API headers and examples inside
    the Windows installation, usually under:

        C:\ForexTester6\Examples\Strategies

    Copy SaiScannerCore.hpp/.cpp into a Forex Tester example strategy project,
    then replace the TODO sections below with the concrete function names from
    your installed Forex Tester API example.

    Recommended first mode:
      1. Scanner mode: draw/alert candidate signals only.
      2. Manual validation: confirm markers match Sai examples.
      3. EA mode: allow orders only after scanner precision is acceptable.
*/

#include "../src/SaiScannerCore.hpp"

#include <vector>
#include <string>

namespace {

enum class RunMode {
    ScannerOnly,
    AutoTrade
};

RunMode g_mode = RunMode::ScannerOnly;
sai::ScannerConfig g_config;
sai::SaiScanner g_scanner(g_config);

std::vector<sai::Candle> g_h1Candles;
std::string g_symbol;

// TODO: Replace with Forex Tester API calls.
std::vector<sai::Candle> loadH1CandlesFromForexTester() {
    std::vector<sai::Candle> candles;

    /*
        Pseudocode:

        int bars = FT_GetBarsCount(Symbol(), PERIOD_H1);
        for (int i = 0; i < bars; ++i) {
            sai::Candle c;
            c.time  = FT_GetBarTime(Symbol(), PERIOD_H1, i);
            c.open  = FT_GetOpen(Symbol(), PERIOD_H1, i);
            c.high  = FT_GetHigh(Symbol(), PERIOD_H1, i);
            c.low   = FT_GetLow(Symbol(), PERIOD_H1, i);
            c.close = FT_GetClose(Symbol(), PERIOD_H1, i);
            candles.push_back(c);
        }

        Important:
        - Keep candle order oldest -> newest.
        - Run on H1 data even if the chart view differs.
    */

    return candles;
}

// TODO: Replace with Forex Tester API calls.
std::string loadSymbolFromForexTester() {
    /*
        Pseudocode:
        return FT_CurrentSymbol();
    */
    return g_symbol;
}

// TODO: Replace with Forex Tester date API.
void loadMonthDayFromForexTester(int& month, int& day) {
    /*
        Pseudocode:
        DateTime t = FT_CurrentTime();
        month = t.month;
        day = t.day;
    */
    month = 0;
    day = 0;
}

// TODO: Replace with chart drawing/alert API.
void publishScannerSignal(const sai::ScanResult& result) {
    if (!result.signal.active) return;

    /*
        Pseudocode:

        string label = "Sai " + toString(result.signal.setup) + " "
                     + toString(result.signal.direction);

        FT_DrawVerticalLine("SaiSignal_" + TimeToString(CurrentTime()), CurrentTime(), color);
        FT_DrawText(label, CurrentTime(), result.signal.entryLevel, color);
        FT_DrawHorizontalLine("SaiStop_" + ..., result.signal.stopLevel, red);
        FT_Log(label + " entry=" + DoubleToString(result.signal.entryLevel));

        In scanner-only mode, do not place orders.
    */
}

// TODO: Replace with Forex Tester order API only after scanner is validated.
void placeOrderIfEnabled(const sai::ScanResult& result) {
    if (g_mode != RunMode::AutoTrade || !result.signal.active) return;

    /*
        Pseudocode:

        if (result.signal.direction == sai::Direction::Bullish) {
            FT_Buy(lot, result.signal.stopLevel, 0);
        } else if (result.signal.direction == sai::Direction::Bearish) {
            FT_Sell(lot, result.signal.stopLevel, 0);
        }

        Suggested:
        - Use fixed tiny lot while validating.
        - No take-profit initially; exits should be structural.
        - Add max daily/monthly loss guard before enabling.
    */
}

void runSaiScanOnce() {
    g_symbol = loadSymbolFromForexTester();
    g_h1Candles = loadH1CandlesFromForexTester();

    int month = 0;
    int day = 0;
    loadMonthDayFromForexTester(month, day);

    const sai::ScanResult result = g_scanner.scanLatest(g_h1Candles, g_symbol, month, day);
    publishScannerSignal(result);
    placeOrderIfEnabled(result);
}

} // namespace

/*
    TODO: Wire this into the concrete Forex Tester strategy lifecycle.

    Typical strategy APIs have callbacks roughly equivalent to:

      - Init / OnInit
      - Done / OnDeinit
      - OnTick / OnBar
      - Get/Set strategy properties

    In the tick callback, call runSaiScanOnce() only when a new H1 candle closes.
    Calling it on every tick is unnecessary and can create duplicate signals.
*/
