"""Command line: python -m portrait_filters {riso,copper} INPUT OUTPUT [--width N] [--gamma G]"""
import argparse

from .filters import load, riso, copper_halftone


def main():
    p = argparse.ArgumentParser(prog="portrait_filters")
    p.add_argument("filter", choices=["riso", "copper"])
    p.add_argument("input", help="photo; a transparent PNG cutout gives the cleanest result")
    p.add_argument("output")
    p.add_argument("--width", type=int, default=480)
    p.add_argument("--gamma", type=float, default=1.0,
                   help=">1 darkens mid-tones (useful for flash photos), <1 lightens")
    a = p.parse_args()
    rgb, alpha = load(a.input, a.width)
    fn = riso if a.filter == "riso" else copper_halftone
    fn(rgb, alpha, gamma=a.gamma).save(a.output)
    print(f"wrote {a.output}")


if __name__ == "__main__":
    main()
