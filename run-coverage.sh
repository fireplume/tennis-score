#!/usr/bin/env bash

\rm -fr .coverage htmlcov

coverage run -a score.py -h
if (($? != 0)); then
   echo last test failed
fi

coverage run -a score.py results.csv
if (($? != 0)); then
   echo last test failed
fi

coverage run -a score.py -m -3 -v results.csv
if (($? == 0)); then
   echo last test should have failed
fi

coverage run -a score.py -v -m 2000 results.csv
if (($? != 0)); then
   echo last test failed
fi

coverage run -a score.py -v -m 7 results.csv
if (($? != 0)); then
   echo last test failed
fi

coverage run -a score.py -v -p math results.csv
if (($? != 0)); then
   echo last test failed
fi

coverage run -a score.py results.csv
if (($? != 0)); then
   echo last test failed
fi

coverage run -a score.py -i results.csv
if (($? != 0)); then
   echo last test failed
fi

coverage run -a score.py --ppp=100 --rfc=1 --rdfc=1 --rfbp=3 --lbsf=0.01 results.csv
if (($? != 0)); then
   echo last test failed
fi

coverage run -a score.py --doubles results.csv
if (($? != 0)); then
   echo last test failed
fi

coverage html
firefox htmlcov/index.html
