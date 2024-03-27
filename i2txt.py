#!/usr/bin/python3

import sys
import argparse
from PIL import Image

escape_char = '\033['

def convert_image(image, mode="RGBA"):
	# Convert image to our desired format if needed.
	if image.mode != mode:
		return image.convert(mode)
	else:
		return image

def convert_to_txt_1_1(image, fg=False):
	"""
	Convert the image using a 1:1 scale using two characters for each "pixel".
	By default it will use spaces and set the background color to the pixel color.
	If 'fg' is set to True it will instead use the foreground and two '█' characters.
	"""
	PIXEL_CHAR_1_1_FG = '██'
	PIXEL_CHAR_1_1_BG = '  '

	image = convert_image(image)

	src_image = list(image.getdata())
	lines = []

	# Create a list of pixels for each row of the image.
	while len(lines) < image.height:
		lines.append(src_image[:image.width])
		del src_image[:image.width]

	output_string = ''

	for line in lines:
		output_line = ''
		last_ansi_code = ''

		for char in line:
			if char[3] != 0:
				# Set color values for non-transparent pixels.
				if fg:
					ansi_code = f'{escape_char}38;2;{char[0]};{char[1]};{char[2]}m'
					ansi_char = PIXEL_CHAR_1_1_FG
				else:
					ansi_code = f'{escape_char}48;2;{char[0]};{char[1]};{char[2]}m'
					ansi_char = PIXEL_CHAR_1_1_BG
			else:
				# Reset if the pixel is transparent.
				ansi_code = f'{escape_char}0m'
				ansi_char = PIXEL_CHAR_1_1_BG

			# Avoid repeating the previous escape code if it's unchanged.
			if ansi_code == last_ansi_code:
				output_line = output_line + ansi_char
			else:
				output_line = output_line + ansi_code + ansi_char
				last_ansi_code = ansi_code

		output_string = output_string + output_line + f'{escape_char}0m\n'

	return output_string

def convert_to_txt_1_4(image):
	"""
	Convert the image using a 1:4 scale utilizing '▀' and '▄' characters to allow for two
	rows of pixels on each line of text and reducing the footprint to 25% compared to 1:1.
	The function will choose which character to use depending on if there are transparent pixels.
	"""
	PIXEL_CHAR_1_4_TOP = '▀'
	PIXEL_CHAR_1_4_LOW = '▄'

	image = convert_image(image)

	src_image = list(image.getdata())
	lines = []

	# Create a list of pixels for each row of the image.
	while len(lines) < image.height/2:
		lines.append(src_image[:image.width*2])
		del src_image[:image.width*2]

	output_string = ''

	for line in lines:
		output_line = ''
		last_ansi_code = ''

		# Split the line into even and odd rows of pixels.
		line = [line[:image.width]] + [line[image.width:]]
		char_index = 0

		# Loop through pixels in the even row.
		for char in line[0]:
			try:
				# Append pixel from the odd row.
				char = char + line[1][char_index]
			except IndexError:
				# Add dummy row of pixels if the image height is odd.
				char = char + (0, 0, 0, 0)

			char_index = char_index + 1

			# Set color values for non-transparent pixels.
			if char[3] != 0 and char[7] != 0:
				# If neither top or bottom pixel is transparent.
				ansi_code = f'{escape_char}38;2;{char[0]};{char[1]};{char[2]};48;2;{char[4]};{char[5]};{char[6]}m'
				ansi_char = PIXEL_CHAR_1_4_TOP
			elif char[3] != 0:
				# If bottom pixel is transparent reset and only set top pixel.
				ansi_code = f'{escape_char}0;38;2;{char[0]};{char[1]};{char[2]}m'
				ansi_char = PIXEL_CHAR_1_4_TOP
			elif char[7] != 0:
				# If top pixel is transparent reset and only set bottom pixel.
				ansi_code = f'{escape_char}0;38;2;{char[4]};{char[5]};{char[6]}m'
				ansi_char = PIXEL_CHAR_1_4_LOW
			else:
				# Reset if the pixel is transparent.
				ansi_code = f'{escape_char}0m'
				ansi_char = ' '

			# Avoid repeating the previous escape code if it's unchanged.
			if ansi_code == last_ansi_code:
				output_line = output_line + ansi_char
			else:
				output_line = output_line + ansi_code + ansi_char
				last_ansi_code = ansi_code

		output_string = output_string + output_line + f'{escape_char}0m\n'

	return output_string

parser = argparse.ArgumentParser(prog='i2txt', description='Convert images to 24-bit ANSI escape codes.',)
parser.add_argument('-f', '--format', default='1', help='Output format can be one of: 1: "1:4" (default), 2: "1:1", 3: "1:1_fg"')
parser.add_argument('-p', '--printf', action='store_true', help='Make the output copyable for use with e.g. printf.')
parser.add_argument('-d', '--printfilename', action='store_true', help='Print the filename for each converted image.')
parser.add_argument('-i', '--printinfo', action='store_true', help='Print information about the source image.')
parser.add_argument('filename', nargs='+', help='File to convert to ANSI text. (required)')

args = parser.parse_args()

if args.printf:
	escape_char = '\\033['

for i in args.filename:
	try:
		from PIL import UnidentifiedImageError
		if args.printfilename:
			print(f'{i}:')

		with Image.open(i) as image:
			if args.printinfo:
				print(f'File: {image.filename}')
				print(f'Resolution: {image.size[0]}x{image.size[1]}')
				print(f'Format: {image.format}')
				print(f'Mode: {image.mode}\n')

			if args.format in ["1", "1:4"]:
				print(convert_to_txt_1_4(image))
			elif args.format in ["2", "1:1"]:
				print(convert_to_txt_1_1(image))
			elif args.format.lower() in ["3", "1:1_fg"]:
				print(convert_to_txt_1_1(image, fg=True))
			else:
				print(f'ERROR: "Format must be one of: 1: "1:4", 2: "1:1", 3: "1:1_fg". Not "{args.format}".\n')

	except UnidentifiedImageError:
		print(f'ERROR: "{i}" is not a valid image.\n')
	except FileNotFoundError:
		print(f'ERROR: "{i}" does not exist.\n')
