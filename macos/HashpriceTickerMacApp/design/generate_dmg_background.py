#!/usr/bin/env python3

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont


WIDTH = 1200
HEIGHT = 760
OUTPUT = Path(__file__).with_name("dmg-background.png")


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def cubic_point(p0, p1, p2, p3, t: float):
    mt = 1 - t
    x = (
        mt * mt * mt * p0[0]
        + 3 * mt * mt * t * p1[0]
        + 3 * mt * t * t * p2[0]
        + t * t * t * p3[0]
    )
    y = (
        mt * mt * mt * p0[1]
        + 3 * mt * mt * t * p1[1]
        + 3 * mt * t * t * p2[1]
        + t * t * t * p3[1]
    )
    return (x, y)


def draw_curved_arrow(draw: ImageDraw.ImageDraw):
    points = [
        cubic_point((410, 485), (575, 290), (845, 330), (1040, 425), step / 100)
        for step in range(101)
    ]
    draw.line(points, fill=(31, 31, 35, 255), width=22, joint="curve")
    head = [(1035, 425), (965, 385), (982, 458)]
    draw.polygon(head, fill=(31, 31, 35, 255))


def main():
    image = Image.new("RGBA", (WIDTH, HEIGHT), (246, 246, 248, 255))
    gradient = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gradient_draw = ImageDraw.Draw(gradient)

    gradient_draw.ellipse((-120, 140, 500, 980), fill=(245, 171, 89, 38))
    gradient_draw.ellipse((320, 300, 820, 840), fill=(255, 255, 255, 125))
    gradient_draw.ellipse((560, 160, 1350, 920), fill=(132, 148, 255, 24))
    gradient = gradient.filter(ImageFilter.GaussianBlur(48))
    image.alpha_composite(gradient)

    panel = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    panel_draw = ImageDraw.Draw(panel)
    panel_draw.rounded_rectangle(
        (14, 14, WIDTH - 14, HEIGHT - 14),
        radius=24,
        outline=(215, 218, 224, 255),
        width=2,
        fill=(255, 255, 255, 92),
    )
    panel = panel.filter(ImageFilter.GaussianBlur(0.4))
    image.alpha_composite(panel)

    draw = ImageDraw.Draw(image)
    title_font = load_font(42, bold=True)
    subtitle_font = load_font(20)
    caption_font = load_font(18)

    draw.text(
        (WIDTH / 2, 92),
        "Install Hashprice Ticker",
        font=title_font,
        fill=(26, 26, 31, 255),
        anchor="mm",
    )
    draw.text(
        (WIDTH / 2, 132),
        "Drag the app into Applications.",
        font=subtitle_font,
        fill=(94, 103, 117, 255),
        anchor="mm",
    )

    draw_curved_arrow(draw)

    draw.text(
        (246, 616),
        "Hashprice Ticker",
        font=caption_font,
        fill=(34, 39, 48, 255),
        anchor="mm",
    )
    draw.text(
        (960, 616),
        "Applications",
        font=caption_font,
        fill=(34, 39, 48, 255),
        anchor="mm",
    )

    image.save(OUTPUT)


if __name__ == "__main__":
    main()
