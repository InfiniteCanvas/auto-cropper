import itertools
import json
import os
import re
from collections import namedtuple
from pathlib import Path

from PIL import Image
from alive_progress import alive_bar
from toolz import functoolz

unwrap = functoolz.compose_left(itertools.chain.from_iterable, list)
mapl = functoolz.compose_left(map, list)


def coalesce(*arg):
    return next((item for item in arg if item is not None), None)


def get_folders_and_images(path: str, extensions=["jpg", "png"], group_by: str = "(.+)(_hover|_idle)"):
    grouped_dict = {}
    single_dict = {}
    all_images = namedtuple('ImageDicts', ['singles', 'grouped'])
    # walk through all sub folders
    for currentdir, _, files in os.walk(path):
        # get list of files with defined extensions
        images = list(filter(lambda filename: any(
            f".{e}" in filename for e in extensions), files))
        # process unless there are no image files or has "cropped" in folder path
        if len(images) > 0 and 'cropped' not in currentdir:
            r = re.compile(group_by)
            grouped_images = itertools.groupby(
                images, lambda x: r.match(x).group(1) if r.match(x) else None)
            grouped_images = list(
                map(lambda x: (x[0], list(x[1])), grouped_images))
            # put them in the dicts as folder:[images] or folder:[groups]
            single_dict[currentdir] = images
            grouped_dict[currentdir] = grouped_images

    return all_images(singles=single_dict, grouped=grouped_dict)


def get_formatting(path: str):
    # default formatting
    formatting = {".*_hover": '    imagebutton:\n        hover "{path}"\n',
                  ".*_idle": '        idle "{path}"\n        xpos {x} ypos {y} focus_mask True\n',
                  "bg_.*|bg.*": '    add "{path}" xpos {x} ypos {y}\n',
                  ".png": "{name} {x},{y}\n"}
    if path:
        p = Path(path)
        if p.is_file() & p.suffix.__eq__(".json"):
            formatting = json.loads(p.read_text())
    return formatting


def save_coordinate(path: Path, bbox, substitutions, match_path):
    x, y = bbox[0], bbox[1]
    bx, by = bbox[2], bbox[3]
    name = path.name
    pattern = str(path) if match_path else name
    f = "{path} {x},{y},{bx},{by}"
    if substitutions:
        # take first matching key
        key = list(filter(lambda k: re.search(k, pattern), substitutions.keys()))
        f = coalesce(substitutions[key[0]], f)
    with open(path.parent.joinpath("screen.rpy"), mode='a+') as screen:
        screen.write(f.format(x=x, y=y, name=name, bx=bx, by=by, path=path.absolute()))


def get_absolute_paths(kvp):
    """
    :param kvp: Key-Value pair of (folder,[files])
    """
    return [Path(os.path.join(kvp[0], file)) for file in kvp[1]]


def load_image(path: str or Path) -> Image:
    image = Image.open(path)
    return image


def save_image(image: Image, path: Path):
    path.parent.mkdir(exist_ok=True, parents=True)
    image.save(path)


def get_grouped_bounding_boxes(data):
    res = []
    f = functoolz.compose_left(get_paths, itertools.chain.from_iterable, list, load_images, get_bboxes)
    for group, files in data[1]:
        bboxes = f([(data[0], files)])
        tx = min(bboxes, key=lambda x: x[0])[0]
        ty = min(bboxes, key=lambda x: x[1])[1]
        bx = max(bboxes, key=lambda x: x[2])[2]
        by = max(bboxes, key=lambda x: x[3])[3]
        biggest = (tx, ty, bx, by)
        res.append(list(itertools.repeat(biggest, len(files))))
    res = unwrap(res)
    return res


def get_grouped_paths_helper(data):
    res = []
    for _, files in data[1]:
        res.append([Path(data[0]).joinpath(x) for x in files])
    res = unwrap(res)
    return res


def get_grouped_output_paths_helper(data, output, relpath):
    res = []
    for _, files in data[1]:
        res.append([Path(output).joinpath(relpath).joinpath(x) for x in files])
    res = unwrap(res)
    return res


def get_grouped_output_paths(images_dict: dict, input_dir: str, output: str = None):
    if not input_dir:
        input_dir = os.path.commonpath(images_dict.keys())
    rel_paths = [os.path.relpath(p, input_dir) for p in images_dict.keys()]
    if not output:
        output = input_dir
    return unwrap(
        [get_grouped_output_paths_helper(item, output, rel) for item, rel in zip(images_dict.items(), rel_paths)])


def get_bounding_box(image: Image):
    return image.getbbox()


def get_cropped_paths(images_dict: dict, input_dir: str, output: str = None):
    if not input_dir:
        input_dir = os.path.commonpath(images_dict.keys())
    rel_paths = [os.path.relpath(p, input_dir) for p in images_dict.keys()]
    if not output:
        output = input_dir
    cropped_paths = get_paths([(os.path.join(output, p[1]), p[0][1])
                               for p in zip(images_dict.items(), rel_paths)])
    return list(itertools.chain.from_iterable(cropped_paths))


def get_cropped_image(image, bbox, border=(0, 0)):
    # Crop the image to the contents of the bounding box
    cropped = image.crop(bbox)
    # Determine the width and height of the cropped image
    (width, height) = cropped.size
    # Add border
    width += border[0] * 2
    height += border[1] * 2
    # Create a new image object for the output image
    cropped_image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    # Paste the cropped image onto the new image
    cropped_image.paste(cropped, (border[0], border[1]))
    return cropped_image


def func_with_progressbar(callback, func, *data):
    res = func(*data)
    callback.text = data
    callback()
    return res


def get_len(data):
    if hasattr(data, '__len__'):
        return len(data)
    else:
        return len(list(data))


def mapl_with_progress(func, *data, **kwargs):
    size = get_len(min(data, key=get_len))
    with alive_bar(size, **kwargs) as bar:
        f = functoolz.partial(func_with_progressbar, bar)
        g = functoolz.partial(f, func)
        return mapl(g, *data)


""" [paths:str] -> [(int,int,int,int)] """
get_bboxes = functoolz.partial(
    mapl_with_progress, get_bounding_box, title="Getting boundings".ljust(20), bar="filling", dual_line=True)

""" [(folder:str,[files:str])] -> [paths:str] """
get_paths = functoolz.partial(mapl, get_absolute_paths)

""" [path:str] -> [image:Image] """
load_images = functoolz.partial(
    mapl_with_progress, load_image, title="Loading images".ljust(20), bar="filling", dual_line=True)

""" [image:Image], [bbox:(int,int,int.int)], [border:(int,int)] -> [image:Image] """
get_cropped_images = functoolz.partial(
    mapl_with_progress, get_cropped_image, title="Cropping images".ljust(20), bar="filling", dual_line=True)

""" [image:Image, path:str] -> None """
save_coordinates = functoolz.partial(
    mapl_with_progress, save_coordinate, title="Saving coordinates".ljust(20), bar="filling", dual_line=True)

""" [image:Image, path:str] -> None """
save_images = functoolz.partial(
    mapl_with_progress, save_image, title="Saving images".ljust(20), bar="filling", dual_line=True)

""" {(folder:str,[files:str])} -> [image:image] """
load_singles = functoolz.compose_left(
    lambda x: x.items(),
    # make them all to path strings for paths of [[folder1][folder2]...[folder-n]]
    get_paths,
    itertools.chain.from_iterable,  # flatten list of lists to [paths]
    list,
    load_images,
)

get_grouped_bboxes = functoolz.compose_left(lambda x: x.items(),
                                            functoolz.partial(mapl_with_progress, get_grouped_bounding_boxes,
                                                              title="Getting grouped bboxes".ljust(20), bar="filling",
                                                              dual_line=True),
                                            unwrap)

get_grouped_paths = functoolz.partial(mapl_with_progress, get_grouped_paths_helper,
                                      title="Getting grouped paths".ljust(20), bar="filling", dual_line=True)

load_grouped = functoolz.compose_left(
    lambda x: x.items(),
    # make them all to path strings for paths of [[folder1][folder2]...[folder-n]]
    get_grouped_paths,
    itertools.chain.from_iterable,  # flatten list of lists to [paths]
    list,
    load_images,
)
