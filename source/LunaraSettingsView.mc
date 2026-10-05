import Toybox.Lang;
using Toybox.Application;
using Toybox.Graphics;
using Toybox.System;
using Toybox.WatchUi;

(:typecheck(false))
class LunaraSettingsView extends WatchUi.View {
    private var currentIndex = 0;
    private var menuItems = [
        ["Language", "Language"],
        ["Lunar Info (3H)", "LunarDisplayMode"],
        ["Battery (9H)", "BatteryStyle"],
        ["Reset Defaults", "ResetDefaults"]
    ];

    function initialize() {
        View.initialize();
    }

    function getSelectedIndex() { return currentIndex; }
    function setSelectedIndex(idx) { currentIndex = idx; }
    function getMenuItems() { return menuItems; }

    function onUpdate(dc) {
        var w = dc.getWidth();
        var h = dc.getHeight();
        var cx = w / 2;
        var cy = h / 2;
        var scale  = w / 260.0;
        var sz     = (4.5 * scale).toNumber();
        var arrowH = (4.5 * scale).toNumber();

        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear();

        // 1. Resolve active item details
        var itemKey    = menuItems[currentIndex][1];
        var itemTitle  = menuItems[currentIndex][0];
        var headerText = "SETTING " + (currentIndex + 1) + " OF " + menuItems.size();
        var subText    = "";
        var subColor   = 0xD07A4A; // Luxury terracotta accent

        if (itemKey.equals("Language")) {
            var langVal = getPropVal("Language", 0);
            var langNames = [
                "Auto (Watch)",
                "English",
                "Français",
                "Español",
                "Chinese (Simp)",
                "Chinese (Trad)",
                "Japanese (Kanji)",
                "Japanese (Hira)",
                "Japanese (Kata)",
                "Hindi",
                "Italiano",
                "Deutsch"
            ];
            subText = (langVal >= 0 && langVal < langNames.size()) ? langNames[langVal] : langNames[0];
            subColor = 0xE09568;
        } else if (itemKey.equals("LunarDisplayMode")) {
            var lunarVal = getPropVal("LunarDisplayMode", 0);
            var lunarNames = [
                "Phase Name",
                "Illumination %",
                "Hindu Panchang",
                "Lunar Age (Days)",
                "Hidden / None"
            ];
            subText = (lunarVal >= 0 && lunarVal < lunarNames.size()) ? lunarNames[lunarVal] : lunarNames[0];
            subColor = 0x82A8D8; // Lunar sky blue
        } else if (itemKey.equals("BatteryStyle")) {
            var battVal = getPropVal("BatteryStyle", 0);
            var battNames = [
                "Time of Day",
                "Classic Palette",
                "Morning Sky",
                "Golden Day",
                "Sunset Flame",
                "Night Indigo"
            ];
            subText = (battVal >= 0 && battVal < battNames.size()) ? battNames[battVal] : battNames[0];
            subColor = 0x72B095; // Sage green
        } else if (itemKey.equals("ResetDefaults")) {
            subText = "Tap to Reset All";
            subColor = 0xDE5D5D;
        }

        // 2. Exact Font Height Metrics & Even Gap Formula
        var fontHeader = Graphics.FONT_XTINY;
        var fontTitle  = Graphics.FONT_SMALL;
        var fontSub    = Graphics.FONT_TINY;

        var hHeader = dc.getFontHeight(fontHeader);
        var hTitle  = dc.getFontHeight(fontTitle);
        var hSub    = dc.getFontHeight(fontSub);

        var uniformGap = (16 * scale).toNumber();
        var itemGap    = (4 * scale).toNumber();

        // Total central block height (title + gap + sublabel)
        var totalTextH = hTitle + itemGap + hSub;

        // Title Top Y (Centered at cy)
        var titleY = cy - (totalTextH / 2);
        var subY   = titleY + hTitle + itemGap;

        // Top Chevron Y (Base placed uniformGap above titleY)
        var pyUp = titleY - uniformGap;

        // Bottom Chevron Y (Base placed uniformGap below subY + hSub)
        var pyDown = subY + hSub + uniformGap;

        // Header Text Y (Placed uniformGap above top chevron tip)
        var headerY = (pyUp - arrowH) - uniformGap - hHeader;

        // 3. Draw Header
        dc.setColor(Graphics.COLOR_DK_GRAY, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, headerY, fontHeader, headerText, Graphics.TEXT_JUSTIFY_CENTER);

        // 4. Draw Top Vector Chevron ▲
        dc.setColor(Graphics.COLOR_LT_GRAY, Graphics.COLOR_TRANSPARENT);
        dc.fillPolygon([
            [cx - sz, pyUp],
            [cx + sz, pyUp],
            [cx, pyUp - arrowH]
        ]);

        // 5. Draw Title
        dc.setColor(0xF0ECE1, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, titleY, fontTitle, itemTitle, Graphics.TEXT_JUSTIFY_CENTER);

        // 6. Draw Sublabel Value in Vibrant Accent Color
        dc.setColor(subColor, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, subY, fontSub, subText, Graphics.TEXT_JUSTIFY_CENTER);

        // 7. Draw Bottom Vector Chevron ▼
        dc.setColor(Graphics.COLOR_LT_GRAY, Graphics.COLOR_TRANSPARENT);
        dc.fillPolygon([
            [cx - sz, pyDown],
            [cx + sz, pyDown],
            [cx, pyDown + arrowH]
        ]);

        // 8. Right Edge Page Indicator Dots
        var dotX = w - (14 * scale).toNumber();
        var startY = cy - (16 * scale).toNumber();
        var dotSpacing = (9 * scale).toNumber();
        for (var i = 0; i < menuItems.size(); i++) {
            var dotY = startY + i * dotSpacing;
            if (i == currentIndex) {
                dc.setColor(0xF0ECE1, Graphics.COLOR_TRANSPARENT);
                dc.fillCircle(dotX, dotY, (2.5 * scale).toNumber());
            } else {
                dc.setColor(Graphics.COLOR_DK_GRAY, Graphics.COLOR_TRANSPARENT);
                dc.fillCircle(dotX, dotY, (1.5 * scale).toNumber());
            }
        }

        // 9. Instruction hint (two lines comfortably fit within round screen chords)
        var footerY = pyDown + arrowH + (8 * scale).toNumber();
        dc.setColor(Graphics.COLOR_DK_GRAY, Graphics.COLOR_TRANSPARENT);
        dc.drawText(cx, footerY, fontHeader, "SELECT: Change", Graphics.TEXT_JUSTIFY_CENTER);
        dc.drawText(cx, footerY + hHeader, fontHeader, "BACK: Exit", Graphics.TEXT_JUSTIFY_CENTER);
    }

    function getPropVal(key, defaultVal) {
        try {
            if (Application has :Properties) {
                var v = Application.Properties.getValue(key);
                if (v != null) { return v; }
            }
        } catch (e) {}
        return defaultVal;
    }
}

(:typecheck(false))
class LunaraSettingsDelegate extends WatchUi.BehaviorDelegate {
    private var customView;

    function initialize(view) {
        BehaviorDelegate.initialize();
        customView = view;
    }

    function onNextPage() { return cycleDown(); }
    function onPreviousPage() { return cycleUp(); }

    function onKey(evt) {
        var key = evt.getKey();
        if (key == WatchUi.KEY_DOWN) {
            return cycleDown();
        } else if (key == WatchUi.KEY_UP) {
            return cycleUp();
        } else if (key == WatchUi.KEY_ENTER || key == WatchUi.KEY_START) {
            return changeCurrentValue();
        }
        return false;
    }

    function onSwipe(evt) {
        var dir = evt.getDirection();
        if (dir == WatchUi.SWIPE_DOWN) {
            return cycleDown();
        } else if (dir == WatchUi.SWIPE_UP) {
            return cycleUp();
        }
        return false;
    }

    function cycleDown() {
        var idx = customView.getSelectedIndex();
        var items = customView.getMenuItems();
        customView.setSelectedIndex((idx + 1) % items.size());
        WatchUi.requestUpdate();
        return true;
    }

    function cycleUp() {
        var idx = customView.getSelectedIndex();
        var items = customView.getMenuItems();
        customView.setSelectedIndex((idx - 1 + items.size()) % items.size());
        WatchUi.requestUpdate();
        return true;
    }

    function onTap(evt) {
        var xy = evt.getCoordinates();
        var y = xy[1];
        var screenH = System.getDeviceSettings().screenHeight;
        var cy = screenH / 2;

        if (y < cy - 25) {
            return cycleUp();
        } else if (y > cy + 25) {
            return cycleDown();
        } else {
            return changeCurrentValue();
        }
    }

    function changeCurrentValue() {
        var idx = customView.getSelectedIndex();
        var items = customView.getMenuItems();
        var itemKey = items[idx][1];

        if (itemKey.equals("Language")) {
            var current = getPropVal("Language", 0);
            current = (current + 1) % 12; // 0..11
            setPropVal("Language", current);
        } else if (itemKey.equals("LunarDisplayMode")) {
            var current = getPropVal("LunarDisplayMode", 0);
            current = (current + 1) % 5; // 0..4
            setPropVal("LunarDisplayMode", current);
        } else if (itemKey.equals("BatteryStyle")) {
            var current = getPropVal("BatteryStyle", 0);
            current = (current + 1) % 6; // 0..5
            setPropVal("BatteryStyle", current);
        } else if (itemKey.equals("ResetDefaults")) {
            setPropVal("Language", 0);
            setPropVal("LunarDisplayMode", 0);
            setPropVal("BatteryStyle", 0);
        }

        WatchUi.requestUpdate();
        return true;
    }

    function onBack() {
        WatchUi.popView(WatchUi.SLIDE_IMMEDIATE);
        return true;
    }

    function getPropVal(key, defaultVal) {
        try {
            if (Application has :Properties) {
                var v = Application.Properties.getValue(key);
                if (v != null) { return v; }
            }
        } catch (e) {}
        return defaultVal;
    }

    function setPropVal(key, val) {
        try {
            if (Application has :Properties) {
                Application.Properties.setValue(key, val);
            }
        } catch (e) {}
    }
}
