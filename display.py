"""Wetterzustände und ASCII-Bilder für die Terminalausgabe."""

from __future__ import annotations

import os
import re
import shutil
import sys
import time

ART = {
    "sun": r"""
                             .
                \            |            /
                 \           |           /
        `.        \      .-===== -.     /        .'
          `.       \  .='          '=. /       .'
            `.      .'    . . . .     '.     .'
     -----------   /   .             .  \   -----------
                  /  .    .-'''-.    .  \
                 |  .    /       \    .  |
   ==============|       |       |       |==============
                 |  .    \       /    .  |
                  \  .    '-...-'    .  /
     -----------   \   .             . /   -----------
            .'      '.    . . . .   .'      `.
          .'       /  '=._       _.='  \       `.
        .'        /      '====='       \        `.
                 /           |           \
              /\       /\    |    /\       /\
         ____/  \_____/  \___|___/  \_____/  \____
      __/          /         |        \            \__
""".strip("\n").splitlines(),
    "moon": r"""
        .          +                              .
                     .                *
             *                 _...-----..._
                           .-'         _..-'`
      +                  .'         .-'
                        /         .'
               .       /         /
                      |         |              +
         *            |         |     .
                      |          \
                       \          '.
      .                 '.          '-..____..-'
                 +        '-._             _.-'
                              '---.....---'
         .          *                            .
                         .          +
          /\                     /\
     /\  /  \     /\     /\    /  \       /\
 ___/  \/    \___/  \___/  \__/    \_____/  \____
       /          \         /           \
""".strip("\n").splitlines(),
    "cloud": r"""
                     .--------.
                  .-'          '-.
           .----.'                '.----.
        .-'                              '-.
      .'                                    '.
     (                                        )
      '._                                  _.'
         '----....________________....----'







              .       .           .
       ___        ____        ___       ____
  ____|   |__ ___|    |___ ___|   |__ __|    |___
      | . |  |   | [] |   |   | . |  |  | [] |
""".strip("\n").splitlines(),
    "partly": r"""
        \    |    /
         \ .---. /
          /     \    .--------.
    ---- (       ).-'          '-.
          \ .----.'                '.----.
        .-'                              '-.
      .'                                    '.
     (                                        )
      '._                                  _.'
         '----....________________....----'





                        /\
          /\      /\   /  \       /\
     ____/  \____/  \_/    \_____/  \_________
""".strip("\n").splitlines(),
    "fog": r"""
                       _...---..._
                 _..-''           ''-.._
           _..--'                       '--.._
          (___________________________________)

        ~~~~~~~~~~~~~~      ~~~~~~~~~~~~~~~~~~
    ~~~~~~~~~~~~~~~~~~~~      ~~~~~~~~~~~~~~~~~~~~
           ~~~~~~~~~~~~~~~~~~~~~~
      ~~~~~~~~~~~~~       ~~~~~~~~~~~~~~~~~~~~~
                        /\
    ~~~~~~~~~~~~~~~~~~~/  \~~~~~~~~~~~~~~~~~~~~~~
             /\       /    \        /\
    ~~~~~~~~/  \~~~~~/      \~~~~~~/  \~~~~~~~~~
           /    \   /        \    /    \
     ~~~~~~~~~~~~~~~~~    ~~~~~~~~~~~~~~~~~~~~~~
          ~~~~~~~~~~~~~~~~     ~~~~~~~~~~~~~
    ~~~~~~~~~~~~~~~~~~~~~~~      ~~~~~~~~~~~~~~~
        ~~~~~~~~~~~~~~     ~~~~~~~~~~~~~~~~~~~
""".strip("\n").splitlines(),
    "rain": r"""
                     .--------.
                  .-'          '-.
           .----.'                '.----.
        .-'                              '-.
      .'                                    '.
     (                                        )
      '._                                  _.'
         '----....________________....----'


         /    /    /    /    /    /    /    /
       /    /    /    /    /    /    /    /
          /    /    /    /    /    /    /    /
        /    /    /    /    /    /    /    /
      /    /    /    /    /    /    /    /    /
         /    /    /    /    /    /    /    /
     ~~~\_/~~~~\_/~~~~\_/~~~~\_/~~~~\_/~~~~\_/~~
        ~~~~       ~~~~       ~~~~       ~~~~
      ~~~~~~~~   ~~~~~~~~   ~~~~~~~~   ~~~~~~~~
""".strip("\n").splitlines(),
    "snow": r"""
                     .--------.
                  .-'          '-.
           .----.'                '.----.
        .-'                              '-.
      .'                                    '.
     (                                        )
      '._                                  _.'
         '----....________________....----'

           \|/          *          \|/
        * --+--    *         *    --+--   *
           /|\        \|/          /|\
              *      --+--    *         *
         \|/          /|\        \|/
        --+--    *         *    --+--
         /|\         /\          /|\
              /\    /  \    /\         /\
        /\   /  \__/ /\ \__/  \   /\  /  \
     __/  \_/ /\   \/  \/   /\ \_/  \/    \___
        *       *       *       *       *
""".strip("\n").splitlines(),
    "storm": r"""
                     .--------.
                  .-'          '-.
           .----.'                '.----.
        .-'       .::::.  .::::.          '-.
      .'       .::::::::::::::::::.         '.
     (        ::::::::::::::::::::::          )
      '._                                  _.'
         '----....________________....----'
           '    '   /   /    '    '     '
        '    '     /   /  '    '     '
           '      /   /___   '    '     '
        '    '   /      /  '    '    '
            '   /___   /     '    '    '
         '         /  /   '      '    '
            '     /  /      '     '
         '       /  /    '     '      '
                / /        '      '
      '    '   //    '    '     '     '
     ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ~~~~~~~~    ~~~~~~~~    ~~~~~~~~
""".strip("\n").splitlines(),
    "unknown": r"""
                 .----------------.
                /   .----------.   \
               |   /            \   |
                '--'        _   /   |
                           /   /   /
                          /   /_.-'
                         /   /
                         '---'
                          ___
                         (___)

                 NO WEATHER SIGNAL
""".strip("\n").splitlines(),
}


def weather_picture(code: int, is_day: bool) -> tuple[str, list[str]]:
    if code in (0, 1):
        return ("Sonnig", ART["sun"]) if is_day else ("Klar / meist klar", ART["moon"])
    if code == 2:
        return "Teilweise bewölkt", ART["partly"] if is_day else ART["cloud"]
    if code == 3:
        return "Bedeckt", ART["cloud"]
    if code in (45, 48):
        return "Nebel", ART["fog"]
    if code in (51, 53, 55, 56, 57):
        return "Nieselregen", ART["rain"]
    if code in (61, 63, 65, 66, 67, 80, 81, 82):
        return "Regen", ART["rain"]
    if code in (71, 73, 75, 77, 85, 86):
        return "Schnee", ART["snow"]
    if code in (95, 96, 97, 99):
        return "Gewitter", ART["storm"]
    return f"Unbekannter Wettercode ({code})", ART["unknown"]



def _paint(text: str, shade: int, color: bool, *, bold: bool = False) -> str:
    if not color or not text:
        return text
    weight = "1;" if bold else ""
    return f"\033[{weight}38;5;{shade}m{text}\033[0m"


def _paint_scene(art: list[str], code: int, is_day: bool, color: bool) -> list[str]:
    """Color clouds, precipitation and lightning independently."""
    if not color:
        return art
    painted = []
    for row, line in enumerate(art):
        pieces = []
        previous = None
        for column, char in enumerate(line):
            shade = 250 if row < 7 else 245
            if code in (0, 1):
                shade = (228, 220, 214, 208)[min(row // 5, 3)] if is_day else 147
                if not is_day and char in "*+":
                    shade = 229
                if row > 16:
                    shade = 66
            elif code in (95, 96, 97, 99):
                shade = 141 if row < 8 else 39
                if row >= 8 and char in "/_|":
                    shade = 226
                elif char == ':':
                    shade = 60
            elif code in (71, 73, 75, 77, 85, 86):
                shade = 255 if row < 8 else 159
                if char in '*+':
                    shade = 231
                elif row > 14:
                    shade = 111
            elif code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
                shade = 250 if row < 10 else 39
                if row > 15:
                    shade = 31
            elif code in (45, 48):
                shade = (250, 245, 240)[min(row // 6, 2)]
            elif code == 2 and row < 5 and column < (60, 60, 21, 18, 12)[row]:
                shade = 220 if is_day else 147
            if shade != previous:
                pieces.append(f"\033[1;38;5;{shade}m")
                previous = shade
            pieces.append(char)
        painted.append(''.join(pieces) + '\033[0m')
    return painted


DIGITS = {
    "0": ["###", "# #", "# #", "# #", "###"],
    "1": [" # ", "## ", " # ", " # ", "###"],
    "2": ["###", "  #", "###", "#  ", "###"],
    "3": ["###", "  #", "###", "  #", "###"],
    "4": ["# #", "# #", "###", "  #", "  #"],
    "5": ["###", "#  ", "###", "  #", "###"],
    "6": ["###", "#  ", "###", "# #", "###"],
    "7": ["###", "  #", "  #", "  #", "  #"],
    "8": ["###", "# #", "###", "# #", "###"],
    "9": ["###", "# #", "###", "  #", "###"],
    ".": [" ", " ", " ", " ", "#"],
    "-": ["   ", "   ", "###", "   ", "   "],
}


def animate_scene(art: list[str], code: int, is_day: bool, frame: int) -> list[str]:
    """Build a fresh frame; the original artwork always stays unchanged."""
    width = max(map(len, art))
    canvas = [list(line.ljust(width)) for line in art]
    storm = code in (95, 96, 97, 99)
    rain = code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82)
    if rain or storm:
        start, end = (8, 18) if storm else (10, 16)
        flash = frame % 48 in (2, 3, 7)
        for y in range(start, end):
            for x in range(width):
                # Preserve the bolt briefly; otherwise rain fills the sky.
                bolt = storm and art[y].ljust(width)[x] in '/_|'
                drop = "'" if storm else '/'
                canvas[y][x] = (art[y].ljust(width)[x] if bolt and flash else
                                drop if 5 < x < width - 5 and (x + y + frame) % 7 == 0 else ' ')
    elif code in (71, 73, 75, 77, 85, 86):
        for y in range(8, 15):
            canvas[y] = [' '] * width
        for particle in range(24):
            y = 8 + (particle * 3 + frame // 2) % 7
            x = 5 + (particle * 11 + frame // 5) % (width - 10)
            canvas[y][x] = '*+.'[(particle + frame // 8) % 3]
    elif code in (0, 1) and not is_day:
        for y, line in enumerate(art[:16]):
            for x, char in enumerate(line):
                if char in '*+' or (char == '.' and (x < 20 or x > 44)):
                    canvas[y][x] = ['.', '+', '*', '+'][(frame // 4 + x + y) % 4]
    elif code in (0, 1):
        for y, line in enumerate(art[:17]):
            for x, char in enumerate(line):
                if char in '-=|/\\' and (x < 17 or x > 39 or y < 3):
                    if (x + y + frame // 3) % 5 == 0:
                        canvas[y][x] = ' '
    elif code in (3, 2, 45, 48):
        # Shift the entire cloud silhouette; leave sun and ground fixed.
        offset = (0, 1, 2, 1, 0, -1, -2, -1)[(frame // 5) % 8]
        moving_rows = range(8) if code == 3 else range(len(art))
        if code == 2:
            # Keep this overlapping silhouette intact instead of tearing its edges
            # apart by moving only some rows. Animate the exposed sun rays.
            for y in (0, 1, 3):
                for x, char in enumerate(art[y]):
                    if x < 10 and char in '\\-' and (x + frame // 3) % 4 == 0:
                        canvas[y][x] = ' '
            return [''.join(line) for line in canvas]
        for y in moving_rows:
            if code in (45, 48) and '~' not in art[y]:
                continue
            line = art[y].ljust(width)
            canvas[y] = list((' ' * offset + line)[:width] if offset >= 0
                             else line[-offset:] + ' ' * -offset)
    return [''.join(line) for line in canvas]


def format_weather(
    city: str, weather: dict[str, float | int | str], *, color: bool = False,
    width: int | None = None, frame: int | None = None,
) -> str:

    if width is None:
        width = shutil.get_terminal_size(fallback=(110, 30)).columns
    code = int(weather["code"])
    is_day = bool(weather["is_day"])
    condition, art = weather_picture(code, is_day)
    if frame is not None:
        art = animate_scene(art, code, is_day, frame)
    temperature = f"{weather['temperature']:.1f}"
    big_number = [
        ' '.join(DIGITS[char][row] for char in temperature)
        for row in range(5)
    ]
    accent = (220 if is_day else 141) if code in (0, 1, 2) else (
        141 if code in (95, 96, 97, 99) else 45)
    timestamp = str(weather['time'])
    if timestamp[10:11] == 'T':
        timestamp = timestamp[:10] + ' ' + timestamp[11:]
    humidity = max(0, min(100, int(weather['humidity'])))
    meter = '#' * (humidity // 10) + '.' * (10 - humidity // 10)
    left = [
        ("01 / LIVE WEATHER", accent),
        (city.upper(), 231),
        (condition.upper(), accent),
        ("", 245),
        *[(line.replace('#', '@'), 231) for line in big_number],
        ("DEG C  /  AKTUELL", accent),
        ("", 245),
        (f"FEELS LIKE   {weather['feels_like']:.1f} C", 250),
        (f"HUMIDITY     {weather['humidity']} %", 250),
        (f"             [{meter}]", accent),
        (f"WIND         {weather['wind']:.1f} km/h", 250),
        ("", 245),
        ("LOCAL TIME / DATENZEIT", 245),
        (timestamp, 250),
    ]
    art_width = max(map(len, art))
    left_width = max(28, *(len(line) for line, _ in left))
    painted_art = _paint_scene(art, code, is_day, color)
    wide = width >= left_width + art_width + 9
    panel_width = left_width + art_width + 7 if wide else max(left_width + 4, art_width + 4)
    rule = _paint('+' + '-' * (panel_width - 2) + '+', accent, color)
    title = " ATMOSPHERE / WEATHER CLI "
    header = _paint('+' + title + '-' * max(0, panel_width - len(title) - 2) + '+', accent, color, bold=True)
    rows = [header]
    if wide:
        for i in range(max(len(left), len(art))):
            text, shade = left[i] if i < len(left) else ('', 245)
            sky = painted_art[i] if i < len(painted_art) else ''
            sky_padding = art_width - len(art[i]) if i < len(art) else art_width
            rows.append(_paint('| ', accent, color) + _paint(text.ljust(left_width), shade, color, bold=1 <= i <= 2 or 4 <= i <= 8) +
                        _paint(' | ', 238, color) + sky + ' ' * sky_padding + _paint(' |', accent, color))
    else:
        for i, (line, shade) in enumerate(left):
            rows.append(_paint('| ', accent, color) + _paint(line.ljust(panel_width - 4), shade, color, bold=1 <= i <= 2 or 4 <= i <= 8) + _paint(' |', accent, color))
        rows.append(rule)
        for i, sky in enumerate(painted_art):
            rows.append(_paint('| ', accent, color) + sky + ' ' * (panel_width - 4 - len(art[i])) + _paint(' |', accent, color))
    rows.append(rule)
    rows.append(_paint('  OPEN-METEO  /  WEATHER DATA', 245, color))
    return '\n'.join(rows)


class TerminalScreen:
    """Redraw in place and always restore the cursor and normal terminal."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled and sys.stdout.isatty() and os.environ.get('TERM') != 'dumb'

    def __enter__(self):
        if self.enabled:
            print('\033[?1049h\033[?25l', end='', flush=True)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.enabled:
            print('\033[0m\033[?25h\033[?1049l', end='', flush=True)

    def draw(self, content: str) -> None:
        if not self.enabled:
            print(content, flush=True)
            return
        columns, rows = shutil.get_terminal_size()
        lines = content.splitlines()
        if len(lines) > rows - 1:
            lines = lines[:max(0, rows - 2)] + [lines[-1]]
        clipped = []
        for line in lines:
            tokens = re.findall(r'\x1b\[[0-9;]*m|.', line)
            visible = 0
            parts = []
            for token in tokens:
                if not token.startswith('\033'):
                    if visible >= max(0, columns - 1):
                        break
                    visible += 1
                parts.append(token)
            clipped.append(''.join(parts) + '\033[0m\033[K')
        print('\033[H' + '\n'.join(clipped) + '\033[J', end='', flush=True)


if __name__ == '__main__':
    import argparse
    import os
    import sys

    parser = argparse.ArgumentParser(description='ASCII-Wetterszenen ohne API-Aufruf ansehen.')
    parser.add_argument('scene', choices=list(ART), nargs='?', default='storm')
    parser.add_argument('--animate', action='store_true', help='Animierte Vorschau (Ctrl+C beendet)')
    args = parser.parse_args()
    codes = dict(sun=0, moon=0, cloud=3, partly=2, fog=45, rain=63, snow=73, storm=95, unknown=999)
    sample = dict(temperature=10.3, feels_like=8.2, humidity=83, wind=28.4,
                  code=codes[args.scene], is_day=int(args.scene != 'moon'), time='DEMO / BEISPIELDATEN')
    try:
        with TerminalScreen(args.animate) as screen:
            frame = 0
            while True:
                content = format_weather(
                    'ASCII PREVIEW', sample,
                    color=sys.stdout.isatty() and 'NO_COLOR' not in os.environ,
                    frame=frame if args.animate else None,
                )
                screen.draw(content + ('\nVORSCHAU | Beenden: Ctrl+C' if args.animate else ''))
                if not args.animate or not screen.enabled:
                    break
                frame += 1
                time.sleep(0.15)
    except KeyboardInterrupt:
        pass
