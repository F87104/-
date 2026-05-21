#include "SaiScannerCore.hpp"

#include <algorithm>
#include <cmath>
#include <cctype>
#include <limits>
#include <numeric>

namespace sai {
namespace {

double absd(double value) {
    return std::fabs(value);
}

bool sameDirection(double value, Direction direction) {
    if (direction == Direction::Bullish) return value > 0.0;
    if (direction == Direction::Bearish) return value < 0.0;
    return false;
}

bool breaksZone(const Candle& candle, Direction direction, double level, double buffer) {
    if (direction == Direction::Bullish) return candle.close > level + buffer;
    if (direction == Direction::Bearish) return candle.close < level - buffer;
    return false;
}

double highestHigh(const std::vector<Candle>& candles, int begin, int endExclusive) {
    double value = -std::numeric_limits<double>::infinity();
    for (int i = begin; i < endExclusive; ++i) value = std::max(value, candles[i].high);
    return value;
}

double lowestLow(const std::vector<Candle>& candles, int begin, int endExclusive) {
    double value = std::numeric_limits<double>::infinity();
    for (int i = begin; i < endExclusive; ++i) value = std::min(value, candles[i].low);
    return value;
}

double averageClose(const std::vector<Candle>& candles, int begin, int endExclusive) {
    if (begin >= endExclusive) return 0.0;
    double sum = 0.0;
    for (int i = begin; i < endExclusive; ++i) sum += candles[i].close;
    return sum / static_cast<double>(endExclusive - begin);
}

} // namespace

SaiScanner::SaiScanner(ScannerConfig config) : config_(config) {}

ScanResult SaiScanner::scanLatest(const std::vector<Candle>& candles,
                                  const std::string& symbol,
                                  int month,
                                  int day) const {
    ScanResult result;
    const int n = static_cast<int>(candles.size());
    if (n < std::max({config_.mediumTrendLookbackBars,
                      config_.keyLevelLookbackBars,
                      config_.rangeMinBars,
                      config_.vShapeLookbackBars}) + 5) {
        result.noTradeReasons.push_back("Not enough candles for 1H Sai scan.");
        return result;
    }

    const int latest = n - 1;
    const double atrValue = atr(candles, latest - 1, config_.atrPeriod);
    if (atrValue <= 0.0) {
        result.noTradeReasons.push_back("ATR is not available.");
        return result;
    }

    const std::string normalizedSymbol = normalizeSymbol(symbol);
    result.lowPrioritySymbol = config_.skipUsdJpy && normalizedSymbol == "USDJPY";
    result.seasonalAvoid = config_.skipDecemberHolidayMarket && isSeasonalAvoid(month, day);

    result.mediumDirection = directionByWindow(candles, latest - 1,
                                               config_.mediumTrendLookbackBars, atrValue);
    const Direction shortWindowDirection = directionByWindow(candles, latest - 1,
                                                            config_.shortTrendLookbackBars, atrValue);
    result.shortDirection = recentDirection(candles, latest - 1, atrValue);
    if (result.shortDirection == Direction::None) result.shortDirection = shortWindowDirection;

    result.shortMidAligned = result.mediumDirection != Direction::None &&
                             result.mediumDirection == result.shortDirection;
    result.momentumStrong = result.shortMidAligned &&
                            hasMomentum(candles, latest - 1, result.mediumDirection, atrValue);

    const RangeBox range = detectRange(candles, latest - 1, atrValue);
    result.rangeLike = range.valid;

    if (result.lowPrioritySymbol) {
        result.noTradeReasons.push_back("USDJPY is configured as low priority for Sai method.");
    }
    if (result.seasonalAvoid) {
        result.noTradeReasons.push_back("Seasonal avoid period is active.");
    }
    if (!result.shortMidAligned) {
        result.noTradeReasons.push_back("Short-mid alignment is absent.");
    }
    if (!result.momentumStrong) {
        result.noTradeReasons.push_back("Momentum is not strong enough.");
    }

    double secondBreakLevel = 0.0;
    const bool secondBreak = result.shortMidAligned &&
                             isSecondRangeBreakout(candles, latest, result.mediumDirection,
                                                   atrValue, secondBreakLevel);

    if (range.valid && !secondBreak) {
        result.noTradeReasons.push_back("Range-like market without valid second breakout.");
    }

    if (result.lowPrioritySymbol || result.seasonalAvoid ||
        !result.shortMidAligned || !result.momentumStrong) {
        return result;
    }

    const Direction direction = result.mediumDirection;
    const Candle& current = candles[latest];
    const double buffer = atrValue * config_.breakoutBufferAtr;

    if (secondBreak && breaksZone(current, direction, secondBreakLevel, buffer)) {
        result.signal.active = true;
        result.signal.direction = direction;
        result.signal.setup = SetupType::SecondRangeBreakout;
        result.signal.entryLevel = current.close;
        result.signal.stopLevel = direction == Direction::Bullish
            ? secondBreakLevel - atrValue
            : secondBreakLevel + atrValue;
        result.signal.keyLevel = secondBreakLevel;
        result.signal.score = 0.85;
        result.signal.reason = std::string(directionName(direction)) +
            " second range breakout after failed first breakout.";
        result.noTradeReasons.clear();
        return result;
    }

    Zone tight = findStagnationBeforeLatest(candles, latest, atrValue,
                                            config_.stagnationMaxAtr);
    Zone wide = findStagnationBeforeLatest(candles, latest, atrValue,
                                           config_.wideStagnationMaxAtr);
    if (!tight.valid && wide.valid) {
        wide.wide = true;
    }

    const Zone zone = tight.valid ? tight : wide;
    if (!zone.valid) {
        result.noTradeReasons.push_back("No valid stagnation zone before latest candle.");
        return result;
    }

    const double triggerLevel = direction == Direction::Bullish ? zone.high : zone.low;
    if (!breaksZone(current, direction, triggerLevel, buffer)) {
        result.noTradeReasons.push_back("Stagnation exists, but trigger has not broken yet.");
        return result;
    }

    double keyLevel = 0.0;
    const bool nearKey = nearKeyLevel(candles, latest - 1, direction, zone, atrValue, keyLevel);
    const bool vShape = hasVShapeContext(candles, latest - 1, direction, atrValue);

    result.signal.active = true;
    result.signal.direction = direction;
    result.signal.entryLevel = current.close;
    result.signal.zoneHigh = zone.high;
    result.signal.zoneLow = zone.low;
    result.signal.keyLevel = keyLevel;
    result.signal.stopLevel = direction == Direction::Bullish
        ? zone.low - atrValue * 0.25
        : zone.high + atrValue * 0.25;

    if (vShape && nearKey) {
        result.signal.setup = SetupType::VShapeStagnation;
        result.signal.score = 0.90;
        result.signal.reason = "V-shape context plus key-level stagnation break.";
    } else if (vShape) {
        result.signal.setup = SetupType::SuddenReversalStagnation;
        result.signal.score = 0.78;
        result.signal.reason = "Sudden reversal/V-shape context plus stagnation break.";
    } else if (nearKey && zone.wide) {
        result.signal.setup = SetupType::WideStagnation;
        result.signal.score = 0.76;
        result.signal.reason = "Wide/irregular stagnation near key level has broken.";
    } else if (nearKey) {
        result.signal.setup = SetupType::KeyLevelStagnation;
        result.signal.score = 0.82;
        result.signal.reason = "Key-level stagnation has broken.";
    } else {
        result.signal.setup = SetupType::SimpleStagnation;
        result.signal.score = 0.65;
        result.signal.reason = "Simple trend/momentum stagnation has broken.";
    }

    result.noTradeReasons.clear();
    return result;
}

double SaiScanner::atr(const std::vector<Candle>& candles, int endIndex, int period) const {
    if (endIndex <= 0 || period <= 0 || endIndex - period + 1 <= 0) return 0.0;
    double total = 0.0;
    for (int i = endIndex - period + 1; i <= endIndex; ++i) {
        const double highLow = candles[i].high - candles[i].low;
        const double highClose = absd(candles[i].high - candles[i - 1].close);
        const double lowClose = absd(candles[i].low - candles[i - 1].close);
        total += std::max({highLow, highClose, lowClose});
    }
    return total / static_cast<double>(period);
}

Direction SaiScanner::directionByWindow(const std::vector<Candle>& candles,
                                        int endIndex,
                                        int lookback,
                                        double atrValue) const {
    if (endIndex - lookback + 1 < 0 || lookback < 20) return Direction::None;

    const int start = endIndex - lookback + 1;
    const int segment = std::max(5, lookback / 5);
    const double first = averageClose(candles, start, start + segment);
    const double last = averageClose(candles, endIndex - segment + 1, endIndex + 1);
    const double delta = last - first;

    if (delta > atrValue * config_.trendMinAtr) return Direction::Bullish;
    if (delta < -atrValue * config_.trendMinAtr) return Direction::Bearish;
    return Direction::None;
}

Direction SaiScanner::recentDirection(const std::vector<Candle>& candles,
                                      int endIndex,
                                      double atrValue) const {
    if (endIndex - config_.recentTrendBars < 0) return Direction::None;
    const double delta = candles[endIndex].close - candles[endIndex - config_.recentTrendBars].close;
    if (delta > atrValue * 0.35) return Direction::Bullish;
    if (delta < -atrValue * 0.35) return Direction::Bearish;
    return Direction::None;
}

bool SaiScanner::hasMomentum(const std::vector<Candle>& candles,
                             int endIndex,
                             Direction direction,
                             double atrValue) const {
    if (direction == Direction::None || endIndex - config_.momentumLookbackBars < 0) return false;
    const int start = endIndex - config_.momentumLookbackBars + 1;
    const double net = candles[endIndex].close - candles[start].open;
    if (!sameDirection(net, direction) || absd(net) < atrValue * config_.momentumMinAtr) return false;

    int directionalBodies = 0;
    for (int i = start; i <= endIndex; ++i) {
        const double body = candles[i].close - candles[i].open;
        if (sameDirection(body, direction)) ++directionalBodies;
    }
    const double ratio = static_cast<double>(directionalBodies) /
                         static_cast<double>(config_.momentumLookbackBars);
    return ratio >= config_.directionalBodyRatio;
}

SaiScanner::Zone SaiScanner::findStagnationBeforeLatest(const std::vector<Candle>& candles,
                                                        int latestIndex,
                                                        double atrValue,
                                                        double maxAtrMultiple) const {
    Zone best;
    const int endExclusive = latestIndex;
    const int maxBars = std::min(config_.stagnationMaxBars, endExclusive);
    for (int bars = config_.stagnationMinBars; bars <= maxBars; ++bars) {
        const int begin = endExclusive - bars;
        const double high = highestHigh(candles, begin, endExclusive);
        const double low = lowestLow(candles, begin, endExclusive);
        const double height = high - low;
        if (height <= atrValue * maxAtrMultiple) {
            best.valid = true;
            best.bars = bars;
            best.high = high;
            best.low = low;
            best.wide = maxAtrMultiple > config_.stagnationMaxAtr;
        }
    }
    return best;
}

SaiScanner::RangeBox SaiScanner::detectRange(const std::vector<Candle>& candles,
                                             int endIndex,
                                             double atrValue) const {
    RangeBox box;
    if (endIndex - config_.rangeMinBars + 1 < 0) return box;
    const int begin = endIndex - config_.rangeMinBars + 1;
    const double high = highestHigh(candles, begin, endIndex + 1);
    const double low = lowestLow(candles, begin, endIndex + 1);
    if (high - low > atrValue * config_.rangeMaxAtr) return box;

    int highTouches = 0;
    int lowTouches = 0;
    const double tolerance = atrValue * config_.rangeTouchAtr;
    for (int i = begin; i <= endIndex; ++i) {
        if (absd(candles[i].high - high) <= tolerance) ++highTouches;
        if (absd(candles[i].low - low) <= tolerance) ++lowTouches;
    }
    if (highTouches >= config_.rangeMinTouchesEachSide &&
        lowTouches >= config_.rangeMinTouchesEachSide) {
        box.valid = true;
        box.high = high;
        box.low = low;
    }
    return box;
}

bool SaiScanner::nearKeyLevel(const std::vector<Candle>& candles,
                              int endIndex,
                              Direction direction,
                              const Zone& zone,
                              double atrValue,
                              double& keyLevel) const {
    if (endIndex - config_.keyLevelLookbackBars + 1 < 0) return false;
    const int begin = endIndex - config_.keyLevelLookbackBars + 1;
    const double tolerance = atrValue * config_.keyLevelNearAtr;
    if (direction == Direction::Bullish) {
        keyLevel = highestHigh(candles, begin, endIndex + 1);
        return absd(zone.high - keyLevel) <= tolerance || zone.high >= keyLevel - tolerance;
    }
    if (direction == Direction::Bearish) {
        keyLevel = lowestLow(candles, begin, endIndex + 1);
        return absd(zone.low - keyLevel) <= tolerance || zone.low <= keyLevel + tolerance;
    }
    return false;
}

bool SaiScanner::isSecondRangeBreakout(const std::vector<Candle>& candles,
                                       int latestIndex,
                                       Direction direction,
                                       double atrValue,
                                       double& rangeLevel) const {
    const int priorEnd = latestIndex - config_.rangeRetestLookbackBars;
    if (priorEnd <= config_.rangeMinBars) return false;

    const int rangeBegin = priorEnd - config_.rangeMinBars;
    const double rangeHigh = highestHigh(candles, rangeBegin, priorEnd);
    const double rangeLow = lowestLow(candles, rangeBegin, priorEnd);
    if (rangeHigh - rangeLow > atrValue * config_.rangeMaxAtr) return false;

    bool firstBreak = false;
    bool returnedInside = false;
    double firstBreakExtreme = direction == Direction::Bullish
        ? -std::numeric_limits<double>::infinity()
        : std::numeric_limits<double>::infinity();

    for (int i = priorEnd; i < latestIndex; ++i) {
        if (direction == Direction::Bullish) {
            if (candles[i].high > rangeHigh + atrValue * config_.breakoutBufferAtr) {
                firstBreak = true;
                firstBreakExtreme = std::max(firstBreakExtreme, candles[i].high);
            }
            if (firstBreak && candles[i].close < rangeHigh) returnedInside = true;
        } else if (direction == Direction::Bearish) {
            if (candles[i].low < rangeLow - atrValue * config_.breakoutBufferAtr) {
                firstBreak = true;
                firstBreakExtreme = std::min(firstBreakExtreme, candles[i].low);
            }
            if (firstBreak && candles[i].close > rangeLow) returnedInside = true;
        }
    }

    if (!firstBreak || !returnedInside) return false;
    rangeLevel = firstBreakExtreme;
    return true;
}

bool SaiScanner::hasVShapeContext(const std::vector<Candle>& candles,
                                  int latestIndex,
                                  Direction direction,
                                  double atrValue) const {
    if (latestIndex - config_.vShapeLookbackBars + 1 < 0) return false;
    const int begin = latestIndex - config_.vShapeLookbackBars + 1;

    if (direction == Direction::Bullish) {
        int valley = begin;
        for (int i = begin; i <= latestIndex; ++i) {
            if (candles[i].low < candles[valley].low) valley = i;
        }
        if (valley <= begin + 2 || valley >= latestIndex - 2) return false;
        const double preHigh = highestHigh(candles, begin, valley);
        const double drop = preHigh - candles[valley].low;
        const double recovery = candles[latestIndex].close - candles[valley].low;
        return drop >= atrValue * config_.vShapeMinMoveAtr &&
               recovery >= drop * config_.vShapeRecoveryRatio;
    }

    if (direction == Direction::Bearish) {
        int peak = begin;
        for (int i = begin; i <= latestIndex; ++i) {
            if (candles[i].high > candles[peak].high) peak = i;
        }
        if (peak <= begin + 2 || peak >= latestIndex - 2) return false;
        const double preLow = lowestLow(candles, begin, peak);
        const double rally = candles[peak].high - preLow;
        const double recovery = candles[peak].high - candles[latestIndex].close;
        return rally >= atrValue * config_.vShapeMinMoveAtr &&
               recovery >= rally * config_.vShapeRecoveryRatio;
    }

    return false;
}

bool SaiScanner::isSeasonalAvoid(int month, int day) const {
    if (month == 0 || day == 0) return false;
    if (month == config_.holidayStartMonth && day >= config_.holidayStartDay) return true;
    if (month == config_.holidayEndMonth && day <= config_.holidayEndDay) return true;
    return false;
}

std::string SaiScanner::normalizeSymbol(std::string symbol) {
    std::string out;
    for (char ch : symbol) {
        if (std::isalnum(static_cast<unsigned char>(ch))) {
            out.push_back(static_cast<char>(std::toupper(static_cast<unsigned char>(ch))));
        }
    }
    return out;
}

const char* SaiScanner::directionName(Direction direction) {
    return toString(direction);
}

const char* SaiScanner::setupName(SetupType setup) {
    return toString(setup);
}

const char* toString(Direction direction) {
    switch (direction) {
        case Direction::Bullish: return "Bullish";
        case Direction::Bearish: return "Bearish";
        default: return "None";
    }
}

const char* toString(SetupType setup) {
    switch (setup) {
        case SetupType::SimpleStagnation: return "SimpleStagnation";
        case SetupType::KeyLevelStagnation: return "KeyLevelStagnation";
        case SetupType::PostBreakoutStagnation: return "PostBreakoutStagnation";
        case SetupType::WideStagnation: return "WideStagnation";
        case SetupType::VShapeStagnation: return "VShapeStagnation";
        case SetupType::SuddenReversalStagnation: return "SuddenReversalStagnation";
        case SetupType::SecondRangeBreakout: return "SecondRangeBreakout";
        default: return "None";
    }
}

} // namespace sai
