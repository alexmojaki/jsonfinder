#! /usr/bin/env python

from itertools import imap
import sys
from json import dumps
from __init__ import jsonfinder, check_min_elements
from optparse import OptionParser


def parse_args(args=None, raise_option_exceptions=False):

    parser = OptionParser(usage="Usage: [python -m] jsonfinder [OPTIONS] [FILTERS]",
                          description="Detect JSON in the input and format it or filter based on its presence. "
                                      "Optionally specify space-separated filters so that the program will only pay "
                                      "attention to JSON where the source contains all the filters as substrings.")

    parser.add_option("-i", "--infile", help="Read data from INFILE instead of stdin")

    parser.add_option("-o", "--outfile", help="Write output to OUTFILE instead of stdout")

    parser.add_option("-d", "--delete",
                      help="Delete the given sections in the output. The output is partitioned into three sections:\n"
                           "J/json: JSON that has been detected and selected by the given FILTERS values.\n"
                           "C/context: data/text not within the json section but in the same line(s).\n"
                           "L/other-lines: lines not containing any JSON.\n"
                           "The values can be specified using either the capital letters or long names separated by "
                           "commas. For example, if you want the output to contain json only, you can specify:\n"
                           "-dCL  or  --delete=context,other-lines.")

    delete_options_short_to_long = {
        "J": "json",
        "C": "context",
        "L": "other-lines"
    }

    parser.add_option("-f", "--format", type="choice", choices="on off mini tiny".split(), default="on",
                      help="Choose the output format of the JSON. The possible values are:\n"
                           "on (default): pretty-print values on separate lines with indentation (see -n/--indent).\n"
                           "off: output as in input.\n"
                           "mini: shrink JSON into a single line of output, while keeping spaces after the , and : "
                           "separators.\n"
                           "tiny: like mini, but without any extra spaces at all.\n"
                           "Unless FORMAT is off, the keys will be sorted lexicographically in the output.")

    parser.add_option("-n", "--indent", type="int", default=4,
                      help="Number of spaces in each level of indentation when FORMAT is on. Default is 4.")

    parser.add_option("-l", "--linewise", action="store_true",
                      help="By default the program reads in all input at once and parses the result in memory. If the "
                           "input is large and you need a live stream of results then set this flag. However JSON "
                           "that is split across multiple lines will not be detected, meaning that FORMAT=mini/tiny "
                           "will probably not do what you want.")

    parser.add_option("-m", "--min-size", type="int", default=2, metavar="MIN",
                      help="Only pay attention to (in a similar manner to the filters) objects/arrays with at least "
                           "MIN elements. This prevents things like [1] from being recognised, which you probably "
                           "don't want. Default is 2.")

    options, args = parser.parse_args(args)

    try:
        delete = options.delete
        if delete:
            assert isinstance(delete, str)
            if len(delete) <= 3:
                try:
                    delete = {delete_options_short_to_long[opt] for opt in delete}
                except KeyError:
                    raise OptionException("The only short options allowed for DELETE are J, C, and L.")
            else:
                delete = set(delete.split(","))
                if not delete.issubset(delete_options_short_to_long.values()):
                    raise OptionException("The only long options allowed for DELETE are json, context, "
                                          "and other-lines, and they must be separated by only a comma.")
        else:
            delete = ()
        options.delete = delete

    except OptionException as exc:
        if raise_option_exceptions:
            raise
        else:
            parser.error(exc.message)

    return options, args


class OptionException(Exception):
    pass


def process_files(infile, outfile, options, filters):
    incl_other = "other-lines" not in options.delete
    incl_context = "context" not in options.delete
    incl_json = "json" not in options.delete

    def filtered_jsonfinder(string):
        current_start = 0
        current_end = None
        for start, end, json in jsonfinder(string):
            if (json is not None and all(imap(string[start:end].__contains__, filters)) and
                    check_min_elements(json, options.min_size)):
                yield current_start, current_end, None
                yield start, end, json
                current_start = end
            else:
                current_end = end
        yield current_start, current_end, None

    def process_string(string):
        for start, end, json in filtered_jsonfinder(string):
            section = string[start:end]
            if json is None:
                if options.linewise:
                    section *= incl_other if len(section) == len(string) else incl_context
                else:
                    other_start = section.find("\n")
                    if other_start == -1:
                        section *= incl_context
                    else:
                        deleted_other = "\n"
                        if start == 0:
                            deleted_other = ""
                            other_start = 0
                        if end == len(string):
                            other_end = end
                            deleted_other = ""
                        else:
                            other_end = (section.rfind("\n") + 1)
                        section = (incl_context * section[:other_start] +
                                   (section[other_start:other_end] if incl_other else deleted_other) +
                                   incl_context * section[other_end:])
            else:
                if not incl_json:
                    section = ""
                elif options.format == "on":
                    section = dumps(json, sort_keys=True, separators=(",", ": "), indent=options.indent)
                elif options.format == "mini":
                    section = dumps(json, sort_keys=True)
                elif options.format == "tiny":
                    section = dumps(json, sort_keys=True, separators=(",", ":"))

            yield section

    if options.linewise:
        for line in infile:
            newline = line and line[-1] == "\n"
            if newline:
                line = line[:-1]
            result = "".join(process_string(line))
            outfile.write(result)
            if newline and result:
                outfile.write("\n")
    else:
        infile_contents = infile.read()
        part = None
        for part in process_string(infile_contents):
            outfile.write(part)
        if part and part[-1] != "\n" and infile_contents[-1] == "\n":
            outfile.write("\n")

    outfile.flush()


def process_args(options, filters):

    def get_file(opt, mode, default):
        if opt:
            try:
                return open(opt, mode)
            except IOError as err:
                print >> sys.stderr, "IOError:", err
                sys.exit(1)
        else:
            return default

    infile = get_file(options.infile, "r", sys.stdin)
    outfile = get_file(options.outfile, "w", sys.stdout)

    try:
        process_files(infile, outfile, options, filters)
    finally:
        if options.infile:
            infile.close()
        if options.outfile:
            outfile.close()


def main():
    # Ignore SIG_PIPE and don't throw exceptions on it...
    # (http://docs.python.org/library/signal.html)
    from signal import signal, SIGPIPE, SIG_DFL
    try:
        signal(SIGPIPE, SIG_DFL)
    except ValueError:
        pass

    process_args(*parse_args())


if __name__ == "__main__":
    main()