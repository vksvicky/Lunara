using Toybox.Graphics;
using Toybox.Math;

// High-end Dauphine faceted hands with 3D metallic specular split
// and polished multi-tiered center pinion cap.
class Hands {
    static function draw(dc, hour, minute, cx, cy, radius) {
        var minuteAngle = (minute / 60.0) * Math.PI * 2.0 - Math.PI / 2.0;
        var hourAngle = ((hour % 12) / 12.0) * Math.PI * 2.0;
        hourAngle = hourAngle + (minute / 60.0) * (Math.PI / 6.0) - Math.PI / 2.0;

        // 1. Draw Hour Hand (Dauphine Faceted)
        Hands._drawDauphine(dc, cx, cy, hourAngle, radius * 0.60, radius * 0.11, radius * 0.018);

        // 2. Draw Minute Hand (Dauphine Faceted)
        Hands._drawDauphine(dc, cx, cy, minuteAngle, radius * 0.80, radius * 0.13, radius * 0.012);

        // 3. Multi-tiered Polished Center Pinion Cap
        var capR = (radius * 0.032).toNumber();
        if (capR < 3) {
            capR = 3;
        }

        // Dark ring edge
        dc.setColor(0x23201C, Graphics.COLOR_TRANSPARENT);
        dc.fillCircle(cx, cy, capR + 1);

        // Polished steel dome
        dc.setColor(0xD8D8DC, Graphics.COLOR_TRANSPARENT);
        dc.fillCircle(cx, cy, capR);

        // Specular highlight off-center
        var hlOff = (capR * 0.25).toNumber();
        var hlR = (capR * 0.50).toNumber();
        if (hlR < 2) { hlR = 2; }
        dc.setColor(0xFFFFFF, Graphics.COLOR_TRANSPARENT);
        dc.fillCircle(cx - hlOff, cy - hlOff, hlR);

        // Dark center axle core
        var axleR = (capR * 0.28).toNumber();
        if (axleR < 1) { axleR = 1; }
        dc.setColor(0x26221E, Graphics.COLOR_TRANSPARENT);
        dc.fillCircle(cx, cy, axleR);
    }

    static function _drawDauphine(dc, cx, cy, angle, length, tail, width) {
        var ux = Math.cos(angle);
        var uy = Math.sin(angle);
        var px = -uy;
        var py = ux;
        var sDist = length * 0.28;

        var tip   = [ (cx + ux * length).toNumber(), (cy + uy * length).toNumber() ];
        var baseL = [ (cx - ux * tail + px * (width * 0.35)).toNumber(), (cy - uy * tail + py * (width * 0.35)).toNumber() ];
        var baseR = [ (cx - ux * tail - px * (width * 0.35)).toNumber(), (cy - uy * tail - py * (width * 0.35)).toNumber() ];
        var shdL  = [ (cx + ux * sDist + px * width).toNumber(), (cy + uy * sDist + py * width).toNumber() ];
        var shdR  = [ (cx + ux * sDist - px * width).toNumber(), (cy + uy * sDist - py * width).toNumber() ];
        var centerPt = [ cx.toNumber(), cy.toNumber() ];

        // 1. Dark perimeter outline for razor definition
        dc.setColor(0x23201C, Graphics.COLOR_TRANSPARENT);
        dc.fillPolygon([ tip, shdL, baseL, baseR, shdR ]);

        // 2. Light facet (Left: polished silver catching direct light)
        dc.setColor(0xF8FAFC, Graphics.COLOR_TRANSPARENT);
        dc.fillPolygon([ tip, shdL, baseL, centerPt ]);

        // 3. Shadow facet (Right: shaded brushed steel in shadow)
        dc.setColor(0x78736C, Graphics.COLOR_TRANSPARENT);
        dc.fillPolygon([ tip, centerPt, baseR, shdR ]);

        // 4. Center ridge seam (sharp 3D crease)
        dc.setColor(0x282420, Graphics.COLOR_TRANSPARENT);
        dc.setPenWidth(1);
        dc.drawLine((cx - ux * tail).toNumber(), (cy - uy * tail).toNumber(), (cx + ux * length).toNumber(), (cy + uy * length).toNumber());
    }
}
