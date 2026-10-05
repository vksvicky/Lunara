import Toybox.Lang;
using Toybox.Test;
using Toybox.Time;
using Toybox.Time.Gregorian;

(:test)
class DialPhaseTest {
    (:test)
    static function testMoonIndexBins(logger as Test.Logger) as Lang.Boolean {
        Test.assertEqual(Dial.moonIndex(0.0), 0);
        Test.assertEqual(Dial.moonIndex(0.5), 15);
        Test.assertEqual(Dial.moonIndex(0.999), 0);
        Test.assertEqual(Dial.moonIndex(1.0333), 1);
        return true;
    }

    (:test)
    static function testLunarComplication(logger as Test.Logger) as Lang.Boolean {
        Test.assertEqual(LunarComplication.text(0.48, LunarComplication.MODE_HINDU_PANCHANG), "Purnima");
        Test.assertEqual(LunarComplication.text(0.50, LunarComplication.MODE_HINDU_PANCHANG), "K. Pratipada");
        Test.assertEqual(LunarComplication.text(0.00, LunarComplication.MODE_PHASE_NAME), "New Moon");
        Test.assertEqual(LunarComplication.text(0.10, LunarComplication.MODE_PHASE_NAME), "Crescent");
        Test.assertEqual(LunarComplication.text(0.25, LunarComplication.MODE_PHASE_NAME), "Quarter");
        Test.assertEqual(LunarComplication.text(0.35, LunarComplication.MODE_PHASE_NAME), "Gibbous");
        Test.assertEqual(LunarComplication.text(0.50, LunarComplication.MODE_PHASE_NAME), "Full Moon");
        Test.assertEqual(LunarComplication.text(0.65, LunarComplication.MODE_PHASE_NAME), "Gibbous");
        Test.assertEqual(LunarComplication.text(0.75, LunarComplication.MODE_PHASE_NAME), "Quarter");
        Test.assertEqual(LunarComplication.text(0.90, LunarComplication.MODE_PHASE_NAME), "Crescent");
        Test.assertEqual(LunarComplication.text(0.50, LunarComplication.MODE_ILLUMINATION), "100%");
        Test.assertEqual(LunarComplication.text(0.75, LunarComplication.MODE_ILLUMINATION), "50%");
        Test.assertEqual(LunarComplication.text(0.50, LunarComplication.MODE_NONE), "");
        return true;
    }

    (:test)
    static function testEpochIsANewMoon(logger as Test.Logger) as Lang.Boolean {
        var moment = new Time.Moment(NEW_MOON_EPOCH);
        var phase = Dial.moonPhase(moment);
        var distance = phase < 0.5 ? phase : 1.0 - phase;
        Test.assert(distance < 0.02);
        return true;
    }
}
