# Standard Library Imports
import io
import json
import os
import random
import re
import shutil
import string
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime
from multiprocessing import Pool
from unicodedata import normalize

# Third-Party Library Imports
import cv2
import fitz  # PyMuPDF
import matplotlib.pyplot as plt
import nltk
import numpy as np
import tensorflow_hub as hub
from PIL import Image
from pdf2image import convert_from_path
from pdfrw import PdfReader
from skimage.metrics import structural_similarity as ssim
from sklearn.feature_extraction.text import TfidfVectorizer

# PDF Processing Related Imports
from pdfminer3.converter import PDFPageAggregator, TextConverter
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer3.pdfpage import PDFPage

# Concurrent Execution
import concurrent.futures


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

# difficulty: handling ascii encoding + unicode characters


def preprocess_text(input, cutthreshold):
    subtext = input[0:cutthreshold]
    # replace typical break characters
    subtext = subtext.replace("\n", "").replace(
        "\r", "").replace("\t", "").replace("\f", "")
    subtext = re.sub(r'[^\x00-\x7F]+', '', subtext)

    breaktext = breakpt_gen()
    for txt in breaktext:
        subtext.replace(txt, '')

    # change to lower space
    subtext = subtext.lower()
    # remove all unicode characters
    # subtext = subtext.encode('ascii', 'ignore').decode('ascii')
    return subtext


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


def renameFileToPDFTitle(fullName, path):
    try:
        # Extract pdf title from pdf file
        newName = PdfReader(fullName).Info.Title
        if str(newName) == "()":
            raise ValueError
        # Remove surrounding brackets that some pdf titles have
        newName = newName.strip('()') + '.pdf'
        newName = newName.replace("\\", "").replace("/", "")
        newFullName = os.path.join(path, newName)
        os.rename(fullName, newFullName)
        return [newFullName, newName, 1]
    except:
        filename = fullName.replace(path, "")
        # print(f"filename: {filename}")
        return [fullName, filename, 0]


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


def open_pdf_file(file_path):
    if platform.system() == 'Darwin':  # macOS
        subprocess.call(['open', file_path])
    elif platform.system() == 'Windows':  # Windows
        subprocess.call(['start', file_path], shell=True)
    elif platform.system() == 'Linux':  # Linux
        subprocess.call(['xdg-open', file_path])
    else:
        print("Unsupported operating system.")


def generate_json(allpath, allabstract, alltext, alltitle, renamecnt, filename="loaddata.json"):
    # remove old database
    try:
        os.remove(filename)
        print("=== Old Database is Removed ===")
    except OSError:
        tb = traceback.format_exc()
        print(f"An error occurred: {e}\nTraceback details:\n{tb}")

    data = {
        "the_path": allpath,
        "art_title": alltitle,
        "this_abstract": allabstract,
        "full_content": alltext
    }

    with open(filename, "w") as json_file:
        json.dump(data, json_file)

    print(f"=== JSON database is generated (length={len(allpath)})===")
    print(f"=== Total number of {sum(renamecnt)} files have been renamed ===")


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
