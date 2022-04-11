import pathlib
import shutil
import sys
import argparse
from processing import *


def get_dir(path):
    path = pathlib.Path(path)
    if path.is_dir():
        return str(path.absolute())
    else:
        return str(path.parent.absolute())


def parse_arguments(args) -> dict:
    """
    :param args: Arguments to parse
    :return: Parsed arguments dictionary
    """
    parser = argparse.ArgumentParser(prog="Auto Cropper Tool",
                                     description="Processes all files with specified extensions in given image folders.")
    parser.add_argument('-i', '--input', default=sys.path[0], nargs='?', type=get_dir,
                        help="Set the working directory. Images are loaded from here. Defaults to script starting directory.")
    parser.add_argument('-o', '--output', nargs='?', default=sys.path[0], type=str,
                        help="Set output directory to save cropped images. Defaults to script starting directory.")
    parser.add_argument('-e', '--extensions', nargs='*', default=['.jpg', '.png'],
                        help="Choose file extensions to process. Must be images. Defaults are ['.jpg', '.png']")
    parser.add_argument('-g', '--group', action='store_true', default=False,
                        help="Crop matched images (with '-r pattern') with the same sized box.")
    parser.add_argument('-d', '--difference', action='store_true', default=False,
                        help="Get the difference of single and group crop")
    parser.add_argument('--remove-output', action='store_true', default=False,
                        help="Removes output folder before proceeding.")
    parser.add_argument('-f', '--formatting', nargs='?', default="formatting.json", type=str,
                        help="Path to the formatting JSON file.")
    parser.add_argument('-bw', '--border-width', nargs='?', default=0, type=int,
                        help="Set border width to add to cropping bounding box.")
    parser.add_argument('-bh', '--border-height', nargs='?', default=0, type=int,
                        help="Set border height to add to cropping bounding box.")
    parser.add_argument('-r', '--regex-group-by', nargs='?', default="(.+)(_hover|_idle)",
                        help="Regex to use for grouping images by for cropping, uses the first capture group and puts all identicals in the same bucket. Default is '(.+)(_hover|_idle)' to group hover and idle images.")
    parameters = vars(parser.parse_args(args))

    return parameters


if __name__ == '__main__':
    args = parse_arguments(sys.argv[1:])
    if args["remove_output"]:
        shutil.rmtree(Path(args['output']), ignore_errors=True)
    print(
        f"------------\nNew run in {args['input']}, with output in {args['output']}:")

    extensions = list(map(lambda ext: ext.replace('.', ''), args['extensions']))

    images = get_folders_and_images(
        args['input'], extensions, args['regex_group_by'])

    if args['difference']:
        single_images = get_cropped_paths(
                images.singles, args['input'], args['output'])
        a = zip(single_images, get_bboxes(load_singles(images.singles)))
        grouped_images = get_grouped_output_paths(
                images.grouped, args['input'], args['output'])
        b = zip(grouped_images, get_grouped_bboxes(images.grouped))
        a = set({item[0]:item[1] for item in (a)})
        b = set({item[0]:item[1] for item in (b)})
        print("Showing differences:\n")
        print(a - b)
        quit()

    # process grouped images
    if args['group']:
        print("Processing files by groupings..\n")
        grouped_images = load_grouped(images.grouped)
        bboxes = get_grouped_bboxes(images.grouped)
        cropped_images = get_cropped_images(grouped_images, bboxes, list(
            itertools.repeat((args['border_width'], args['border_height']), len(bboxes))))
        output_paths = get_grouped_output_paths(
            images.grouped, args['input'], args['output'])
        save_images(cropped_images, output_paths)
        substitutions = list(itertools.repeat(get_formatting(args['formatting']), len(bboxes)))
        save_coordinates(output_paths, bboxes, substitutions)

    # process single images
    else:
        print("Processing files by themselves..\n")
        single_images = load_singles(images.singles)
        bboxes = get_bboxes(single_images)
        cropped_images = get_cropped_images(single_images, bboxes, list(
            itertools.repeat((args['border_width'], args['border_height']), len(bboxes))))
        output_paths = get_cropped_paths(
            images.singles, args['input'], args['output'])
        save_images(cropped_images, output_paths)
        substitutions = list(itertools.repeat(get_formatting(args['formatting']), len(bboxes)))
        save_coordinates(output_paths, bboxes, substitutions)
