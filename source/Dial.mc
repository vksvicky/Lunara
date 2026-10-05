import Toybox.Lang;
using Toybox.Application;
using Toybox.Graphics;
using Toybox.Math;
using Toybox.System;
using Toybox.Time;
using Toybox.Time.Gregorian;
using Toybox.WatchUi;

// Fractions match tools/dial_layout.py. Positive Y is down, as a fraction of radius.
const MONTH_Y = -0.55;
const MONTH_HALF_W = 0.27;
const MONTH_HALF_H = 0.044;
const WINDOW_Y = -0.39;
const WINDOW_CX = 0.0;
const SUBDIAL_Y = 0.335;
const MOON_WELL_R = 0.195;
const DATE_HAND_R = 0.208;
const DATE_TIP_R = 0.208;
const DATE_BASE_R = 0.192;
const BATTERY_X = -0.42;
const BATTERY_Y = -0.16;
const BATTERY_TEXT_DY = 0.10;
const LUNAR_INFO_X = 0.38;
const LUNAR_INFO_Y = -0.10;
const BRAND_Y = -0.23;
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
        var brandFont = font;
        var legend = width >= 390 ? _legendLarge : _legendSmall;
        var center = Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER;
        var batteryStyle = Application.Properties.getValue("BatteryStyle");
        var hour = info.hour as Lang.Number;
        var level = System.getSystemStats().battery;

        Dial._label(dc, cx, cy + MONTH_Y * radius, font, _face.month(language, month));
        Dial._label(dc, cx + WINDOW_CX * radius, cy + WINDOW_Y * radius, font, _face.weekday(language, weekday));
        Dial._label(dc, cx, cy + BRAND_Y * radius, brandFont, "LUNARA");

        Dial._battery(dc, cx + BATTERY_X * radius, cy + BATTERY_Y * radius, level, batteryStyle, hour, _batteryIcon);
        // Percentage text in classic dial ink for high-end look
        dc.setColor(ink, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx + BATTERY_X * radius, cy + (BATTERY_Y + BATTERY_TEXT_DY) * radius, legend, Battery.text(level), center);

        var phase = Dial.moonPhase(moment);
        var lunarMode = Application.Properties.getValue("LunarDisplayMode") as Lang.Number;
        var lunarStr = LunarComplication.textForLanguage(phase, lunarMode, language, _face);
        if (lunarStr.length() > 0) {
            dc.setColor(ink, Graphics.COLOR_TRANSPARENT);
            dc.drawText(cx + LUNAR_INFO_X * radius, cy + LUNAR_INFO_Y * radius, legend, lunarStr, center);
        }

        var moonIdx = Dial.moonIndex(phase);
        if (moonIdx != _currentMoonIndex || _currentMoon == null) {
            _currentMoon = WatchUi.loadResource(_moonResIds[moonIdx]);
            _currentMoonIndex = moonIdx;
        }
        var moonX = cx - _currentMoon.getWidth() / 2.0;
        var moonY = cy + SUBDIAL_Y * radius - _currentMoon.getHeight() / 2.0;
        dc.drawBitmap(moonX, moonY, _currentMoon);
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

    static function _dateHighlight(dc, sx, sy, radius, day) {
        var angle = -Math.PI / 2.0 + ((day - 1) / 31.0) * Math.PI * 2.0;
        var rTip = DATE_TIP_R * radius;
        var rBase = DATE_BASE_R * radius;
        var wAngle = 0.061; // 3.5 degrees in radians

        var tipX = (sx + rTip * Math.cos(angle)).toNumber();
        var tipY = (sy + rTip * Math.sin(angle)).toNumber();
        var b1X = (sx + rBase * Math.cos(angle - wAngle)).toNumber();
        var b1Y = (sy + rBase * Math.sin(angle - wAngle)).toNumber();
        var b2X = (sx + rBase * Math.cos(angle + wAngle)).toNumber();
        var b2Y = (sy + rBase * Math.sin(angle + wAngle)).toNumber();

        // Terracotta pointer triangle on inner bezel pointing at the active date
        dc.setColor(0xE14B2D, Graphics.COLOR_TRANSPARENT);
        dc.fillPolygon([ [tipX, tipY], [b1X, b1Y], [b2X, b2Y] ]);
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
