import Toybox.Lang;
using Toybox.Math;

// Stops match tools/battery_style.py. Full, middle, empty.
const BATTERY_INK = 0x26221E;
const CLASSIC_FULL = 0x2E9A4A;
const CLASSIC_MID = 0xE08C18;
const CLASSIC_EMPTY = 0xC62828;
const MORNING_FULL = 0x3E8C5A;
const MORNING_MID = 0xD4A017;
const MORNING_EMPTY = 0xE07A4C;
const EVENING_FULL = 0xC4A35A;
const EVENING_MID = 0xE07A2F;
const EVENING_EMPTY = 0xA32030;
const NIGHT_FULL = 0x3D6B62;
const NIGHT_MID = 0xA6843C;
const NIGHT_EMPTY = 0x8C3A3A;

// The only data metric on the Lunara dial.
class Battery {
    static function text(level) as Lang.String {
        if (level == null) {
            return "--%";
        }
        return Battery.percent(level).toString() + "%";
    }

    // style 0 follows the hour. 1 is green/amber/red. 2–5 lock a time of day.
    static function color(level, style, hour) as Lang.Number {
        if (level == null) {
            return BATTERY_INK;
        }
        var pct = Battery.percent(level);
        var resolved = Battery.resolveStyle(style, hour);
        if (pct >= 50) {
            return Battery.mix(Battery.mid(resolved), Battery.full(resolved), (pct - 50) / 50.0);
        }
        return Battery.mix(Battery.empty(resolved), Battery.mid(resolved), pct / 50.0);
    }

    static function percent(level) as Lang.Number {
        var pct = Math.floor(level + 0.5).toNumber();
        if (pct < 0) {
            pct = 0;
        }
        if (pct > 100) {
            pct = 100;
        }
        return pct;
    }

    static function resolveStyle(style, hour) as Lang.Number {
        if (style == null || style == 0) {
            return Battery.period(hour);
        }
        if (style < 1 || style > 5) {
            return 1;
        }
        return style;
    }

    static function period(hour) as Lang.Number {
        var h = hour;
        if (h == null || h < 0) {
            h = 0;
        }
        h = h % 24;
        if (h >= 5 && h <= 10) {
            return 2;
        }
        if (h >= 11 && h <= 16) {
            return 3;
        }
        if (h >= 17 && h <= 20) {
            return 4;
        }
        return 5;
    }

    static function full(style) as Lang.Number {
        if (style == 2) {
            return MORNING_FULL;
        }
        if (style == 4) {
            return EVENING_FULL;
        }
        if (style == 5) {
            return NIGHT_FULL;
        }
        return CLASSIC_FULL;
    }

    static function mid(style) as Lang.Number {
        if (style == 2) {
            return MORNING_MID;
        }
        if (style == 4) {
            return EVENING_MID;
        }
        if (style == 5) {
            return NIGHT_MID;
        }
        return CLASSIC_MID;
    }

    static function empty(style) as Lang.Number {
        if (style == 2) {
            return MORNING_EMPTY;
        }
        if (style == 4) {
            return EVENING_EMPTY;
        }
        if (style == 5) {
            return NIGHT_EMPTY;
        }
        return CLASSIC_EMPTY;
    }

    static function mix(from, to, amount) as Lang.Number {
        var red = Battery.channel(from, to, amount, 16);
        var green = Battery.channel(from, to, amount, 8);
        var blue = Battery.channel(from, to, amount, 0);
        return (red << 16) | (green << 8) | blue;
    }

    static function channel(from, to, amount, shift) as Lang.Number {
        var origin = (from >> shift) & 0xFF;
        var destination = (to >> shift) & 0xFF;
        var mixed = Math.floor(origin + (destination - origin) * amount + 0.5).toNumber();
        if (mixed < 0) {
            mixed = 0;
        }
        if (mixed > 255) {
            mixed = 255;
        }
        return mixed;
    }
}
