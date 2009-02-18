#!/usr/bin/python
# -=- encoding: utf-8 -=-
# Author: Alexandre Bourget
# Copyright (c) 2008: Alexandre Bourget
# LICENSE: GPLv3


import lxml.etree
import sys
import os



# Grab user arguments
if len(sys.argv) < 2 or sys.argv[1].startswith('--'):
    print "Usage: %s [svgfilename]" % sys.argv[0]
    sys.exit(1)

FILENAME = sys.argv[1]


# Verify pdfjoin exists in PATH
err = os.system('which pdfjoin > /dev/null')

if err:
    print "Please install pdfjam, which provides the required 'pdfjoin' program."
    sys.exit(1)
    

# Take the Wireframes.svg
f = open(FILENAME)
cnt = f.read()
f.close()

doc = lxml.etree.fromstring(cnt)

# Get all layers
layers = [x for x in doc.iterdescendants(tag='{http://www.w3.org/2000/svg}g') if x.attrib.get('{http://www.inkscape.org/namespaces/inkscape}groupmode', False) == 'layer']

# Scan the 'content' layer
content_layer = [x for x in layers if x.attrib.get('{http://www.inkscape.org/namespaces/inkscape}label', False).lower() == 'content']

if not content_layer:
    print "No 'content'-labeled layer."
    print "Create a 'content'-labeled layer and put a text box (no flowRect),"
    print "with each line looking like:"
    print ""
    print "   background, layer1"
    print "   background, layer2"
    print "   background, layer2, layer3"
    #print "   +layer4"
    print ""
    #print "each name being the label of another layer. Lines starting with"
    #print "a '+' will add to the layers of the preceding line, creating"
    #print "incremental display"
    sys.exit(1)

content = content_layer[0]

# Find the text stuff, everythign starting with SLIDE:
#   take all the layer names separated by ','..
preslides = [x.text for x in content.findall('{http://www.w3.org/2000/svg}text/{http://www.w3.org/2000/svg}tspan')]


if not bool(preslides):
    print "Make sure you have a text box (with no flowRect) in the 'content'"
    print "layer, and rerun this program."
    sys.exit(1)


print preslides


slides = []
for sl in preslides:
    if sl:
        slides.append([x.strip() for x in sl.split(',')])

for i, slide in enumerate(slides):
    # Hide all layers
    for l in layers:
        l.attrib['style'] = 'display:none'

    # Show only slide layers
    for l in layers:
        if l.attrib.get('{http://www.inkscape.org/namespaces/inkscape}label') in slide:
            l.attrib['style'] = 'display:inline'
    
    # Write the XML to file, "wireframes.p1.svg"
    f = open(FILENAME+".p%d.svg" % i, 'w')
    f.write(lxml.etree.tostring(doc))
    f.close()
    
    # Run inkscape -A wireframes.p1.pdf wireframes.p1.svg
    os.system("inkscape -A %s.p%d.pdf %s.p%d.svg" % (FILENAME, i, FILENAME, i))
    print "Generated page %d." % (i+1)


# In the end, run: pdfjoin wireframes.p*.pdf -o Wireframes.pdf
os.system("pdfjoin --outfile %s.pdf %s.p*.pdf" % (FILENAME, FILENAME))

# Clean up
os.system("rm -f %s.p*.pdf %s.p*.svg" % (FILENAME, FILENAME))



