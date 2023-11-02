# res-helper

This repository is regularly updated with short scripts (tested in Python 3.9.0) that can be valuable for academic research purposes.

[article_search.py](https://github.com/StevenZhang0116/res-helper/blob/main/article_search.py): provide various functions to analyze pdfs (mainly academic literatures), including keyword searching and detection of duplicated files. Hope to replace [Mendeley](https://www.mendeley.com/) at some level, which has storage limitation. 

[testpaper]: include several arbitrarily chosen academic literature for test purpose. 

[loaddata.json]: sample database. 

Strongly suggest to run the code in '''conda'''. To use, simply: 
```
conda create -n "testpdf" python=3.9.0
python -m pip install -r requirements.txt
python article_search.py
```