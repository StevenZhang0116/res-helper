from multiprocessing import Pool
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import PDFPageAggregator
from pdfminer3.converter import TextConverter

from pdf2image import convert_from_path
from PIL import Image
import shutil

import fitz
from skimage.metrics import structural_similarity as ssim
import traceback

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
import json
from datetime import datetime
import functools
import fnmatch
import threading
import warnings
import time
import scipy
import cv2
import argparse


# inspired from: https://stackoverflow.com/questions/8897593/how-to-compute-the-similarity-between-two-text-documents
stemmer = nltk.stem.porter.PorterStemmer()
remove_punctuation_map = dict((ord(char), None) for char in string.punctuation)


def stem_tokens(tokens):
    return [stemmer.stem(item) for item in tokens]


def normalize(text):
    return stem_tokens(nltk.word_tokenize(text.lower().translate(remove_punctuation_map)))


vectorizer = TfidfVectorizer(tokenizer=normalize, stop_words='english')


def cosine_sim(text1, text2):
    tfidf = vectorizer.fit_transform([text1, text2])
    return ((tfidf * tfidf.T).A)[0, 1]


def pdf_first_page_to_image(rawrootdir, pdfpath):
    break_loc = find_occurrences(pdfpath, "/")[-1]
    out_image_path = f"{rawrootdir}{pdfpath[break_loc+1:]}.png"
    
    images = convert_from_path(pdfpath, first_page=1, last_page=1)
    for image in images:
        image.save(out_image_path, 'PNG')
        print(f"Save image to {out_image_path}")

    # saved path of the image
    return out_image_path 


def find_occurrences(s, char):
    return [index for index, c in enumerate(s) if c == char]

# process the pdf file


def process_pdf(xpath, sepkeystrig, xordef, cutthreshold, img_output):
    reslst = []  # filtered filepath
    allreslst = []  # all filepath
    abslst = []  # filtered abstract (should have same length with [reslst])
    allabslst = []  # all abstract
    firstpagelst = [] # filtered image (based on the filtered abstract)
    allfirstpagelst = [] # all output image

    try:
        resource_manager = PDFResourceManager()
        fake_file_handle = io.StringIO()
        converter = TextConverter(
            resource_manager, fake_file_handle, laparams=LAParams())
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
            # all information include
            allreslst.append(xpath)
            allabslst.append(subtext)

            # save loaded first image

            # out_image_path = pdf_first_page_to_image(img_output, xpath)
            # allfirstpagelst.append(out_image_path)

            # only the desired information included
            # "AND" or "OR" judgement
            if xordef == 0:
                if any([x in subtext for x in sepkeystrig]):
                    reslst.append(xpath)
                    abslst.append(subtext)
                    # firstpagelst.append(out_image_path)
            elif xordef == 1:
                if all([x in subtext for x in sepkeystrig]):
                    reslst.append(xpath)
                    abslst.append(subtext)
                    # firstpagelst.append(out_image_path)

            converter.close()
            fake_file_handle.close()
    except Exception as e:
        tb = traceback.format_exc()
        print(f"An error occurred: {e}\nTraceback details:\n{tb}")

    return [reslst, abslst, firstpagelst, allreslst, allabslst, allfirstpagelst]


def breakpt_gen():
    init = '\n'
    numbers = list(range(10))
    char_num = [init + str(i) for i in numbers]
    letters = list(string.ascii_letters)
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

# check whether there are duplicated documents contained in the folder
# this part will be time-consuming if there are a large number of files stored in the folder


def duplicate_search_by_words_and_photos(rootfolder, cutthreshold, img_output, thres1=0.99, thres2=0.70):
    sepkeystrig = []
    xordef = 1

    # extract information from all literature from scratch;
    # to know which current files are duplicated (most updated)
    # therefore the loading interface using pre-created database is not provided
    arr = []
    for root, dirnames, filenames in os.walk(rootfolder):
        for filename in fnmatch.filter(filenames, '*.pdf'):
            arr.append(os.path.join(root, filename))

    textreslst = []
    namelst = []
    imagelst = []
    with Pool() as pool:
        textresults = []
        for xpath in arr:
            result = pool.apply_async(
                process_pdf, (xpath, sepkeystrig, xordef, cutthreshold, img_output))
            textresults.append(result)

        for result in textresults:
            namelst.extend(result.get()[0])
            textreslst.extend(result.get()[1])
            imagelst.extend(result.get()[2])

    print("== Abstract Texts are generated; Start Duplication Search ==")
    # generate all unordered 2-dimensional tuples within the specified range
    unique_tuples_set = {tuple(sorted((x, y))) for x in range(
        len(textreslst)) for y in range(len(textreslst))}
    # remove tuples with the same elements and filter out tuples where x and y are equal
    unique_tuples_list = [t for t in unique_tuples_set if t[0] != t[1]]

    simpaperlst = []
    with Pool() as pool:
        partial_process_tuple = functools.partial(
            process_tuple, textreslst=textreslst, namelst=namelst, imagelst=imagelst, word_threshold=thres1, image_threshold=thres2)
        results = pool.map(partial_process_tuple, unique_tuples_list)

    simpaperlst.extend(filter(None, results))
    print("== Duplication Test is finished ==")

    return simpaperlst

def resize_image(image, size):
    inm = cv2.resize(image, (3507, 2481), interpolation=cv2.INTER_LINEAR)
    gray = cv2.cvtColor(inm, cv2.COLOR_BGR2GRAY)
    return gray

def compare_image_similarity(image_path1, image_path2, size=1000):
    # Load and convert images to grayscale
    image1 = cv2.imread(image_path1, cv2.COLOR_BGR2GRAY)
    image2 = cv2.imread(image_path2, cv2.COLOR_BGR2GRAY)

    # Resize images
    image1_resized = resize_image(image1, size)
    image2_resized = resize_image(image2, size)

    # Compute SSIM
    score, _ = ssim(image1_resized, image2_resized, full=True)
    return score

def process_tuple(thetuple, textreslst, namelst, imagelst, word_threshold=0.99, image_threshold=0.70):
    try:
        current_thread = threading.current_thread()
        thread_name = current_thread.name
        thread_ident = current_thread.ident

        i, j = thetuple[0], thetuple[1]
        text1, text2 = textreslst[i], textreslst[j]

        # cosine angle approach
        similarity1 = cosine_sim(text1, text2)
        # similarity2 = compare_image_similarity(imagelst[i], imagelst[j])
        
        # if similarity1 > word_threshold or similarity2 > image_threshold:
        if similarity1 > word_threshold: 
            # print(f"Finished comparison bewteen {namelst[i]} and {namelst[j]}")
            return [namelst[i], namelst[j]]

        return None

    except Exception as e:
        tb = traceback.format_exc()
        print(f"An error occurred: {e}\nTraceback details:\n{tb}")
        return None


def merge_tuple(input):
    merged_tuples = {}

    for thetuple in input:
        # sort the tuple to handle (x, y) and (y, x) cases
        sorted_tuple = tuple(sorted(thetuple))
        if sorted_tuple in merged_tuples:
            merged_tuples[sorted_tuple] += thetuple
        else:
            merged_tuples[sorted_tuple] = thetuple

    merged_tuple_list = list(merged_tuples.values())
    return merged_tuple_list

# split keywords into separate words (contained in the list)


def splitkey(keystring):
    sepkeystrig = []
    for txt in keystring:
        for j in txt.split():
            sepkeystrig.append(j.lower())

    return sepkeystrig

# search through all articles in the designated folder that may contain certain keystring


def article_search_by_words(rootfolder, keystring, cutthreshold, img_output):
    sepkeystrig = splitkey(keystring)

    xordef = 1

    arr = []
    for root, dirnames, filenames in os.walk(rootfolder):
        for filename in fnmatch.filter(filenames, '*.pdf'):
            arr.append(os.path.join(root, filename))
    print(f"Total number of files: {len(arr)}")

    reslst = []  # desired filepath
    allreslst = []  # all path for all files
    allabslst = []  # all path for all extracted information from all files

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

            result = pool.apply_async(
                process_pdf, (xpath, sepkeystrig, xordef, cutthreshold, img_output))
            results.append(result)

            cnt += 1

        # Retrieve the results from the multiprocessing tasks
        for result in results:
            reslst.extend(result.get()[0])
            allreslst.extend(result.get()[2])
            allabslst.extend(result.get()[3])

    return [reslst, allreslst, allabslst]


def open_pdf_file(file_path):
    if platform.system() == 'Darwin':  # macOS
        subprocess.call(['open', file_path])
    elif platform.system() == 'Windows':  # Windows
        subprocess.call(['start', file_path], shell=True)
    elif platform.system() == 'Linux':  # Linux
        subprocess.call(['xdg-open', file_path])
    else:
        print("Unsupported operating system.")


def generate_json(allpath, allabstract, filename="loaddata.json"):
    # remove old database
    try:
        os.remove(filename)
        print("Old Database is Removed")
    except OSError:
        tb = traceback.format_exc()
        print(f"An error occurred: {e}\nTraceback details:\n{tb}")

    data = {
        "path": allpath,
        "abstract": allabstract
    }

    with open(filename, "w") as json_file:
        json.dump(data, json_file)

    print("== JSON database is generated ==")


def delete_files(file_paths):
    # input type: list of list
    # total number of files that have been deleted
    cnt = 0
    for thepath in file_paths:
        print(thepath)
        assert len(thepath) >= 2
        # delete everything except the first one
        for i in range(1, len(thepath)):
            try:
                os.remove(thepath[i])
                cnt += 1
                print(f"Remove {thepath[i]}")
            except Exception as e:
                tb = traceback.format_exc()
                print(f"An error occurred: {e}\nTraceback details:\n{tb}")
    return cnt


def delete_pycache(directory):
    for root, dirs, files in os.walk(directory):
        if '__pycache__' in dirs:
            print(f"Deleting: {os.path.join(root, '__pycache__')}")
            shutil.rmtree(os.path.join(root, '__pycache__'))
