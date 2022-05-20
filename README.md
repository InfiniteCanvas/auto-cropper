This is a tool written specifically to make cropping images for RenPy games easier. It crops the images using their bounding box and spits out the coordinates for easy use as, for example, Imagebuttons.

You can use the __-f formatting.json__ option to customize how coordinates are spat out.<br>
Define a regex pattern to match against the file to use the formatting for. Available variables are:

| Variable | Description |
| :-- | :-- |
| x | Top left x-coordinate |
| y | Top left y-coordinate |
| bx | Bottom right x-coordinate |
| by | Bottom right y-coordinate |
| size | width x height |
| area | area in pixels |
| name | File name |
| path | File path of the output image |
| rel_path | File path relative to output path |

<br>

Example:

```json
{
   ".*_hover":"    imagebutton:\n        hover \"{path}\"\n",
   ".*_idle":"        idle \"{path}\"\n        xpos {x} ypos {y} focus_mask True\n",
   "bg_.*|bg.*":"    add \"{path}\" xpos {x} ypos {y}\n",
   ".png":"{name} {x},{y}\n"
}
```

would result in something like

```
afternoon_icon.png 15,15
    add "C:\Repos\Python\auto-cropper\output\bag\bagbg.png" xpos 389 ypos 0
    imagebutton:
        hover "C:\Repos\Python\auto-cropper\output\bag\close_hover.png"
        idle "C:\Repos\Python\auto-cropper\output\bag\close_idle.png"
        xpos 496 ypos 177 focus_mask True
daytime_icon.png 16,15
evening_icon.png 16,14
```

For things that don't match anything at all, formatting falls back to ``"{rel_path} {x},{y},{bx},{by}"``.<br>
Matching happens from top to bottom and files are loaded in alphanumerically sorted.

<br>

```
usage: Auto Cropper Tool [-h] [-i [INPUT]] [-o [OUTPUT]] [-e [EXTENSIONS ...]] [-g] [-d] [-m] [-f [FORMATTING]] [--remove-output] [--output-file-name [OUTPUT_FILE_NAME]]
                         [--border-width [BORDER_WIDTH]] [--border-height [BORDER_HEIGHT]] [--regex-group-by [REGEX_GROUP_BY]]

Processes all files with specified extensions in given image folders.

options:
  -h, --help            show this help message and exit
  -i [INPUT], --input [INPUT]
                        Set the working directory. Images are loaded from here. Defaults to script starting directory.
  -o [OUTPUT], --output [OUTPUT]
                        Set output directory to save cropped images. Defaults to script starting directory.
  -e [EXTENSIONS ...], --extensions [EXTENSIONS ...]
                        Choose file extensions to process. Must be images. Defaults are ['.jpg', '.png']
  -g, --group           Crop matched images (with '-r pattern') with the same sized box.
  -d, --difference      Get the difference of single and group crop
  -m, --match-path      Matches with path instead of file name when matching against formatting rules.
  -f [FORMATTING], --formatting [FORMATTING]
                        Path to the formatting JSON file.
  --remove-output       Removes output folder before proceeding.
  --output-file-name [OUTPUT_FILE_NAME]
                        Name of the file where the cropping's information is saved in each folder.
  --border-width [BORDER_WIDTH]
                        Set border width to add to cropping bounding box.
  --border-height [BORDER_HEIGHT]
                        Set border height to add to cropping bounding box.
  --regex-group-by [REGEX_GROUP_BY]
                        Regex to use for grouping images by for cropping, uses the first capture group and puts all identicals in the same bucket. Default is '(.+)(_hover|_idle)' to group hover and     
                        idle images.

```                        