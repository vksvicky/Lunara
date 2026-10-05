import Toybox.Lang;
using Toybox.Application;
using Toybox.Graphics;
using Toybox.Math;
using Toybox.System;
using Toybox.Time;
using Toybox.Time.Gregorian;
using Toybox.WatchUi;

// Fractions match tools/dial_layout.py. Positive Y is down, as a fraction of radius.
const MONTH_Y = -0.52;
const MONTH_HALF_W = 0.27;
const MONTH_HALF_H = 0.044;
const WINDOW_Y = -0.41;
const WINDOW_CX = 0.0;
const SUBDIAL_Y = 0.335;
const MOON_WELL_R = 0.195;
const DATE_HAND_R = 0.2325;
const BATTERY_X = -0.42;
const BATTERY_Y = -0.16;
const BATTERY_TEXT_DY = 0.10;
const LUNAR_INFO_X = 0.42;
const BRAND_Y = -0.30;
const SYNODIC_DAYS = 29.530588853;
const NEW_MOON_EPOCH = 947182440;

class Dial {
    private var _background as WatchUi.BitmapResource;
    private var _batteryIcon as WatchUi.BitmapResource;
    private var _moonResIds as Lang.Array<Lang.ResourceId>;
    private var _currentMoon as WatchUi.BitmapResource?;
    private var _currentMoonIndex as Lang.Number = -1;
    private var _face as FaceText;
    private var _fontSmall;
    private var _fontLarge;
    private var _legendSmall;
    private var _legendLarge;

    function initialize() {
        _background = WatchUi.loadResource(Rez.Drawables.dial_bg);
        _batteryIcon = WatchUi.loadResource(Rez.Drawables.battery_icon);
        _moonResIds = [
            Rez.Drawables.moon_0,
            Rez.Drawables.moon_1,
            Rez.Drawables.moon_2,
            Rez.Drawables.moon_3,
            Rez.Drawables.moon_4,
            Rez.Drawables.moon_5,
            Rez.Drawables.moon_6,
            Rez.Drawables.moon_7,
            Rez.Drawables.moon_8,
            Rez.Drawables.moon_9,
            Rez.Drawables.moon_10,
            Rez.Drawables.moon_11,
            Rez.Drawables.moon_12,
            Rez.Drawables.moon_13,
            Rez.Drawables.moon_14,
            Rez.Drawables.moon_15,
            Rez.Drawables.moon_16,
            Rez.Drawables.moon_17,
            Rez.Drawables.moon_18,
            Rez.Drawables.moon_19,
            Rez.Drawables.moon_20,
            Rez.Drawables.moon_21,
            Rez.Drawables.moon_22,
            Rez.Drawables.moon_23,
            Rez.Drawables.moon_24,
            Rez.Drawables.moon_25,
            Rez.Drawables.moon_26,
            Rez.Drawables.moon_27,
            Rez.Drawables.moon_28,
            Rez.Drawables.moon_29
        ];
        _face = new FaceText();
        _fontSmall = WatchUi.loadResource(Rez.Fonts.FaceSmall);
        _fontLarge = WatchUi.loadResource(Rez.Fonts.FaceLarge);
        _legendSmall = WatchUi.loadResource(Rez.Fonts.FaceLegendSmall);
        _legendLarge = WatchUi.loadResource(Rez.Fonts.FaceLegendLarge);
    }

    function draw(dc, moment) {
        var width = dc.getWidth();
        var height = dc.getHeight();
        var side = width < height ? width : height;
        var radius = side / 2.0;
        var cx = width / 2.0;
        var cy = height / 2.0;

        var bgW = _background.getWidth();
        var bgH = _background.getHeight();
        dc.drawBitmap(cx - bgW / 2.0, cy - bgH / 2.0, _background);

        var info = Gregorian.info(moment, Time.FORMAT_SHORT);
        var month = info.month as Lang.Number;
        var weekday = info.day_of_week as Lang.Number;
        var day = info.day as Lang.Number;
        var ink = 0x26221E;
        var language = FaceText.resolve(Application.Properties.getValue("Language"), System.getDeviceSettings().systemLanguage);
        var font = width >= 390 ? _fontLarge : _fontSmall;
        var legend = width >= 390 ? _legendLarge : _legendSmall;
        var center = Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER;
        var batteryStyle = Application.Properties.getValue("BatteryStyle");
        var hour = info.hour as Lang.Number;
        var level = System.getSystemStats().battery;

        Dial._label(dc, cx, cy + MONTH_Y * radius, font, _face.month(language, month));
        Dial._label(dc, cx + WINDOW_CX * radius, cy + WINDOW_Y * radius, font, _face.weekday(language, weekday));
        Dial._label(dc, cx, cy + BRAND_Y * radius, font, "LUNARA");

        Dial._battery(dc, cx + BATTERY_X * radius, cy + BATTERY_Y * radius, level, batteryStyle, hour, _batteryIcon);
        // Percentage text in classic dial ink for high-end look
        dc.setColor(ink, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx + BATTERY_X * radius, cy + (BATTERY_Y + BATTERY_TEXT_DY) * radius, legend, Battery.text(level), center);

        var phase = Dial.moonPhase(moment);
        var lunarMode = Application.Properties.getValue("LunarDisplayMode") as Lang.Number;
        var lunarStr = LunarComplication.text(phase, lunarMode);
        if (lunarStr.length() > 0) {
            dc.setColor(ink, Graphics.COLOR_TRANSPARENT);
            dc.drawText(cx + LUNAR_INFO_X * radius, cy + (BATTERY_Y + BATTERY_TEXT_DY) * radius, legend, lunarStr, center);
        }

        var moonIdx = Dial.moonIndex(phase);
        if (moonIdx != _currentMoonIndex || _currentMoon == null) {
            _currentMoon = WatchUi.loadResource(_moonResIds[moonIdx]);
            _currentMoonIndex = moonIdx;
        }
        var moonX = cx - _currentMoon.getWidth() / 2.0;
        var moonY = cy + SUBDIAL_Y * radius - _currentMoon.getHeight() / 2.0;
        dc.drawBitmap(moonX, moonY, _currentMoon);
        Dial._drawTimelineMilestones(dc, cx, cy + SUBDIAL_Y * radius, radius, moment);
        Dial._dateHighlight(dc, cx, cy + SUBDIAL_Y * radius, radius, day);
    }

    static function _label(dc, x, y, font, text) {
        var center = Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER;
        dc.setColor(0x000000, Graphics.COLOR_TRANSPARENT);
        dc.drawText(x, y, font, text, center);
    }

    static function _battery(dc, x, y, level, style, hour, icon) {
        var bmpW = icon.getWidth().toFloat();
        var bmpH = icon.getHeight().toFloat();
        var left = x - bmpW / 2.0;
        var top = y - bmpH / 2.0;
        if (level != null) {
            var pct = Battery.percent(level);
            var insetX = bmpW * 0.08;
            var insetY = bmpH * 0.22;
            var body = bmpW * 0.90;
            var inner = (body - 2.0 * insetX) * pct / 100.0;
            if (inner > 0) {
                dc.setColor(Battery.color(level, style, hour), Graphics.COLOR_TRANSPARENT);
                var fillH = bmpH - 2.0 * insetY;
                dc.fillRoundedRectangle(left + insetX, top + insetY, inner, fillH, fillH * 0.35);
            }
        }
        dc.drawBitmap(left, top, icon);
    }

    static function _abs(val as Lang.Float) as Lang.Float {
        return val < 0.0 ? -val : val;
    }

    static function getMonthMilestones(moment as Time.Moment) as Lang.Array<Lang.Number> {
        var info = Gregorian.info(moment, Time.FORMAT_SHORT);
        var curDay = info.day as Lang.Number;
        var curPhase = Dial.moonPhase(moment);

        var bestNew = 1;
        var diffNew = 2.0;
        var bestFirst = 1;
        var diffFirst = 2.0;
        var bestFull = 1;
        var diffFull = 2.0;
        var bestThird = 1;
        var diffThird = 2.0;

        for (var d = 1; d <= 31; d++) {
            var p = curPhase + (d - curDay) / SYNODIC_DAYS;
            p = p - Math.floor(p);
            if (p < 0.0) {
                p = p + 1.0;
            }

            var dNew = p < (1.0 - p) ? p : (1.0 - p);
            if (dNew < diffNew) {
                diffNew = dNew;
                bestNew = d;
            }

            var dFirst = _abs(p - 0.25);
            if (dFirst < diffFirst) {
                diffFirst = dFirst;
                bestFirst = d;
            }

            var dFull = _abs(p - 0.50);
            if (dFull < diffFull) {
                diffFull = dFull;
                bestFull = d;
            }

            var dThird = _abs(p - 0.75);
            if (dThird < diffThird) {
                diffThird = dThird;
                bestThird = d;
            }
        }

        return [bestNew, bestFirst, bestFull, bestThird];
    }

    static function _drawTimelineMilestones(dc, sx, sy, radius, moment as Time.Moment) {
        var milestones = Dial.getMonthMilestones(moment);
        var trackR = radius * 0.203;
        var pipR = (radius * 0.012).toNumber();
        if (pipR < 2) { pipR = 2; }

        for (var i = 0; i < 4; i++) {
            var day = milestones[i];
            var angle = -Math.PI / 2.0 + ((day - 1) / 31.0) * Math.PI * 2.0;
            var px = sx + trackR * Math.cos(angle);
            var py = sy + trackR * Math.sin(angle);

            if (i == 0) {
                // New Moon: dark navy
                dc.setColor(0x0C1932, Graphics.COLOR_TRANSPARENT);
                dc.fillCircle(px, py, pipR);
            } else if (i == 1) {
                // First Quarter: left dark navy, right ivory
                dc.setColor(0x0C1932, Graphics.COLOR_TRANSPARENT);
                dc.fillCircle(px, py, pipR);
                dc.setColor(0xFFFCF0, Graphics.COLOR_TRANSPARENT);
                dc.setClip(px, py - pipR, pipR + 2, pipR * 2 + 2);
                dc.fillCircle(px, py, pipR);
                dc.clearClip();
            } else if (i == 2) {
                // Full Moon: ivory
                dc.setColor(0xFFFCF0, Graphics.COLOR_TRANSPARENT);
                dc.fillCircle(px, py, pipR);
            } else if (i == 3) {
                // Third Quarter: left ivory, right dark navy
                dc.setColor(0x0C1932, Graphics.COLOR_TRANSPARENT);
                dc.fillCircle(px, py, pipR);
                dc.setColor(0xFFFCF0, Graphics.COLOR_TRANSPARENT);
                dc.setClip(px - pipR - 1, py - pipR, pipR + 1, pipR * 2 + 2);
                dc.fillCircle(px, py, pipR);
                dc.clearClip();
            }

            // Outline pip
            dc.setColor(0x645F5A, Graphics.COLOR_TRANSPARENT);
            dc.setPenWidth(1);
            dc.drawCircle(px, py, pipR);
        }
    }

    static function _dateHighlight(dc, sx, sy, radius, day) {
        var angle = -Math.PI / 2.0 + ((day - 1) / 31.0) * Math.PI * 2.0;
        var r = DATE_HAND_R * radius;
        var hx = sx + r * Math.cos(angle);
        var hy = sy + r * Math.sin(angle);
        var hl_r = radius * 0.024;
        if (hl_r < 3.0) { hl_r = 3.0; }
        var penW = (radius * 0.007).toNumber();
        if (penW < 1) { penW = 1; }
        // Terracotta accent orange
        dc.setColor(0xE14B2D, Graphics.COLOR_TRANSPARENT);
        dc.setPenWidth(penW);
        dc.drawCircle(hx, hy, hl_r);
    }

    static function _dateHand(dc, sx, sy, radius, day) {
        _dateHighlight(dc, sx, sy, radius, day);
    }

    static function moonPhase(moment as Time.Moment) as Lang.Float {
        var seconds = moment.value() - NEW_MOON_EPOCH;
        var days = seconds / 86400.0;
        var cycles = Math.floor(days / SYNODIC_DAYS);
        var into = days - cycles * SYNODIC_DAYS;
        if (into < 0.0) {
            into = into + SYNODIC_DAYS;
        }
        return into / SYNODIC_DAYS;
    }

    static function moonIndex(phase) {
        var wrapped = phase - Math.floor(phase);
        if (wrapped < 0.0) {
            wrapped = wrapped + 1.0;
        }
        var index = Math.floor(wrapped * 30.0 + 0.5).toNumber() % 30;
        if (index < 0) {
            index = index + 30;
        }
        return index;
    }
}
