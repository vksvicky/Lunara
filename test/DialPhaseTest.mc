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
        Test.assertEqual(LunarComplication.text(0.50, LunarComplication.MODE_ILLUMINATION), "100% Wax");
        Test.assertEqual(LunarComplication.text(0.75, LunarComplication.MODE_ILLUMINATION), "50% Wan");
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

    (:test)
    static function testMonthMilestones(logger as Test.Logger) as Lang.Boolean {
        var moment = new Time.Moment(NEW_MOON_EPOCH);
        var milestones = Dial.getMonthMilestones(moment);
        Test.assertEqual(milestones.size(), 4);
        Test.assert(milestones[0] >= 5 && milestones[0] <= 8);
        return true;
    }
}
