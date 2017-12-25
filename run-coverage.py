#!/usr/bin/env python3

import os
import sys
import subprocess
import shutil
import webbrowser
import glob

def run_command(cmd, expected_success=True):
    success = subprocess.call(cmd, shell=True) == 0
    if success != expected_success:
        print("%s failed" % cmd)
        sys.exit(1)


if __name__ == "__main__":
    import pathlib

    if len(sys.argv) != 1:
        print("Usage: 'run-coverage.py' without arguments")
        print("Run 'score.py demo_csv --seed 0' for a sample player data csv file.")
        sys.exit(0)

    try:
        shutil.rmtree("htmlcov")
    except:
        pass

    try:
        os.remove(".coverage")
    except:
        pass

    csv_file = "score.test.csv"
    for i in range(0, 6):
        # Generate random csv
        run_command("coverage run -a score.py demo_csv --seed %d > %s " % (i, csv_file))
        run_command("coverage run -a score.py -h")
        run_command("coverage run -a score.py demo_csv -h")
        run_command("coverage run -a score.py input_csv -h")
        run_command("coverage run -a score.py input_csv %s" % csv_file)
        run_command("coverage run -a score.py input_csv --list-players %s" % csv_file)
        run_command("coverage run -a score.py -v input_csv -m -3 %s" % csv_file)
        run_command("coverage run -a score.py -v input_csv -m 2000 %s" % csv_file)
        run_command("coverage run -a score.py -v input_csv -m 7 %s" % csv_file)
        run_command("coverage run -a score.py -v input_csv -p math %s" % csv_file)
        run_command("coverage run -a score.py input_csv %s" % csv_file)
        run_command("coverage run -a score.py input_csv -i %s" % csv_file)
        run_command("coverage run -a score.py -v input_csv --ppp=100 --rfc=1 --rdfc=1 --rfbp=3 --lbsf=0.01 %s" % csv_file)
        run_command("coverage run -a score.py -v input_csv --doubles %s" % csv_file)
        run_command("coverage run -a score.py -v input_csv --doubles %s" % csv_file)

    # Run tests too
    for test in glob.glob(os.path.join(".", "tests", "test*.py")):
        run_command("coverage run -a %s" % test)

    run_command("coverage html")
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "htmlcov/index.html"))
    p = pathlib.PurePath(path)
    w = webbrowser.get()
    w.open_new_tab(p.as_uri())

    try:
        os.remove(csv_file)
    except:
        pass


