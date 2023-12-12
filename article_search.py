# this code serves for quickly search information,
# including title, authors' names, etc., from a designated root folder
# specifically designed for a "raw" literature search

# jul 2 update -- change the code to multiprocessing version
# oct 30 update -- update duplication check
# nov 1st update -- add I/O interface [embedded into article search]

# Author: Zihan Zhang, UW

from article_search_helper import *

if __name__ == "__main__":
    warnings.filterwarnings("ignore")

    # Create the parser
    parser = argparse.ArgumentParser(
        description='Process inputs for document handling in a specified folder.')

    # Add arguments
    # filepath of designated folder
    parser.add_argument('--rootfolder', type=str, default="../paper/",
                        help="Filepath of the designated folder")

    # keywords list you want to search on;
    # for more precise result, keep it short and concise without special characters;
    # e.g. article's title, author's name, or article's keyword
    parser.add_argument('--keystring', type=str, help="Keywords to search")

    # which functionality to choose
    # 0: search content &/ (re)create database
    # 1: duplication search & remove undesired documents
    parser.add_argument('--index', type=int, choices=[0, 1], required=True,
                        help='Functionality to choose (0: search content/create database, 1: duplication search)')

    # The following options are only needed when index == 0
    # I/O index [whether to use existed database to speed up searching (though might not be exhaustive)]
    parser.add_argument('--ioindex', type=int,
                        choices=[0, 1], default=1, help='I/O index')

    # database index [whether to rewrite old database]
    parser.add_argument('--databaseindex', type=int,
                        choices=[0, 1], default=0, help='Database index')

    # output image folder
    parser.add_argument('--imgout', type=str, default="image_save/",
                        help="Output path of first image extraction")

    # Parse the arguments
    args = parser.parse_args()

    # Assigning values from arguments
    rootfolder = args.rootfolder
    keystring = [args.keystring]
    index = args.index
    img_output = f"{rootfolder}{args.imgout}"

    # Create image output folder
    os.makedirs(img_output, exist_ok=True)
    print(f"Path '{img_output}' ensured.")

    # The following options are only needed when index == 0
    if index == 0:
        ioindex = args.ioindex
        databaseindex = args.databaseindex
    else:
        ioindex = None
        databaseindex = None

    print("=== Experiment Start ===")

    start_time = time.time()

    if index == 0:
        file_name = "loaddata.json"
        file_path = os.path.join(os.getcwd(), file_name)
        if os.path.exists(file_path):
            timestamp = os.path.getmtime(file_path)
            formatted_timestamp = datetime.fromtimestamp(
                timestamp).strftime('%H:%M at %m:%d:%Y')
            # output timestamp info
            print(
                f"Database file with path: {file_path} generated at {formatted_timestamp}")
        else:
            print("No database is existed")

        if ioindex == 0:
            print("== Starting searching from scratch ==")
            # keyword search demo
            cutthreshold = 1000
            keywordresult, allresult, allabstract = article_search_by_words(
                rootfolder, keystring, cutthreshold, img_output)

            resultlist = keywordresult
            # check
            assert len(allresult) == len(allabstract)

            if databaseindex == 1:
                generate_json(allresult, allabstract)

        elif ioindex == 1:
            print("== Use database result ==")
            # keyword search demo, but using pregenerated database
            try:
                resultlist = []
                sepkeystrig = splitkey(keystring)

                with open(file_path, "r") as json_file:
                    data = json.load(json_file)
                    allpath = data["path"]
                    allabstract = data["abstract"]
                    print(f"Total number of files: {len(allpath)}")
                    # searching over list is efficient, so parallel computation is not needed
                    for i in range(len(allpath)):
                        theabstract = allabstract[i]
                        if all([x in theabstract for x in sepkeystrig]):
                            resultlist.append(allpath[i])

            except Exception as e:
                print(e)

        # whether to open the selected files
        openindex = input(
            f"Do you want to open these {len(resultlist)} files? ")
        # open the files (in default application) if permitted
        # DON'T DO THAT IF THERE ARE TOO MANY FILES IN THE SEARCHED LIST
        if int(openindex) == 1:
            print(f"Search Files: {resultlist}")
            for i in resultlist:
                open_pdf_file(i)

    elif index == 1:
        # duplication search demo
        cutthreshold = 1000
        duplicateresult = duplicate_search_by_words_and_photos(rootfolder, cutthreshold, img_output, 0.99)
        resultlist = duplicateresult
        # resultlist = merge_tuple(resultlist)
        print(resultlist)
        deleteindex = input(f"Delete these files? ")
        if int(deleteindex) == 1:
            cnt = delete_files(resultlist)
            print(f"Total number of files for deletion: {cnt}")

    end_time = time.time()
    running_time = end_time - start_time
    print(f"Program running time: {int(running_time)}s")

    # Delete cache folder
    delete_pycache(os.getcwd())
