# Academic Literature Organizer

This repository is consistently updated with succinct scripts (validated in Python 3.9.0), which are highly useful for academic research.

****

[article_search.py](https://github.com/StevenZhang0116/res-helper/blob/main/article_search.py): This script offers a range of functionalities for analyzing PDFs (primarily academic papers), encompassing keyword searches and the identification of duplicate files. It aims to provide an alternative to [Mendeley](https://www.mendeley.com/) to some extent, which imposes storage limits (2GB for free users, 5GB for subscribers). For an enhanced experience, users are encouraged to adjust parameter settings directly within the file.

* (2024.02.04): Add UI handler. 

* The task of duplication removal can be time-consuming. In my local tests, comparing approximately 2000 articles takes about 10 minutes. Regrettably, the comparison is conducted pairwise, implying the time complexity is O(N^2).

* Functions of image comparison are included, but hard to be implemented in large-scale. 

* [testpaper]: include several arbitrarily chosen academic literatures for testing purposes.

* [loaddata.json]: a sample database.

* Current Drawback: The setup of a relatively high cut-off threshold for comparing similarity significantly increases the likelihood that the code will fail to identify identical articles published under different entities (e.g., arXiv, other journals, or conferences) or in various versions.

It is highly recommended to run the code in a [conda] environment for optimal version control. To use, simply execute: 
```
conda create -n "testpdf" python=3.9.0
python -m pip install -r requirements.txt
python article_search.py --index 0 --key "reinforcement learning" --ioindex 1
```

If want to use UI, simply execute: 
```
python ui.py
```
and choose functionalities from the displayed screen.  