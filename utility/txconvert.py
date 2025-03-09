#!/usr/bin/env python

# Command-line utility for running maketx on multiple files with options like string filtering/colorspace detection based on flags etc
# Only tested on Windows with Python3, Arnold as target dcc. May need to tweak some options if using prman for example.
# You can add this to PATH to call it from command line, or to a .bashrc like so:
# txconvert() {
#    python path_to_txconvert.py $1 $2 $3 $4
#}

import subprocess
import argparse
import os
from concurrent import futures
import sys

# Run maketx
def run_maketx(filename, verbose):
    cmd = "maketx " # This can be modified to a direct binary, otherwise maketx directory needs to be in PATH
    cmd += '"' + filename + '"'
    ocio = os.environ['OCIO'] #Can be manually remapped to a .ocio file
    cmd += ' --colorconfig ' + ocio

    # Note that lanczos3 is used for filtering for quality, but is a bit slower - can be modified
    cmd += ' --opaque-detect --constant-color-detect --monochrome-detect --fixnan box3 -u --filter lanczos3 --threads 12 --attrib tiff:half 1 -v --unpremult --oiio --colorconvert '
    
    # These tags are used to determine certain settings that can be modified
    color_tags = ('srgb', 'basecolor', 'albedo', 'color', 'diffuse')
    disp_tags = ('dsp', 'disp', 'displacement', 'zdisp', 'height')
    color_tag_found = any(tag in filename.lower() for tag in color_tags)
    dsp_tag_found = any(tag in filename.lower() for tag in disp_tags)

    if dsp_tag_found: color_tag_found==False

    if color_tag_found:
        cmd += ' "Utility - sRGB - Texture" '
    else:
        cmd += ' "Utility - Raw" '
    cmd += '"ACES - ACEScg" --format exr '

    if dsp_tag_found:
        cmd += '-d float --compression zip '
    else:
        cmd += '-d half --compression dwaa '
    
    if not verbose:
        subprocess.run(cmd, stdout=subprocess.DEVNULL)
    else:
        subprocess.run(cmd, shell=True)
    return "Converted {} ...".format(filename)


# Main function to crawl for valid files/deal with flags, then call maketx
def main(path, filter, recursive, verbose, *args):
    # Initial path
    cwd = os.getcwd()
    if path != '.':
        cwd = os.path.abspath(path)

    # Get all recursive files from target path
    def get_files_recursive(start_path):
        file_list = []
        for root, dirs, files in os.walk(os.path.abspath(start_path)):
            for file in files:
                file_list.append(os.path.join(root, file))
        return file_list

    # Get all texture files
    all_files = None
    if recursive:
        all_files = get_files_recursive(cwd)
    else:
        all_files = [os.path.join(cwd, file) for file in os.listdir(cwd)]
    if not all_files:
        print("No files in directory, exiting...")
        sys.exit()

    # Get all valid files based on file extensions
    print('Processing textures in root path {0}. Recursive is {1}'.format(cwd, recursive))
    texture_files = []
    valid_formats = ('png', 'jpg', 'jpeg', 'tif', 'tiff', 'exr', 'dds', 'tga', 'bmp', 'psd')

    for filename in all_files:
        if filename.endswith(valid_formats):
            if filter and (filter not in filename):
                continue
            else:
                texture_files.append(os.path.abspath(filename))

    if not texture_files:
        print("No valid texture files, exiting...")
        sys.exit()

    # Run maketx function
    print("Processing {0} texture files...".format(len(texture_files)))
    with futures.ThreadPoolExecutor(len(texture_files)) as executor:
        tasks = [executor.submit(run_maketx, file, verbose) for file in texture_files]
        print("Starting maketx process...\n", flush=True)
        for task in futures.as_completed(tasks):
            print(task.result(), flush=True)

# Parse arguments and run main function
if not __name__ == '__main__':
    sys.exit()

parser = argparse.ArgumentParser(description='Arnold maketx batch utility.')
parser.add_argument('path', help='Path for converting tx.')
parser.add_argument('-f', '--filter', action='store', type=str, help='Optional string filter to limit files to maketx')
parser.add_argument('-r', '--recursive', action="store_true", help='Recursively look in subdirectories')
parser.add_argument('-v', '--verbose', action="store_true", help='Show verbose output of maketx')
args = parser.parse_args()

main(args.path, args.filter, args.recursive, args.verbose)