using Toybox.Application;
using Toybox.WatchUi;

class LunaraApp extends Application.AppBase {
    function initialize() {
        AppBase.initialize();
    }

    function onStart(state) {
    }

    function onStop(state) {
    }

    function getInitialView() {
        return [ new LunaraView() ];
    }

    function onSettingsChanged() {
        WatchUi.requestUpdate();
    }
}
