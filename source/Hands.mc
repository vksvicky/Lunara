using Toybox.Graphics;
using Toybox.Math;

// Hour and minute hands drawn over the dial. There is no second hand.
// Tapered, the way the cream calendar mockup draws them at 10:10.
class Hands {
    static function draw(dc, hour, minute, cx, cy, radius) {
        var minuteAngle = (minute / 60.0) * Math.PI * 2.0 - Math.PI / 2.0;
        var hourAngle = ((hour % 12) / 12.0) * Math.PI * 2.0;
        hourAngle = hourAngle + (minute / 60.0) * (Math.PI / 6.0) - Math.PI / 2.0;

        dc.setColor(0x1C1A16, Graphics.COLOR_TRANSPARENT);
        Hands._taper(dc, cx, cy, hourAngle, radius * 0.58, radius * 0.14, radius * 0.012);
        Hands._taper(dc, cx, cy, minuteAngle, radius * 0.74, radius * 0.16, radius * 0.007);

        dc.setColor(0xC4A46A, Graphics.COLOR_TRANSPARENT);
        var cap = (radius * 0.016).toNumber();
        if (cap < 2) {
            cap = 2;
        }
        dc.fillCircle(cx, cy, cap);
    }

    static function _taper(dc, cx, cy, angle, length, tail, width) {
        var ux = Math.cos(angle);
        var uy = Math.sin(angle);
        var tip = [cx + ux * length, cy + uy * length];
        var left = [cx - ux * tail - uy * width, cy - uy * tail + ux * width];
        var right = [cx - ux * tail + uy * width, cy - uy * tail - ux * width];
        dc.fillPolygon([tip, left, right]);
    }
}
