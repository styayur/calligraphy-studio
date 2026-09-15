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


def logo(size: int, *, transparent: bool = False) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0) if transparent else PAPER)
    draw = ImageDraw.Draw(image)
    margin = int(size * 0.12)
    radius = int(size * 0.18)
    if not transparent:
        draw.rounded_rectangle(
            (margin, margin, size - margin, size - margin),
            radius=radius,
            fill=CINNABAR,
            outline=INK,
            width=max(2, size // 180),
        )
    else:
        draw.ellipse(
            (margin, margin, size - margin, size - margin),
            fill=CINNABAR,
            outline=INK,
            width=max(2, size // 180),
        )
    font_path = find_font()
    font = ImageFont.truetype(str(font_path), int(size * 0.52)) if font_path else ImageFont.load_default()
    text = "集"
    box = draw.textbbox((0, 0), text, font=font)
    x = (size - (box[2] - box[0])) / 2 - box[0]
    y = (size - (box[3] - box[1])) / 2 - box[1] - size * 0.02
    draw.text((x, y), text, font=font, fill=WHITE)
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
