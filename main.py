import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import os
import sys
import time
from urllib.error import URLError

from display import TerminalScreen, format_weather
from weather import get_coordinates, get_weather


def positive_minutes(value: str) -> int:
    try:
        minutes = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Das Intervall muss eine ganze Zahl sein.") from None
    if minutes < 1:
        raise argparse.ArgumentTypeError("Das Intervall muss mindestens 1 Minute betragen.")
    return minutes


def main() -> int:
    parser = argparse.ArgumentParser(description="Aktuelles Wetter mit ASCII-Wetterbild.")
    parser.add_argument("city", help='Stadt, z. B. Berlin oder "Bad Homburg"')
    parser.add_argument(
        "--interval", type=positive_minutes, default=5, metavar="MINUTEN",
        help="Abstand zwischen Abrufen in Minuten (Standard: 5)",
    )
    parser.add_argument("--once", action="store_true", help="Nur einmal abrufen und beenden")
    parser.add_argument("--no-animation", action="store_true", help="Animation ausschalten")
    args = parser.parse_args()

    try:
        latitude, longitude = get_coordinates(args.city)
    except (URLError, OSError):
        print("Ortssuche fehlgeschlagen: Verbindung zur API nicht möglich.", file=sys.stderr)
        return 1
    except (ValueError, KeyError, TypeError, IndexError):
        print("Stadt nicht gefunden oder ungültige Antwort der Ortssuche.", file=sys.stderr)
        return 1

    last_weather = None
    last_success = None
    error = None
    next_fetch = 0.0
    pending = None
    frame = 0
    color = sys.stdout.isatty() and "NO_COLOR" not in os.environ

    # Network calls run in one worker so the scene keeps moving during requests.
    with ThreadPoolExecutor(max_workers=1) as worker, TerminalScreen(not args.once) as screen:
        animate = screen.enabled and not args.no_animation
        while True:
            now = time.monotonic()
            changed = False
            if pending is None and now >= next_fetch:
                pending = worker.submit(get_weather, latitude, longitude)
            if pending is not None and pending.done():
                try:
                    last_weather = pending.result()
                    last_success = datetime.now().astimezone().strftime("%H:%M:%S %Z")
                    error = None
                except (URLError, OSError):
                    error = "Verbindung fehlgeschlagen."
                except (ValueError, KeyError, TypeError):
                    error = "Ungültige Wetterantwort erhalten."
                pending = None
                next_fetch = time.monotonic() + args.interval * 60
                changed = True

            if changed or animate:
                lines = []
                if last_weather is not None:
                    lines.append(format_weather(
                        args.city, last_weather, color=color,
                        frame=frame if animate else None,
                    ))
                    lines.append(f"\nLetzter erfolgreicher Abruf: {last_success}")
                else:
                    lines.append(f"Wetter für {args.city} wird geladen ...")
                if error:
                    lines.append(error)
                    if last_weather is not None:
                        lines.append("Angezeigt werden die letzten verfügbaren Daten.")
                if not args.once:
                    status = ("Wetterdaten werden aktualisiert ..." if pending is not None else
                              f"Nächster Abruf in {max(0, int(next_fetch - now))} s")
                    lines.append(f"{status} | Beenden: Ctrl+C")
                screen.draw("\n".join(lines))
            if args.once and changed:
                return 1 if error else 0
            frame += 1
            time.sleep(0.15 if animate else 0.1 if pending is not None else 0.5)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nWeather CLI beendet.")
