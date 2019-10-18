#!/bin/env python3


def error_args():
    print("ERROR")


def aq_ls():
    print("ls")


def main():
    import argparse
    import sys

    if len(sys.argv) < 2:
        error_args()

    elif sys.argv[1] == "ls":
        aq_ls()

    else:
        error_args()
