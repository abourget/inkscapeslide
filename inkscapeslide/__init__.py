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
#   +layer4
#   background, layer2 * 0.5, layer3 * 0.5, layer5
#


import lxml.etree
import sys
import os
import re
from optparse import OptionParser


def main():
    import warnings
    # HIDE DEPRECATION WARINGS ONLY IN RELEASES. SHOW THEM IN DEV. TRUNKS
    warnings.filterwarnings('ignore', category=DeprecationWarning)

    parser = OptionParser()
    parser.add_option("-i", "--imageexport", action="store_true", dest="imageexport", default=False, help="Use PNG files as export content")
    (options, args) = parser.parse_args()

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
        print "   background, layer2 * 0.5, layer3"
        print "   +layer4 * 0.5"
        print ""
        print "each name being the label of another layer. Lines starting with"
        print "a '+' will add to the layers of the preceding line, creating"
        print "incremental display (note there must be no whitespace before '+')"
        print ""
        print "The opacity of a layer can be set to 50% for example by adding "
        print "'*0.5' after the layer name."
        sys.exit(1)

    content = content_layer[0]

    # Find the text stuff, everything starting with SLIDE:
    #   take all the layer names separated by ','..
    preslides = [x.text for x in content.findall('{http://www.w3.org/2000/svg}text/{http://www.w3.org/2000/svg}tspan') if x.text]


    if not bool(preslides):
        print "Make sure you have a text box (with no flowRect) in the " \
            "'content' layer, and rerun this program."
        sys.exit(1)


    #print preslides


    # Get the initial style attribute and keep it
    orig_style = {}
    for l in layers:
        label = l.attrib.get('{http://www.inkscape.org/namespaces/inkscape}label') 
        if 'style' not in l.attrib:
            l.set('style', '')
        # Save initial values
        orig_style[label] = l.attrib['style']


    slides = [] # Contains seq of [('layer', opacity), ('layer', opacity), ..]
    for sl in preslides:
        if sl:
            if sl.startswith('+'):
                sl = sl[1:]
                sl_layers = slides[-1].copy()
            else:
                sl_layers = {}

            for layer in sl.split(','):
                elements = layer.strip().split('*')
                name = elements[0].strip()
                opacity = None
                if len(elements) == 2:
                    opacity = float(elements[1].strip())
                sl_layers[name] = {'opacity': opacity}
            slides.append(sl_layers)


    def set_style(el, style, value):
        """Set the display: style, add it if it isn't there, don't touch the
        rest
        """
        if re.search(r'%s: ?[a-zA-Z0-9.]*' % style, el.attrib['style']):
            el.attrib['style'] = re.sub(r'(.*%s: ?)([a-zA-Z0-9.]*)(.*)' % style,
                                        r'\1%s\3' % value, el.attrib['style'])
        else:
            el.attrib['style'] = '%s:%s;%s' % (style, value, el.attrib['style'])


    pdfslides = []
    for i, slide_layers in enumerate(slides):
        for l in layers:
            label = l.attrib.get('{http://www.inkscape.org/namespaces/inkscape}label')
            # Set display mode to original
            l.set('style', orig_style[label])

            # Don't show it by default...
            set_style(l, 'display', 'none')

            if label in slide_layers:
                set_style(l, 'display', 'inline')
                opacity = slide_layers[label]['opacity']
                if opacity:
                    set_style(l, 'opacity', str(opacity))
            #print l.attrib['style']
        svgslide = os.path.abspath(os.path.join(os.curdir,
                                                "%s.p%d.svg" % (FILENAME, i)))
        pdfslide = os.path.abspath(os.path.join(os.curdir,
                                                "%s.p%d.pdf" % (FILENAME, i)))
        # Use the correct extension if using images
        if options.imageexport:
            pdfslide = os.path.abspath(os.path.join(os.curdir,
                                                "%s.p%d.png" % (FILENAME, i)))

        # Write the XML to file, "wireframes.p1.svg"
        f = open(svgslide, 'w')
        f.write(lxml.etree.tostring(doc))
        f.close()

        # Determine whether to export pdf's or images (e.g. inkscape -A versus inkscape -e)
        cmd = "inkscape -A %s %s" % (pdfslide, svgslide)
        if options.imageexport:
            cmd = "inkscape -d 180 -e %s %s" % (pdfslide, svgslide)

        os.system(cmd)
        os.unlink(svgslide)
        pdfslides.append(pdfslide)

        print "Generated page %d." % (i+1)

    joinedpdf = False
    outputFilename = "%s.pdf" % FILENAME.split(".svg")[0]
    outputDir = os.path.dirname(outputFilename)
    print "Output file %s" % outputFilename

    if options.imageexport:
        if not os.system('which convert > /dev/null'):
            print "Using 'convert' to join PNG's"
            os.system("convert %s -resample 180 %s" % (os.path.join(outputDir, "*.png"), outputFilename))
            joinedpdf = True
        else:
            print "Please install ImageMagick to provide the 'convert' utility"
    else:
        # Join PDFs
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
            outputStream = file(outputFilename, "wb")
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
            print "Please install pdfjam, pdftk or install the 'pyPdf' python " \
                "package, to join PDFs."

    # Clean up
    if joinedpdf:
        for pdfslide in pdfslides:
            os.unlink(pdfslide)
