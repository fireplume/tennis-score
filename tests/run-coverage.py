#!/usr/bin/env python3

import os
import sys
import subprocess
import shutil
import webbrowser
import glob

test_path = os.path.abspath(os.path.dirname(__file__))
root_path = os.path.abspath(os.path.join(test_path, ".."))
score_file_path = os.path.join(root_path, 'score.py')

failure_messages = []


def run_command(cmd, expected_success=True, exit_on_fail=True):
    try:
        success = subprocess.call(cmd, shell=True) == 0
    except:
        success = False

    if success != expected_success:
        failure_messages.append("%s failed" % cmd)
        if exit_on_fail:
            print("%s failed" % cmd)
            sys.exit(1)


if __name__ == "__main__":
    import pathlib

    if len(sys.argv) != 1:
        print("Usage: 'run-coverage.py' without arguments")
        print("Run 'score.py demo_csv --seed 0' for a sample player data csv file.")
        sys.exit(0)

    os.chdir(root_path)

    try:
        shutil.rmtree("htmlcov")
    except:
        pass

    try:
        os.remove(".coverage")
    except:
        pass

    # Run tests
    for test in glob.glob(os.path.join(test_path, "test*.py")):
        run_command("coverage run -a %s" % test, exit_on_fail=False)

    # No point in running the regression if unit tests failed
    if not failure_messages:
        csv_file = "score.test.csv"
        for i in range(0, 3):
            # Generate random csv
            run_command("coverage run -a %s demo_csv --seed %d > %s " % (score_file_path, i, csv_file))
            run_command("coverage run -a %s -h" % score_file_path)
            run_command("coverage run -a %s demo_csv -h" % score_file_path)
            run_command("coverage run -a %s input_csv -h" % score_file_path)
            run_command("coverage run -a %s input_csv %s" % (score_file_path, csv_file))
            run_command("coverage run -a %s input_csv --list-players %s" % (score_file_path, csv_file))
            run_command("coverage run -a %s -v input_csv -m -3 %s" % (score_file_path, csv_file), expected_success=False)
            run_command("coverage run -a %s input_csv -m 2000 %s" % (score_file_path, csv_file))
            run_command("coverage run -a %s input_csv -m 1 --pms %s" % (score_file_path, csv_file))
            run_command("coverage run -a %s -v input_csv -p math %s" % (score_file_path, csv_file))
            run_command("coverage run -a %s input_csv %s" % (score_file_path, csv_file))
            run_command("coverage run -a %s input_csv -i %s" % (score_file_path, csv_file))
            run_command("coverage run -a %s input_csv --ppm=100 --rfc=1 --rdfc=1 --rfbp=3 --lbsf=0.01 %s" % (score_file_path, csv_file))
            run_command("coverage run -a %s -v input_csv --doubles %s" % (score_file_path, csv_file))
            run_command("coverage run -a %s input_csv --doubles %s" % (score_file_path, csv_file))

    run_command("coverage html")
    path = os.path.join(root_path, "htmlcov/index.html")
    p = pathlib.PurePath(path)
    w = webbrowser.get()
    w.open_new_tab(p.as_uri())

    try:
        os.remove(csv_file)
    except:
        pass

    print()
    print("###########################################################")
    print("STATUS")
    print("###########################################################")

    if failure_messages:
        for m in failure_messages:
            print(m)
        sys.exit(1)
    else:
        print("ALL GOOD!")

