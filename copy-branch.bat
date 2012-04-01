@echo off
svn copy https://libraryhippo.googlecode.com/svn/trunk https://libraryhippo.googlecode.com/svn/branches/%1 -m "branching for %1"
svn switch https://libraryhippo.googlecode.com/svn/branches/%1
