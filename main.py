import pathlib
import os
import sys
import argparse
from os import path as p
from PIL import Image
from alive_progress import alive_bar


class Object(object):
    pass


def autocrop_image(image: Image, border: int = 0):
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
    width += border * 2
    height += border * 2
    # Create a new image object for the output image
    cropped_image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    # Paste the cropped image onto the new image
    cropped_image.paste(cropped, (border, border))

    return cropped_image, (bbox[0], bbox[1])


def process_image_file(path: str) -> (Image, [int, int]):
    """
    :param path: Path to the image file
    :return: Returns the cropped image and coordinates of top-left bounding box
    """
    # Load image file
    original = Image.open(path)
    # Crop image
    result = Object()
    cropped, pos = autocrop_image(original)
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


def save_coordinates_to_file(name: str, x: int, y: int, path: str, format):
    with open(path, mode='a+') as txt:
        txt.write(format.format(name=name, x=x, y=y))


def get_folders_and_images(path: str, extensions=[".jpg", ".png"]):
    images_dict = {}
    print(path)
    for currentdir, subdirs, files in os.walk(path):
        images = list(filter(lambda filename: any(e in filename for e in extensions), files))
        if len(images) > 0 and 'cropped' not in currentdir:
            rel = p.relpath(currentdir, path)
            images_dict[rel] = images
    return images_dict


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
    parameters = vars(parser.parse_args(args))

    return parameters


def get_formatting():
    if pathlib.Path(os.path.join(working, folders[0]), "format.txt").exists():
        result = pathlib.Path(os.path.join(working, folders[0], "format.txt")).read_text()
    else:
        result = "add {name} xpos {x} ypos {y}\n"
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
    extensions = args['extensions']
    folders_and_files = get_folders_and_images(working, extensions)

    for folders in folders_and_files.items():
        # create folder for cropped images
        pathlib.Path(os.path.join(working, "cropped", folders[0])).mkdir(parents=True, exist_ok=True)
        # check if custom formatting exists
        formatting = get_formatting()
        # initiate coords file
        init_coords_file(pathlib.Path(os.path.join(working, folders[0])), pathlib.Path(os.path.join(working, "cropped", folders[0])))

        with alive_bar(len(folders[1]), bar='smooth', spinner='classic', title=f"Cropping images in {folders[0]}") as files_bar:
            for image_file in folders[1]:
                # print(f"Cropping {os.path.join(working, folders[0], image_file)}")

                # process image
                image_file_path = os.path.join(working, folders[0], image_file)
                cropped_image = process_image_file(image_file_path)

                # save image to file
                save_file_path = os.path.join(working, "cropped", folders[0], image_file)
                coords_file_path = os.path.join(working, "cropped", folders[0], "coords.txt")
                save_image_to_file(cropped_image.image, save_file_path)
                save_coordinates_to_file(image_file, cropped_image.x, cropped_image.y, coords_file_path, formatting)
                files_bar()