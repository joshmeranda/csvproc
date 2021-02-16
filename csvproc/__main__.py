#!/user/bin/env python

import argparse
import sys
import typing

import csvproc.summarize as summarize


def parse() -> typing.Optional[argparse.Namespace]:
    parser = argparse.ArgumentParser("csvproc", "csv file and column summarizer")

    parser.add_argument("file")

    out_group = parser.add_mutually_exclusive_group()
    out_group.add_argument("--json", action="store_const", const=summarize.SummaryFormat.JSON, dest="format",
                           help="output the summary as json")
    out_group.add_argument("--json-pretty", action="store_const", const=summarize.SummaryFormat.JSON_PRETTY, dest="format",
                           help="output the summary nicely formatted json")
    out_group.add_argument("--default", action="store_const", const=summarize.SummaryFormat.DEFAULT, dest="format",
                           default=summarize.SummaryFormat.DEFAULT,
                           help="use the default output format, displaying only relevant information")
    out_group.add_argument("--verbose", action="store_const", const=summarize.SummaryFormat.VERBOSE, dest="format",
                           help="use the default output format, displaying all information")
    parser.set_defaults(format=summarize.SummaryFormat.DEFAULT)

    if len(sys.argv) == 1:
        parser.print_help()
        return None

    return parser.parse_args()


def main():
    args = parse()

    if args is None:
        return

    summary = summarize.CsvSummary(path="/home/josh/PycharmProjects/csvproc/lotr.csv")

    summary.write_summary(sys.stdout, args.format)


if __name__ == "__main__":
    main()
