from app.image.WandManip import wand
from app.image.decorators import executor
from wand.image import Image

__all__ = (
    "charcoal",
    "floor",
    "grayscale",
    "night",
    "swirl",
    "paint",
    "polaroid",
    "poster",
    "sepia",
    "solar",
    "rainbow",
    "magik",
    "cube",)


@executor
@wand
def sepia(image):
    image.sepia_tone(threshold=0.8)
    return image


@executor
@wand
def rainbow(image):
    frequency = 3
    phase_shift = -90
    amplitude = 0.2
    bias = 0.7
    image.function('sinusoid', [frequency, phase_shift, amplitude, bias])
    return image


@executor
@wand
def grayscale(image):
    image.transform_colorspace("gray")
    return image


@executor
@wand
def charcoal(image):
    image.transform_colorspace("gray")
    image.sketch(0.5, 0.0, 98.0)
    return image


@executor
@wand
def solar(image):
    image.solarize(threshold=0.5 * image.quantum_range)
    return image


@executor
@wand
def paint(image):
    image.oil_paint(sigma=3)
    return image


@executor
@wand
def poster(image):
    image.posterize(2)
    return image


@executor
@wand
def floor(image):
    print("floor")
    image.virtual_pixel = "tile"
    image.resize(300, 300)
    x, y = image.width, image.height
    arguments = (0, 0, 77, 153, x, 0, 179, 153, 0, y, 51, 255, x, y, 204, 255)
    image.distort("perspective", arguments)
    return image


@executor
@wand
def swirl(image):
    image.swirl(degree=-90)
    return image


@executor
@wand
def polaroid(image):
    image.polaroid()
    return image


@executor
@wand
def edge(image):
    image.alpha_channel = False
    image.transform_colorspace("gray")
    image.edge(2)
    return image


@executor
@wand
def night(image):
    image.blue_shift(factor=1.25)
    return image


@executor
@wand
def magik(image, scale: int = None):
    """
    https://github.com/lolaristocrat/magik/blob/master/magik.py
    Heavily inspired by this
    """
    image.liquid_rescale(width=int(image.width * 0.5),
                         height=int(image.height * 0.5),
                         delta_x=int(0.5 * scale) if scale else 1,
                         rigidity=0)
    image.liquid_rescale(
        width=int(image.width * 1.5),
        height=int(image.height * 1.5),
        delta_x=scale or 2,
        rigidity=0,
    )

    return image


@executor
@wand
def cube(image):
    
    def p(x):
        return int(x / 3)
    
    image.resize(p(1000), p(860))
    image.format = "png"
    image.alpha_channel = "opaque"
    
    image1 = image
    image2 = image1.clone()
    
    final = Image(width=p(2550), height=p(760) * 3)
    final.format = "png"
    
    image1.shear(background="none", x=(-30))
    image1.rotate(-30)
    final.composite(image1, left=p(250), top=p(-230) + p(118))
    image1.close()
    
    image2.shear(background="rgba(0,0,0,0)", x=30)
    image2.rotate(-30)
    image3 = image2.clone()
    final.composite(image2, left=p(750) - p(72), top=p(630))
    image2.close()
    
    image3.flop()
    final.composite(image3, left=p(-250) + p(68), top=p(630))
    image3.close()
    
    final.crop(left=80, top=40, right=665, bottom=710)
    
    return final
