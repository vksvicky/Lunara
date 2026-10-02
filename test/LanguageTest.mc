import Toybox.Lang;
using Toybox.System;
using Toybox.Test;

(:test)
class LanguageTest {
    (:test)
    static function testExplicitLanguageWins(logger as Test.Logger) as Lang.Boolean {
        Test.assertEqual(FaceText.resolve(9, System.LANGUAGE_ENG), 9);
        Test.assertEqual(FaceText.resolve(8, System.LANGUAGE_ENG), 8);
        Test.assertEqual(FaceText.resolve(4, System.LANGUAGE_ENG), 4);
        Test.assertEqual(FaceText.resolve(5, System.LANGUAGE_ENG), 5);
        return true;
    }

    (:test)
    static function testSameAsWatchMapsTheDevice(logger as Test.Logger) as Lang.Boolean {
        Test.assertEqual(FaceText.resolve(0, System.LANGUAGE_FRE), 2);
        Test.assertEqual(FaceText.resolve(0, System.LANGUAGE_SPA), 3);
        Test.assertEqual(FaceText.resolve(0, System.LANGUAGE_CHS), 4);
        Test.assertEqual(FaceText.resolve(0, System.LANGUAGE_CHT), 5);
        Test.assertEqual(FaceText.resolve(0, System.LANGUAGE_JPN), 6);
        Test.assertEqual(FaceText.resolve(0, System.LANGUAGE_ITA), 10);
        Test.assertEqual(FaceText.resolve(0, System.LANGUAGE_DEU), 11);
        Test.assertEqual(FaceText.resolve(0, System.LANGUAGE_ENG), 1);
        Test.assertEqual(FaceText.resolve(null, System.LANGUAGE_FRE), 2);
        return true;
    }

    (:test)
    static function testUnknownSettingFallsBackToEnglish(logger as Test.Logger) as Lang.Boolean {
        Test.assertEqual(FaceText.resolve(99, System.LANGUAGE_JPN), 1);
        return true;
    }
}
