# import classla
# classla.download(lang='sl', type='standard_jos')

"""
Tests

python svala2tei.py `
    --svala_folder data_sample/KOST/svala_small `
    --raw_text data_sample/KOST/raw_small `
    --results_folder data_sample/KOST/results_small `
    --texts_metadata data_sample/KOST/texts_metadata5.csv `
    --authors_metadata data_sample/KOST/authors_metadata5.csv `
    --teachers_metadata data_sample/KOST/teachers_metadata.csv `
    --translations data_sample/KOST/translations.csv `
    --tokenization_interprocessing data_sample/processing.tokenization `
    --annotation_interprocessing data_sample/processing.annotation `
    --overwrite_tokenization `
    --overwrite_annotation

python svala2tei.py `
    --svala_folder data/KOST_1_0/svala_1_0 `
    --raw_text data/KOST_1_0/raw_1_0 `
    --results_folder data/KOST_1_0/results_1_0 `
    --texts_metadata data/KOST_1_0/texts_metadata5.csv `
    --authors_metadata data/KOST_1_0/authors_metadata5.csv `
    --teachers_metadata data/KOST_1_0/teachers_metadata.csv `
    --translations data/KOST_1_0/translations.csv `
    --tokenization_interprocessing data/processing.tokenization `
    --annotation_interprocessing data/processing.annotation `
    --overwrite_tokenization `
    --overwrite_annotation
    
python svala2tei.py `
    --svala_folder data/KOST_2_0/svala_2_0 `
    --raw_text data/KOST_2_0/raw_2_0 `
    --results_folder data/KOST_2_0/results_2_0 `
    --texts_metadata data/KOST_2_0/texts_metadata.csv `
    --authors_metadata data/KOST_2_0/authors_metadata.csv `
    --teachers_metadata data/KOST_2_0/teachers_metadata.csv `
    --translations data/KOST_2_0/translations.csv `
    --tokenization_interprocessing data/processing.tokenization `
    --annotation_interprocessing data/processing.annotation `
    --overwrite_tokenization `
    --overwrite_annotation


"""

import svala2tei
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--svala_folder', default='data/KOST_2_0/svala_2_0')
parser.add_argument('--results_folder', default='data/KOST_2_0/results_2_0')
parser.add_argument('--raw_text', default='data/KOST_2_0/raw_2_0')
parser.add_argument('--texts_metadata', default='data/KOST_2_0/texts_metadata_2_0.csv')
parser.add_argument('--authors_metadata', default='data/KOST_2_0/authors_metadata_2_0.csv')
parser.add_argument('--teachers_metadata', default='data/KOST_2_0/teachers_metadata_2_0.csv')
parser.add_argument('--translations', default='data/KOST_2_0/translations_2_0.csv')
parser.add_argument('--tokenization_interprocessing', default='data/processing.tokenization')
parser.add_argument('--overwrite_tokenization', action='store_true')
parser.add_argument('--annotation_interprocessing', default='data/processing.annotation')
parser.add_argument('--overwrite_annotation', action='store_true')
args = parser.parse_args()

svala2tei.main(args)