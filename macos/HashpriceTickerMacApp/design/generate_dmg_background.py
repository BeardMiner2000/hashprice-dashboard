#!/usr/bin/env python3

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont


WIDTH = 1200
HEIGHT = 760
OUTPUT = Path(__file__).with_name("dmg-background.png")
ARROW_SOURCE = Path("/Users/jl/Downloads/arrow.jpg")


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


def add_arrow(image: Image.Image):
    arrow = Image.open(ARROW_SOURCE).convert("RGBA")
    arrow = arrow.resize((500, 167), Image.Resampling.LANCZOS)
    pixels = arrow.load()
    for y in range(arrow.height):
        for x in range(arrow.width):
            r, g, b, a = pixels[x, y]
            if r > 235 and g > 235 and b > 235:
                pixels[x, y] = (255, 255, 255, 0)
            else:
                pixels[x, y] = (r, g, b, a)
    image.alpha_composite(arrow, (360, 352))


def main():
    image = Image.new("RGBA", (WIDTH, HEIGHT), (246, 246, 248, 255))
    gradient = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gradient_draw = ImageDraw.Draw(gradient)

    gradient_draw.ellipse((-120, 140, 500, 980), fill=(245, 171, 89, 38))
    gradient_draw.ellipse((320, 300, 820, 840), fill=(255, 255, 255, 125))
    gradient_draw.ellipse((560, 160, 1350, 920), fill=(132, 148, 255, 24))
    gradient = gradient.filter(ImageFilter.GaussianBlur(48))
    image.alpha_composite(gradient)

    draw = ImageDraw.Draw(image)
    title_font = load_font(42, bold=True)
    subtitle_font = load_font(20)
    detail_font = load_font(18)

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
    draw.text(
        (WIDTH / 2, 160),
        "Then right-click the app and choose Open.",
        font=detail_font,
        fill=(94, 103, 117, 255),
        anchor="mm",
    )

    add_arrow(image)

    image.save(OUTPUT)


if __name__ == "__main__":
    main()
