import sys
sys.path.append('/usr/share/java/itext5.jar')

from com.itextpdf.text.pdf import PdfReader
from com.itextpdf.text.pdf.parser import PdfTextExtractor, TextExtractionStrategy

class AssemblyTextExtractionStrategy(TextExtractionStrategy):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.infos = []
        self.texts = []
    def renderText(self, info):
        text = info.text
        if text.isspace():
            return
        baseline = info.baseline
        start = baseline.startPoint
        end = baseline.endPoint
        x1 = start.get(0)
        x2 = end.get(0)
        y = self.height - start.get(1)
        if x1 * 2 > self.width:
            y += self.height
        self.infos.append((y, x1, x2, text))
    def getResultantText(self):
        self.infos.sort()
        lasty = None
        lastx = None
        for y, x1, x2, text in self.infos:
            if lasty is not None and abs(y - lasty) > 1:
                lastx = None
                self.texts.append('\n')
            if lastx is not None and abs(x1 - lastx) > 1:
                self.texts.append(' ')
            self.texts.append(text)
            lasty = y
            lastx = x2
        return ''.join(self.texts)

def main(pdf):
    reader = PdfReader(pdf)
    page = 1
    size = reader.getPageSize(page)
    strategy = AssemblyTextExtractionStrategy(size.width, size.height)
    text = PdfTextExtractor.getTextFromPage(reader, page, strategy)
    txt = pdf.replace('.pdf', '.txt')
    f = open(txt, 'w')
    f.write(text.encode('utf-8'))
    f.close()

if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) != 1:
        print 'Usage: assembly.py PDF'
        sys.exit()
    pdf = args[0]
    main(pdf)
