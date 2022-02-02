import itertools
import pathlib
import os
import re
import sys
import argparse
from os import path as p
from PIL import Image
from alive_progress import alive_bar


class Object(object):
    pass


def autocrop_image(image: Image, border: (int, int) = (0, 0)):
    """
    :param image: Image to crop
    :param border: Border to add
    :return: Cropped Image
    """
    # Get the bounding box
    bbox = image.getbbox()
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

    return cropped_image, (bbox[0], bbox[1])


def get_area(coords: (int, int, int, int)):
    width = coords[2] - coords[0]
    height = coords[3] - coords[1]
    result = Object()
    result.bbox = coords
    result.area = width * height
    return result


def group_crop_images(images: [Image], border: (int, int) = (0, 0), callback=None):
    """
    :param images:
    :param border:
    :return:
    """
    bboxes = [get_area(image.getbbox()) for image in images]
    bbox = sorted(bboxes, key=lambda x: x.area, reverse=True)[0].bbox  # monkey patched
    cropped_images = []
    for image in images:
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
        cropped_images.append((cropped_image, (bbox[0], bbox[1])))
        if callback:
            callback()
    return cropped_images


def process_image_files(paths: [str], **kwargs) -> [(Image, [int, int])]:
    """
    :param paths: Paths to the image files
    :return: Returns the cropped image and coordinates of top-left bounding box
    """
    results = []
    # load image files
    originals = [Image.open(path) for path in paths]
    # crop images
    cropped_images = group_crop_images(originals, (kwargs['border_width'], kwargs['border_height']), kwargs['callback'])

    for cropped, (x, y) in cropped_images:
        result = Object()
        result.image = cropped
        result.x = x
        result.y = y
        results.append(result)
    return results


def process_image_file(path: str, **kwargs) -> (Image, [int, int]):
    """
    :param path: Path to the image file
    :return: Returns the cropped image and coordinates of top-left bounding box
    """
    # Load image file
    original = Image.open(path)
    # Crop image
    result = Object()
    cropped, pos = autocrop_image(original, (kwargs['border_width'], kwargs['border_height']))
    result.image = cropped
    result.x = pos[0]
    result.y = pos[1]
    return result


def save_image_to_file(image: Image, path: str):
    """
    :param image: Image  to save
    :param path: Path to save image to
    :return: None
    """
    image.save(path)


def save_coordinates_to_file(name: str, x: int, y: int, path: str, formatting):
    with open(path, mode='a+') as txt:
        txt.write(formatting.format(name=name, x=x, y=y))


def get_folders_and_images(path: str, extensions=["jpg", "png"]):
    images_dict = {}
    grouped_dict = {}
    print(path)
    # walk through all sub folders
    for currentdir, subdirs, files in os.walk(path):
        # get list of files with defined extensions
        images = list(filter(lambda filename: any(f".{e}" in filename for e in extensions), files))
        # process unless there are no image files or is in cropped folder
        if len(images) > 0 and 'cropped' not in currentdir:
            rel = p.relpath(currentdir, path)
            # group images that match (.*_(idle|hover)\.(extensions))
            r = re.compile("(.+)(_morning|_afternoon|_noon|_evening|_night)*(_hover|_idle)")
            grouped_images = itertools.groupby(images, lambda x: r.match(x).groups()[0] if r.match(x) else None)
            grouped_images = list(map(lambda x: (x[0], list(x[1])), grouped_images))
            grouped_dict[rel] = grouped_images, len(images)
            images_dict[rel] = images
    return images_dict, grouped_dict


def get_work_dir(path):
    path = pathlib.Path(path)
    if not pathlib.Path.is_dir(path):
        return str(path.parent)
    else:
        return str(path)


def parse_arguments(args) -> dict:
    """
    :param args: Arguments to parse
    :return: Parsed arguments dictionary
    """
    parser = argparse.ArgumentParser(prog="Auto Cropper Tool",
                                     description="Processes all files with specified extensions in given image folders.")
    parser.add_argument('-w', '--work-dir', default=sys.path[0], nargs='?', type=get_work_dir,
                        help="Set the working directory. Cropped images are put here. Default is script starting directory.")
    parser.add_argument('-e', '--extensions', nargs='*', default=['.jpg', '.png'],
                        help="Choose file extensions to process. Must be images. Defaults are ['.jpg', '.png']")
    parser.add_argument('-g', '--group', nargs='?', default=True, type=bool,
                        help="Crop hover/idle images with the same sized box.")
    parser.add_argument('-bw', '--border-width', nargs='*', default=0, type=int,
                        help="Set border width to add to cropping bounding box.")
    parser.add_argument('-bh', '--border-height', nargs='*', default=0, type=int,
                        help="Set border height to add to cropping bounding box.")
    parameters = vars(parser.parse_args(args))

    return parameters


def get_formatting(folder:str):
    if pathlib.Path(os.path.join(working, folder), "format.txt").exists():
        result = pathlib.Path(os.path.join(working, folder, "format.txt")).read_text()
    else:
        result = 'add "{name}" xpos {x} ypos {y}\n'
    return result


def init_coords_file(working, cropped):
    if pathlib.Path(os.path.join(working, "init.txt")).exists():
        result = pathlib.Path(os.path.join(working, "init.txt")).read_text()
        with open(pathlib.Path(os.path.join(cropped, "coords.txt")), mode='w+') as f:
            f.write(result)
    elif pathlib.Path(os.path.join(working, "start.txt")).exists():
        result = pathlib.Path(os.path.join(working, "start.txt")).read_text()
        with open(pathlib.Path(os.path.join(cropped, "coords.txt")), mode='w+') as f:
            f.write(result)
    else:
        with open(pathlib.Path(os.path.join(cropped, "coords.txt")), mode='w+') as f:
            f.write("")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    args = parse_arguments(sys.argv[1:])

    working = args['work_dir']
    # strip the dot
    extensions = list(map(lambda x: x.replace('.', ''), args['extensions']))
    folders_and_files, grouped_dict = get_folders_and_images(working, extensions)

    # process grouped images
    if args['group']:
        for folder, (groups, image_count) in grouped_dict.items():
            # create folder for cropped images
            pathlib.Path(os.path.join(working, "cropped", folder)).mkdir(parents=True, exist_ok=True)
            # check if custom formatting exists
            formatting = get_formatting(folder)
            # initiate coords file
            init_coords_file(pathlib.Path(os.path.join(working, folder)),
                             pathlib.Path(os.path.join(working, "cropped", folder)))
            with alive_bar(image_count, bar='smooth', spinner='classic',
                           title=f"Cropping images in {folder}") as files_bar:
                for prefix, group in groups:
                    # prefix is not needed
                    files = [os.path.join(folder, file) for file in group]
                    cropped_images = process_image_files(files, **args, callback=files_bar)
                    save_file_paths = [os.path.join(working, "cropped", folder, file) for file in group]
                    coords_file_path = os.path.join(working, "cropped", folder, "coords.txt")
                    for cropped_image, file_name in zip(cropped_images, group):
                        save_file_path = os.path.join(working, "cropped", folder, file_name)
                        save_image_to_file(cropped_image.image, save_file_path)
                        save_coordinates_to_file(pathlib.Path(os.path.join(folder, file_name)).as_posix(), cropped_image.x, cropped_image.y, coords_file_path,
                                             formatting)


    # process images by themselves
    else:
        for folders in folders_and_files.items():
            print(folders)
            # create folder for cropped images
            current_folder = folders[0]
            file_names = folders[1]
            pathlib.Path(os.path.join(working, "cropped", current_folder)).mkdir(parents=True, exist_ok=True)
            # check if custom formatting exists
            formatting = get_formatting(current_folder)
            # initiate coords file
            init_coords_file(pathlib.Path(os.path.join(working, current_folder)),
                             pathlib.Path(os.path.join(working, "cropped", current_folder)))

            with alive_bar(len(file_names), bar='smooth', spinner='classic',
                           title=f"Cropping images in {current_folder}") as files_bar:
                for image_file_name in file_names:
                    # print(f"Cropping {os.path.join(working, folders[0], image_file)}")

                    # process image
                    image_file_path = os.path.join(working, current_folder, image_file_name)
                    cropped_image = process_image_file(image_file_path, **args)

                    # save image to file
                    save_file_path = os.path.join(working, "cropped", current_folder, image_file_name)
                    coords_file_path = os.path.join(working, "cropped", current_folder, "coords.txt")
                    save_image_to_file(cropped_image.image, save_file_path)
                    save_coordinates_to_file(image_file_name, cropped_image.x, cropped_image.y, coords_file_path, formatting)
                    files_bar()
