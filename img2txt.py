#!/usr/bin/python3

import sys
import argparse
from PIL import Image

PIXEL_CHAR_1_1_BG = '  '
PIXEL_CHAR_1_1_FG = '██'
PIXEL_CHAR_1_4_TOP = '▀'
PIXEL_CHAR_1_4_LOW = '▄'
BLANK = ' '

def convert_image(image, format="RGBA"):
	if image.mode != format:
		return image.convert(format)
	else:
		return image

def convert_to_txt_1_1(image, fg=False):
	image = convert_image(image)

	src_image = list(image.getdata())
	lines = []

	while len(lines) < image.height:
		lines.append(src_image[:image.width])
		del src_image[:image.width]

	output_string = ''

	for line in lines:
		output_line = ''
		last_ansi_code = ''

		for char in line:
			if char[3] != 0:
				if fg:
					ansi_code = f'{escape_char}38;2;{char[0]};{char[1]};{char[2]}m'
					ansi_char = PIXEL_CHAR_1_1_FG
				else:
					ansi_code = f'{escape_char}48;2;{char[0]};{char[1]};{char[2]}m'
					ansi_char = PIXEL_CHAR_1_1_BG

			else:
				ansi_code = f'{escape_char}0m'
				ansi_char = PIXEL_CHAR_1_1_BG

			if ansi_code == last_ansi_code:
				output_line = output_line + ansi_char

			else:
				output_line = output_line + ansi_code + ansi_char

			last_ansi_code = ansi_code

		output_string = output_string + output_line + f'{escape_char}0m\n'

	return output_string

def convert_to_txt_1_4(image):
	image = convert_image(image)

	src_image = list(image.getdata())
	lines = []

	while len(lines) < image.height/2:
		lines.append(src_image[:image.width*2])
		del src_image[:image.width*2]

	output_string = ''

	for line in lines:
		output_line = ''
		last_ansi_code = ''

		line = [line[:image.width]] + [line[image.width:]]
		char_index = 0

		for char in line[0]:
			try:
				char = char + line[1][char_index]
			except IndexError:
				char = char + (0, 0, 0, 0)*image.width

			char_index = char_index + 1

			if char[3] != 0 and char[7] != 0:
				ansi_code = f'{escape_char}38;2;{char[0]};{char[1]};{char[2]};48;2;{char[4]};{char[5]};{char[6]}m'
				ansi_char = PIXEL_CHAR_1_4_TOP

			elif char[3] != 0:
				ansi_code = f'{escape_char}0;38;2;{char[0]};{char[1]};{char[2]}m'
				ansi_char = PIXEL_CHAR_1_4_TOP

			elif char[7] != 0:
				ansi_code = f'{escape_char}0;38;2;{char[4]};{char[5]};{char[6]}m'
				ansi_char = PIXEL_CHAR_1_4_LOW

			else:
				ansi_code = f'{escape_char}0m'
				ansi_char = BLANK

			if ansi_code == last_ansi_code:
				output_line = output_line + ansi_char
			else:
				output_line = output_line + ansi_code + ansi_char

			last_ansi_code = ansi_code

		output_string = output_string + output_line + f'{escape_char}0m\n'

	return output_string

parser = argparse.ArgumentParser(prog='i2a', description='Convert images to 24-bit ANSI escape codes.',)
parser.add_argument('-f', '--format', default='1', help='Output format can be one of: 1: "1:4" (default), 2: "1:1", 3: "1:1_fg"')
parser.add_argument('-p', '--printf', action='store_true', help='Make the output copyable for use with e.g. printf.')
parser.add_argument('-d', '--printfilename', action='store_true', help='Print the filename for each converted image.')
parser.add_argument('filenames', nargs='+', help='Files to convert to ANSI text. (required)')

args = parser.parse_args()

if args.printf:
	escape_char = '\\033['
else:
	escape_char = '\033['

for i in args.filenames:
	try:
		from PIL import UnidentifiedImageError
		if args.printfilename:
			print(f'{i}:')

		with Image.open(i) as image:

			if args.format.lower() in ["1", "1:4"]:
				print(convert_to_txt_1_4(image))
			elif args.format.lower() in ["2", "1:1"]:
				print(convert_to_txt_1_1(image))
			elif args.format.lower() in ["3", "1:1_fg"]:
				print(convert_to_txt_1_1(image, fg=True))

	except UnidentifiedImageError:
		print(f'ERROR: The image file at "{i}" is not valid.\n')
