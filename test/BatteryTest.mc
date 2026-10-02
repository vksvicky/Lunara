import Toybox.Lang;
using Toybox.Test;

(:test)
class BatteryTest {
    (:test)
    static function testBatteryTextBounds(logger as Test.Logger) as Lang.Boolean {
        Test.assertEqual(Battery.text(86), "86%");
        Test.assertEqual(Battery.text(0), "0%");
        Test.assertEqual(Battery.text(100), "100%");
        Test.assertEqual(Battery.text(-4), "0%");
        Test.assertEqual(Battery.text(140), "100%");
        Test.assertEqual(Battery.text(null), "--%");
        return true;
    }

    (:test)
    static function testClassicGradientStops(logger as Test.Logger) as Lang.Boolean {
        Test.assertEqual(Battery.color(100, 1, 12), CLASSIC_FULL);
        Test.assertEqual(Battery.color(50, 1, 12), CLASSIC_MID);
        Test.assertEqual(Battery.color(0, 1, 12), CLASSIC_EMPTY);
        Test.assertEqual(Battery.color(null, 1, 12), BATTERY_INK);
        return true;
    }

    (:test)
    static function testTimeOfDayChangesThePalette(logger as Test.Logger) as Lang.Boolean {
        Test.assertEqual(Battery.color(100, 0, 14), CLASSIC_FULL);
        Test.assertEqual(Battery.color(100, 0, 23), NIGHT_FULL);
        Test.assertEqual(Battery.color(100, 5, 12), NIGHT_FULL);
        Test.assertEqual(Battery.color(40, 5, 14), Battery.color(40, 5, 2));
        Test.assertEqual(Battery.color(80, 99, 19), Battery.color(80, 1, 19));
        return true;
    }
}
