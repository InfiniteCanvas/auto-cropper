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


def get_repeated_list(element, repeats):
    return list(itertools.repeat(element, repeats))


def parse_arguments(arguments) -> dict:
    """
    :param arguments: Arguments to parse
    :return: Parsed arguments dictionary
    """
    parser = argparse.ArgumentParser(prog="Auto Cropper Tool",
                                     description="Processes all files with specified extensions in given image folders.")
    parser.add_argument('-i', '--input', default=sys.path[0], nargs='?', type=get_dir,
                        help="Set the working directory. Images are loaded from here. Defaults to script starting directory.")
    parser.add_argument('-o', '--output', nargs='?', default="output", type=str,
                        help="Set output directory to save cropped images. Defaults to script starting directory.")
    parser.add_argument('-e', '--extensions', nargs='*', default=['.jpg', '.png'],
                        help="Choose file extensions to process. Must be images. Defaults are ['.jpg', '.png']")
    parser.add_argument('-g', '--group', action='store_true', default=False,
                        help="Crop matched images (with '-r pattern') with the same sized box.")
    parser.add_argument('-d', '--difference', action='store_true', default=False,
                        help="Get the difference of single and group crop")
    parser.add_argument('-m', '--match-path', action='store_true', default=False,
                        help="Matches with path instead of file name when matching against formatting rules.")
    parser.add_argument('-f', '--formatting', nargs='?', default="formatting.json", type=str,
                        help="Path to the formatting JSON file.")
    parser.add_argument('--remove-output', action='store_true', default=False,
                        help="Removes output folder before proceeding.")
    parser.add_argument('--output-file-name', nargs='?', default="coords.txt", type=str,
                        help="Name of the file where the cropping's information is saved in each folder.")                        
    parser.add_argument('--border-width', nargs='?', default=0, type=int,
                        help="Set border width to add to cropping bounding box.")
    parser.add_argument('--border-height', nargs='?', default=0, type=int,
                        help="Set border height to add to cropping bounding box.")
    parser.add_argument('--regex-group-by', nargs='?', default="(.+)(hover|idle)",
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
        a = {item[0]: item[1] for item in a}
        b = {item[0]: item[1] for item in b}
        c = {key: processing.get_area(a[key]) - processing.get_area(b[key]) for key in a}
        d = dict(filter(lambda kvp: kvp[1] != 0, c.items()))
        print("Showing files with size differences:\n")
        print("\n".join(p.as_posix() for p in d.keys()))
        quit()

    # process grouped images
    if args['group']:
        print("Processing files by groupings..\n")
        grouped_images = processing.load_grouped(images.grouped)
        bboxes = processing.get_grouped_bboxes(images.grouped)
        bblen = len(bboxes)
        cropped_images = processing.get_cropped_images(grouped_images, bboxes, get_repeated_list((args['border_width'], args['border_height']), bblen))
        output_paths = processing.get_grouped_output_paths(images.grouped, args['input'], args['output'])
        processing.save_images(cropped_images, output_paths)
        substitutions = get_repeated_list(processing.get_formatting(args['formatting']), bblen)
        processing.save_coordinates(output_paths, bboxes, substitutions, get_repeated_list(args['match_path'], bblen), get_repeated_list(args['output'], bblen), get_repeated_list(args['output_file_name'], bblen))

    # process single images
    else:
        print("Processing files by themselves..\n")
        single_images = processing.load_singles(images.singles)
        bboxes = processing.get_bboxes(single_images)    
        bblen = len(bboxes)
        cropped_images = processing.get_cropped_images(single_images, bboxes, list(
            itertools.repeat((args['border_width'], args['border_height']), bblen)))
        output_paths = processing.get_cropped_paths(
            images.singles, args['input'], args['output'])
        processing.save_images(cropped_images, output_paths)
        substitutions = list(itertools.repeat(processing.get_formatting(args['formatting']), bblen))
        processing.save_coordinates(output_paths, bboxes, substitutions, get_repeated_list(args['match_path'], bblen), get_repeated_list(args['output'], bblen), get_repeated_list(args['output_file_name'], bblen))
