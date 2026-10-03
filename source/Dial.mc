import Toybox.Lang;
using Toybox.Application;
using Toybox.Graphics;
using Toybox.Math;
using Toybox.System;
using Toybox.Time;
using Toybox.Time.Gregorian;
using Toybox.WatchUi;

// Fractions match tools/dial_layout.py. Positive Y is down, as a fraction of radius.
const MONTH_Y = -0.48;
const MONTH_HALF_W = 0.27;
const MONTH_HALF_H = 0.044;
const WINDOW_Y = -0.36;
const WINDOW_CX = 0.0;
const SUBDIAL_Y = 0.18;
const MOON_WELL_R = 0.175;
const DATE_HAND_R = 0.30;
const BATTERY_X = -0.42;
const BATTERY_Y = -0.16;
const BATTERY_TEXT_DY = 0.09;
const BRAND_Y = -0.26;
const SYNODIC_DAYS = 29.530588853;
const NEW_MOON_EPOCH = 947182440;

class Dial {
    private var _background as WatchUi.BitmapResource;
    private var _batteryIcon as WatchUi.BitmapResource;
    private var _moons as Lang.Array<WatchUi.BitmapResource>;
    private var _face as FaceText;
    private var _fontSmall;
    private var _fontLarge;
    private var _legendSmall;
    private var _legendLarge;

    function initialize() {
        _background = WatchUi.loadResource(Rez.Drawables.dial_bg);
        _batteryIcon = WatchUi.loadResource(Rez.Drawables.battery_icon);
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

        Dial._label(dc, cx, cy + MONTH_Y * radius, font, _face.month(language, month));
        Dial._label(dc, cx + WINDOW_CX * radius, cy + WINDOW_Y * radius, font, _face.weekday(language, weekday));
        Dial._label(dc, cx, cy + BRAND_Y * radius, font, "LUNARA");

        Dial._battery(dc, cx + BATTERY_X * radius, cy + BATTERY_Y * radius, level, batteryStyle, hour, _batteryIcon);
        // Percentage text in classic dial ink for high-end look
        dc.setColor(ink, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx + BATTERY_X * radius, cy + (BATTERY_Y + BATTERY_TEXT_DY) * radius, legend, Battery.text(level), center);

        var moon = _moons[Dial.moonIndex(Dial.moonPhase(moment))];
        var moonX = cx - moon.getWidth() / 2.0;
        var moonY = cy + SUBDIAL_Y * radius - moon.getHeight() / 2.0;
        dc.drawBitmap(moonX, moonY, moon);
        Dial._dateHand(dc, cx, cy + SUBDIAL_Y * radius, radius, day);
    }

    static function _label(dc, x, y, font, text) {
        var center = Graphics.TEXT_JUSTIFY_CENTER | Graphics.TEXT_JUSTIFY_VCENTER;
        dc.setColor(0x968878, Graphics.COLOR_TRANSPARENT);
        dc.drawText(x, y + 1, font, text, center);
        dc.setColor(0x26221E, Graphics.COLOR_TRANSPARENT);
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

    static function _dateHand(dc, sx, sy, radius, day) {
        var angle = -Math.PI / 2.0 + ((day - 1) / 31.0) * Math.PI * 2.0;
        var inner = 0.26 * radius;
        var outer = DATE_HAND_R * radius;
        var ux = Math.cos(angle);
        var uy = Math.sin(angle);
        var px = -uy;
        var py = ux;

        var startX = sx + inner * ux;
        var startY = sy + inner * uy;
        var endX   = sx + outer * ux;
        var endY   = sy + outer * uy;

        var width = (radius * 0.008).toNumber();
        if (width < 1) { width = 1; }

        dc.setColor(0x1C1A16, Graphics.COLOR_TRANSPARENT);
        dc.setPenWidth(width);
        dc.drawLine(startX, startY, endX, endY);

        // Arrow pointer tip
        var tipLen = radius * 0.022;
        var tipW   = radius * 0.011;
        var tip    = [ endX.toNumber(), endY.toNumber() ];
        var left   = [ (endX - ux * tipLen + px * tipW).toNumber(), (endY - uy * tipLen + py * tipW).toNumber() ];
        var right  = [ (endX - ux * tipLen - px * tipW).toNumber(), (endY - uy * tipLen - py * tipW).toNumber() ];
        dc.fillPolygon([ tip, left, right ]);
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
