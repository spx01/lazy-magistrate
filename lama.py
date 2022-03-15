#!/bin/env python3

import argparse
import subprocess
import os
import glob
import shutil
import re
from colorama import Fore
from parse import parse

compiler_flags = [
    "g++",
    "-O2",
    "-pipe",
    "-w",
    "-fsanitize=address,signed-integer-overflow,undefined",
    "-DLAMA_JUDGE",
]

target_in_file = "{}.in"
target_out_file = "{}.out"
test_in_glob = "input.*"
test_in = "input.{}"
test_ok = "output.{}"
failed_prefix = Fore.RED + "\tFAILED" + Fore.RESET
passed_prefix = Fore.GREEN + "\tPASSED" + Fore.RESET


def compile(source):
    ret = subprocess.run(compiler_flags + [source])
    return ret.returncode == 0


def get_name(source):
    return os.path.basename(os.path.dirname(os.path.abspath(source)))


def get_tests(path):
    tests = []
    in_files = glob.glob(os.path.join(path, test_in_glob))
    for in_file in in_files:
        test_no = parse(test_in, os.path.basename(in_file))
        if not test_no:
            continue
        ok_file = os.path.join(path, test_ok.format(test_no[0]))
        if not os.path.exists(ok_file):
            continue
        try:
            test_no = int(test_no[0])
        except:
            continue
        tests.append((test_no, in_file, ok_file))
    tests.sort()
    return tests


def get_comparable_content(file):
    f = open(file)
    content = f.read()
    f.close()
    return re.sub("( )+", " ", content).strip()


def compare(output_file, ok_file):
    return get_comparable_content(output_file) == get_comparable_content(ok_file)


def backup(file):
    if os.path.exists(file):
        shutil.copy(file, file + ".old")


def restore(file):
    if os.path.exists(file + ".old"):
        shutil.move(file + ".old", file)


parser = argparse.ArgumentParser()
parser.add_argument("source", type=str, help="source file to compile and evaluate")
parser.add_argument("testdir", type=str, help="directory containing the test files")
parser.add_argument(
    "--quiet",
    "-q",
    action="count",
    default=0,
    help="disable stderr for program, -qq also makes the result display concise",
)

args = parser.parse_args()

if not os.path.isfile(args.source) or not os.path.isdir(args.testdir):
    print(Fore.RED + "ERROR: invalid source file or test directory" + Fore.RESET)
    exit(1)

name = get_name(args.source)
target_in_file = target_in_file.format(name)
target_out_file = target_out_file.format(name)
tests = get_tests(args.testdir)
max_test_no_len = len(str(max(tests)[0]))

if not compile(args.source):
    print(Fore.RED + "compilation error" + Fore.RESET)
    exit(1)
exe = os.path.join(os.path.dirname(args.source), "a.out")
backup(target_in_file)
backup(target_out_file)
run_args = {
    "stdout": subprocess.DEVNULL,
    "stderr": subprocess.DEVNULL if args.quiet > 0 else None,
}

passed = 0
for test in tests:
    (no, in_file, ok_file) = test
    shutil.copy(in_file, target_in_file)
    rc = subprocess.run(os.path.abspath(exe), timeout=5, **run_args).returncode
    message = ""
    if rc != 0:
        message = failed_prefix + f": program exited with return code {rc}"
        continue
    if not os.path.exists(target_out_file):
        message = failed_prefix + ": no output file generated"
        continue
    if compare(target_out_file, ok_file):
        message = passed_prefix
        passed += 1
    else:
        message = failed_prefix
    if args.quiet < 2:
        print(
            f"Evaluating test {(max_test_no_len - len(str(no))) * ' '}#{no}: {message}"
        )
    os.remove(target_in_file)
    os.remove(target_out_file)

print(
    f"TOTAL: {Fore.GREEN}{int(passed / len(tests) * 100):3d}%{Fore.RESET} ({Fore.GREEN}{passed} tests passed{Fore.RESET}, {Fore.RED}{len(tests) - passed} tests failed{Fore.RESET})"
)
restore(target_in_file)
restore(target_out_file)
os.remove("a.out")
