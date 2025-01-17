# coding=utf-8

import csv
import argparse, argcomplete
import os.path
import sys
import brewer2mpl
import pyssed
import jenks
from itertools import groupby    #for function most_common
from operator  import itemgetter #for function most_common

#Check if file exists
def is_valid_file(parser, arg):
    if not os.path.exists(arg):
       parser.error("The file %s does not exist!" % arg)
    else:
       return arg

#Check if values are numbers, for our purposes
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

#Check if values are years
def isYear(s):
	try:
		float(s)
		if 4 is len(s):
			return True
		else:
			return False
	except ValueError:
		return False
        
#Find the most common _numerical_ value, or False if most values are non numerical
#From http://stackoverflow.com/questions/1518522/python-most-common-element-in-a-list
def most_common(L):
  # get an iterable of (item, iterable) pairs
  SL = sorted((x, i) for i, x in enumerate(L))
  # print 'SL:', SL
  groups = groupby(SL, key=itemgetter(0))
  # auxiliary function to get "quality" for an item
  def _auxfun(g):
    item, iterable = g
    count = 0
    min_index = len(L)
    for _, where in iterable:
      count += 1
      min_index = min(min_index, where)
    # print 'item %r, count %r, minind %r' % (item, count, min_index)
    return count, -min_index
  # pick the highest-count/earliest item
  return max(groups, key=_auxfun)[0]

# Add fill color to dict
fillColors = {} # save all css rules here
css = {}
def addFillColor(year,land,color):
	if color not in fillColors:
		fillColors[color] = []
	fillColors[color].append(".y{0} .{1} > *".format(year, land))
def addFillColorToLand(year,land,color):
	if isYear(year):
		if color not in fillColors:
			fillColors[color] = []
		fillColors[color].append(".y{0} .{1} > .land".format(year, land))
def addFillColorNoYear(land,color):
	if color not in fillColors:
		fillColors[color] = []
	fillColors[color].append(".%s > *" % land)
	
################################################################################################333

#Define command line arguments
parser = argparse.ArgumentParser(description='Converts data to color codes, using Jenks natural breaks optimization and ColorBrewer.')

#Input file
parser.add_argument("-i", "--input", dest="infile", required=True,
    help="input file", metavar="FILE",
    type=lambda x: is_valid_file(parser,x))

#Output file
parser.add_argument("-o", "--output", dest="outfile",
    help="output file", metavar="FILE")

#Color scheme
parser.add_argument("-m", "--map", dest="colormap",
    help="Color map, see https://github.com/jiffyclub/brewer2mpl/wiki/Sequential", default='YlOrRd',
    choices=('Blues','BuGn','BuPu','GnBu','Greens','Greys','OrRd','Oranges','PuBu','PuBuGn','PuRd','Purples','RdPu','Reds','YlGn','YlGnBu','YlOrBr','YlOrRd'))

argcomplete.autocomplete(parser)

args = parser.parse_args()

inputFile = args.infile

if args.outfile is None:
	outputFile = os.path.splitext(inputFile)[0] + ".css"
	print "No output file given, using %s" % outputFile
else:
	outputFile = args.outfile

if os.path.isfile(outputFile):
	print "File %s already exists. Overwrite? [y/N]" % args.outfile
	choice = raw_input().lower()
	if not choice in ('y', 'yes'):
		sys.exit()

numberOfJenksBreaks = 8
colorMap = args.colormap

#####################################################################################

values = []
headers = []
#Open file
try:
	with open(inputFile, 'rb') as csvfile:
		datacsv = csv.reader(csvfile,delimiter=',',quotechar='"')
		firstRow = True
		for row in datacsv:
			if firstRow:
				firstRow = False
				for col in row:
					headers.append(col)
			else:
				for col in row:
					if is_number(col):
						values.append(col)
    
except IOError:
    print ("Could not open input file")

# Calculate breaks    
jenksBreaks = jenks.getJenksBreaks( values, numberOfJenksBreaks )
print "JenkBreaks:",
print jenksBreaks # [0, '0.308', '0.396', '0.489', '0.584', '0.674', '0.755', '0.843', 0.955]

#Loop through all rows and cols and convert any numerical values to a color
bmap = brewer2mpl.get_map(colorMap, 'sequential', numberOfJenksBreaks)
colors = bmap.hex_colors
#bmap.colorbrewer2()

try:
	with open(inputFile, 'rb') as csvfile:
		datacsv = csv.reader(csvfile,delimiter=',',quotechar='"')
		firstRow = True
		for row in datacsv:
			if firstRow:
				firstRow = False
			else:

				colorrow = []
				#Replace values with color codes
				firstCol = True
				for col in row:
					if firstCol:
						firstCol = False
					else:
						if is_number(col):
							for x in range(0, numberOfJenksBreaks-1):
								if float(col) > float(jenksBreaks[x]):
									code = colors[x]
							colorrow.append(code)
						else:
							colorrow.append(False)

				#Set default color
				defaultColorForNation = most_common(colorrow)
				print defaultColorForNation
				if defaultColorForNation is not False:
					addFillColorNoYear(row[0],defaultColorForNation) # land,color
					
				#Set other colors
				i = 0
				for c in colorrow:
					i += 1
					if c is not defaultColorForNation:
						if c is not False:
							addFillColor(headers[i] ,row[0], c) # year,land,color
						else:
							# We need to unset default colors again for years without values. 
							addFillColorToLand(headers[i] ,row[0], "lightgray")

except IOError:
    print ("Could not open input file")
    
for color in fillColors:
	classes = ",".join(fillColors[color])
	css[classes] = { 'fill': color }

# Write to file
try:
	f = open(outputFile, "w")
	try:
		f.write('\n'.join(pyssed.generate(css))) # Write a string to a file
	finally:
		f.close()
except IOError:
	print "Could not write to css file (%s)" % outputFile
