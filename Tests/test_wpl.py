#!/usr/bin/env python

import py.test
import datetime

import gael.testing
gael.testing.add_appsever_import_paths()

from BeautifulSoup import BeautifulSoup
import wpl
import kpl
from data import Hold
from data import LoginError

from fakes import MyCard
from fakes import MyLibrary
from fakes import MyOpener

def test__parse_holds__numeric_position__reads_position():
    response = BeautifulSoup(
        '''<table>
        <tr class="patFuncHeaders"><th>STATUS</th></tr>
        <tr><td> 9 of 83 holds </td></tr>
        </table>''')
    
    w = wpl.LibraryAccount(MyCard(), MyOpener())
    assert (9, 83) == w.parse_holds(response)[0].status

def test__parse_holds__title_with_slash__reads_title():
    response = BeautifulSoup(
        '''<table>
        <tr class="patFuncHeaders"><th> TITLE </th></tr>
        <tr><td align="left"><a href="/BLAH"> Either/Or / Boo! </a></td></tr>
        </table>''')
    w = wpl.LibraryAccount(MyCard(), MyOpener())
    hold = w.parse_holds(response)[0]
    assert ('Either/Or') == hold.title

def test__parse_holds__author_with_slash__reads_author():
    response = BeautifulSoup(
        '''<table>
        <tr class="patFuncHeaders"><th> TITLE </th></tr>
        <tr><td align="left"><a href="/BLAH"> JustOne / Bo/o! </a></td></tr>
        </table>''')
    w = wpl.LibraryAccount(MyCard(), MyOpener())
    hold = w.parse_holds(response)[0]
    assert ('Bo/o!') == hold.author

def test__parse_holds__named_position__parses_position():
    def check(expected, hold_text):
        print 'expected =', expected, 'hold_text =', hold_text
        response = BeautifulSoup(
            '''<table>
            <tr class="patFuncHeaders"><th>STATUS</th></tr>
            <tr><td> %s </td></tr>
            </table>''' % hold_text)
        w = wpl.LibraryAccount(MyCard(), MyOpener())
        assert  expected == w.parse_holds(response)[0].status

    for text, status in (
        ('Ready.', Hold.READY),
        ('IN TRANSIT', Hold.IN_TRANSIT),
        ('CHECK SHELVES', Hold.CHECK_SHELVES),
        ('TRACE', Hold.DELAYED),
        ):
        yield check, status, text
    
def test__parse_holds___location_dropdown__location_is_read():
    response = BeautifulSoup('''<table lang="en" class="patFunc"><tr class="patFuncTitle">
<th colspan="6" class="patFuncTitle">
6 HOLDS
</th>
</tr>

<tr class="patFuncHeaders">
<th class="patFuncHeaders"> CANCEL </th>
<th class="patFuncHeaders"> TITLE </th>
<th class="patFuncHeaders"> STATUS </th>
<th class="patFuncHeaders">PICKUP LOCATION</th>
<th class="patFuncHeaders"> CANCEL IF NOT FILLED BY </th>
<th class="patFuncHeaders"> FREEZE </th>
</tr>


<tr class="patFuncEntry">
<td  class="patFuncMark" align="center">
<input type="checkbox" name="cancelb2193902x00" /></td>
<td  class="patFuncTitle">
<a href="/patroninfo~S3/1307788/item&2193902"> Stories </a>
<br />
</td>
<td  class="patFuncStatus"> 1 of 1 holds </td>
<td class="patFuncPickup"><select name=locb2193902x00>
<option value="ch+++" >Country Hills Library-KPL</option>
<option value="fh+++" >Forest Heights Library-KPL</option>

<option value="g++++" >Grand River Stanley Pk Lib-KPL</option>
<option value="m++++" >Main Library-KPL</option>
<option value="pp+++" >Pioneer Park Library-KPL</option>
<option value="w++++" >WPL Main Library</option>
<option value="wm+++" selected="selected">WPL McCormick Branch</option>
</select>
</td>
<td class="patFuncCancel">04-03-11</td>
<td  class="patFuncFreeze" align="center"><input type="checkbox" name="freezeb2193902" /></td>
</tr>
</table>
''')
    w = wpl.LibraryAccount(MyCard(), MyOpener())
    assert 'WPL McCormick Branch' == w.parse_holds(response)[0].pickup

    
def test__parse_holds___with_expiration_date__reads_expiration():
    response = BeautifulSoup(
        '''<table>
        <tr class="patFuncHeaders"><th>CANCEL IF NOT FILLED BY</th></tr>
        <tr><td>04-03-11</td></tr>
        </table>''')
    
    w = wpl.LibraryAccount(MyCard(), MyOpener())
    hold = w.parse_holds(response)[0]
    assert datetime.date(2011,4,3) == hold.expires

def test__parse_holds___frozen__added_to_status_notes():
    response = BeautifulSoup(
        '''<table>
        <tr class="patFuncHeaders"><th> FREEZE </th></tr>
        <tr><td  class="patFuncFreeze" align="center"><input type="checkbox" name="freezeb2186875" checked /></td></tr>
        </table>''')
    
    w = wpl.LibraryAccount(MyCard(), MyOpener())
    assert ['frozen'] == w.parse_holds(response)[0].status_notes

    
def test__parse_holds___empty_freeze_field__is_not_frozen():
    response = BeautifulSoup(
        '''<table>
        <tr class="patFuncHeaders"><th> FREEZE </th></tr>
        <tr><td  class="patFuncFreeze" align="center">&nbsp;</td></tr>
        </table>''')
    
    w = wpl.LibraryAccount(MyCard(), MyOpener())
    assert 'frozen' not in w.parse_holds(response)[0].status_notes
    
def test__parse_holds___hold_for_waterloo__finds_correct_url():
    response = BeautifulSoup('''<table>
    <tr class="patFuncHeaders"><th> TITLE </th></tr>
    <tr class="patFuncEntry"> 
      <td  class="patFuncTitle"> 
        <label for="canceli3337880x00"><a href="/record=b2247789~S3"> The profession : a thriller / Steven Pressfield </a></label> 
        <br /> 
      </td> 
    </tr>
    </table>''')
    w = wpl.LibraryAccount(MyCard(), MyOpener())
    assert 'https://books.kpl.org/record=b2247789~S3' == w.parse_holds(response)[0].url

def test__parse_holds___hold_for_kitchener__finds_correct_url():
    response = BeautifulSoup('''<table>
      <tr class="patFuncHeaders"><th> TITLE </th></tr>
      <tr class="patFuncEntry"> 
        <td  class="patFuncTitle"> 
          <label for="cancelb2232976x09"><a href="/record=b2232976~S1"> Live wire / Harlan Coben. -- </a></label> 
          <br /> 
        </td> 
      </tr> 
      </table>''')
    k = kpl.LibraryAccount(MyCard(), MyOpener())
    assert 'https://books.kpl.org/record=b2232976~S1' == k.parse_holds(response)[0].url


def test__parse_items__title_has_slash__parses_title():
    response = BeautifulSoup(
        '''
        <table lang="en">
        <tr class="patFuncHeaders"><th> RENEW </th><th> TITLE </th><th > BARCODE </th><th> STATUS </th><th > CALL NUMBER </th></tr>
        <tr><td align="left"><input type="checkbox" name="renew0" value="i3103561" /></td><td align="left"><a href="/patroninfo~S3/1307788/item&2160792"> The city/the city / China Mi\u00E9ville </a></td>
        <td align="left"> 33420011304806 </td>
        <td align="left"> DUE 07-20-09  <span >Renewed 1 time</span>
        </td>
        <td align="left"> MIEVI  </td>
        </tr>
        </table>
        ''')
    
    w = wpl.LibraryAccount(MyCard(), MyOpener())
    item =  w.parse_items(response)[0]
    assert 'The city/the city' == item.title

def test__parse_items__author_has_accent__parses_author():
    response = BeautifulSoup(
        '''
        <table lang="en">
        <tr class="patFuncHeaders"><th> RENEW </th><th> TITLE </th><th > BARCODE </th><th> STATUS </th><th > CALL NUMBER </th></tr>
        <tr><td align="left"><input type="checkbox" name="renew0" value="i3103561" /></td><td align="left"><a href="/patroninfo~S3/1307788/item&2160792"> The city/the city / China Mi\u00E9ville </a></td>
        <td align="left"> 33420011304806 </td>
        <td align="left"> DUE 07-20-09  <span >Renewed 1 time</span>
        </td>
        <td align="left"> MIEVI  </td>
        </tr>
        </table>
        ''')
    
    w = wpl.LibraryAccount(MyCard(), MyOpener())
    item =  w.parse_items(response)[0]
    assert 'China Mi\u00E9ville' == item.author

def test__parse_items__with_status_notes__finds_status_notes():
    response = BeautifulSoup(
        '''
        <table lang="en">
        <tr class="patFuncHeaders"><th> RENEW </th><th> TITLE </th><th > BARCODE </th><th> STATUS </th><th > CALL NUMBER </th></tr>
        <tr><td align="left"><input type="checkbox" name="renew0" value="i3103561" /></td><td align="left"><a href="/patroninfo~S3/1307788/item&2160792"> The city/the city / China Mi\u00E9ville </a></td>
        <td align="left"> 33420011304806 </td>
        <td align="left"> DUE 07-20-09  <span >Renewed 1 time</span>
        </td>
        <td align="left"> MIEVI  </td>
        </tr>
        </table>
        ''')
    
    w = wpl.LibraryAccount(MyCard(), MyOpener())
    item =  w.parse_items(response)[0]
    assert ['Renewed 1 time'] == item.status_notes

def test__parse_items__span_in_title__all_text_in_title():
    response = BeautifulSoup(
        '''
        <table lang="en">
        <tr class="patFuncHeaders"><th> RENEW </th><th> TITLE </th><th > BARCODE </th><th> STATUS </th><th > CALL NUMBER </th></tr>
        <tr class="patFuncEntry"><td align="left" class="patFuncMark"><input type="checkbox" name="renew3" id="renew3" value="i2626300" /></td><td align="left" class="patFuncTitle"><label for="renew3"><a href="/record=b1945079~S3"> Hiking the redwood coast : best hikes along Northern and Central California's coastline. -- <span class="patFuncVol">2004</span></a></label>
        <br />
        
        </td>
        <td align="left" class="patFuncBarcode"> 33420007964514 </td>
        <td align="left" class="patFuncStatus"> DUE 05-29-10 
        </td>
        <td align="left" class="patFuncCallNo"> 917.9404 Hik  </td>
        </tr>
        </table>
        ''')
    w = wpl.LibraryAccount(MyCard(), MyOpener())
    item =  w.parse_items(response)[0]
    assert '''Hiking the redwood coast : best hikes along Northern and Central California's coastline. -- 2004''' == item.title

def test__parse_items__no_author__author_blank():
    response = BeautifulSoup(
        '''
        <table lang="en">
        <tr class="patFuncHeaders"><th> RENEW </th><th> TITLE </th><th > BARCODE </th><th> STATUS </th><th > CALL NUMBER </th></tr>
        <tr class="patFuncEntry"><td align="left" class="patFuncMark"><input type="checkbox" name="renew3" id="renew3" value="i2626300" /></td><td align="left" class="patFuncTitle"><label for="renew3"><a href="/record=b1945079~S3"> Hiking the redwood coast</a></label>
        <br />
        
        </td>
        <td align="left" class="patFuncBarcode"> 33420007964514 </td>
        <td align="left" class="patFuncStatus"> DUE 05-29-10 
        </td>
        <td align="left" class="patFuncCallNo"> 917.9404 Hik  </td>
        </tr>
        </table>
        ''')
    w = wpl.LibraryAccount(MyCard(), MyOpener())
    item =  w.parse_items(response)[0]
    assert '' == item.author

def test__parse_status__status_notes_jammed_up_against_date__date_parsed():
    response = BeautifulSoup(
        '''
        <table lang="en">
        <tr class="patFuncHeaders"><th> RENEW </th><th> TITLE </th><th > BARCODE </th><th> STATUS </th><th > CALL NUMBER </th></tr>
        <tr><td align="left"><input type="checkbox" name="renew0" value="i3103561" /></td><td align="left"><a href="/patroninfo~S3/1307788/item&2160792"> The city/the city / China Mi\u00E9ville </a></td>
        <td align="left"> 33420011304806 </td>
        <td align="left"> DUE 10-07-09IN LIBRARY USE </span>
        </td>
        <td align="left"> MIEVI  </td>
        </tr>
        </table>
        ''')
    
    w = wpl.LibraryAccount(MyCard(), MyOpener())
    item = w.parse_items(response)[0]
    assert 'The city/the city' == item.title
    assert 'China Mi\u00E9ville' == item.author

    assert datetime.date(2009,10,7) == item.status

def test__parse_status__status_notes_jammed_up_against_date__status_notes_found():
    response = BeautifulSoup(
        '''
        <table lang="en">
        <tr class="patFuncHeaders"><th> RENEW </th><th> TITLE </th><th > BARCODE </th><th> STATUS </th><th > CALL NUMBER </th></tr>
        <tr><td align="left"><input type="checkbox" name="renew0" value="i3103561" /></td><td align="left"><a href="/patroninfo~S3/1307788/item&2160792"> The city/the city / China Mi\u00E9ville </a></td>
        <td align="left"> 33420011304806 </td>
        <td align="left"> DUE 10-07-09IN LIBRARY USE </span>
        </td>
        <td align="left"> MIEVI  </td>
        </tr>
        </table>
        ''')
    
    w = wpl.LibraryAccount(MyCard(), MyOpener())
    item = w.parse_items(response)[0]

    assert ['IN LIBRARY USE'] == item.status_notes


failing_login_response =  '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"><html lang="en">
<head>
<title>Kitchener and Waterloo Public Libraries                                    /WPL</title>
<base target="_self"/>
<link rel="stylesheet" type="text/css" href="/scripts/ProStyles.css" />
<link rel="stylesheet" type="text/css" href="/screens/w-stylesheet-3a.css" />
<link rel="shortcut icon" type="ximage/icon" href="/screens/favicon.ico" />
<script language="JavaScript" type="text/javascript" src="/scripts/common.js"></script>

<link rel="icon" href="/screens/favicon.ico"><link rel="shortcut icon" href="/screens/favicon.ico"><meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
</head>
<body onLoad='if (document.forms.length > 0) { for (var i=0; i<document.forms[0].elements.length; i++) { if (document.forms[0].elements[i].type == "text") { document.forms[0].elements[i].focus(); document.forms[0].elements[i].select(); return; } } }'>
<h1>WPL Login</h1>

<div class="patform">
<form method="POST">

<div class="notice">

Sorry, the information you submitted was invalid. Please try again.</div>

<p>To login, please enter the following information and click "Login". Use Tab to move between fields.

<table>


<tr>
<th>First and Last Name</th>
<td><input name="name" size="40" maxlength="40"></td>
</tr>



<tr>
<th>Library card number (no spaces)</th>

<td><input name="code" size="40" maxlength="40"></td>
</tr>


<tr>
<th>Personal Identification Number</th>
<td><input name="pin" type="password" size="40" maxlength="40"></td>
</tr>


</table>

<div class="submit-button">
<input name="submit" type="submit" value="Login">
</div>

</form>
</div>
'''

def test__login__login_fails__throws():

    w = wpl.LibraryAccount(MyCard(),
                           MyOpener('',
                                    failing_login_response))
    py.test.raises(LoginError, w.login)


def test__login__new_kpl_format__passes():
    w = wpl.LibraryAccount(MyCard(), MyOpener('', '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"> 
<head> 
<title>Kitchener and Waterloo Public Libraries                                    /WPL</title> 
<base target="_self"/> 
<link rel="stylesheet" type="text/css" href="/scripts/ProStyles.css" /> 
<link rel="stylesheet" type="text/css" href="/screens/w-stylesheet.css" /> 
<link rel="shortcut icon" type="ximage/icon" href="/screens/favicon.ico" /> 
<script language="JavaScript" type="text/javascript" src="/scripts/common.js"></script> 
<script language="JavaScript" type="text/javascript" src="/scripts/elcontent.js"></script> 
 
<link rel="icon" href="/screens/favicon.ico"><link rel="shortcut icon" href="/screens/favicon.ico"><meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1"> 
</head> 
<body > 
<script language="JavaScript" type="text/javascript">
var min=8;
var max=22;
function increaseFontSize() {
   var p = document.getElementsByTagName('*')
   for(i=0;i<p.length;i++) {
      if(p[i].style.fontSize) {
         var s = parseInt(p[i].style.fontSize.replace("px",""));
      } else {
         var s = 14;
      }
      if(s!=max) {
         s += 2;
      }
      p[i].style.fontSize = s+"px"
   }
}
function decreaseFontSize() {
   var p = document.getElementsByTagName('*');
   for(i=0;i<p.length;i++) {  
      if(p[i].style.fontSize) {
         var s = parseInt(p[i].style.fontSize.replace("px",""));
      } else {
         var s = 14;
      }
      if(s!=min) {
         s -= 2;
      }
      p[i].style.fontSize = s+"px"
   }   
}
</script>
<script language="JavaScript" type="text/javascript">
<!-- Hide the JS
startTimeout(600000, "/search~S3/");
-->
</script>
<!-- begin toplogo.html file -->
<!-- HEADER -->
<a class="linkskip" href="#content">Skip over navigation</a>
<div id="container-header">
<div id="header-main1-background">
<div id="container-header-content">
<div id="header-logo"><a href="http://www.wpl.ca"><img src="/screens/wpl-logo-main1.jpg" alt="Waterloo Public Library"/></a></div>
<div id="header-sub"><img src="/screens/wpl-sub-main1.jpg" alt="Waterloo Public Library"/></div>
<div id="header-main1-utility">
<div id="header-title" class=title1><a href="/search~S3/">Catalogue</a></div>
<div id="font-size"><a href="javascript:decreaseFontSize();"><img src="/screens/wpl-font-smaller.gif" alt="Font Smaller" width="15" height="38"/></a><a href="javascript:increaseFontSize();" ><img src="/screens/wpl-font-larger.gif" alt="Font Larger" width="19" height="38"/></a></div>
</div>
</div>
</div>
</div>

<!-- NAV -->

<div id="container-nav" align=center>
<div id="nav">
<ul><li><a href="http://www.wpl.ca" class="navline">Home</a></li><li><a href="http://books.kpl.org/search~S3/">Catalogue</a></li><li><a href="http://www.wpl.ca/location">Locations & Hours</a></li><li><a href="http://books.kpl.org/patroninfo~S3/top">My Account</a></li><li><a href="http://www.wpl.ca/ebooks">eBooks</a></li><li><a href="http://www.wpl.ca/ebranch">eBranch</a></li><li><a href="http://www.wpl.ca/book-a-computer">Book a Computer</a></li><li><a href="http://www.wpl.ca/blogs-more">Blogs</a></li><li><a href="http://www.wpl.ca/contact">Contact Us</a></li></ul>
</div>
</div>
<div align=center>
<a href="http://wplreads.wordpress.com">WPL Reads</a> |
<a href="http://books.kpl.org/screens/newitems.html">New Items</a> | <a href="http://www.wpl.ca/about/borrowing/interlibrary-loan-form/">Interlibrary Loan</a>  | <a href="http://www.wpl.ca/ebranch/databases-and-weblinks">Databases and WebLinks</a> | <a href="http://www.wpl.ca/services/ask-us/">Ask Us</a> 
</div>
<!--end toplogo.html--> 
<br /><p align=center><font size=4 color=#0066cc>Kitchener and Waterloo Public Libraries                                    /WPL <br />You are logged in as Conrad, Blair E..</font><p><br /> 
<br /> 
<div class="srchhelpHeader" align="center"> 
<form name="searchtool" action="/search~S3/"> 
    <select tabindex="1" name="searchtype" id="searchtype" onChange="initSort()"> 
    <option value="X" selected>Keyword</option> 
    <option value="t">Title</option> 
    <option value="a">Author</option> 
    <option value="s">Series</option> 
    <option value="d">Subject</option> 
    <option value="c">Call Number</option> 
    <option value="i">ISBN/ISSN</option> 
  </select> 
  <input tabindex="2" type="text" name="searcharg" size="50"  maxlength="75"> 
  <input type="hidden" name="searchscope" value="3"> 
  <input tabindex="3" type="submit" value="Search"> 
</div> 
 
<div class="media"> 
  <div align="center">Media (book, DVD, etc.):
    <select tabindex="4" name="searchlimits"> 
      <option value="" selected>Any</option> 
      <option value="m=d">DVD</option> 
      <option value="m=j">CD Audio</option> 
      <option value="m=m">CD-ROM</option> 
      <option value="m=z">E-audio Book</option> 
      <option value="m=e">E-book</option> 
      <option value="m=a">Book</option> 
      <option value="m=l">Large Print Book</option> 
      <option value="m=v">Government Document</option> 
      <option value="m=c">Magazine/Newspaper</option> 
      <option value="m=o">Kit</option> 
    </select> 
  </div> 
</div> 
<label class="limit-to-available"> 
  <div align="center"> 
    <input tabindex="5" type="checkbox" name="availlim" value="1"> 
    Limit results to available items
	</div> 
</label> 
</form> 
<br /> 
<a name="content" id="content"></a> 
<!--{patron}--> 
 
 
 
<table> 
<tr> 
<td valign=top> 
<div class="patNameAddress"> 
<strong>Conrad, Blair E.</strong><br /> 
558 Rock Point Cres<br /> 
Waterloo ON  N2V 2K3<br /> 
519-725-0257 (E)<br /> 
EXP DATE:07-01-2012<br /> 
<br/> 
<div> 
</div> 
<div> 
<a href="/patroninfo~S3/1408880/holds" target="_self">9 requests (holds).</a> 
</div> 
<div> 
<a href="/patroninfo~S3/1408880/items" target="_self">3 Items currently checked out</a> 
</div> 
</div> 
 
 
</td> 
<td> 
 
<div class="patActionsLinks"> 
<div> 
<a href="#" onClick="return open_new_window( '/patroninfo~S3/1408880/newpin' )">Modify your PIN</a> 
</div> 
<div><p> 
<a href="/patroninfo~S3/1408880/readinghistory" target="_self">My Reading History</a> 
</p></div> 
<div><p> 
<a href="/patroninfo~S3/1408880/getpsearches" target="_self">Preferred Searches</a> 
</p></div> 
</div> 
</td> 
</tr> 
</table> 
<table> 
<tr> 
<td> 
<div class="patActionsLinks"> 
<p valign=top><a href="/logout?" target="_self"><img src="/screens/b-logout.gif" alt="Log Out" border="0" /></a></p> 
</div></td> 
</tr> 
</table> 
 
<br/><br/> 
 
<div class="patFuncArea" style="border:0px #555555;"> 
</div> 
<br /> 
</div>
<div class="botlogo">
WPL Catalogue and your library account may not be available
<br />
Mon-Thur 10:00-11:30PM and Fri-Sat 6:00-7:30PM for scheduled maintenance.
<br />
</div>

 
</body> 
</html> 
 
<!--this is customized <screens/patronview_web_s3.html>-->'''))
    w.login()


    
def test__get_status__with_card_expiry_date__reads_date():
    w = wpl.LibraryAccount(MyCard(), MyOpener('', '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"><html lang="en"> 
<head> 
<title>Kitchener and Waterloo Public Libraries                                    /WPL</title> 
<base target="_self"/> 
<link rel="stylesheet" type="text/css" href="/scripts/ProStyles.css" /> 
<link rel="stylesheet" type="text/css" href="/screens/w-stylesheet-3a.css" /> 
<link rel="shortcut icon" type="ximage/icon" href="/screens/favicon.ico" /> 
<script language="JavaScript" type="text/javascript" src="/scripts/common.js"></script> 
 
<link rel="icon" href="/screens/favicon.ico"><link rel="shortcut icon" href="/screens/favicon.ico"><meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1"> 
</head> 
<body > 
<div id="toplogo"> 
 
<div id="topbar"> 
 
<div class="wpl-logo"> 
<a href="http://www.wpl.ca/"><img src="/screens/w-banner.gif" alt="Waterloo Public Library" title="Waterloo Public Library"></a> 

</div> 
 
<div class="text-on-ca"> 
Ontario, Canada
 
<div class="flag-ca"> 
<img src="/screens/w-flag-ca.gif" alt="Canada Flag" title="Canada Flag"> 
</div> 
 
</div> 
 
<div class="text-place-to-grow">A <b>place</b> to <b>grow</b></div> 
 
<ul id="mainNav" title="Main Navigation"> 
<li><a href="http://www.wpl.ca/" title="WPL Home Page">Home</a></li> 
<li id="viewRecord"><a href="/patroninfo~S3/top">View Your Account</a></li><!-- /top means it bypasses login screen if already logged in --> 

<li><a href="http://www.wpl.ca/site/kidbits/kidbits.asp" title="This section is just for kids!">KidBits</a></li> 
<li><a href="http://www.wpl.ca/site/4Teens/4teens.asp" title="Homework, reading, fun, life, your turn!">/4teens</a></li> 
<li><a href="http://www.wpl.ca/site/goodreads/good_reads.asp" title="Looking for a good book? This is the place">Reader's Corner</a></li> 
<li><a href="http://www.wpl.ca/site/ebranch/ebranch.asp" title="A wide range of virtual collections and services, open 24 hours">e-Branch</a></li> 
</ul> 
 
</div> 
 
<div id="sidebar-show" onclick="document.getElementById('sidebar').style.display = 'block'; document.getElementById('sidebar-show').style.display = 'none';" title="Show sidebar">Show sidebar</div> 
 
<div id="sidebar" title="Search Help Navigation"> 
 
<img id="sidebar-closebox" title="Hide sidebar"
	onclick="document.getElementById('sidebar').style.display = 'none';
		document.getElementById('sidebar-show').style.display = 'block';"
	src="/screens/w-close.gif" width="14" height="13" alt="Hide sidebar"> 
 
<ul> 
<li id="small-print"><a href="/search~S3">Small Print</a> 

<li id="large-print"><a href="/search~S4">Large Print</a> 
<li id="sidebar-searchCatalogue"><a href="/search~S3">Search Catalogue</a> 
	<ul> 
	<li><a href="/search~S3/X">Keyword</a></li> 
	<li><a href="/search~S3/t">Title</a></li> 
	<li><a href="/search~S3/a">Author</a></li> 
	<li><a href="/search~S3/s">Series</a></li> 
	<li><a href="/search~S3/d">Subject</a></li> 
	<li><a href="/search~S3/c">Call Number</a></li> 
	<li><a href="/search~S3/i"><acronym title="International Standard Book Number">ISBN</acronym>/<acronym title="International Standard Serial Number">ISSN</acronym></a></li> 
	</ul> 
	</li> 

<li id="sidebar-articles"><a href="http://www.wpl.ca/site/ebranch/ebranch_databases_and_weblinks.asp">Databases &amp; WebLinks</a></li> 
<li id="sidebar-searchInternet"><a href="http://www.wpl.ca/site/ebranch/ebranch_internet_search_engines.asp">Search Internet</a></li> 
 
<li id="sidebar-renew"><a href="/patroninfo~S3/top">Renew Items</a></li><!-- /top means it bypasses login screen if already logged in --> 
 
</ul> 
 
</div> 
 
</div><!--toplogo--> 
<div id="main"> 
<font color="purple">You are logged in to Kitchener and Waterloo Public Libraries                                    /WPL as: </font><font color="purple" size="+2">MY NAME</font><BR> 
<br /> 
<!--this is default <patronview_web>--> 
 

<!-- default form outer table begin --> 
<table lang="en" class="patDisplay"> 
<tr class="patDisplay"> 
<td width="50%" class="patDisplay"> 
<table  class="patInfo"><tr class="patInfo"> 
<td valign="top" class="patInfo"> 
<strong>MY NAME</strong><br /> 
100 Regina Street S<br /> 
WATERLOO, ON.   N2J 4A8<br /> 
519-886-1550<br /> 
EXP DATE:12-04-2009<br /> 
</td> 

</tr><tr class="patInfo"><td class="patInfo"> 
<form> 
<a href="/logout~S3?" target="_self"><img src="/screens/b-logout.gif" alt="Log Out" border="0" /></a> 
<br /> 
</form> 
</td></tr> 
</table> 
</td><td width="50%" class="patDisplayFunc"> 
<table  class="patFuncBtns"> 
<form method="POST"> 
<tr class="patFuncBtns"><td class="patFuncBtns"> 
<a href="#" onClick="return open_new_window( '/patroninfo~S3/XXXXXXX/newpin' )">Modify your PIN</a> 
</td></tr> 
<tr class="patFuncBtns"><td class="patFuncBtns"> 
<a href="/patroninfo~S3/XXXXXXX/items" target="_self">957 Items currently checked out</a> 

</td></tr> 
<tr class="patFuncBtns"><td class="patFuncBtns"> 
<a href="/patroninfo~S3/XXXXXXX/holds" target="_self">1 request (hold).</a> 
</td></tr> 
<tr class="patFuncBtns"><td class="patFuncBtns"> 
<a href="/patroninfo~S3/XXXXXXX/msg" target="_self">IMPORTANT LIBRARY INFORMATION</a> 
</td></tr> 
<tr class="patFuncBtns"><td class="patFuncBtns"> 
<a href="/patroninfo~S3/XXXXXXX/searchcatalog" target="_self">Search the Catalog</a> 
</td></tr> 
<tr class="patFuncBtns"><td class="patFuncBtns"> 
<a href="/patroninfo~S3/XXXXXXX/getpsearches" target="_self">Preferred Searches</a> 
</td></tr> 

<tr class="patFuncBtns"><td class="patFuncBtns"> 
<a href="/patroninfo~S3/XXXXXXX/readinghistory" target="_self">My Reading History</a> 
</td></tr> 
</form> 
 
</table> 
</td></tr> 
</table> 
<!-- outer table end --> 
<br /> 
</div><!--main--> 
<div id="botlogo"><ul> WPL Catalogue may not be available on Mon 8-9 am for scheduled maintenance.<br> Your library account may not be available during scheduled system maintenance 11-11:30 pm Mon
 to Thurs, & 6-6:30 pm Fri-Sun.</div><!--botlogo--> 

<!--this is customized <screens/w-botlogo.html>--> 
 
</body> 
</html> ''', '', '', ''))
    card_info = w.get_status()
    assert datetime.date(2009,12,4) == card_info.expires

def test__get_status__wpl_login__finds_correct_holds_url():
    w = wpl.LibraryAccount(MyCard(), MyOpener('#login', '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"> 
<body > 
  <table> 
    <tr> 
      <td valign=top> 
	<div class="patNameAddress"> 
	  <div> 
	    <a href="/patroninfo~S3/4249154/holds" target="_self">4 requests (holds).</a> 
	  </div> 
	  <div> 
	    <a href="/patroninfo~S3/4249154/items" target="_self">5 Items currently checked out</a> 
	  </div> 
	</div> 
      </td> 
      <td> 
	<div class="patActionsLinks"> 
	  <div> 
	    <a href="#" onClick="return open_new_window( '/patroninfo~S3/4249154/newpin' )">Modify your PIN</a> 
	  </div> 
	  <div><p> 
	      <a href="/patroninfo~S3/4249154/readinghistory" target="_self">My Reading History</a> 
	  </p></div> 
	  <div><p> 
	      <a href="/patroninfo~S3/4249154/getpsearches" target="_self">Preferred Searches</a> 
	  </p></div> 
	</div> 
      </td> 
    </tr> 
  </table>
</body> 
</html>''', '''<table>
  <tr class="patFuncHeaders"><th> TITLE </th></tr>
  <tr><td align="left"><a href="/BLAH"> Either/Or / Bo/o! </a></td></tr>
  </table>''', '#items', '#logout'))
    status = w.get_status()
    assert 'https://books.kpl.org/patroninfo~S3/4249154/holds' == status.holds[0].holds_url


def test__get_status__wpl_login_no_holds__finds_no_holds():
    w = wpl.LibraryAccount(MyCard(), MyOpener('#login', '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"> 
<body > 
  <table> 
    <tr> 
      <td valign=top> 
	<div class="patNameAddress"> 
	  <div> 
	    <a href="/patroninfo~S3/4249154/items" target="_self">5 Items currently checked out</a> 
	  </div> 
	</div> 
      </td> 
      <td> 
	<div class="patActionsLinks"> 
	  <div> 
	    <a href="#" onClick="return open_new_window( '/patroninfo~S3/4249154/newpin' )">Modify your PIN</a> 
	  </div> 
	  <div><p> 
	      <a href="/patroninfo~S3/4249154/readinghistory" target="_self">My Reading History</a> 
	  </p></div> 
	  <div><p> 
	      <a href="/patroninfo~S3/4249154/getpsearches" target="_self">Preferred Searches</a> 
	  </p></div> 
	</div> 
      </td> 
    </tr> 
  </table>
</body> 
</html>''', '#holds', '#items', '#logout'))
    status = w.get_status()
    assert status.holds == []

def test__get_status__wpl_login_no_items__finds_no_items():
    w = wpl.LibraryAccount(MyCard(), MyOpener('#login', '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"> 
<body > 
  <table> 
    <tr> 
      <td valign=top> 
	<div class="patNameAddress"> 
	  <div> 
	    <a href="/patroninfo~S3/4249154/holds" target="_self">4 requests (holds).</a> 
	  </div> 
	</div> 
      </td> 
      <td> 
	<div class="patActionsLinks"> 
	  <div> 
	    <a href="#" onClick="return open_new_window( '/patroninfo~S3/4249154/newpin' )">Modify your PIN</a> 
	  </div> 
	  <div><p> 
	      <a href="/patroninfo~S3/4249154/readinghistory" target="_self">My Reading History</a> 
	  </p></div> 
	  <div><p> 
	      <a href="/patroninfo~S3/4249154/getpsearches" target="_self">Preferred Searches</a> 
	  </p></div> 
	</div> 
      </td> 
    </tr> 
  </table>
</body> 
</html>''', '#holds', '#items', '#logout'))
    status = w.get_status()
    assert status.items == []
