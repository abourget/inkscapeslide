#!/usr/bin/python
# -=- encoding: utf-8 -=-
# Author: Alexandre Bourget 
# Copyright (c) 2008: Alexandre Bourget 
# LICENSE: GPLv3

# How to use this script
# ------------------------
# Create a "content" labeled layer and put a text box (no flowRect), with each
# line looking like:
#
#   background, layer1
#   background, layer2
#   background, layer2, layer3


import lxml.etree
import sys
import os
import re


# Grab user arguments
if len(sys.argv) < 2 or sys.argv[1].startswith('--'):
    print "Usage: %s [svgfilename]" % sys.argv[0]
    sys.exit(1)

FILENAME = sys.argv[1]
    

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
    print "No 'content'-labeled layer. Create a 'content'-labeled layer and "\
          "put a text box (no flowRect), with each line looking like:"
    print ""
    print "   background, layer1"
    print "   background, layer2"
    print "   background, layer2, layer3"
    print "   +layer4"
    print ""
    print "each name being the label of another layer. Lines starting with"
    print "a '+' will add to the layers of the preceding line, creating"
    print "incremental display (note there must be no whitespace before '+')"
    sys.exit(1)

content = content_layer[0]

# Find the text stuff, everything starting with SLIDE:
#   take all the layer names separated by ','..
preslides = [x.text for x in content.findall('{http://www.w3.org/2000/svg}text/{http://www.w3.org/2000/svg}tspan') if x.text]


if not bool(preslides):
    print "Make sure you have a text box (with no flowRect) in the 'content' "\
          "layer, and rerun this program."
    sys.exit(1)


print preslides


slides = []
for sl in preslides:
    if sl:
        if sl.startswith('+'):
            sl = ','.join(slides[-1]) + ',' + sl[1:]
        slides.append([x.strip() for x in sl.split(',')])

pdfslides = []
for i, slide in enumerate(slides):
    # Hide all layers
    for l in layers:
        # Set display mode to none
        try:
            l.attrib['style'] = re.sub(r'(.*display:)([a-zA-Z]*)(.*)',
                                       r'\1none\3', l.attrib['style'])
        except KeyError, e:
            # The 'style' attibut doesn't exist. Create one
            l.set('style','display:none')

    # Show only slide layers
    for l in layers:
        if l.attrib.get('{http://www.inkscape.org/namespaces/inkscape}label') in slide:
            # Set display mode to inline
            l.attrib['style'] = re.sub(r'(.*display:)([a-zA-Z]*)(.*)',
                                       r'\1inline\3', l.attrib['style'])
    
    svgslide = os.path.abspath(os.path.join(os.curdir, "%s.p%d.svg" % (FILENAME, i)))
    pdfslide = os.path.abspath(os.path.join(os.curdir, "%s.p%d.pdf" % (FILENAME, i)))
    # Write the XML to file, "wireframes.p1.svg"
    f = open(svgslide, 'w')
    f.write(lxml.etree.tostring(doc))
    f.close()

    # Run inkscape -A wireframes.p1.pdf wireframes.p1.svg
    os.system("inkscape -A %s %s" % (pdfslide, svgslide))
    os.unlink(svgslide)
    pdfslides.append(pdfslide)

    print "Generated page %d." % (i+1)

# Join PDFs
joinedpdf = False
has_pyPdf = False
try:
    import pyPdf
    has_pyPdf = True
except:
    pass

if has_pyPdf:
    print "Using 'pyPdf' to join PDFs"
    output = pyPdf.PdfFileWriter()
    inputfiles = []
    for slide in pdfslides:
        inputstream = file(slide, "rb")
        inputfiles.append(inputstream)
        input = pyPdf.PdfFileReader(inputstream)
        output.addPage(input.getPage(0))
    outputStream = file("%s.pdf" % FILENAME.split(".svg")[0], "wb")
    output.write(outputStream)
    outputStream.close()
    for f in inputfiles:
        f.close()
    joinedpdf = True

# Verify pdfjoin exists in PATH
elif not os.system('which pdfjoin > /dev/null'):
    # In the end, run: pdfjoin wireframes.p*.pdf -o Wireframes.pdf
    print "Using 'pdfsam' to join PDFs"
    os.system("pdfjoin --outfile %s.pdf %s" % (FILENAME.split(".svg")[0],
                                               " ".join(pdfslides)))
    joinedpdf = True

# Verify pdftk exists in PATH
elif not os.system('which pdftk > /dev/null'):
    # run: pdftk in1.pdf in2.pdf cat output Wireframes.pdf
    print "Using 'pdftk' to join PDFs"
    os.system("pdftk %s cat output %s.pdf" % (" ".join(pdfslides),
                                               FILENAME.split(".svg")[0]))
    joinedpdf = True
else:
    print "Please install pdfjam, pdftk or install the 'pyPdf' python package, "\
          "to join PDFs."

# Clean up
if joinedpdf:
    for pdfslide in pdfslides:
        os.unlink(pdfslide)
