# Geomech Classifier script
### Demo version for GitHub
### Developed by: Jakub Pitera 


Script for file classification based on the contents.  
It was used to classify 86,000 files from geomechanics domain.

The content of each file is analysed in search for keywords from particular label using regex. The keywords from higher priority label are searched first and if at least one is found, then that label is assigned. 

Text of the file is preprocessed to increase accuracy. 

Files description:
* geomech_classifier.py - python script with GeomechClassifier class to run classification
* filelist.py - python script to generate a filelist used by the classifier
* filelist.csv - list of files with absolute paths. output of filelist.py. input of geomech_classifier.py
* parameters.xlsx - dictionary with keywords for each label
* Reports - directory where reports are saved by the script
