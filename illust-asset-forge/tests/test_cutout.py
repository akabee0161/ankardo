from PIL import Image, ImageDraw

from artgen.config import ClearColor, CutoutOutput
from artgen.cutout import clear_background, output_name, output_size, prepared_mask, render

WHITE = (255, 255, 255)
GRAY = (90, 90, 90)
RED = (255, 0, 0)


def canvas(size=20, color=WHITE):
    return Image.new("RGB", (size, size), color)


def test_output_name_and_size():
    assert output_name("face_hurt.png", "-small") == "face_hurt-small.png"
    assert output_name("face.png", "") == "face.png"
    assert output_size((0, 0, 600, 300), 256) == (256, 128)
    assert output_size((10, 10, 110, 60), None) == (100, 50)


def test_render_matte_uses_mask_as_alpha_and_marks_check_red():
    im = canvas(64, color=WHITE)
    mask = Image.new("L", (64, 64), 255)
    ImageDraw.Draw(mask).rectangle([32, 0, 63, 63], fill=0)
    out, check = render(im, CutoutOutput("", None, None), "matte", (), mask)
    assert out.mode == "RGBA" and out.size == (64, 64) and check.mode == "RGB"
    assert out.getpixel((10, 10))[3] == 255 and out.getpixel((50, 10))[3] == 0
    assert check.getpixel((50, 10)) == RED and check.getpixel((10, 10)) == WHITE


def test_render_matte_crops_mask_with_box():
    im = canvas(64, color=GRAY)
    mask = Image.new("L", (64, 64), 0)
    ImageDraw.Draw(mask).rectangle([32, 32, 63, 63], fill=255)
    out, check = render(im, CutoutOutput("", (32, 32, 64, 64), 16), "matte", (), mask)
    assert out.size == (16, 16) and check.size == (32, 32)
    assert all(out.getpixel((x, y))[3] == 255 for x in range(16) for y in range(16))


def test_prepared_mask_hardens_and_erases_polygons():
    mask = Image.new("L", (20, 20), 150)
    out = prepared_mask(mask, (((0, 0), (9, 0), (9, 9), (0, 9)),))
    assert out.getpixel((15, 15)) == round((150 - 128) * 255 / 72)
    assert out.getpixel((4, 4)) == 0


def test_clear_background_outer_white_only():
    im = canvas()
    d = ImageDraw.Draw(im)
    d.rectangle([3, 3, 16, 16], fill=GRAY)
    d.rectangle([8, 8, 11, 11], fill=WHITE)
    out, check = clear_background(im, ())
    assert out.getpixel((0, 0))[3] == 0 and check.getpixel((0, 0)) == RED
    assert out.getpixel((9, 9))[3] == 255 and check.getpixel((9, 9)) != RED


def test_render_colors_clears_white_connected_to_edges_only():
    im = canvas(40)
    d = ImageDraw.Draw(im)
    d.rectangle([5, 5, 34, 34], fill=GRAY)
    d.rectangle([15, 15, 24, 24], fill=WHITE)
    out, _ = render(im, CutoutOutput("", None, None), "colors", (), None)
    assert out.getpixel((1, 1))[3] == 0
    assert out.getpixel((20, 20))[3] == 255


def test_render_colors_min_rg_keeps_cream():
    beige, cream = (205, 182, 168), (251, 243, 228)
    im = canvas(color=beige)
    ImageDraw.Draw(im).rectangle([0, 10, 19, 19], fill=cream)
    out, _ = render(im, CutoutOutput("", None, None), "colors", (ClearColor(160, 28, 18, min_rg=16),), None)
    assert out.getpixel((10, 2))[3] == 0
    assert out.getpixel((10, 15))[3] == 255


def test_clear_color_is_cleared_only_when_connected():
    cream = (236, 226, 218)
    im = canvas()
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 4, 19], fill=cream)
    d.rectangle([7, 7, 16, 16], fill=GRAY)
    d.rectangle([10, 10, 12, 12], fill=cream)
    out, _ = clear_background(im, [ClearColor(214, 14, 16)])
    assert out.getpixel((2, 10))[3] == 0
    assert out.getpixel((11, 11))[3] == 255


def test_render_none_keeps_everything_opaque():
    im = canvas(100, color=WHITE)
    out, check = render(im, CutoutOutput("", (0, 0, 100, 50), 20), "none", (), None)
    assert out.size == (20, 10)
    assert all(out.getpixel((x, y))[3] == 255 for x in range(20) for y in range(10))
    assert check.size == (100, 50) and check.getpixel((5, 5)) == WHITE


def test_render_box_none_uses_whole_image():
    im = canvas(64, color=WHITE)
    out, check = render(im, CutoutOutput("", None, 32), "none", (), None)
    assert out.size == (32, 32) and check.size == (64, 64)


def test_render_resize_does_not_darken_transparent_edges():
    im = canvas(64)
    ImageDraw.Draw(im).rectangle([20, 20, 43, 43], fill=(255, 0, 0))
    out, _ = render(im, CutoutOutput("", None, 16), "colors", (), None)
    edge = [out.getpixel((x, y)) for x in range(16) for y in range(16) if 0 < out.getpixel((x, y))[3] < 255]
    assert edge and all(p[0] >= 200 for p in edge)
