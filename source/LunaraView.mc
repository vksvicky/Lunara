using Toybox.Graphics;
using Toybox.System;
using Toybox.Time;
using Toybox.WatchUi;

class LunaraView extends WatchUi.WatchFace {
    private var _dial;

    function initialize() {
        WatchFace.initialize();
        _dial = new Dial();
    }

    function onLayout(dc) {
    }

    function onShow() {
    }

    function onUpdate(dc) {
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear();

        var now = Time.now();
        _dial.draw(dc, now);

        var clock = System.getClockTime();
        var cx = dc.getWidth() / 2;
        var cy = dc.getHeight() / 2;
        var radius = cx < cy ? cx : cy;
        Hands.draw(dc, clock.hour, clock.min, cx, cy, radius);
    }

    function onHide() {
    }

    function onExitSleep() {
        WatchUi.requestUpdate();
    }

    function onEnterSleep() {
        WatchUi.requestUpdate();
    }
}
