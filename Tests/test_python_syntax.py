import sys
import flake8.main


def test_syntax():
    sys.argv = ['check', '--max-line-length=120', '--exclude=BeautifulSoup.py', '.']
    try:
        flake8.main.main()
    except SystemExit, e:
        assert e.code is False
