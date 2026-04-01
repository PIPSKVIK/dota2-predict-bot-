"""
Список героев с русскими алиасами для распознавания голоса.
"""
from typing import Optional

# Загружается один раз при старте бота из OpenDota API
_heroes_by_id: dict[int, dict] = {}
_heroes_by_name: dict[str, int] = {}  # localized_name.lower() -> id

# Русские алиасы (как люди говорят голосом)
RUSSIAN_ALIASES: dict[str, str] = {
    "антимаг": "Anti-Mage",
    "ам": "Anti-Mage",
    "акс": "Axe",
    "бладсикер": "Bloodseeker",
    "бс": "Bloodseeker",
    "кристалка": "Crystal Maiden",
    "см": "Crystal Maiden",
    "дроу": "Drow Ranger",
    "дроу рейнджер": "Drow Ranger",
    "земляшка": "Earthshaker",
    "шейкер": "Earthshaker",
    "джаг": "Juggernaut",
    "джаггернаут": "Juggernaut",
    "мипо": "Meepo",
    "миппо": "Meepo",
    "морф": "Morphling",
    "морфлинг": "Morphling",
    "некро": "Necrophos",
    "некрофос": "Necrophos",
    "пак": "Puck",
    "пудж": "Pudge",
    "разор": "Razor",
    "санд": "Sand King",
    "санд кинг": "Sand King",
    "шторм": "Storm Spirit",
    "шторм спирит": "Storm Spirit",
    "свен": "Sven",
    "тайни": "Tiny",
    "виспер": "Vengeful Spirit",
    "войд": "Faceless Void",
    "фейслес": "Faceless Void",
    "войд спирит": "Void Spirit",
    "врайт кинг": "Wraith King",
    "врайт": "Wraith King",
    "скелет кинг": "Wraith King",
    "зевс": "Zeus",
    "клинкз": "Clinkz",
    "клинк": "Clinkz",
    "энигма": "Enigma",
    "кunkka": "Kunkka",
    "кунка": "Kunkka",
    "лина": "Lina",
    "лион": "Lion",
    "найт сталкер": "Night Stalker",
    "НС": "Night Stalker",
    "обсидиан": "Outworld Destroyer",
    "ОД": "Outworld Destroyer",
    "квоп": "Queen of Pain",
    "куин": "Queen of Pain",
    "коп": "Queen of Pain",
    "ропа": "Riki",
    "рики": "Riki",
    "шадоу шаман": "Shadow Shaman",
    "шаман": "Shadow Shaman",
    "снайпер": "Sniper",
    "сорла": "Sorla Khan",
    "спектра": "Spectre",
    "спек": "Spectre",
    "шторм дух": "Storm Spirit",
    "тинкер": "Tinker",
    "уиндрейнджер": "Windranger",
    "ветер": "Windranger",
    "вингрейнджер": "Windranger",
    "виспа": "Wisp",
    "io": "Wisp",
    "ио": "Wisp",
    "зен": "Zen",
    "вейвер": "Weaver",
    "якиро": "Jakiro",
    "джарик": "Jakiro",
    "джарико": "Jakiro",
    "баратрум": "Batrider",
    "батрайдер": "Batrider",
    "баат": "Batrider",
    "ченн": "Chen",
    "директайд": "Tidehunter",
    "тайдхантер": "Tidehunter",
    "тайд": "Tidehunter",
    "кентавр": "Centaur Warrunner",
    "кент": "Centaur Warrunner",
    "магнус": "Magnus",
    "маг": "Magnus",
    "тимберсо": "Timbersaw",
    "тимбер": "Timbersaw",
    "bristle": "Bristleback",
    "бристл": "Bristleback",
    "бристлбек": "Bristleback",
    "скайрат": "Skywrath Mage",
    "скайврат": "Skywrath Mage",
    "абаддон": "Abaddon",
    "абадон": "Abaddon",
    "абаддон": "Abaddon",
    "аба": "Abaddon",
    "элдер титан": "Elder Titan",
    "ет": "Elder Titan",
    "леганта": "Legion Commander",
    "лк": "Legion Commander",
    "легион": "Legion Commander",
    "техиес": "Techies",
    "техис": "Techies",
    "мины": "Techies",
    "ем берлинк": "Ember Spirit",
    "эмбер": "Ember Spirit",
    "эмбер спирит": "Ember Spirit",
    "земля дух": "Earth Spirit",
    "ёрс спирит": "Earth Spirit",
    "терра": "Terrorblade",
    "тб": "Terrorblade",
    "террор": "Terrorblade",
    "феникс": "Phoenix",
    "оракл": "Oracle",
    "оракул": "Oracle",
    "трол": "Troll Warlord",
    "тролль": "Troll Warlord",
    "виппер": "Viper",
    "вайпер": "Viper",
    "роши": "Roshan",
    "нага": "Naga Siren",
    "нага сирен": "Naga Siren",
    "медуза": "Medusa",
    "ланая": "Leshrac",
    "лешрак": "Leshrac",
    "гирокоптер": "Gyrocopter",
    "гиро": "Gyrocopter",
    "хускар": "Huskar",
    "омникнайт": "Omniknight",
    "омник": "Omniknight",
    "дарк сир": "Dark Seer",
    "дарк": "Dark Seer",
    "клок": "Clockwerk",
    "клоквёрк": "Clockwerk",
    "дазл": "Dazzle",
    "дисраптор": "Disruptor",
    "диср": "Disruptor",
    "гандолин": "Undying",
    "андайнг": "Undying",
    "руббик": "Rubick",
    "рубик": "Rubick",
    "дота": "Death Prophet",
    "деф профет": "Death Prophet",
    "дп": "Death Prophet",
    "натурал спринг": "Nature's Prophet",
    "нп": "Nature's Prophet",
    "фурион": "Nature's Prophet",
    "сила природы": "Nature's Prophet",
    "инвокер": "Invoker",
    "инвок": "Invoker",
    "слардар": "Slardar",
    "вайп": "Viper",
    "урса": "Ursa",
    "лесник": "Nature's Prophet",
    "пангор": "Pangolier",
    "монки": "Monkey King",
    "монк": "Monkey King",
    "мк": "Monkey King",
    "дарк уилоу": "Dark Willow",
    "уилоу": "Dark Willow",
    "гримстрок": "Grimstroke",
    "грим": "Grimstroke",
    "марс": "Mars",
    "snapfire": "Snapfire",
    "снапфайр": "Snapfire",
    "войд спирит": "Void Spirit",
    "везир": "Vizier",
    "агс": "Arc Warden",
    "арк варден": "Arc Warden",
    "арк": "Arc Warden",
    "хоодвинк": "Hoodwink",
    "муэрта": "Muerta",
    "прайм": "Primal Beast",
    "примал": "Primal Beast",
    "марси": "Marci",
}


def init_heroes(heroes_data: list[dict]):
    global _heroes_by_id, _heroes_by_name
    for h in heroes_data:
        _heroes_by_id[h["id"]] = h
        _heroes_by_name[h["localized_name"].lower()] = h["id"]


def find_hero(query: str) -> Optional[dict]:
    """Найти героя по запросу (EN или RU алиас)"""
    q = query.strip().lower()

    # Прямое совпадение по английскому имени
    if q in _heroes_by_name:
        hero_id = _heroes_by_name[q]
        return _heroes_by_id[hero_id]

    # Точное совпадение по русскому алиасу
    if q in RUSSIAN_ALIASES:
        en_name = RUSSIAN_ALIASES[q].lower()
        if en_name in _heroes_by_name:
            hero_id = _heroes_by_name[en_name]
            return _heroes_by_id[hero_id]

    # Частичное совпадение по русскому алиасу
    for alias, en_name in RUSSIAN_ALIASES.items():
        if q in alias or alias in q:
            en = en_name.lower()
            if en in _heroes_by_name:
                return _heroes_by_id[_heroes_by_name[en]]

    # Частичное совпадение по английскому имени — предпочитаем самое длинное совпадение
    candidates = [(name, hero_id) for name, hero_id in _heroes_by_name.items() if q in name]
    if candidates:
        candidates.sort(key=lambda x: len(x[0]))  # короткое = более точное совпадение
        return _heroes_by_id[candidates[0][1]]

    return None


def suggest_heroes(query: str, limit: int = 5) -> list[dict]:
    """Топ-N героев похожих на запрос (для подсказок)"""
    q = query.strip().lower()
    if not q:
        return []
    results = []
    for name, hero_id in _heroes_by_name.items():
        if name.startswith(q):
            results.append((0, _heroes_by_id[hero_id]))  # приоритет 0 — начало слова
        elif q in name:
            results.append((1, _heroes_by_id[hero_id]))
    results.sort(key=lambda x: (x[0], len(x[1]["localized_name"])))
    return [h for _, h in results[:limit]]


def get_all_heroes() -> list[dict]:
    return list(_heroes_by_id.values())
