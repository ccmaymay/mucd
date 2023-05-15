#!/usr/bin/env python3

from itertools import cycle
from pathlib import Path
from pyparsing import (
    alphanums, alphas, printables,
    delimited_list, one_of,
    Char, CharsNotIn, Group, Literal, Word,
    Combine, FollowedBy, Opt, StringEnd, StringStart, Suppress,
    ParserElement,
)

import click


DATA_PATHS = [
    path
    for split in ('train', 'dev')
    for path in Path('.').glob(f'data/raw/splits/{split}/docs/*')
]

COLOR_ITER = cycle(('yellow', 'cyan'))


ParserElement.set_default_whitespace_chars('')

sentence_punct_chars = '.?!'
personal_title_strs = """
ADM. CAPT. CMDR. COL. CPT. GEN. MAJ. SGT.
DR. HON. JR. MR. MRS. MS. REP. REV. SEN. SR. ST.
""".strip().split()

whitespace_chars = ' \t\r\n'
space = Word(' \t')
newline = Suppress(Opt(space) + (Literal('\r\n') | Literal('\n')))
token_space = Combine((newline + Opt(space)) | space)
section_indent = Suppress(Literal(' ')[1, ...])
section_sep = Suppress(newline[2, ...])

personal_title = one_of(personal_title_strs)
number_abbrev = Literal('NO.')
initial = Combine(Char(alphas) + Literal('.'))
acronym = Combine(initial[1, ...])

token = Combine((Opt(Literal('...') | Char(sentence_punct_chars)) +
                 delimited_list(CharsNotIn(sentence_punct_chars + whitespace_chars),
                                delim=(Literal('...') | Char(sentence_punct_chars))) +
                 Opt(Literal('...') + ~Literal('.'))) |
                (Literal('...') + ~Literal('.')) |
                (CharsNotIn(alphanums + whitespace_chars) +
                 (personal_title | number_abbrev | acronym) +
                 ~Literal('.'))).set_name('token')
sentence = Combine(delimited_list(token, delim=token_space, combine=True) +
                   ((Opt(token_space) + Char(sentence_punct_chars)) |
                    FollowedBy(section_sep | (Opt(token_space) + Literal('....'))))).set_name('sentence')
section = Group(section_indent +
                Suppress(Opt(Literal('....') + Opt(token_space))) +
                delimited_list(sentence,
                               delim=token_space | (Opt(token_space) + Literal('....') + Opt(token_space)),
                               combine=True).set_results_name('sentences') +
                Suppress(Opt(Opt(token_space) + Literal('....')))).set_name('section')
title = Combine(delimited_list(Word(printables), delim=Word(' \t'))).set_name('title')
document = Group(title.set_results_name('title') +
                 section_sep +
                 delimited_list(section, delim=section_sep).set_results_name('sections')).set_name('document')
corpus = Group(StringStart() +
               newline[...] +
               delimited_list(document, delim=section_sep).set_results_name('documents') +
               newline[...] +
               StringEnd()).set_name('corpus')

for path in DATA_PATHS:
    click.echo(click.style(path, fg='magenta', bold=True))
    click.echo()
    result = corpus.parse_file(path, parse_all=True)
    for document in result['documents']:
        click.echo(document['title'])
        click.echo()
        for section in document['sections']:
            for sentence in section['sentences']:
                click.echo(click.style(sentence.replace('\n', ' '), fg=next(COLOR_ITER)))
            click.echo()
        click.echo()
