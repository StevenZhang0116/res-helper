from auxiliary import *

# process the pdf file


def process_pdf(xpath, sepkeystrig, xordef, cutthreshold, img_output, rootfolder):
    reslst = []  # filtered filepath
    allreslst = []  # all filepath
    abslst = []  # filtered abstract (should have same length with [reslst])
    allabslst = []  # all abstract
    textlst = []  # filtered (based on abstract) text
    alltextlst = []  # all text
    titlelst = []  # title
    alltitlelst = []  # all title
    firstpagelst = []  # filtered image (based on the filtered abstract)
    allfirstpagelst = []  # all output image
    checklst = []

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
            alltext = preprocess_text(text, len(text))
            # all information include
            allabslst.append(subtext)
            alltextlst.append(alltext)

            # extract new fullname
            [newFullPath, newFullName, renamecheck] = renameFileToPDFTitle(
                xpath, rootfolder)

            # add path only after the name is possibly revised
            allreslst.append(newFullPath)
            alltitlelst.append(newFullName)
            checklst.append(renamecheck)

            # save loaded first image [time consuming]

            # out_image_path = pdf_first_page_to_image(img_output, xpath)
            # allfirstpagelst.append(out_image_path)

            # only the desired information included
            # "AND" or "OR" judgement
            if xordef == 0:
                if any([x in subtext for x in sepkeystrig]):
                    # reslst.append(xpath)

                    # append new path (after possible renaming)
                    reslst.append(newFullPath)
                    abslst.append(subtext)
                    textlst.append(alltext)
                    titlelst.append(newFullName)
                    # firstpagelst.append(out_image_path)
            elif xordef == 1:
                if all([x in subtext for x in sepkeystrig]):
                    # reslst.append(xpath)
                    reslst.append(newFullPath)
                    abslst.append(subtext)
                    textlst.append(alltext)
                    titlelst.append(newFullName)
                    # firstpagelst.append(out_image_path)

            converter.close()
            fake_file_handle.close()
    except Exception as e:
        tb = traceback.format_exc()
        print(f"An error occurred: {e}\nTraceback details:\n{tb}")

    return [reslst, abslst, textlst, titlelst, firstpagelst, allreslst, allabslst, alltextlst, alltitlelst, allfirstpagelst, checklst]


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

    namelst = []
    textreslst = []
    fulltextlst = []
    imagelst = []
    titlelst = []
    with Pool() as pool:
        textresults = []
        for xpath in arr:
            result = pool.apply_async(
                process_pdf, (xpath, sepkeystrig, xordef, cutthreshold, img_output, rootfolder))
            textresults.append(result)

        for result in textresults:
            namelst.extend(result.get()[0])
            textreslst.extend(result.get()[1])
            fulltextlst.extend(result.get()[2])
            titlelst.extend(result.get()[3])
            imagelst.extend(result.get()[4])

    print("== Abstract Texts are generated; Start Duplication Search ==")
    # generate all unordered 2-dimensional tuples within the specified range
    unique_tuples_set = {tuple(sorted((x, y))) for x in range(
        len(textreslst)) for y in range(len(textreslst))}
    # remove tuples with the same elements and filter out tuples where x and y are equal
    unique_tuples_list = [t for t in unique_tuples_set if t[0] != t[1]]

    simpaperlst = []
    with Pool() as pool:
        # do not need full text to do duplication check
        # time consuming and hard to pick a reasonable and stable threshold
        partial_process_tuple = functools.partial(
            process_tuple, textreslst=textreslst, namelst=namelst, imagelst=imagelst, word_threshold=thres1, image_threshold=thres2)
        results = pool.map(partial_process_tuple, unique_tuples_list)

    simpaperlst.extend(filter(None, results))
    print("== Duplication Test is finished ==")

    return simpaperlst


# search through all articles in the designated folder that may contain certain keystring


def article_search_by_words(rootfolder, keystring, cutthreshold, img_output):
    sepkeystrig = splitkey(keystring)

    xordef = 1

    arr = []
    for root, dirnames, filenames in os.walk(rootfolder):
        for filename in fnmatch.filter(filenames, '*.pdf'):
            arr.append(os.path.join(root, filename))
    print(f"Total number of files: {len(arr)}")

    reslst = []  # desired (filtered) filepath based on keyword search
    allreslst = []  # path for all files in the designated folder
    allabslst = []  # extracted abstract information from all files
    alltextlst = []  # extracted full text information from all files
    alltitlelst = []  # extracted title information from all files
    renamecnt = []

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
                process_pdf, (xpath, sepkeystrig, xordef, cutthreshold, img_output, rootfolder))
            results.append(result)

            cnt += 1

        # Retrieve the results from the multiprocessing tasks
        for result in results:
            reslst.extend(result.get()[0])
            allreslst.extend(result.get()[5])
            allabslst.extend(result.get()[6])
            alltextlst.extend(result.get()[7])
            alltitlelst.extend(result.get()[8])
            renamecnt.extend(result.get()[10])

    return [reslst, allreslst, allabslst, alltextlst, alltitlelst, renamecnt]

