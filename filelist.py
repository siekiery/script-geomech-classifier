import os
import os.path as osp
import csv
import pandas as pd

PATH = r"home" # path to root directory
FOLDERS = ['dir1', 'dir2', 'dir3', 'dir4', 'dir5'] # selected directories
OUTPUT1 = r"output_path1"
OUTPUT2 = r"output_path2"


filepaths = []
i = 0
for fldr in FOLDERS:
    for root, _, files in os.walk(osp.join(PATH, fldr)):
        for file in files:
            abspath = osp.join(root, file)
            relpath = osp.relpath(abspath, PATH)
            filepaths.append(relpath)
            if i % 100 == 0:
                print(f"File {i}")
            i += 1

size = len(filepaths)

with open(OUTPUT1, 'w', newline="", encoding='utf-8') as csvfile:
    csvwriter = csv.writer(csvfile)

    HEADERS = ['NAME', 'FORMAT', 'FILEPATH']
    csvwriter.writerow(HEADERS)

    i = 0

    for file in filepaths:
        i += 1
        name = osp.basename(file)
        format = osp.splitext(file)[1].upper()
        row = [name, format, file]
        csvwriter.writerow(row)
        if i % 1000 == 0:
            print(f"File {i}/{size}")

    print("Finished.")

# Format value counts
df = pd.read_csv(OUTPUT1)
df_valcounts = df.value_counts(subset='FORMAT')
df_valcounts.to_csv(OUTPUT2)


