This is a tool written specifically to make cropping images for RenPy games easier. It crops the images using their bounding box and spits out the coordinates for easy use as, for example, Imagebuttons.

You can use the __-f formatting.json__ option to customize how coordinates are spat out.<br>
Define a regex pattern to match against the file to use the formatting for. Available variables are:
| Variable | Description |
| :-- | :-- |
| x | Top left x-coordinate |
| y | Top left y-coordinate |
| bx | Bottom right x-coordinate |
| by | Bottom right y-coordinate |
| name | File name |
| path | File path (of the output image) |
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

usage: <br>
python main.py [-h] [-i [INPUT]] [-o [OUTPUT]] [-e [EXTENSIONS ...]] [-g [GROUP]] [-d [DIFFERENCE]] [-f [FORMATTING]] [-bw [BORDER_WIDTH ...]] [-bh [BORDER_HEIGHT ...]] [-r [REGEX_GROUP_BY]]

Processes all files with specified extensions in given image folders.

| option | description |
| :-- | :-- |
|-h, --help|            show this help message and exit|
|-i [INPUT], --input [INPUT]|Set the working directory. Images are loaded from here. Default is script starting directory.|
|-o [OUTPUT], --output [OUTPUT]|Set output directory to save cropped images.
|-e [EXTENSIONS ...], --extensions [EXTENSIONS ...]|Choose file extensions to process. Must be images. Defaults are ['.jpg', '.png']
|-g [GROUP], --group [GROUP]|Crop matched images (with '-r pattern') with the same sized box.
|-d [DIFFERENCE], --difference [DIFFERENCE]|Get the difference of single and group crop
|-f [FORMATTING], --formatting [FORMATTING]|Path to the formatting JSON file.
|-bw [BORDER_WIDTH ...], --border-width [BORDER_WIDTH ...]|                        Set border width to add to cropping bounding box.
|-bh [BORDER_HEIGHT ...], --border-height [BORDER_HEIGHT ...]|                        Set border height to add to cropping bounding box.
|-r [REGEX_GROUP_BY], --regex-group-by [REGEX_GROUP_BY]|                        Regex to use for grouping images by for cropping, uses the first capture group and puts all identicals in the same bucket. Default is '(.+)(_hover\|_idle)' to group hover and idle images.|