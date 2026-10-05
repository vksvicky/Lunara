"""Lunara language catalog.

Japanese is three selectable scripts because Connect IQ has a single
Japanese device language. Chinese is simplified and traditional.
Hindi is an in-app choice: Garmin's language list has no Hindi code.

Hindi is stored here as real Devanagari. The watch font cannot shape
Devanagari, so each Hindi word is baked into one glyph in the private
use area and the generated Monkey C refers to that glyph.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

FACE_SMALL_PX = 11
FACE_LARGE_PX = 16
LEGEND_SMALL_PX = 12
LEGEND_LARGE_PX = 18
PUA_START = 0xE000

_DEVICE = {
    "eng": "eng",
    "fre": "fre",
    "spa": "spa",
    "zhs": "zhs",
    "zht": "zht",
    "jpn": "jpn_kanji",
    "ita": "ita",
    "deu": "deu",
}


@dataclass(frozen=True)
class Language:
    setting_id: int
    key: str
    native_name: str
    months: tuple[str, ...]
    weekdays: tuple[str, ...]
    automatic: str
    perpetual: tuple[str, str]
    moon_phases: tuple[str, ...]


def _lang(setting_id: int, key: str, native_name: str, months: list[str], weekdays: list[str], automatic: str, perpetual: tuple[str, str], moon_phases: tuple[str, ...]) -> Language:
    return Language(setting_id, key, native_name, tuple(months), tuple(weekdays), automatic, perpetual, tuple(moon_phases))


LANGUAGES: tuple[Language, ...] = (
    _lang(1, "eng", "English",
          ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"],
          ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"],
          "AUTOMATIC", ("PERPETUAL", "CALENDAR"),
          ("New Moon", "Crescent", "Quarter", "Gibbous", "Full Moon")),
    _lang(2, "fre", "Français",
          ["JANVIER", "FÉVRIER", "MARS", "AVRIL", "MAI", "JUIN", "JUILLET", "AOÛT", "SEPTEMBRE", "OCTOBRE", "NOVEMBRE", "DÉCEMBRE"],
          ["DIM", "LUN", "MAR", "MER", "JEU", "VEN", "SAM"],
          "AUTOMATIQUE", ("PERPÉTUEL", "CALENDRIER"),
          ("Nlle Lune", "Croissant", "Quartier", "Gibbeuse", "Pleine Lune")),
    _lang(3, "spa", "Español",
          ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"],
          ["DOM", "LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB"],
          "AUTOMÁTICO", ("PERPETUO", "CALENDARIO"),
          ("Luna Nueva", "Creciente", "Cuarto", "Gibosa", "Luna Llena")),
    _lang(4, "zhs", "简体中文",
          ["一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"],
          ["周日", "周一", "周二", "周三", "周四", "周五", "周六"],
          "自动", ("万年", "日历"),
          ("新月", "蛾眉月", "弦月", "凸月", "满月")),
    _lang(5, "zht", "繁體中文",
          ["一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"],
          ["週日", "週一", "週二", "週三", "週四", "週五", "週六"],
          "自動", ("萬年", "日曆"),
          ("新月", "蛾眉月", "弦月", "凸月", "滿月")),
    _lang(6, "jpn_kanji", "日本語（漢字）",
          ["一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"],
          ["日", "月", "火", "水", "木", "金", "土"],
          "自動", ("永久", "暦"),
          ("新月", "三日月", "弦月", "凸月", "満月")),
    _lang(7, "jpn_hira", "日本語（ひらがな）",
          ["いちがつ", "にがつ", "さんがつ", "しがつ", "ごがつ", "ろくがつ", "しちがつ", "はちがつ", "くがつ", "じゅうがつ", "じゅういちがつ", "じゅうにがつ"],
          ["にち", "げつ", "か", "すい", "もく", "きん", "ど"],
          "じどう", ("えいきゅう", "こよみ"),
          ("しんげつ", "みかづき", "ゆみはり", "とつげつ", "まんげつ")),
    _lang(8, "jpn_kata", "日本語（カタカナ）",
          ["イチガツ", "ニガツ", "サンガツ", "シガツ", "ゴガツ", "ロクガツ", "シチガツ", "ハチガツ", "クガツ", "ジュウガツ", "ジュウイチガツ", "ジュウニガツ"],
          ["ニチ", "ゲツ", "カ", "スイ", "モク", "キン", "ド"],
          "ジドウ", ("エイキュウ", "コヨミ"),
          ("シンゲツ", "ミカヅキ", "ユミハリ", "トツゲツ", "マンゲツ")),
    _lang(9, "hin", "हिन्दी",
          ["जनवरी", "फरवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"],
          ["रवि", "सोम", "मंगल", "बुध", "गुरु", "शुक्र", "शनि"],
          "स्वचालित", ("शाश्वत", "पंचांग"),
          ("अमावस्या", "बालचंद्र", "अर्धचंद्र", "कुबड़ा चाँद", "पूर्णिमा")),
    _lang(10, "ita", "Italiano",
          ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"],
          ["DOM", "LUN", "MAR", "MER", "GIO", "VEN", "SAB"],
          "AUTOMATICO", ("PERPETUO", "CALENDARIO"),
          ("Luna Nuova", "Crescente", "Quarto", "Gibbosa", "Luna Piena")),
    _lang(11, "deu", "Deutsch",
          ["JANUAR", "FEBRUAR", "MÄRZ", "APRIL", "MAI", "JUNI", "JULI", "AUGUST", "SEPTEMBER", "OKTOBER", "NOVEMBER", "DEZEMBER"],
          ["SON", "MON", "DIE", "MIT", "DON", "FRE", "SAM"],
          "AUTOMATIK", ("EWIGER", "KALENDER"),
          ("Neumond", "Sichel", "Viertel", "Dreiviertel", "Vollmond")),
)

_BY_ID = {lang.setting_id: lang.key for lang in LANGUAGES}


def device_language(setting: int | None, device: str) -> str:
    """Resolve a settings value and a Garmin device language to a catalog key."""
    if isinstance(setting, int) and setting in _BY_ID:
        return _BY_ID[setting]
    return _DEVICE.get(device, "eng")


def format_battery(level: float | None) -> str:
    """Percent text. None is an unknown reading. Values clamp to 0–100."""
    if level is None:
        return "--%"
    pct = int(math.floor(float(level) + 0.5))
    pct = max(0, min(100, pct))
    return f"{pct}%"


def shaped_words() -> list[tuple[str, str]]:
    """Hindi words as private-use glyphs. The watch draws one glyph per word."""
    hindi = next(lang for lang in LANGUAGES if lang.key == "hin")
    words: list[str] = []
    words.extend(hindi.months)
    words.extend(hindi.weekdays)
    words.append(hindi.automatic)
    words.extend(hindi.perpetual)
    words.extend(hindi.moon_phases)
    return [(chr(PUA_START + index), word) for index, word in enumerate(words)]


def _watch_text(lang: Language, kind: str, index: int = 0) -> str:
    shaped = {word: glyph for glyph, word in shaped_words()}
    if lang.key != "hin":
        if kind == "month":
            return lang.months[index]
        if kind == "weekday":
            return lang.weekdays[index]
        if kind == "automatic":
            return lang.automatic
        if kind == "moon_phase":
            return lang.moon_phases[index]
        return lang.perpetual[index]
    if kind == "month":
        return shaped[lang.months[index]]
    if kind == "weekday":
        return shaped[lang.weekdays[index]]
    if kind == "automatic":
        return shaped[lang.automatic]
    if kind == "moon_phase":
        return shaped[lang.moon_phases[index]]
    return shaped[lang.perpetual[index]]


def legend_shaped_words() -> list[tuple[str, str]]:
    """Hindi legend words, using the same private-use codes as the face font."""
    hindi = next(lang for lang in LANGUAGES if lang.key == "hin")
    shaped = {word: glyph for glyph, word in shaped_words()}
    words = [hindi.automatic, hindi.perpetual[0], hindi.perpetual[1]]
    words.extend(hindi.moon_phases)
    return [(shaped[word], word) for word in words]


def legend_charset() -> str:
    """Characters used under the battery, the lunar complication, and side legends.

    Hindi words are shaped glyphs. Includes ASCII alphanumeric and symbols for
    battery, percentage, illumination, lunar age, and tithi names.
    """
    chars: list[str] = list(
        "0123456789%-. "
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "abcdefghijklmnopqrstuvwxyz"
    )
    for lang in LANGUAGES:
        if lang.key == "hin":
            continue
        for text in (lang.automatic, *lang.perpetual, *lang.moon_phases):
            chars.extend(text)
    seen = []
    for char in chars:
        if char not in seen:
            seen.append(char)
    return "".join(seen)


def catalog_charset() -> str:
    """Characters drawn one-by-one. Hindi words are excluded; they are shaped glyphs."""
    chars: list[str] = []
    for lang in LANGUAGES:
        if lang.key == "hin":
            continue
        for text in (*lang.months, *lang.weekdays, lang.automatic, *lang.perpetual, *lang.moon_phases):
            chars.extend(text)
    chars.extend("0123456789%")
    seen = []
    for char in chars:
        if char not in seen:
            seen.append(char)
    return "".join(seen)


def render_monkey() -> str:
    """Monkey C tables. Language id 0 means follow the watch."""
    month_rows = []
    weekday_rows = []
    automatic_row = []
    perpetual_a = []
    perpetual_b = []
    moon_phase_rows = []
    for lang in LANGUAGES:
        month_rows.append(", ".join(_mc(_watch_text(lang, "month", i)) for i in range(12)))
        weekday_rows.append(", ".join(_mc(_watch_text(lang, "weekday", i)) for i in range(7)))
        automatic_row.append(_mc(_watch_text(lang, "automatic")))
        perpetual_a.append(_mc(_watch_text(lang, "perpetual", 0)))
        perpetual_b.append(_mc(_watch_text(lang, "perpetual", 1)))
        moon_phase_rows.append(", ".join(_mc(_watch_text(lang, "moon_phase", i)) for i in range(5)))

    def block(rows: list[str]) -> str:
        return ",\n".join(f"        [{row}]" for row in rows)

    return f"""import Toybox.Lang;
using Toybox.System;

// Generated by tools/languages.py. Do not edit by hand.
class FaceText {{
    private var _months as Lang.Array<Lang.Array<Lang.String>>;
    private var _weekdays as Lang.Array<Lang.Array<Lang.String>>;
    private var _automatic as Lang.Array<Lang.String>;
    private var _perpetualA as Lang.Array<Lang.String>;
    private var _perpetualB as Lang.Array<Lang.String>;
    private var _moonPhases as Lang.Array<Lang.Array<Lang.String>>;

    function initialize() {{
        _months = [
{block(month_rows)}
        ];
        _weekdays = [
{block(weekday_rows)}
        ];
        _automatic = [{", ".join(automatic_row)}];
        _perpetualA = [{", ".join(perpetual_a)}];
        _perpetualB = [{", ".join(perpetual_b)}];
        _moonPhases = [
{block(moon_phase_rows)}
        ];
    }}

    function month(languageId as Lang.Number, monthNumber as Lang.Number) as Lang.String {{
        return _months[languageId - 1][monthNumber - 1];
    }}

    function weekday(languageId as Lang.Number, dayOfWeek as Lang.Number) as Lang.String {{
        return _weekdays[languageId - 1][dayOfWeek - 1];
    }}

    function automatic(languageId as Lang.Number) as Lang.String {{
        return _automatic[languageId - 1];
    }}

    function perpetualLine(languageId as Lang.Number, line as Lang.Number) as Lang.String {{
        if (line == 0) {{
            return _perpetualA[languageId - 1];
        }}
        return _perpetualB[languageId - 1];
    }}

    function moonPhase(languageId as Lang.Number, phaseIndex as Lang.Number) as Lang.String {{
        return _moonPhases[languageId - 1][phaseIndex];
    }}

    static function resolve(setting, systemLanguage) as Lang.Number {{
        if (setting != null && setting != 0) {{
            var chosen = setting;
            if (chosen < 1 || chosen > 11) {{
                return 1;
            }}
            return chosen;
        }}
        if (systemLanguage == System.LANGUAGE_FRE) {{ return 2; }}
        if (systemLanguage == System.LANGUAGE_SPA) {{ return 3; }}
        if (systemLanguage == System.LANGUAGE_CHS) {{ return 4; }}
        if (systemLanguage == System.LANGUAGE_CHT) {{ return 5; }}
        if (systemLanguage == System.LANGUAGE_JPN) {{ return 6; }}
        if (systemLanguage == System.LANGUAGE_ITA) {{ return 10; }}
        if (systemLanguage == System.LANGUAGE_DEU) {{ return 11; }}
        return 1;
    }}
}}
"""


def _mc(text: str) -> str:
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
