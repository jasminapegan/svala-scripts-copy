import argparse
import copy
import logging
import os
import time
from xml.etree import ElementTree

logging.basicConfig(level=logging.INFO)


def process_file(et):
    errors = {}
    L1_num = 0
    L2_num = 0
    L3_num = 0
    L4_num = 0
    L5_num = 0
    for div in et.iter('div'):
        bibl = div.find('bibl')
        file_name = bibl.get('n')
        paragraphs = div.findall('p')
        for paragraph in paragraphs:
            sentences = paragraph.findall('s')
            for sentence in sentences:
                sent_id = sentence.get('{http://www.w3.org/XML/1998/namespace}id')
                errorsL1 = sentence.findall('u1')
                for errorL1 in errorsL1:
                    errors.setdefault((errorL1.get('kat'), errorL1.get('tip'), errorL1.get('podtip')), []).append([file_name, sent_id])
                    errorsL2 = errorL1.findall('u2')
                    L1_num += 1
                    for errorL2 in errorsL2:
                        errors.setdefault((errorL2.get('kat'), errorL2.get('tip'), errorL2.get('podtip')), []).append([file_name, sent_id])
                        errorsL3 = errorL2.findall('u3')
                        L2_num += 1
                        for errorL3 in errorsL3:
                            errors.setdefault((errorL3.get('kat'), errorL3.get('tip'), errorL3.get('podtip')), []).append([file_name, sent_id])
                            errorsL4 = errorL3.findall('u4')
                            L3_num += 1
                            for errorL4 in errorsL4:
                                errors.setdefault((errorL4.get('kat'), errorL4.get('tip'), errorL4.get('podtip')), []).append([file_name, sent_id])
                                errorsL5 = errorL4.findall('u5')
                                L4_num += 1
                                for errorL5 in errorsL5:
                                    errors.setdefault((errorL5.get('kat'), errorL5.get('tip'), errorL5.get('podtip')), []).append([file_name, sent_id])
                                    L5_num += 1
    print(f'L1: {L1_num}|L2: {L2_num}|L3: {L3_num}|L4: {L4_num}|L5: {L5_num}|')
    text = ''
    for k, v in errors.items():
        for el in v:
            text += f'{k[0]}\t{k[1]}\t{k[2]}\t{el[0]}\t{el[1]}\n'

    return text


def main(args):
    with open(args.input_file, 'r') as fp, open(args.output_file, 'w', encoding='utf-8') as wf:
        logging.info(args.input_file)
        et = ElementTree.XML(fp.read())
        wf.write(process_file(et))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Read already processed xmls, erase entries without examples and limit gigafida examples to 1 per entry.')
    parser.add_argument('--input_file', default='data/Solar2.0/solar2.xml',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    parser.add_argument('--output_file', default='data/tags.tsv',
                        help='input file in (gz or xml currently). If none, then just database is loaded')
    args = parser.parse_args()

    start = time.time()
    main(args)
    logging.info("TIME: {}".format(time.time() - start))
