import argparse
import itertools
import shutil
import sys
from pathlib import Path

import processing


def get_dir(path):
    path = Path(path)
    if path.is_dir():
        return str(path.absolute())
    else:
        return str(path.parent.absolute())


def parse_arguments(arguments) -> dict:
    """
    :param arguments: Arguments to parse
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
    parser.add_argument('-mp', '--match-path', action='store_true', default=False,
                        help="Matches with path instead of name when matching against formatting rules.")
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
    parameters = vars(parser.parse_args(arguments))

    return parameters


if __name__ == '__main__':
    args = parse_arguments(sys.argv[1:])
    if args["remove_output"]:
        shutil.rmtree(Path(args['output']), ignore_errors=True)
    print(
        f"------------\nNew run in {args['input']}, with output in {args['output']}:")

    extensions = list(map(lambda ext: ext.replace('.', ''), args['extensions']))

    images = processing.get_folders_and_images(
        args['input'], extensions, args['regex_group_by'])

    if args['difference']:
        single_images = processing.get_cropped_paths(
            images.singles, args['input'], args['output'])
        a = zip(single_images, processing.get_bboxes(processing.load_singles(images.singles)))
        grouped_images = processing.get_grouped_output_paths(
            images.grouped, args['input'], args['output'])
        b = zip(grouped_images, processing.get_grouped_bboxes(images.grouped))
        a = set({item[0]: item[1] for item in a})
        b = set({item[0]: item[1] for item in b})
        print("Showing differences:\n")
        print(a - b)
        quit()

    # process grouped images
    if args['group']:
        print("Processing files by groupings..\n")
        grouped_images = processing.load_grouped(images.grouped)
        bboxes = processing.get_grouped_bboxes(images.grouped)
        cropped_images = processing.get_cropped_images(grouped_images, bboxes, list(
            itertools.repeat((args['border_width'], args['border_height']), len(bboxes))))
        output_paths = processing.get_grouped_output_paths(
            images.grouped, args['input'], args['output'])
        processing.save_images(cropped_images, output_paths)
        substitutions = list(itertools.repeat(processing.get_formatting(args['formatting']), len(bboxes)))
        processing.save_coordinates(output_paths, bboxes, substitutions, list(itertools.repeat(args['match_path'], len(bboxes))), list(itertools.repeat(args['output'], len(bboxes))))

    # process single images
    else:
        print("Processing files by themselves..\n")
        single_images = processing.load_singles(images.singles)
        bboxes = processing.get_bboxes(single_images)
        cropped_images = processing.get_cropped_images(single_images, bboxes, list(
            itertools.repeat((args['border_width'], args['border_height']), len(bboxes))))
        output_paths = processing.get_cropped_paths(
            images.singles, args['input'], args['output'])
        processing.save_images(cropped_images, output_paths)
        substitutions = list(itertools.repeat(processing.get_formatting(args['formatting']), len(bboxes)))
        processing.save_coordinates(output_paths, bboxes, substitutions, list(itertools.repeat(args['match_path'], len(bboxes))), list(itertools.repeat(args['output'], len(bboxes))))
