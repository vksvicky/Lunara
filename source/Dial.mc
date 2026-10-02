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
const WINDOW_Y = -0.30;
const WINDOW_CX = 0.0;
const SUBDIAL_Y = 0.42;
const MOON_WELL_R = 0.175;
const DATE_HAND_R = 0.25;
const BATTERY_X = -0.50;
const BATTERY_Y = 0.0;
const BATTERY_TEXT_DY = 0.075;
const SYNODIC_DAYS = 29.530588853;
const NEW_MOON_EPOCH = 947182440;

class Dial {
    private var _background as WatchUi.BitmapResource;
    private var _moons as Lang.Array<WatchUi.BitmapResource>;
    private var _face as FaceText;
    private var _fontSmall;
    private var _fontLarge;
    private var _legendSmall;
    private var _legendLarge;

    function initialize() {
        _background = WatchUi.loadResource(Rez.Drawables.dial_bg);
        _moons = [
            WatchUi.loadResource(Rez.Drawables.moon_0),
            WatchUi.loadResource(Rez.Drawables.moon_1),
            WatchUi.loadResource(Rez.Drawables.moon_2),
            WatchUi.loadResource(Rez.Drawables.moon_3),
            WatchUi.loadResource(Rez.Drawables.moon_4),
            WatchUi.loadResource(Rez.Drawables.moon_5),
            WatchUi.loadResource(Rez.Drawables.moon_6),
            WatchUi.loadResource(Rez.Drawables.moon_7)
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
        var shade = 0x968878;
        var highlight = 0xFFFCF6;

        dc.setColor(highlight, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx - 1, cy + MONTH_Y * radius - 1, font, _face.month(language, month), center);
        dc.drawText(cx + WINDOW_CX * radius - 1, cy + WINDOW_Y * radius - 1, font, _face.weekday(language, weekday), center);
        dc.setColor(shade, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx + 1, cy + MONTH_Y * radius + 1, font, _face.month(language, month), center);
        dc.drawText(cx + WINDOW_CX * radius + 1, cy + WINDOW_Y * radius + 1, font, _face.weekday(language, weekday), center);
        dc.setColor(ink, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, cy + MONTH_Y * radius, font, _face.month(language, month), center);
        dc.drawText(cx + WINDOW_CX * radius, cy + WINDOW_Y * radius, font, _face.weekday(language, weekday), center);

        Dial._battery(dc, cx + BATTERY_X * radius, cy + BATTERY_Y * radius, radius, level, batteryStyle, hour);
        dc.setColor(Battery.color(level, batteryStyle, hour), Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx + BATTERY_X * radius, cy + (BATTERY_Y + BATTERY_TEXT_DY) * radius, legend, Battery.text(level), center);

        var moon = _moons[Dial.moonIndex(Dial.moonPhase(moment))];
        var moonX = cx - moon.getWidth() / 2.0;
        var moonY = cy + SUBDIAL_Y * radius - moon.getHeight() / 2.0;
        dc.drawBitmap(moonX, moonY, moon);
        Dial._dateHand(dc, cx, cy + SUBDIAL_Y * radius, radius, day);
    }

    static function _battery(dc, x, y, radius, level, style, hour) {
        var width = radius * 0.20;
        var height = radius * 0.072;
        var left = x - width / 2.0;
        var top = y - height / 2.0;
        var stroke = (radius * 0.006).toNumber();
        if (stroke < 1) {
            stroke = 1;
        }
        dc.setColor(0x1C1A16, Graphics.COLOR_TRANSPARENT);
        dc.setPenWidth(stroke);
        dc.drawRoundedRectangle(left, top, width, height, height * 0.22);
        var nubH = height * 0.38;
        var nubW = radius * 0.016;
        dc.fillRectangle(left + width, y - nubH / 2.0, nubW, nubH);
        if (level == null) {
            return;
        }
        var pct = Battery.percent(level);
        var pad = stroke + 1;
        var inner = (width - 2 * pad) * pct / 100.0;
        if (inner <= 0) {
            return;
        }
        dc.setColor(Battery.color(level, style, hour), Graphics.COLOR_TRANSPARENT);
        dc.fillRectangle(left + pad, top + pad, inner, height - 2 * pad);
    }

    static function _dateHand(dc, sx, sy, radius, day) {
        var angle = -Math.PI / 2.0 + ((day - 1) / 31.0) * Math.PI * 2.0;
        var inner = (MOON_WELL_R + 0.018) * radius;
        var outer = DATE_HAND_R * radius;
        var width = (radius * 0.010).toNumber();
        if (width < 1) {
            width = 1;
        }
        dc.setColor(0x1C1A16, Graphics.COLOR_TRANSPARENT);
        dc.setPenWidth(width);
        dc.drawLine(sx + inner * Math.cos(angle), sy + inner * Math.sin(angle), sx + outer * Math.cos(angle), sy + outer * Math.sin(angle));
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
        var index = Math.floor(wrapped * 8.0 + 0.5).toNumber() % 8;
        if (index < 0) {
            index = index + 8;
        }
        return index;
    }
}
