#!/usr/bin/env python

import argparse
import sys
import logging
import pdb
import os.path as path
import pickle as pkl
import gzip as gz

import hdf
import h5py


class FastaSeq(object):

    def __init__(self, head, seq):
        self.head = head
        self.seq = seq


def parse_lines(lines):
    seqs = []
    seq = None
    start = None
    lines = [line.strip() for line in lines]
    lines = [line for line in lines if len(line) > 0]
    for i in range(len(lines)):
        if lines[i][0] == '>':
            if start is not None:
                head = lines[start]
                seq = ''.join(lines[start + 1: i])
                seqs.append(FastaSeq(head, seq))
            start = i
    if start is not None:
        head = lines[start]
        seq = ''.join(lines[start + 1:])
        seqs.append(FastaSeq(head, seq))
    return seqs


def read_file(filename, gzip=None):
    if gzip is None:
        gzip = filename.endswith('.gz')
    if gzip:
        lines = gz.open(filename, 'r').read().decode()
    else:
        lines = open(filename, 'r').read()
    lines = lines.splitlines()
    return parse_lines(lines)




if __name__ == '__main__':
    args = sys.argv
    name = path.basename(args[0])
    p = argparse.ArgumentParser(prog=name,
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                description='Parses FASTA sequence')
    p.add_argument('in_file', help='Input file', metavar='file')
    p.add_argument('-o', '--out_file', help='Output file')
    p.add_argument('--out_format', help='Output format', default=None, choices=['pk1', 'h5'])
    p.add_argument('--verbose', help='More detailed log messages', action='store_true')
    p.add_argument('--log_file', help='Write log messages to file')
    opts = p.parse_args()

    logging.basicConfig(filename=opts.log_file,
                        format='%(levelname)s (%(asctime)s): %(message)s')
    log = logging.getLogger(name)
    if opts.verbose:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    log.debug(opts)

    log.info('Reading input ...')
    seqs = read_file(opts.in_file)

    log.info('Writing output ...')
    if opts.out_format is None:
        if opts.out_file.find('.h5') >= 0:
            opts.out_format = 'h5'
        else:
            opts.out_format = 'pk1'
    if opts.out_file is None:
        for seq in seqs:
            print(seq.head)
            print(seq.seq)
    else:
        if opts.out_format == 'h5':
            hdf_file, hdf_path = hdf.split_path(opts.out_file)
            f = h5py.File(hdf_file, 'a')
            if len(seqs) == 1:
                if hdf_path == '/':
                    hdf_path = '/seq'
                if hdf_path in f:
                    del f[hdf_path]
                f.create_dataset(hdf_path, data=seqs[0].seq)
            else:
                for i, seq in enumerate(seqs):
                    p = '%s/%d' % (hdf_path, i)
                    if p in f:
                        del f[p]
                    f.create_dataset(p, data=seq.seq)
            f.close()
        else:
            t = [seq.seq for seq in seqs]
            pkl.dump(t, open(opts.out_file, 'wb'))

    log.info('Done!')
