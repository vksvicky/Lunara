import Toybox.Lang;
using Toybox.Graphics;
using Toybox.System;
using Toybox.Time;
using Toybox.WatchUi;

class LunaraView extends WatchUi.WatchFace {
    private var _dial;
    private var _isSleeping as Lang.Boolean = false;
    private var _burnInProtection as Lang.Boolean = false;

    function initialize() {
        WatchFace.initialize();
        _dial = new Dial();
        var settings = System.getDeviceSettings();
        if (settings has :requiresBurnInProtection) {
            _burnInProtection = settings.requiresBurnInProtection;
        }
    }

    function onLayout(dc) {
    }

    function onShow() {
    }

    function onUpdate(dc) {
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear();

        var clock = System.getClockTime();
        var cx = dc.getWidth() / 2;
        var cy = dc.getHeight() / 2;
        var radius = cx < cy ? cx : cy;

        if (_isSleeping && _burnInProtection) {
            // AMOLED Always-On Display (AOD) in low-power sleep mode:
            // Renders minimalist skeleton Dauphine hands on pure black OLED background.
            // Complies with <10% total pixel luminance budget and 3-minute max pixel on-time.
            Hands.drawAOD(dc, clock.hour, clock.min, cx, cy, radius);
            return;
        }

        var now = Time.now();
        _dial.draw(dc, now);
        Hands.draw(dc, clock.hour, clock.min, cx, cy, radius);
    }

    function onHide() {
    }

    function onExitSleep() {
        _isSleeping = false;
        WatchUi.requestUpdate();
    }

    function onEnterSleep() {
        _isSleeping = true;
        WatchUi.requestUpdate();
    }
}
