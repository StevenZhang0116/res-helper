# playground

import os
from pdfrw import PdfReader
import random

path = "testpaper/"

def renameFileToPDFTitle(path, fileName):
    fullName = os.path.join(path, fileName)
    print(fullName)
    # Extract pdf title from pdf file
    newName = PdfReader(fullName).Info.Title
    if str(newName) == "()":  
        newName = str(random.randint(1, 1e5))
    # Remove surrounding brackets that some pdf titles have
    newName = newName.strip('()') + '.pdf'
    print(newName)
    newFullName = os.path.join(path, newName)
    os.rename(fullName, newFullName)


for fileName in os.listdir(path):
    # Rename only pdf files
    fullName = os.path.join(path, fileName)
    if (not os.path.isfile(fullName) or fileName[-4:] != '.pdf'):
        continue
    renameFileToPDFTitle(path, fileName)