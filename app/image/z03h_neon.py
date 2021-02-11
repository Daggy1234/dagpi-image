# Copyright (C) z03h https://github.com/z03h

import io

import numpy as np

from wand.image import Image as wImage
from PIL import Image, ImageSequence, ImageFilter, ImageChops, ImageEnhance, ImageDraw

def gif_a_neon( oim, **kwargs):
    """Specific function for animated source and animated gradient
    kwargs are similar to neon_static
    """
    # getting options
    sharp = kwargs.get('sharp', True)
    soft = kwargs.get('soft', True)
    if not (sharp or soft):
        raise ValueError('sharp and soft both cannot be False')
    overlay = kwargs.get('overlay', False)
    gradient = kwargs.get('gradient', 0)
    multi = True
    single = False
    try:
        colors = kwargs['colors']
        per_color = kwargs.get('per_color', 6)
        colors_per_frame = kwargs.get('colors_per_frame', 3)
        gradient_direction = kwargs.get('gradient_direction', 1)
    except KeyError:
        raise ValueError('Must set "colors"')

    if not all(isinstance(c, (tuple,list)) for c in colors):
        raise TypeError('colors must be a tuple/list of RGB tuples')

    horizontal = gradient_direction % 2
    # create the gradient
    paste = create_gradient(oim, colors, single, gradient_direction, horizontal,
                                 colors_per_frame)
    if gradient_direction in (0,1):
        # reverse gradient to reverse direction
        paste = paste.rotate(180)

    # starting position of gradient
    position = 0
    num_frames = oim.n_frames

    # calculate pixel to move per frame
    if horizontal:
        # horizontal
        step = int(paste.width/2)
    else:
        # vertical
        step = int(paste.height/2)
    # divmod to get as equal steps as possible while
    # summing to original size
    step, rem = divmod(step, num_frames)
    iter_steps = iter(([step+1]*rem) + ([step]*(num_frames-rem)))

    if gradient_direction in (1,2):
        #reverse the position for reversed gradient
        position = -paste.width+oim.width if horizontal else -paste.height+oim.height
    frames = []
    durations = []
    for im in ImageSequence.Iterator(oim):
        # Processing per frame
        durations.append(oim.info.get('duration', 10))
        im = preprocess_neon(im, single=single, **kwargs)

        # create sharp outline
        outline = create_sharp_outline(im, single, **kwargs)

        # create mask when pasting end result colors
        with im, outline, Image.new('RGBA', im.size, (0,0,0,0)) as mask:
            if soft:
                # create soft outline
                soft = create_soft_outline(outline, single, **kwargs)
                # paste soft outline
                mask.paste(soft, mask=soft)

            if sharp:
                # paste sharp outline
                mask.paste(outline, mask=outline)

            # start pasting gradient
            if overlay:
                temp = im.copy()
            else:
                temp = Image.new('RGBA', im.size, (0,0,0,0))
            if horizontal:
                # horizontal
                temp_paste = paste.crop((-int(position),0, -int(position)+mask.width,mask.height))
            else:
                # vertical
                temp_paste = paste.crop((0,-int(position), mask.width,-int(position)+mask.height))

            temp.paste(temp_paste, mask=mask)
            temp_paste.close()
        frames.append(temp)

        if gradient_direction in (1,2):
            # reverse the step for reverse gradients
            position += next(iter_steps)
        else:
            position -= next(iter_steps)

    return frames, durations

def neon_static( oim, **kwargs):
    """neon colors for single images

    Parameters
    ----------
    sharp: :class:`bool`
        Whether to include the sharp outline. Default is ``True``.
        sharp and soft both cannot be ``False``.
    sharp_brightness: :class:`float`
        How much to adjust the sharp outline brghtneess.
        Default is 3 for static and 2 for animated
    soft: :class:`bool`
        Whether to include the soft outline. Default is ``True``.
        soft and sharp both cannot be ``False``.
    soft_brightness: :class:`float`
        How much to adjust the sharp outline brghtneess.
        Default is 3 for static and 2 for animated
    overlay: :class:`bool`
        Whether outline is overlaid on top of the original image.
        Default is ``False``.
    brightness: :class:`float`
        Brightness of original image if overlaid. Default is ``0.85``
    colors: Union[List[Tuple]]
        List of RGB tuples.
        Ex.  ``[(255,0,0), (0,0,255)]``
    per_color: :class:`int`
        How many frames per color OR % of image to move per frame for
        animated gradient. Does nothing for single color/static gradient.
        Default is ``6``.
    gradient: :class:`int`
        0: no gradient
        1: static gradient
        2: animated gradient
        Default is ``0``.
    gradient_direction: :class:`int`
        direction of the gradient and animation
        left:3
        down:2
        right:1
        up:0
    colors_per_frame: :class:`int`
        How many colors are visible in the starting gradient frame.
        Default is ``3``.
    multi: :class:`bool`
        whether this should be treated as an animated image regardless of
        input. Defaults to ``False``
    saturation: :class:`float`
        How much to saturate or desaturate the image by. Default is ``None``
        for no change. ``0.0`` for grayscale, values > ``1.0`` to increase
        saturation. Does nothing unless overlay is ``True``.

        Passed to preprocessing.
    sharpen: :class:`int`
        0 for sharpen, 1 for enhance edges, 2 for enhance edges more.
        Default is ``None`` for no sharpening.

        Passed to preprocessing
    """
    # getting options
    sharp = kwargs.get('sharp', True)
    soft = kwargs.get('soft', True)
    if not (sharp or soft):
        raise ValueError('sharp and soft both cannot be False')
    overlay = kwargs.get('overlay', False)
    gradient = kwargs.get('gradient', 0)
    multi = kwargs.get('multi', False)
    try:
        colors = kwargs['colors']
    except KeyError:
        raise ValueError('Must set "colors"')
    else:
        per_color = kwargs.get('per_color', 6)
        if all(isinstance(c, (tuple,list)) for c in colors):
            # tuple of rgb tuples
            frames = []
            if len(colors) == 1:
                # single color, statis neon
                single = True
                colors = tuple(colors[0])
            else:
                # multiple colors
                if gradient in (0,1,2):
                    # 0 no gradient, animated
                    # 1 static gradient
                    # 2 animated gradient, animated
                    single = gradient == 1
                    colors_per_frame = kwargs.get('colors_per_frame', 3)
                    gradient_direction = kwargs.get('gradient_direction', 1)
                else:
                    raise ValueError('gradient must be between 0 <= x <= 2')

        elif all(isinstance(c, int) for c in colors) and len(colors) == 3:
            # colors is tuple of (r,g,b) instead of nested tuple ((r,g,b),)
            single = True
        else:
            raise TypeError('colors must be a tuple/list of RGB tuples or RGB tuple')

    # Actual processing
    im = preprocess_neon(oim, single=single, **kwargs)

    # create sharp outline
    outline = create_sharp_outline(im, single, **kwargs)

    # create mask when pasting end result colors
    with Image.new('RGBA', im.size, (0,0,0,0)) as mask:
        if soft:
            # create soft outline
            with create_soft_outline(outline, single, **kwargs) as soft:
                # paste soft outline
                mask.paste(soft, mask=soft)

        if sharp:
            # paste sharp outline
            mask.paste(outline, mask=outline)
            outline.close()

        if gradient:
            return neon_static_gradient(im, mask, colors, single,
                                             gradient_direction,
                                             overlay=overlay,
                                             per_color=per_color,
                                             colors_per_frame=colors_per_frame)
        else:
            return neon_static_breathing(im, mask, colors, single,
                                              overlay=overlay,
                                              per_color=per_color)

def preprocess_neon( im, *, single, **kwargs):
    sharpen = kwargs.get('sharpen', None)
    saturation = kwargs.get('saturation', None)
    overlay = kwargs.get('overlay', False)

    # convert to RGBA
    im = im.convert('RGBA')

    # get kwargs max size or use arg single to determine size
    maxsize = kwargs.get('maxsize', 512 if single else 256)
    size = max(im.size)
    if size > maxsize:
        #resize image while trying to keep ratio
        ratio = size / maxsize
        im = im.resize((int(im.width/ratio), int(im.height/ratio)))
    else:
        im = im

    # Apply sharpening, attemp to enahnce edges before contour
    if sharpen is not None:
        filters = (ImageFilter.SHARPEN,
                   ImageFilter.EDGE_ENHANCE,
                   ImageFilter.EDGE_ENHANCE_MORE)
        try:
            im = im.filter(filters[sharpen])
        except IndexError:
            pass
    # Darken to slightly enhance outline colors
    if overlay:
        enhance = ImageEnhance.Brightness(im)
        im = enhance.enhance(kwargs.get('brightness') or 0.85)

    # Apply saturation
    if saturation is not None:
        enhancer = ImageEnhance.Color(im)
        im = enhancer.enhance(saturation)

    return im

def create_sharp_outline( im, single, **kwargs):
    multi = kwargs.get('multi')
    # get edges, convert to L mode
    countour_outline = ImageChops.invert(im.filter(ImageFilter.CONTOUR).convert('L'))
    # contour creates white lines along the edges of the image
    # remove outer edge with a mask

    # Can potentially clip the image but removing the resulting edge glow
    # is better
    width, height = countour_outline.size
    width -= 1
    height -= 1
    draw = ImageDraw.Draw(countour_outline)
    # draw black lines along edges
    draw.line((0,0, 0,height), 0, 1)
    draw.line((0,0, width,0), 0, 1)
    draw.line((width,height, 0,height), 0, 1)
    draw.line((width,height, width,0), 0, 1)

    # birghten to enhance sharp outline
    enhancer = ImageEnhance.Brightness(countour_outline)
    countour_outline = enhancer.enhance(kwargs.get('sharp_brightness') or (3.0 if single and not multi else 2.0))

    return countour_outline

def create_soft_outline( outline, single, **kwargs):
    multi = kwargs.get('multi')
    # blur to create soft effect
    soft = outline.filter(ImageFilter.GaussianBlur(kwargs.get('soft_softness') or (7 if kwargs.get('overlay', False) else 14)))
    enhancer = ImageEnhance.Brightness(soft)
    # enhance to brighten soft outline colors
    soft = enhancer.enhance(kwargs.get('soft_brightness') or (1.9 if single and not multi else 1.5))
    return soft

def neon_static_breathing( im, mask, colors, single, *, overlay, per_color):
    # handles single color or breathing effect
    if single:
        # single color
        with Image.new('RGB', im.size, colors) as paste:
            # use original if overlay or new image
            temp = im if overlay else Image.new('RGBA', im.size, (0,0,0,0))
            temp.paste(paste, mask=mask)
        return temp
    else:
        # breathing
        frames = []
        # add first color to cycle back to original
        iter_colors = iter(colors + type(colors)((colors[0],)))
        next_color = next(iter_colors)
        while True:
            try:
                # get current and next color
                current = next_color
                next_color = next(iter_colors)
            except StopIteration:
                break
            # get range of colors between current and next
            for color in color_range(current, next_color, per_color):
                with Image.new('RGB', im.size, color) as paste:
                    # copy original if overlay else new image
                    temp = im.copy() if overlay else Image.new('RGBA', im.size, (0,0,0,0))
                    temp.paste(paste, mask=mask)
                frames.append(temp)
        return frames

def color_range( start, end, steps):
    # generator to yield colors between 2 colors and x steps
    delta = tuple((cur - nc)/steps for cur, nc in zip(start, end))
    for i in range(steps):
        yield tuple(cur - int(d*i) for cur, d in zip(start, delta))

def neon_static_gradient( im, mask, colors, single, gradient_direction,
                         *, overlay, per_color, colors_per_frame):
    # handles static or animated gradient effect
    horizontal = gradient_direction % 2
    # create gradient to paste
    paste = create_gradient(im, colors, single, gradient_direction, horizontal,
                                 colors_per_frame)

    if single:
        # non animated image
        if paste.size != mask.size:
            # resize incase of rounding error
            paste = paste.resize(mask.size)
        temp = im if overlay else Image.new('RGBA', im.size, (0,0,0,0))
        with paste, mask:
            temp.paste(paste, mask=mask)
        return temp
    else:
        # animated gradient
        frames = []
        position = 0
        if horizontal:
            # horizontal
            step = int(im.width * per_color)
            min_pos = -int(paste.width/2)
        else:
            # vertical
            step = int(im.height * per_color)
            min_pos = -int(paste.height/2)
        step, rem = divmod(step, 100)
        steps = iter([step+1]*rem)
        while position > min_pos:
            # copy if overlay else new image
            temp = im.copy() if overlay else Image.new('RGBA', im.size, (0,0,0,0))
            if horizontal:
                # horizontal
                temp_paste = paste.crop((-position,0, -position+mask.width,mask.height))
            else:
                # vertical
                temp_paste = paste.crop((0,-position, mask.width,-position+mask.height))
            with temp_paste, mask:
                temp.paste(temp_paste, mask=mask)
            frames.append(temp)
            try:
                # move position step+1 rem times
                position -= next(steps)
            except StopIteration:
                # use step after StopIteration
                position -= step
        return frames

def create_gradient( im, colors, single, gradient_direction, horizontal, colors_per_frame):
    arrays = []
    # add first color to rotate back
    iter_colors = iter(colors) if single else iter(colors + type(colors)((colors[0],)))
    next_color = next(iter_colors)
    # single gradient fits in original image
    # moving gradient is extended part original image
    ratio = len(colors)-1 if single else colors_per_frame-1
    horizontal = gradient_direction % 2
    while True:
        # create gradients with 2 colors
        try:
            current = next_color
            next_color = next(iter_colors)
        except StopIteration:
            break
        with wImage() as wim:
            # use ImageMagick pseudo scripts to create gradients
            wim.clear()
            pseudo =  f'gradient:rgb{tuple(current)}-rgb{tuple(next_color)}'
            if horizontal:
                # horizontal gradient
                wim.options['gradient:direction'] = 'east'
                wim.pseudo(int(im.width/ratio), im.height, pseudo)
            else:
                # vertical gradient
                wim.options['gradient:direction'] = 'north'
                wim.pseudo(im.width, int(im.height/ratio), pseudo)
            # image to array, add array to a list
            arrays.append(np.array(wim))
    if not horizontal:
        # uh idk why, I think it's backwards
        arrays.reverse()
    # use numpy to combine arrays
    # hstack for horizontal // vstack for vertical gradient
    stack = np.hstack if gradient_direction%2 else np.vstack

    # get pil image from stacked arrays
    paste = Image.fromarray(stack(arrays if single else [*arrays, *arrays]))
    if single and gradient_direction in (1,2):
        # reverse the gradient for correct direction
        paste = paste.rotate(180)
    return paste


async def _neon(oim, colors, **kwargs):
    """Handles static source neon images

    Parameters
    ----------
    sharp: :class:`bool`
        Whether to include the sharp outline. Default is ``True``.
        sharp and soft both cannot be ``False``.
    sharp_brightness: :class:`float`
        How much to adjust the sharp outline brghtneess.
        Default is 3 for static and 2 for animated
    soft: :class:`bool`
        Whether to include the soft outline. Default is ``True``.
        soft and sharp both cannot be ``False``.
    soft_brightness: :class:`float`
        How much to adjust the sharp outline brghtneess.
        Default is 3 for static and 2 for animated
    overlay: :class:`bool`
        Whether outline is overlaid on top of the original image.
        Default is ``False``.
    brightness: :class:`float`
        Brightness of original image if overlaid. Default is ``0.85``
    colors: Union[List[Tuple]]
        List of RGB tuples.
        Ex.  ``[(255,0,0), (0,0,255)]``
    per_color: :class:`int`
        How many frames per color OR % of image to move per frame for
        animated gradient. Does nothing for single color/static gradient.
    gradient: :class:`int`
        0: no gradient
        1: static gradient
        2: animated gradient
        Default is ``0``.
    direction: :class:`str`
        direction of the gradient and animation
        [L]eft, [R]ight, [U]p, [D]own
    colors_per_frame: :class:`int`
        How many colors are visible in the starting gradient frame.
        Default is ``3``.
    saturation: :class:`float`
        How much to saturate or desaturate the image by. Default is ``None``
        for no change. ``0.0`` for grayscale, values > ``1.0`` to increase
        saturation. Does nothing unless overlay is ``True``.

        Passed to preprocessing.
    sharpen: :class:`int`
        0 for sharpen, 1 for enhance edges, 2 for enhance edges more.
        Default is ``None`` for no sharpening.

        Passed to preprocessing
    """

    gradient = kwargs.pop('gradient', 0)
    overlay = kwargs.pop('overlay', False)

    animated = gradient!=1 and len(colors)!=1
    directions = {'l':3, 'left':3,
                  'd':2, 'down':2,
                  'r':1, 'right':1,
                  'u':0, 'up':0}
    gradient_direction = directions.get(kwargs.pop('direction','').lower(), 3)

    maxsize = 256 if animated else 512

    per_color = kwargs.pop('per_color', None)
    saturation = kwargs.pop('saturation', None)
    image =  neon_static(oim, colors=colors,
                                     per_color=per_color or (10 if gradient else 8),
                                     saturation=saturation or 0.7,
                                     overlay=overlay,
                                     gradient=gradient,
                                     gradient_direction=gradient_direction,
                                     **kwargs
                                    )
    final = io.BytesIO()
    if isinstance(image, list):
        ext = 'gif'
        if gradient==2 and gradient_direction in (1,2):
            # reverse images to simulate moving the opposite direction
            image.reverse()
        image[0].save(final, format=ext, save_all=True, dispose=2, append_images=image[1:], loop=0)
    else:
        # single image, save normally
        ext = 'png'
        image.save(final, format=ext)
    final.seek(0)
    return final


async def _a_neon(oim, colors, **kwargs):
    """Handles animated souce to neon images"""
    gradient = kwargs.pop('gradient', 0)
    overlay = kwargs.pop('overlay', False)

    directions = {'l':3, 'left':3,
                  'd':2, 'down':2,
                  'r':1, 'right':1,
                  'u':0, 'up':0}
    gradient_direction = directions.get(kwargs.pop('direction','').lower(), 3)

    #start neon process after getting image bytes
    image = []
    durations = []

    try:
        # another animated check
        total_frames = oim.n_frames
        if total_frames < 2:
            raise TypeError('oim not animated')
    except AttributeError:
        raise TypeError('oim not animated')

    if not gradient and len(colors) > 1:
        # create the colors for breathing

        #check # of colors to frames
        if len(colors) >= total_frames:
            raise ValueError('Too many colors to source image frames')

        # divmod to evenly distribute frames per colors
        # and match original frame count
        per, remainder = divmod(total_frames, len(colors))
        _frames_per_color = ([per+1] * remainder) + ([per] * (len(colors) - remainder))
        iter_colors = []
        ic = iter(colors + type(colors)((colors[0],)))
        next_color = next(ic)
        for num_frames in _frames_per_color:
            try:
                current = next_color
                next_color = next(ic)
            except StopIteration:
                break
            iter_colors.extend(color_range(current, next_color, num_frames))
        iter_colors = iter(iter_colors)
    per_color = kwargs.pop('per_color', None)
    saturation = kwargs.pop('saturation', None)
    colors_per_frame = kwargs.pop('colors_per_frame', None)
    if gradient != 2:
        # static/breathing/static gradient
        for im in ImageSequence.Iterator(oim):
            if not gradient and len(colors) > 1:
                # swap color per frame to simluate animated
                # breathing effect
                color = next(iter_colors)
            else:
                # static/static gradient
                # use all normal colors
                color = colors

            durations.append(im.info.get('duration', 10))
            frame = neon_static(im, colors=color,
                                     per_color=per_color or (10 if gradient else 8),
                                     saturation=saturation or 0.7,
                                     overlay=overlay,
                                     gradient=gradient,
                                     gradient_direction=gradient_direction,
                                     max_size=256,
                                     multi=True,
                                     **kwargs
                                    )
            image.append(frame)
    else:
        # animated gradient with animated source
        image, durations = gif_a_neon(oim, colors=colors,
                                saturation=saturation or 0.7,
                                overlay=overlay,
                                gradient=gradient,
                                gradient_direction=gradient_direction,
                                colors_per_frame=colors_per_frame or 2,
                                max_size=256,
                                **kwargs)
    final = io.BytesIO()
    if isinstance(image, list):
        ext = 'gif'
        image[0].save(final, format=ext, save_all=True, dispose=2, append_images=image[1:], duration=durations, loop=0)
    else:
        raise TypeError(f'Got {type(image)} instead of list of PIL.Image')
    final.seek(0)
    return final
