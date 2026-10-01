from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PAPER = (244, 239, 229, 255)
INK = (24, 21, 18, 255)
CINNABAR = (162, 58, 43, 255)
WHITE = (255, 248, 237, 255)


def find_font() -> Path | None:
    candidates = [
        Path("C:/Windows/Fonts/simkai.ttf"),
        Path("C:/Windows/Fonts/msyhbd.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"),
    ]
    return next((path for path in candidates if path.is_file()), None)


DARK = (15, 23, 42, 255)
PURPLE = (217, 70, 239, 255)


def _glyph_points(scale: float) -> list[tuple[float, float]]:
    segments = [
        ((48, 14), (28, 26), (22, 42), (28, 58)),
        ((28, 58), (31, 66), (38, 72), (48, 76)),
        ((48, 76), (62, 72), (68, 64), (70, 52)),
        ((70, 52), (56, 50), (47, 48), (45, 41)),
        ((45, 41), (62, 35), (70, 25), (74, 16)),
    ]
    points: list[tuple[float, float]] = []
    for (x0, y0), (x1, y1), (x2, y2), (x3, y3) in segments:
        for i in range(1, 41):
            t = i / 40.0
            u = 1.0 - t
            x = u**3 * x0 + 3 * u**2 * t * x1 + 3 * u * t**2 * x2 + t**3 * x3
            y = u**3 * y0 + 3 * u**2 * t * y1 + 3 * u * t**2 * y2 + t**3 * y3
            points.append((x * scale, y * scale))
    points.append((48 * scale, 14 * scale))  # Z closes the path
    return points


def logo(size: int, *, transparent: bool = False) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    scale = size / 96.0

    if not transparent:
        margin = max(1, int(size * 0.03))
        radius = int(size * 0.20)
        draw.rounded_rectangle(
            (margin, margin, size - margin, size - margin),
            radius=radius,
            fill=DARK,
        )

    border_inset = max(1, int(size * 0.035))
    draw.rounded_rectangle(
        (border_inset, border_inset, size - border_inset, size - border_inset),
        radius=int(size * 0.18),
        outline=PURPLE,
        width=max(1, size // 32),
    )

    stroke = max(2, int(size * 4 / 96.0) + 1)
    draw.line(_glyph_points(scale), fill=PURPLE, width=stroke, joint="curve")

    dot_r = max(2, int(size * 5 / 96.0))
    cx, cy = 48 * scale, 55 * scale
    draw.ellipse((cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r), fill=PURPLE)
    return image


def splash(size: int) -> Image.Image:
    image = Image.new("RGBA", (size, size), PAPER)
    icon = logo(int(size * 0.34), transparent=False)
    offset = (size - icon.width) // 2
    image.alpha_composite(icon, (offset, offset))
    return image


def _android_splash(size: tuple[int, int]) -> Image.Image:
    image = Image.new("RGBA", size, PAPER)
    diameter = int(min(size) * 0.34)
    icon = logo(diameter)
    image.alpha_composite(icon, ((size[0] - diameter) // 2, (size[1] - diameter) // 2))
    return image


def generate_android_assets(project_root: Path) -> None:
    resources = project_root / "apps" / "web" / "android" / "app" / "src" / "main" / "res"
    if not resources.is_dir():
        return
    for directory in resources.glob("mipmap-*"):
        for name in ("ic_launcher.png", "ic_launcher_round.png", "ic_launcher_foreground.png"):
            target = directory / name
            if not target.is_file():
                continue
            with Image.open(target) as existing:
                size = existing.size[0]
            if name == "ic_launcher.png":
                logo(size).save(target)
            else:
                logo(size, transparent=True).save(target)
    for target in resources.glob("drawable*/splash.png"):
        with Image.open(target) as existing:
            size = existing.size
        _android_splash(size).save(target)


def main() -> None:
    desktop = PROJECT_ROOT / "apps" / "desktop" / "build"
    mobile = PROJECT_ROOT / "apps" / "web" / "assets"
    desktop.mkdir(parents=True, exist_ok=True)
    mobile.mkdir(parents=True, exist_ok=True)

    desktop_icon = logo(512)
    desktop_icon.save(desktop / "icon.png")
    desktop_icon.save(
        desktop / "icon.ico",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    logo(1024).save(mobile / "icon-only.png")
    logo(1024, transparent=True).save(mobile / "icon-foreground.png")
    Image.new("RGBA", (1024, 1024), PAPER).save(mobile / "icon-background.png")
    splash(2732).save(mobile / "splash.png")
    generate_android_assets(PROJECT_ROOT)
    print("generated desktop and Capacitor brand assets")


if __name__ == "__main__":
    main()
