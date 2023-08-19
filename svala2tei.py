import argparse
import logging
import os
import shutil
import time

from src.annotate.annotate import annotate
from src.read.read_and_merge import tokenize
from src.write.write import write_tei

logging.basicConfig(level=logging.DEBUG)

def process_file(args):
    if os.path.exists(args.results_folder):
        shutil.rmtree(args.results_folder)
    os.mkdir(args.results_folder)

    # READ AND MERGE svala tokenization, solar2 tokenization and obeliks tokenization
    tokenized_source_divs, tokenized_target_divs, document_edges = tokenize(args)

    # ANNOTATE WITH CLASSLA
    annotated_source_divs, annotated_target_divs = annotate(tokenized_source_divs, tokenized_target_divs, args)

    # GENERATE TEI AND WRITE OUTPUT
    write_tei(annotated_source_divs, annotated_target_divs, document_edges, args)


def main(args):
    process_file(args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Merges svala data, raw data and metadata into TEI format (useful for corpora like KOST).')
    parser.add_argument('--svala_folder', default='data/KOST/svala',
                        help='Path to directory that contains svala files.')
    parser.add_argument('--results_folder', default='data/KOST/results',
                        help='Path to results directory.')
    parser.add_argument('--raw_text', default='data/KOST/raw',
                        help='Path to directory that contains raw text files.')
    parser.add_argument('--texts_metadata', default='data/KOST/texts_metadata5.csv',
                        help='KOST metadata location')
    parser.add_argument('--authors_metadata', default='data/KOST/authors_metadata5.csv',
                        help='KOST authors location')
    parser.add_argument('--teachers_metadata', default='data/KOST/teachers_metadata.csv',
                        help='KOST teachers location')
    parser.add_argument('--translations', default='data/KOST/translations.csv',
                        help='KOST Slovenian-English column names translations for TEI metadata')
    parser.add_argument('--tokenization_interprocessing', default='data/processing.tokenization',
                        help='Path to file that containing tokenized data.')
    parser.add_argument('--overwrite_tokenization', action='store_true', help='Force retokenization without having to manually delete tokenization file.')
    parser.add_argument('--annotation_interprocessing', default='data/processing.annotation',
                        help='Path to file that containing annotated data.')
    parser.add_argument('--overwrite_annotation', action='store_true', help='Force reannotation without having to manually delete tokenization file.')
    args = parser.parse_args()

    start = time.time()
    main(args)
    logging.info("TIME: {}".format(time.time() - start))
