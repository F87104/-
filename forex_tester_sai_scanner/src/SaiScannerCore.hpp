#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace sai {

struct Candle {
    std::int64_t time = 0;
    double open = 0.0;
    double high = 0.0;
    double low = 0.0;
    double close = 0.0;
};

enum class Direction {
    None,
    Bullish,
    Bearish
};

enum class SetupType {
    None,
    SimpleStagnation,
    KeyLevelStagnation,
    PostBreakoutStagnation,
    WideStagnation,
    VShapeStagnation,
    SuddenReversalStagnation,
    SecondRangeBreakout
};

struct ScannerConfig {
    int atrPeriod = 14;

    int mediumTrendLookbackBars = 520;
    int shortTrendLookbackBars = 72;
    int recentTrendBars = 8;
    double trendMinAtr = 2.0;

    int momentumLookbackBars = 12;
    double momentumMinAtr = 1.2;
    double directionalBodyRatio = 0.55;

    int stagnationMinBars = 7;
    int stagnationMaxBars = 24;
    double stagnationMaxAtr = 1.20;
    double wideStagnationMaxAtr = 2.50;
    double breakoutBufferAtr = 0.10;

    int keyLevelLookbackBars = 720;
    double keyLevelNearAtr = 1.25;

    int rangeMinBars = 480;
    int rangeRetestLookbackBars = 120;
    double rangeMaxAtr = 10.0;
    double rangeTouchAtr = 0.75;
    int rangeMinTouchesEachSide = 2;

    int vShapeLookbackBars = 96;
    double vShapeMinMoveAtr = 3.0;
    double vShapeRecoveryRatio = 0.80;

    bool skipUsdJpy = true;
    bool skipDecemberHolidayMarket = true;
    int holidayStartMonth = 12;
    int holidayStartDay = 15;
    int holidayEndMonth = 1;
    int holidayEndDay = 10;
};

struct Signal {
    bool active = false;
    Direction direction = Direction::None;
    SetupType setup = SetupType::None;
    double entryLevel = 0.0;
    double stopLevel = 0.0;
    double zoneHigh = 0.0;
    double zoneLow = 0.0;
    double keyLevel = 0.0;
    double score = 0.0;
    std::string reason;
};

struct ScanResult {
    Direction mediumDirection = Direction::None;
    Direction shortDirection = Direction::None;
    bool shortMidAligned = false;
    bool momentumStrong = false;
    bool rangeLike = false;
    bool seasonalAvoid = false;
    bool lowPrioritySymbol = false;
    std::vector<std::string> noTradeReasons;
    Signal signal;
};

class SaiScanner {
public:
    explicit SaiScanner(ScannerConfig config = {});

    ScanResult scanLatest(const std::vector<Candle>& candles,
                          const std::string& symbol,
                          int month = 0,
                          int day = 0) const;

private:
    struct Zone {
        bool valid = false;
        int bars = 0;
        double high = 0.0;
        double low = 0.0;
        bool wide = false;
    };

    struct RangeBox {
        bool valid = false;
        double high = 0.0;
        double low = 0.0;
    };

    ScannerConfig config_;

    double atr(const std::vector<Candle>& candles, int endIndex, int period) const;
    Direction directionByWindow(const std::vector<Candle>& candles,
                                int endIndex,
                                int lookback,
                                double atrValue) const;
    Direction recentDirection(const std::vector<Candle>& candles,
                              int endIndex,
                              double atrValue) const;
    bool hasMomentum(const std::vector<Candle>& candles,
                     int endIndex,
                     Direction direction,
                     double atrValue) const;
    Zone findStagnationBeforeLatest(const std::vector<Candle>& candles,
                                    int latestIndex,
                                    double atrValue,
                                    double maxAtrMultiple) const;
    RangeBox detectRange(const std::vector<Candle>& candles,
                         int endIndex,
                         double atrValue) const;
    bool nearKeyLevel(const std::vector<Candle>& candles,
                      int endIndex,
                      Direction direction,
                      const Zone& zone,
                      double atrValue,
                      double& keyLevel) const;
    bool isSecondRangeBreakout(const std::vector<Candle>& candles,
                               int latestIndex,
                               Direction direction,
                               double atrValue,
                               double& rangeLevel) const;
    bool hasVShapeContext(const std::vector<Candle>& candles,
                          int latestIndex,
                          Direction direction,
                          double atrValue) const;
    bool isSeasonalAvoid(int month, int day) const;
    static std::string normalizeSymbol(std::string symbol);
    static const char* directionName(Direction direction);
    static const char* setupName(SetupType setup);
};

const char* toString(Direction direction);
const char* toString(SetupType setup);

} // namespace sai
