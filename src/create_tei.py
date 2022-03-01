import argparse
import re
import sys

from lxml import etree


class Sentence:
    def __init__(self, _id, no_ud=False):
        self._id = _id
        self.items = []
        self.links = []
        self.no_ud = no_ud

    def add_item(self, word_id, token, lemma, upos, upos_other, xpos, misc):
        self.items.append([word_id, token, lemma, upos, upos_other, xpos, "SpaceAfter=No" in misc.split('|')])

    def add_link(self, link_ref, link_type):
        self.links.append([link_ref, link_type])

    def as_xml(self, id_prefix=None):
        if id_prefix:
            xml_id = id_prefix + '.' + self._id
        else:
            xml_id = self._id
        base = etree.Element('s')
        set_xml_attr(base, 'id', xml_id)

        for item in self.items:
            word_id, token, lemma, upos, upos_other, xpos, no_space_after = item

            if xpos in {'U', 'Z'}:  # hmm, safe only as long as U is unused in English tagset and Z in Slovenian one
                to_add = etree.Element('pc')
            else:
                to_add = etree.Element('w')
                to_add.set('lemma', lemma)

            to_add.set('ana', 'mte:' + xpos)
            if not self.no_ud:
                if upos_other != '_':
                    to_add.set('msd', f'UposTag={upos}|{upos_other}')
                else:
                    to_add.set('msd', f'UposTag={upos}')

            set_xml_attr(to_add, 'id', word_id)
            to_add.text = token

            if no_space_after:
                to_add.set('join', 'right')

            base.append(to_add)

        return base


class Paragraph:
    def __init__(self, _id, _doc_id):
        self._id = _id if _id is not None else 'no-id'
        self._doc_id = _doc_id if _doc_id is not None else ''
        self.sentences = []

    def add_sentence(self, sentence):
        self.sentences.append(sentence)

    def as_xml(self, id_prefix=None):
        if id_prefix:
            xml_id = id_prefix + '.' + self._id
        else:
            if self._doc_id:
                xml_id = self._doc_id + '.' + self._id
            else:
                xml_id = self._id

        p = etree.Element('p')
        set_xml_attr(p, 'id', xml_id)

        for sent in self.sentences:
            p.append(sent.as_xml(id_prefix=xml_id))
        return p


class TeiDocument:
    def __init__(self, _id, paragraphs=list()):
        self._id = _id
        self.paragraphs = paragraphs

    def as_xml(self):
        root = etree.Element('TEI')
        root.set('xmlns', 'http://www.tei-c.org/ns/1.0')
        set_xml_attr(root, 'lang', 'sl')

        xml_id = self._id
        if xml_id is not None:
            set_xml_attr(root, 'id', xml_id)

        tei_header = etree.SubElement(root, 'teiHeader')

        text = etree.SubElement(root, 'text')
        body = etree.SubElement(text, 'body')
        for para in self.paragraphs:
            body.append(para.as_xml())

        encoding_desc = etree.SubElement(tei_header, 'encodingDesc')
        tags_decl = etree.SubElement(encoding_desc, 'tagsDecl')
        namespace = etree.SubElement(tags_decl, 'namespace')
        namespace.set('name', 'http://www.tei-c.org/ns/1.0')
        for tag in ['p', 's', 'pc', 'w']:
            count = int(text.xpath('count(.//{})'.format(tag)))
            tag_usage = etree.SubElement(namespace, 'tagUsage')
            tag_usage.set('gi', tag)
            tag_usage.set('occurs', str(count))
        return root

    def add_paragraph(self, paragraph):
        self.paragraphs.append(paragraph)


def build_tei_etrees(documents):
    elements = []
    for document in documents:
        elements.append(document.as_xml())
    return elements

def build_complete_tei(etree_source, etree_target, etree_links):
    root = etree.Element('text')
    group = etree.Element('group')
    group.append(list(etree_source[0])[1])
    group.append(list(etree_target[0])[1])
    # link_text = etree.Element('text')
    # link_body = etree.Element('body')
    # link_body.append(etree_links)
    # link_text.append(link_body)
    group.append(etree_links)
    root.append(group)

    return root

def build_links(all_edges):
    root = etree.Element('text')
    body = etree.Element('body')
    # root.set('xmlns', 'http://www.tei-c.org/ns/1.0')
    # set_xml_attr(root, 'lang', 'sl')

    # elements = []
    for document_edges in all_edges:
        d = etree.Element('linkGrp')
        for paragraph_edges in document_edges:
            p = etree.Element('linkGrp')
            for sentence_edges in paragraph_edges:
                s = etree.Element('linkGrp')
                random_id = ''
                for token_edges in sentence_edges:
                    link = etree.Element('link')
                    link.set('labels', ' '.join(token_edges['labels']))
                    link.set('sources', ' '.join(['#' + source for source in token_edges['source_ids']]))
                    link.set('targets', ' '.join(['#' + source for source in token_edges['target_ids']]))
                    if not random_id:
                        random_id = token_edges['source_ids'][0] if len(token_edges['source_ids']) > 0 else token_edges['target_ids'][0]
                    s.append(link)
                set_xml_attr(s, 'sentence_id', '.'.join(random_id.split('.')[:3]))
                p.append(s)
            set_xml_attr(p, 'paragraph_id', '.'.join(random_id.split('.')[:2]))
            d.append(p)
        set_xml_attr(d, 'document_id', random_id.split('.')[0])
        body.append(d)
    root.append(body)
    return root


def set_xml_attr(node, attribute, value):
    node.attrib['{http://www.w3.org/XML/1998/namespace}' + attribute] = value


def parse_metaline(line):
    tokens = line.split('=', 1)
    key = tokens[0].replace('#', '').strip()
    if len(tokens) > 1 and not tokens[1].isspace():
        val = tokens[1].strip()
    else:
        val = None
    return (key, val)


def is_metaline(line):
    if re.match('# .+ =.*', line):
        return True
    return False


def construct_tei_documents_from_list(object_list):
    documents = []

    doc_id = None
    document_paragraphs = []

    para_id = None
    # para_buffer = []

    # for line in object_list:
    #     if is_metaline(line):
    #         key, val = parse_metaline(line)
    #         if key == 'newdoc id':
    #             if len(para_buffer) > 0:
    #                 document_paragraphs.append(construct_paragraph(para_id, para_buffer))
    #             if len(document_paragraphs) > 0:
    #                 documents.append(
    #                     TeiDocument(doc_id, document_paragraphs))
    #                 document_paragraphs = []
    #             doc_id = val
    #         elif key == 'newpar id':
    #             if len(para_buffer) > 0:
    #                 document_paragraphs.append(construct_paragraph(para_id, para_buffer))
    #                 para_buffer = []
    #             para_id = val
    #         elif key == 'sent_id':
    #             para_buffer.append(line)
    #     else:
    #         if not line.isspace():
    #             para_buffer.append(line)

    if len(object_list) > 0:
        document_paragraphs.append(construct_paragraph(doc_id, para_id, object_list))

    if len(document_paragraphs) > 0:
        documents.append(
            TeiDocument(doc_id, document_paragraphs))

    return documents


def construct_tei_documents(conllu_lines):
    documents = []

    doc_id = None
    document_paragraphs = []

    para_id = None
    para_buffer = []

    for line in conllu_lines:
        if is_metaline(line):
            key, val = parse_metaline(line)
            if key == 'newdoc id':
                if len(para_buffer) > 0:
                    document_paragraphs.append(construct_paragraph(doc_id, para_id, para_buffer))
                if len(document_paragraphs) > 0:
                    documents.append(
                        TeiDocument(doc_id, document_paragraphs))
                    document_paragraphs = []
                doc_id = val
            elif key == 'newpar id':
                if len(para_buffer) > 0:
                    document_paragraphs.append(construct_paragraph(doc_id, para_id, para_buffer))
                    para_buffer = []
                para_id = val
            elif key == 'sent_id':
                para_buffer.append(line)
        else:
            if not line.isspace():
                para_buffer.append(line)

    if len(para_buffer) > 0:
        document_paragraphs.append(construct_paragraph(doc_id, para_id, para_buffer))

    if len(document_paragraphs) > 0:
        documents.append(
            TeiDocument(doc_id, document_paragraphs))

    return documents


def construct_paragraph_from_list(doc_id, para_id, etree_source_sentences):
    para = Paragraph(para_id, doc_id)

    for sentence in etree_source_sentences:
        para.add_sentence(sentence)

    return para


def construct_paragraph(doc_id, para_id, conllu_lines):
    para = Paragraph(para_id, doc_id)

    sent_id = None
    sent_buffer = []

    for line in conllu_lines:
        if is_metaline(line):
            key, val = parse_metaline(line)
            if key == 'sent_id':
                if len(sent_buffer) > 0:
                    para.add_sentence(construct_sentence(sent_id, sent_buffer))
                    sent_buffer = []
                sent_id = val
        elif not line.isspace():
            sent_buffer.append(line)

    if len(sent_buffer) > 0:
        para.add_sentence(construct_sentence(sent_id, sent_buffer))

    return para


def construct_sentence_from_list(sent_id, object_list):
    sentence = Sentence(sent_id, no_ud=True)
    for tokens in object_list:
        word_id = tokens['id']
        token = tokens['token']
        lemma = tokens['lemma']
        upos = '_'
        xpos = tokens['ana'][4:]
        upos_other = '_'
        misc = '_' if tokens['space_after'] else 'SpaceAfter=No'

        sentence.add_item(
            word_id,
            token,
            lemma,
            upos,
            upos_other,
            xpos,
            misc)

    return sentence


def construct_sentence(sent_id, lines):
    sentence = Sentence(sent_id)
    for line in lines:
        if line.startswith('#') or line.isspace():
            continue
        line = line.replace('\n', '')
        tokens = line.split('\t')
        word_id = tokens[0]
        token = tokens[1]
        lemma = tokens[2]
        upos = tokens[3]
        xpos = tokens[4]
        upos_other = tokens[5]
        depparse_link = tokens[6]
        depparse_link_name = tokens[7]
        misc = tokens[9]

        sentence.add_item(
            token,
            lemma,
            upos,
            upos_other,
            xpos,
            misc)

        sentence.add_link(
            depparse_link,
            depparse_link_name)
    return sentence


def construct_tei_etrees(conllu_lines):
    documents = construct_tei_documents(conllu_lines)
    return build_tei_etrees(documents)


def convert_file(input_file_name, output_file_name):
    input_file = open(input_file_name, 'r')
    root = construct_tei_etrees(input_file)[0]
    tree = etree.ElementTree(root)
    tree.write(output_file_name, encoding='UTF-8', pretty_print=True)
    input_file.close()

    tree = etree.ElementTree(root)
    tree.write(output_file_name, pretty_print=True, encoding='utf-8')


system = 'jos'  # default (TODO: make this cleaner)

if __name__ == '__main__':
    import argparse
    from glob import glob

    parser = argparse.ArgumentParser(description='Convert CoNNL-U to TEI.')
    parser.add_argument('files', nargs='+', help='CoNNL-U file')
    parser.add_argument('-o', '--out-file', dest='out', default=None,
                        help='Write output to file instead of stdout.')
    parser.add_argument('-s', '--system', dest='system', default='jos', choices=['jos', 'ud'])

    args = parser.parse_args()

    if args.out:
        f_out = open(args.out, 'w')
    else:
        f_out = sys.stdout

    system = args.system

    for arg in args.files:
        filelist = glob(arg)
        for f in filelist:
            with open(f, 'r') as conllu_f:
                tei_etrees = construct_tei_etrees(conllu_f)
            for tei_etree in tei_etrees:
                f_out.write(etree.tostring(tei_etree, pretty_print=True, encoding='utf-8').decode())
                f_out.write('')
