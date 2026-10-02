using Toybox.Graphics;
using Toybox.Math;

// Hour and minute hands drawn over the dial. There is no second hand.
class Hands {
    static function draw(dc, hour, minute, cx, cy, radius) {
        var minuteAngle = (minute / 60.0) * Math.PI * 2.0 - Math.PI / 2.0;
        var hourAngle = ((hour % 12) / 12.0) * Math.PI * 2.0;
        hourAngle = hourAngle + (minute / 60.0) * (Math.PI / 6.0) - Math.PI / 2.0;

        var hourWidth = (radius * 0.012).toNumber();
        if (hourWidth < 2) {
            hourWidth = 2;
        }
        dc.setColor(0x26221E, Graphics.COLOR_TRANSPARENT);
        dc.setPenWidth(hourWidth);
        Hands._line(dc, cx, cy, hourAngle, radius * 0.30);

        var minuteWidth = (radius * 0.008).toNumber();
        if (minuteWidth < 1) {
            minuteWidth = 1;
        }
        dc.setPenWidth(minuteWidth);
        Hands._line(dc, cx, cy, minuteAngle, radius * 0.42);

        dc.setColor(0xC4A46A, Graphics.COLOR_TRANSPARENT);
        var cap = (radius * 0.028).toNumber();
        if (cap < 2) {
            cap = 2;
        }
        dc.fillCircle(cx, cy, cap);
    }

    static function _line(dc, cx, cy, angle, length) {
        var x = cx + length * Math.cos(angle);
        var y = cy + length * Math.sin(angle);
        dc.drawLine(cx, cy, x, y);
    }
}
