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

    function getSettingsView() {
        if (WatchUi has :WatchFaceDelegate) {
            var view = new LunaraSettingsView();
            return [ view, new LunaraSettingsDelegate(view) ];
        }
        return null;
    }

    function onSettingsChanged() {
        WatchUi.requestUpdate();
    }
}

