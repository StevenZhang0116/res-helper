# this code serves for quickly search information, 
# including title, authors' names, etc., from a designated root folder
# specifically designed for a "raw" literature search

# jul 2 update -- change the code to multiprocessing version

# Author: Zihan (Steven) Zhang, UW

from multiprocessing import Pool
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import PDFPageAggregator
from pdfminer3.converter import TextConverter
import io
import os
import fnmatch
import time
import numpy as np
import sys
import subprocess
import platform

def process_pdf(xpath, sepkeystrig, xordef, cutthreshold):
    reslst = []
    try:
        resource_manager = PDFResourceManager()
        fake_file_handle = io.StringIO()
        converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
        page_interpreter = PDFPageInterpreter(resource_manager, converter)

        fpagechecker = 0
        with open(xpath, 'rb') as fh:
            for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
                if fpagechecker == 0:
                    page_interpreter.process_page(page)
                    fpagechecker += 1
            text = fake_file_handle.getvalue()

            errtest = 0
            if errtest == 1:
                print(text)
                time.sleep(1000)

            subtext = text[0:cutthreshold]
            subtext.replace('\n', '')
            subtext = subtext.lower()

            if xordef == 0:
                if any([x in subtext for x in sepkeystrig]):
                    reslst.append(xpath)
            elif xordef == 1:
                if all([x in subtext for x in sepkeystrig]):
                    reslst.append(xpath)

            converter.close()
            fake_file_handle.close()
    except Exception as e:
        print(e)

    return reslst

def article_search(rootfolder, keystring, cutthreshold):
    sepkeystrig = []
    for txt in keystring:
        for j in txt.split():
            sepkeystrig.append(j.lower())
    xordef = 1

    arr = []
    for root, dirnames, filenames in os.walk(rootfolder):
        for filename in fnmatch.filter(filenames, '*.pdf'):
            arr.append(os.path.join(root, filename))

    reslst = []
    brelst = np.linspace(10, 100, 10)

    cnt = 1
    brkcnt = 0

    with Pool() as pool:
        results = []
        for xpath in arr:
            per = round(cnt / len(arr) * 100, 2)
            if per > brelst[brkcnt]:
                print(f"Search Finished: {brelst[brkcnt]}%")
                brkcnt += 1

            result = pool.apply_async(process_pdf, (xpath, sepkeystrig, xordef, cutthreshold))
            results.append(result)

            cnt += 1

        # Retrieve the results from the multiprocessing tasks
        for result in results:
            reslst.extend(result.get())

    return reslst

def open_pdf_file(file_path):
    if platform.system() == 'Darwin':  # macOS
        subprocess.call(['open', file_path])
    elif platform.system() == 'Windows':  # Windows
        subprocess.call(['start', file_path], shell=True)
    elif platform.system() == 'Linux':  # Linux
        subprocess.call(['xdg-open', file_path])
    else:
        print("Unsupported operating system.")

if __name__ == "__main__":
    # change to the folder 
    rootfolder = "../paper/"
    keystring = ['Towards deep learning with segregated dendrites']
    cutthreshold = 500

    resultlist = article_search(rootfolder, keystring, cutthreshold)
    print(resultlist)
    openindex = input(f"Do you want to open these {len(resultlist)} files? ")
    if openindex == 1:
        for i in resultlist:
            open_pdf_file(i)
