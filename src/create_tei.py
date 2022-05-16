import argparse
import re
import sys
from conversion_utils.jos_msds_and_properties import Converter, Msd
from conversion_utils.translate_conllu_jos import get_syn_map

from lxml import etree


class Sentence:
    def __init__(self, _id, no_ud=False, is_source=None):
        self._id = _id
        self.items = []
        self.links = []
        self.no_ud = no_ud
        self.is_source = is_source

        # JOS-SYN translations from English to Slovene
        self.syn_map = get_syn_map()

    def add_item(self, word_id, token, lemma, upos, upos_other, xpos, head, deprel, no_space_after, ner):
        self.items.append([word_id, token, lemma, upos, upos_other, xpos, head, deprel, no_space_after, ner])

    def add_link(self, link_ref, link_type):
        self.links.append([link_ref, link_type])

    def as_xml(self, id_prefix=None):
        if id_prefix:
            xml_id = id_prefix + '.' + self._id
        else:
            xml_id = self._id
        base = etree.Element('s')
        set_xml_attr(base, 'id', xml_id)

        linkGrp = etree.Element(f'linkGrp')
        linkGrp.attrib[f'corresp'] = f'#{xml_id}'
        linkGrp.attrib[f'targFunc'] = 'head argument'
        linkGrp.attrib[f'type'] = 'JOS-SYN'

        ner_seg = None

        for item in self.items:
            word_id, token, lemma, upos, upos_other, xpos, head, deprel, no_space_after, ner = item

            if xpos in {'U', 'Z'}:  # hmm, safe only as long as U is unused in English tagset and Z in Slovenian one
                to_add = etree.Element('pc')
            else:
                to_add = etree.Element('w')

            to_add.set('ana', 'mte:' + xpos)
            if not self.no_ud:
                if upos_other != '_':
                    to_add.set('msd', f'UPosTag={upos}|{upos_other}')
                else:
                    to_add.set('msd', f'UPosTag={upos}')

            if xpos not in {'U', 'Z'}:
                to_add.set('lemma', lemma)

            set_xml_attr(to_add, 'id', "{}.{}".format(xml_id, word_id))
            to_add.text = token

            if no_space_after:
                to_add.set('join', 'right')

            # handle ner subclass
            if ner[0] == 'B':
                if ner_seg is not None:
                    base.append(ner_seg)
                    del ner_seg

                ner_seg = etree.Element('seg')
                ner_seg.set('type', f'name')
                ner_seg.set('subtype', f'{ner.split("-")[-1].lower()}')
            elif ner[0] == 'O':
                if ner_seg is not None:
                    base.append(ner_seg)
                    del ner_seg
                    ner_seg = None

            if ner_seg is None:
                base.append(to_add)
            else:
                ner_seg.append(to_add)

            # handle links
            link = etree.Element(f'link')
            link.attrib['ana'] = f'jos-syn:{self.syn_map[deprel]}'
            link.attrib['target'] = f'#{xml_id}.{head} #{xml_id}.{word_id}' if head != 0 else f'#{xml_id} #{xml_id}.{word_id}'
            linkGrp.append(link)

        if ner_seg is not None:
            base.append(ner_seg)

        base.append(linkGrp)

        return base


class Paragraph:
    def __init__(self, _id, _doc_id, is_source):
        self._id = _id if _id is not None else 'no-id'
        _doc_id += 's' if is_source else 't'
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
    def __init__(self, _id, divs=list()):
        self._id = _id
        self.divs = divs

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
        for paras, bibl in self.divs:
            div = etree.Element('div')
            set_xml_attr(div, 'id', xml_id)
            div.append(bibl)
            for para in paras:
                div.append(para.as_xml())
            body.append(div)

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


def convert_bibl(bibl):
    etree_bibl = etree.Element('bibl')
    etree_bibl.set('corresp', bibl.get('corresp'))
    etree_bibl.set('n', bibl.get('n'))
    for bibl_el in bibl:
        etree_bibl_el = etree.Element(bibl_el.tag)
        etree_bibl_el.text = bibl_el.text
        for att, val in bibl_el.attrib.items():
            if '{http://www.w3.org/XML/1998/namespace}' in att:
                set_xml_attr(etree_bibl_el, att.split('{http://www.w3.org/XML/1998/namespace}')[-1], val)
            else:
                etree_bibl_el.set(att, val)
        etree_bibl.append(etree_bibl_el)
    return etree_bibl


def build_tei_etrees(documents):
    elements = []
    for document in documents:
        elements.append(document.as_xml())
        # b = elements[-1]
        # a = list(b)
        # c = list(b)[0]
        # d = list(b)[1]
        # for e in d:
        #     for f in e:
        #         for g in f:
        #             print(g)
        # d = list(b)[1]
    return elements


def build_complete_tei(etree_source, etree_target, etree_links):
    root = etree.Element('TEI')
    root.set('xmlns', 'http://www.tei-c.org/ns/1.0')
    tei_header = etree.Element('teiHeader')
    text = etree.Element('text')
    group = etree.Element('group')
    group.append(list(etree_source[0])[1])
    group.append(list(etree_target[0])[1])
    text.append(group)
    root.append(tei_header)
    root.append(text)
    # standoff = etree.Element('standOff')
    # standoff.append(etree_links)
    # root.append(standoff)
    root.append(etree_links)
    return root


def build_links(all_edges):
    # root = etree.Element('text')
    # body = etree.Element('body')
    body = etree.Element('standOff')
    # root.set('xmlns', 'http://www.tei-c.org/ns/1.0')
    # set_xml_attr(root, 'lang', 'sl')

    # elements = []
    for document_edges in all_edges:
        # d = etree.Element('linkGrp')
        for paragraph_edges in document_edges:
            # p = etree.Element('linkGrp')
            for sentence_edges in paragraph_edges:
                s = etree.Element('linkGrp')

                sentence_id = ''
                for token_edges in sentence_edges:
                    if not sentence_id:
                        if len(token_edges['source_ids']) > 0:
                            random_source_id = token_edges['source_ids'][0]
                            sentence_id += '.'.join(random_source_id.split('.')[:3])
                        elif len(token_edges['target_ids']) > 0:
                            random_target_id = token_edges['target_ids'][0]
                            if len(token_edges['source_ids']) > 0:
                                sentence_id += ' #'
                            sentence_id += '.'.join(random_target_id.split('.')[:3])
                    link = etree.Element('link')
                    labels = '|'.join(token_edges['labels']) if len(token_edges['labels']) > 0 else 'ID'
                    link.set('type', labels)
                    link.set('target', ' '.join(['#' + source for source in token_edges['source_ids']] + ['#' + source for source in token_edges['target_ids']]))
                    # link.set('target', ' '.join(['#' + source for source in token_edges['target_ids']]))

                    s.append(link)
                s.set('type', 'CORR')
                s.set('targFunc', 'orig reg')
                s.set('corresp', f'#{sentence_id}')
                # body.append(s)
                body.append(s)
    # root.append(body)
    return body


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


def construct_paragraph_from_list(doc_id, para_id, etree_source_sentences, source_id):
    para = Paragraph(para_id, doc_id, source_id)

    for sentence in etree_source_sentences:
        para.add_sentence(sentence)

    return para


def construct_paragraph(doc_id, para_id, conllu_lines, is_source):
    para = Paragraph(para_id, doc_id, is_source)

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


def construct_sentence_from_list(sent_id, object_list, is_source):
    sentence = Sentence(sent_id)
    converter = Converter()
    for tokens in object_list:
        word_id = f"{tokens['id']}" if is_source else f"{tokens['id']}"
        token = tokens['form']
        lemma = tokens['lemma']
        upos = tokens['upos']
        xpos = converter.properties_to_msd(converter.msd_to_properties(Msd(tokens['xpos'], 'en'), 'sl', lemma), 'sl').code
        upos_other = '|'.join([f'{k}={v}' for k, v in tokens['feats'].items()]) if tokens['feats'] else '_'
        head = tokens['head']
        deprel = tokens['deprel']
        no_space_after = 'SpaceAfter' in tokens['misc'] and tokens['misc']["SpaceAfter"] == "No"
        ner = tokens['misc']['NER']

        sentence.add_item(
            word_id,
            token,
            lemma,
            upos,
            upos_other,
            xpos,
            head,
            deprel,
            no_space_after,
            ner
        )

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

