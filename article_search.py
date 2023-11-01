# this code serves for quickly search information, 
# including title, authors' names, etc., from a designated root folder
# specifically designed for a "raw" literature search

# jul 2 update -- change the code to multiprocessing version
# oct 30 update -- update duplication check

# Author: Zihan Zhang, UW

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
import string
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
import matplotlib.pyplot as plt
import tensorflow_hub as hub
import concurrent.futures


stemmer = nltk.stem.porter.PorterStemmer()
remove_punctuation_map = dict((ord(char), None) for char in string.punctuation)

# inspired from: https://stackoverflow.com/questions/8897593/how-to-compute-the-similarity-between-two-text-documents
def stem_tokens(tokens):
    return [stemmer.stem(item) for item in tokens]

def normalize(text):
    return stem_tokens(nltk.word_tokenize(text.lower().translate(remove_punctuation_map)))

vectorizer = TfidfVectorizer(tokenizer=normalize, stop_words='english')

def cosine_sim(text1, text2):
    tfidf = vectorizer.fit_transform([text1, text2])
    return ((tfidf * tfidf.T).A)[0,1]


def process_pdf(xpath, sepkeystrig, xordef, cutthreshold):
    reslst = []
    abslst = []
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

            subtext = preprocess_text(text, cutthreshold)
            abslst.append(subtext)
            # print(abslst)

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

    return [reslst, abslst]

def breakpt_gen():
    init = '\n'
    numbers = list(range(10))
    char_num = [init + str(i) for i in numbers]
    letters =  list(string.ascii_letters)
    char_letters = [init + i for i in letters]

    lst = []
    lst.extend(char_num)
    lst.extend(char_letters)

    return lst

def preprocess_text(input, cutthreshold):
    subtext = input[0:cutthreshold]
    subtext.replace('\n', '')

    breaktext = breakpt_gen()
    for txt in breaktext:
        subtext.replace(txt, '')

    subtext = subtext.lower()
    return subtext

# check whether there are duplicated documents... 
def duplicate_search(rootfolder, cutthreshold):
    sepkeystrig = []
    xordef = 1

    arr = []
    for root, dirnames, filenames in os.walk(rootfolder):
        for filename in fnmatch.filter(filenames, '*.pdf'):
            arr.append(os.path.join(root, filename))

    textreslst = []
    namelst = []
    with Pool() as pool: 
        textresults = []
        for xpath in arr:
            result = pool.apply_async(process_pdf, (xpath, sepkeystrig, xordef, cutthreshold))
            textresults.append(result)

        for result in textresults:
            namelst.extend(result.get()[0])
            textreslst.extend(result.get()[1])

    print("== Abstract Texts are generated ==")

    # Generate all unordered 2-dimensional tuples within the specified range
    unique_tuples_set = {tuple(sorted((x, y))) for x in range(len(textreslst)) for y in range(len(textreslst))}
    # Remove tuples with the same elements and filter out tuples where x and y are equal
    unique_tuples_list = [t for t in unique_tuples_set if t[0] != t[1]]

    simpaperlst = []
    cnt = 1
    for thetuple in unique_tuples_list:
        try: 
            if cnt % 10000 == 0:
                print(f"{cnt}/{len(unique_tuples_list)}")

            i, j = thetuple[0], thetuple[1]
            text1, text2 = textreslst[i], textreslst[j]

            # cosine angle approach
            similarity1 = cosine_sim(text1, text2)
            if similarity1 > 0.99:
                simpaperlst.append([namelst[i], namelst[j]])
            cnt += 1

        except Exception as e:
            print(e)

    print("== Duplication Test is finished ==")

    return simpaperlst

def merge_tuple(input):
    merged_tuples = {}

    for thetuple in input:
        sorted_tuple = tuple(sorted(thetuple))  # Sort the tuple to handle (x, y) and (y, x) cases
        if sorted_tuple in merged_tuples:
            merged_tuples[sorted_tuple] += thetuple
        else:
            merged_tuples[sorted_tuple] = thetuple

    merged_tuple_list = list(merged_tuples.values())
    return merged_tuple_list


def heatmap(x_labels, y_labels, values):
    fig, ax = plt.subplots()
    im = ax.imshow(values)

    # We want to show all ticks...
    ax.set_xticks(np.arange(len(x_labels)))
    ax.set_yticks(np.arange(len(y_labels)))
    # ... and label them with the respective list entries
    ax.set_xticklabels(x_labels)
    ax.set_yticklabels(y_labels)

    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=10,
         rotation_mode="anchor")

    # Loop over data dimensions and create text annotations.
    for i in range(len(y_labels)):
        for j in range(len(x_labels)):
            text = ax.text(j, i, "%.2f"%values[i, j],
                           ha="center", va="center", color="w", fontsize=6)

    fig.tight_layout()
    plt.show()

# search through all articles in the designated folder that may contain certain keystring
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
            reslst.extend(result.get()[0])

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
    # keywords list you want to search on
    keystring = ['siam']
    
    index = 1 
    if index == 0:
        ## keyword search demo
        cutthreshold = 500
        keywordresult = article_search(rootfolder, keystring, cutthreshold)
        resultlist = keywordresult

        openindex = input(f"Do you want to open these {len(resultlist)} files? ")
        if int(openindex) == 1:
            for i in resultlist:
                open_pdf_file(i)

    elif index == 1:
        ## duplication search demo
        cutthreshold = 1000
        duplicateresult = duplicate_search(rootfolder, cutthreshold)
        resultlist = duplicateresult
        resultlist = merge_tuple(resultlist)

        print(resultlist)
