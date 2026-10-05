import Toybox.Lang;
using Toybox.Math;
using Toybox.Time;

class LunarComplication {
    enum {
        MODE_ILLUMINATION = 0,
        MODE_HINDU_PANCHANG = 1,
        MODE_LUNAR_AGE = 2,
        MODE_NONE = 3
    }

    private static const TITHI_NAMES = [
        "Pratipada",
        "Dwitiya",
        "Tritiya",
        "Chaturthi",
        "Panchami",
        "Shashti",
        "Saptami",
        "Ashtami",
        "Navami",
        "Dashami",
        "Ekadashi",
        "Dvadashi",
        "Trayodashi",
        "Chaturdashi",
        "Purnima"
    ];

    static function text(phase as Lang.Float, mode as Lang.Number) as Lang.String {
        var wrapped = phase - Math.floor(phase);
        if (wrapped < 0.0) {
            wrapped = wrapped + 1.0;
        }

        if (mode == MODE_HINDU_PANCHANG) {
            return tithiText(wrapped);
        } else if (mode == MODE_LUNAR_AGE) {
            var age = wrapped * 29.530588853;
            var whole = Math.floor(age).toNumber();
            var tenth = Math.floor((age - whole) * 10.0).toNumber();
            return "Day " + whole.format("%d") + "." + tenth.format("%d");
        } else if (mode == MODE_ILLUMINATION) {
            var illum = ((1.0 - Math.cos(wrapped * Math.PI * 2.0)) / 2.0) * 100.0;
            var pct = Math.round(illum).toNumber();
            var dir = (wrapped > 0.0 && wrapped <= 0.5) ? "Wax" : "Wan";
            return pct.format("%d") + "% " + dir;
        }
        return "";
    }

    static function tithiText(wrapped as Lang.Float) as Lang.String {
        // Each Tithi is 12 degrees out of 360 degrees = 1/30 of lunar cycle
        var tithiIdx = Math.floor(wrapped * 30.0).toNumber();
        if (tithiIdx < 0) {
            tithiIdx = 0;
        } else if (tithiIdx > 29) {
            tithiIdx = 29;
        }

        if (tithiIdx < 14) {
            return "S. " + TITHI_NAMES[tithiIdx];
        } else if (tithiIdx == 14) {
            return "Purnima";
        } else if (tithiIdx < 29) {
            return "K. " + TITHI_NAMES[tithiIdx - 15];
        } else {
            return "Amavasya";
        }
    }
}
