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

hold_with_pickup_dropdown = '''<table lang="en" class="patFunc"><tr class="patFuncTitle">
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
'''
    
def test__parse_holds___pickup_dropdown__pickup_is_read():
    response = BeautifulSoup(hold_with_pickup_dropdown)
    w = wpl.LibraryAccount(MyCard(), MyOpener())
    assert 'WPL McCormick Branch' == w.parse_holds(response)[0].pickup

def test__parse_holds___pickup_dropdown__pickup_is_string():
    '''makes for better pickling'''
    response = BeautifulSoup(hold_with_pickup_dropdown)
    w = wpl.LibraryAccount(MyCard(), MyOpener())
    assert str == type(w.parse_holds(response)[0].pickup)
    
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


failing_login_response =  '''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
<link rel="stylesheet" type="text/css" href="/scripts/ProStyles.css" />
<link rel="stylesheet" type="text/css" href="/screens/w-stylesheet3.css" />
    <title>Library Log in</title>
    <meta http-equiv="X-UA-Compatible" content="IE=8;FF=3;OtherUA=4" />
	<meta http-equiv="Content-type" content="text/html;charset=UTF-8" />
    <meta name="viewport" content="width=device-width,user-scalable=no" />
    <script type="text/javascript" src="/scripts/common.js"></script>
    <!--<link rel="stylesheet" type="text/css" href="/apps/CAS/resources/login_mobile.css">
    <link rel="stylesheet" type="text/css" href="/apps/CAS/resources/login_s3_html.css" media="screen and (min-device-width: 481px)"> -->
    
    <link rel="stylesheet" type="text/css" href="/apps/CAS/resources/login_mobile_s3.css"  />
	<style type="text/css" media="screen and (min-width: 481px)">
    <!--
    @import url("/apps/CAS/resources/login_s3_html.css");
    -->
    </style>
    <!--[if IE]><link rel="stylesheet" type="text/css" href="/apps/CAS/resources/login_s3_html.css"  media="screen" /><![endif]-->
    <!--<link href="/apps/CAS/resources/login_mobile.css" rel="stylesheet" type="text/css" media="handheld, only screen and (max-device-width: 480px)" />-->
    
</head>

<body id="cas">
<!--[if IE]>
<div id="ie">
<![endif]-->
<div class="loginPage">

<div class="loginTop">
&nbsp;<!-- Prevent div collapse -->
<div class="loginTopLogo">
	<a href="http://www.wpl.ca" tabindex="0">
		<img src="/screens/w-logo-137x60.gif" alt="">
	</a>
</div>
</div>

<!-- Use for library-only authentication: -->
<div class="loginArea loginArea1Col"> 
<!--<div style="text-align:center; background:#FF0077; color:black;" > 
	<strong>Please Note:</strong> Holds placed online are currently not working. Please call us at 519-886-1310 to have staff help you place holds.
	</div>-->
<div class="clearfloats"></div>

 	<!--end theForm1-->
 	<form id="fm1" class="fm-v clearfix" method="post" action="/iii/cas/login?service=https%3A%2F%2Fencore.kpl.org%3A443%2Fiii%2Fencore_wpl%2Fmyaccount?lang=eng&amp;suite=wpl&amp;scope=3">
    <!--display any errors-->
	<div id="status" class="errors">Sorry, the information you submitted was invalid. Please try again.</div>
	<!-- Message from client webapp to be displayed on the CAS login screen -->
  	<div id="clientmessage">
	<!--display any errors-->
	
  	</div> <!-- end clientmessage -->
  	<!--start theForm2-->
	
									
	<!-- Message from client webapp to be displayed on the CAS login screen -->
  	<div id="clientmessage">
	<!--display any errors-->
  	</div> <!-- end clientmessage -->
	   
	<!--display login form-->
	<span style="padding-left:1.8em;"><h3>Library Account Login</h3></span>
	<div id="login">
	   <fieldset>
	        <label for="name">First and Last Name:</label>
            <div class="loginField">
              <input id="name" name="name" class="required" tabindex="3" accesskey="n" type="text" value="" size="20" maxlength="40"/>
	        </div>
	      
            <fieldset class="barcodeAltChoice">
            <!--<legend>Enter your barcode or login name</legend>-->
                    
              <label for="code">Library card number<br />(no spaces):</label>
              <div class="loginField">
        	    <input id="code" name="code" class="required" tabindex="4" accesskey="b" type="text" size="20" maxlength="40" />
		      </div>
                  
            </fieldset>
            
			<!--<div id="ipssopinentry">
            <label for="pin">Personal Identification Number (PIN):</label>
            <div class="loginFieldBg">
              <input id="pin" name="pin" class="required" tabindex="6" accesskey="p" type="password" value="" size="20" maxlength="40" />
	        </div>
			</div>-->


	<!--end theForm2-->
  	
  		
		
		
    
	<!--start theForm3-->
  	

        <!-- This button is hidden unless using mobile devices. Even if hidden it enables Enter key to submit. -->
        <input type="submit" name="Log In" class="loginSubmit" tabindex="35" />
	  </fieldset>
	</div>  <!-- end login -->
    <div class="clearfloats"></div>
    <div class="formButtons">
    	<a href="#" onclick="document.forms['fm1'].submit();" tabindex="40"><div onmousedown="this.className='pressedState';" onmouseout="this.className='';" onmouseup="this.className='';"><div class="buttonSpriteDiv"><span class="buttonSpriteSpan1">
<span class="buttonSpriteSpan2">Submit</span></span></div></div></a>
  	</div>
<br />

<div style="display:none;">

<!--Enable form focus-->
<script type="text/javascript"><!--//--><![CDATA[//><!--
//Hide the main PIN entry if the new pin section is active.
//try { if ( document.getElementById("ipssonewpin") ) {
//	document.getElementById("ipssopinentry").style.display="none"; } }
//catch(err) {}

//Look for the first field in the external patron part of the form. This field will get cursor focus.
var ipssoFirstField;
try { ipssoFirstField = document.forms[0].extpatid; }
catch(err) {
}
//If we still don't have a field, look for the name field in the library account part.
if ( ipssoFirstField==undefined ) { ipssoFirstField = document.forms[0].name; }
//Set focus. Ignore errors.
try { ipssoFirstField.focus(); }
catch(err) {}

document.onkeydown = enterSubmit

function enterSubmit(e) {
var keycode;
if (window.event) keycode = window.event.keyCode;
else if (e) keycode = e.which;
if (keycode==13)
 document.forms[0].submit();
}

//--><!]]>
</script>

  	<!--end theForm3-->
	<!-- Spring Web Flow requirements must be in a certain place -->
	<input type="hidden" name="lt" value="_c761F6248-082B-2453-47FE-DEBB4500C8AD_kF7718391-1925-2239-9B69-01CE8B941744" />
	<input type="hidden" name="_eventId" value="submit" />
	</form>
	<!--start theForm4-->
	

</div>

</div> <!-- end loginArea -->

<div class="loginActions">
<!--
<span class="loginActionText">New to the library?</span>
<span class="loginActionScreenOnly"><a href="/selfreg">Create an account</a></span>
<span class="loginActionSeparator"></span>
-->
</div>
</div> <!-- loginPage -->

<!--[if IE]>
</div>
<![endif]-->
<!-- IPSSO html form updated 2010 June 29 -->
</body>
</html>

<!--this is customized </iiidb/http/apps//CAS/resources/ipsso_s3.html>-->

	<!--end theForm4-->
'''

def test__login__login_fails__throws():

    w = wpl.LibraryAccount(MyCard(),
                           MyOpener('',
                                    failing_login_response))
    py.test.raises(LoginError, w.login)


def test__login__new_kpl_format__passes():
    w = wpl.LibraryAccount(MyCard(), MyOpener('', '''
<!-- Rel 2007 "Skyline" Example Set -->
<!-- This File Last Changed: 02 September 2008 -->
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"> <html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>Kitchener and Waterloo Public Libraries                                    /KPL</title>
<base target="_self"/>
<link rel="stylesheet" type="text/css" href="/scripts/ProStyles.css" />
<link rel="stylesheet" type="text/css" href="/screens/k-stylesheet1.css" />
<link rel="shortcut icon" type="ximage/icon" href="/screens/favicon.ico" />
<script type="text/javascript" src="/scripts/common.js"></script>
<script type="text/javascript" src="/scripts/features.js"></script>
<script type="text/javascript" src="/scripts/elcontent.js"></script>

<link rel="icon" href="/screens/favicon.ico"><meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
</head>
<body >
<body>

<div id="wrapper">

<div id="header">
<a href="http://www.kpl.org/"><img src="/screens/kpl_logo.png" alt="Kitchener Public Library logo" width="250" height="95" border="0" /></a>

<div id="nav">
<ul id="navmenu">
<li><a href="http://books.kpl.org/search~S1/" title="Library Catalogue" class="selected">Catalogue</a></li>
</ul>
</div>

<div id="nav2">&nbsp;</div>

</div>

<font color="purple">You are logged in to Kitchener and Waterloo Public Libraries                                    /KPL as: </font><font color="purple" size="+2">Hippo, Librarian</font><br />
<br />


<script type="text/javascript">
	function SetHTML1(type) {
		document.getElementById("a1").style.display = "none"
		document.getElementById("b1").style.display = "none"
		// Using style.display="block" instead of style.display="" leaves a carriage return
		document.getElementById(type).style.display = ""
	}
</script>

<div align="center">

<span id="a1" style="">
<form method="get" action="http://encore.kpl.org/iii/encore_kpl/Home,$Search.form.sdirect" name="form" id="form">	
<input name="formids" value="target" type="hidden">
<input name="lang" value="eng" type="hidden">
<input name="suite" value="def" type="hidden">
<input name="reservedids" value="lang,suite" type="hidden">
<input name="submitmode" value="" type="hidden">
<input name="submitname" value="" type="hidden">
<table>
<tr>
<td style="padding-right:10px;"><span style="font-family:'Times New Roman', Times, serif; font-size:1.4em;">Search:</span></td>
<td><input name="target" value="" id="target" type="text" style="border:1px solid #555; width:410px; height:30px; font-size:100%;"></td>
<td style="padding-left:10px;"><input type="image" src="http://www.kpl.org/_images/catalogue/go_button.png" value="submit"/></td>
</tr>
<tr><td colspan="3" style="font-size:12px;">&nbsp;</td></tr>
</table>
</form>
</span>

<span id="b1" style="display:none;">
<div  class="bibSearchtool" style="margin-top:5px;"><form target="_self" action="/search~S2/">
      <label for="searchtype" style="display:none;">Search Type1</label><select name="searchtype" id="searchtype">
        <option value="t"> TITLE</option>
        <option value="a"> AUTHOR</option>
        <option value="s"> SERIES</option>
        <option value="d"> SUBJECT</option>
        <option value="c"> CALL NO</option>
        <option value="i"> ISBN/ISSN</option>
        <option value="Y" selected="selected"> KEYWORD</option>
      </select>
      &nbsp;
      <label for="searcharg" style="display:none;">Search</label><input type="text" name="searcharg" id="searcharg" size="30" maxlength="75" value="" />
      &nbsp;
      <label for="searchscope" style="display:none;">Search Scope</label><select name="searchscope" id="searchscope">
        <option value="2" selected>Kitchener Public Library</option>
        <option value="3">Waterloo Public Library</option>
        <option value="5">King Digital Collection</option>
      </select>
      &nbsp;
      <input type="hidden" name="SORT" value="D" /><input type="hidden" name="extended" value="0" /><input type="submit" name="SUBMIT" value="Search" />
<div style="margin-top:6px;">
      <input type="checkbox" name="availlim" value="1"  /> <span class="limit-to-available">Limit results to available items<br/><br/></span>
</div>
</form></div>
</span>

<div align="center" style=" font-family: Arial, Helvetica, sans-serif; font-size:14px;">
<input style="margin-top:5px;" id="multisearch" name="br" type="radio" onClick="SetHTML1('a1')" checked>Search New KPL Catalogue
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
<input style="margin-top:5px;" id="multisearch" name="br" type="radio" onClick="SetHTML1('b1')">Search Classic Catalogue
</div>


<br /><br />
<p style="font-size:0.85em;"><span style="color:#990000; font-weight:bold;">Note:</span> Please remember to <strong>LOG OUT</strong> of your library account when you are finished using the catalogue.<br />The logout option can be found at the bottom of this page, or in the top right corner of the catalogue.</p>

<br />
</div>

<!--{patron}-->

<br/><br/>

<div align="center">
<table>
<tr>
<td>
<div class="patNameAddress">
<strong>Hippo, Librarian</strong><br />
100 Regina Street S<br />
Waterloo ON  N2V 4A8<br />
519-885-1550 (E)<br />
EXP DATE:08-01-2013<br />
<br/>
<div>
</div>
<div>
<a href="/patroninfo~S1/XXXXXXXX/holds" target="_self">4 requests (holds).</a>
</div>
<br><br>
</div>

</td>
<td>

<div class="patActionsLinks">
<div>
<a href="#" onClick="return open_new_window( '/patroninfo~S1/XXXXXXXX/modpinfo' )">Modify Personal Information</a>
</div>
<div><p>
<a href="/patroninfo~S1/XXXXXXXX/readinghistory" target="_self">My Reading History</a>
</p></div>
<br>
Classic catalogue only:
<div><p>
<a href="/patroninfo~S1/XXXXXXXX/getpsearches" target="_self">Preferred Searches</a>
</p></div>
<div>
<a href="/patroninfo~S1/XXXXXXXX/mylists" target="_self">My Lists</a>
</div>
<br>

<p><a href="http://encore.kpl.org/iii/encore_kpl/home?component=pageWrapperComponent.patronToolsComponent.patronAccountLoginComponent.patronLogoutLinkComponent&lang=eng&page=HomePage&service=direct&session=T&suite=kpl"><img src="/screens/b-logout.gif" alt="Log Out" border="0" /></a></p>

<!--
<p valign=top><a href="/logout?" target="_self"><img src="/screens/b-logout.gif" alt="Log Out" border="0" /></a></p>
-->

</div></td>
</tr>
</table>
</div>

<br/><br/>

<div class="patFuncArea" style="border:1px solid #555555;">
</div>

<br />
<div class="footer"></div>
</div>

</body>
</html>
<!--this is customized <screens/patronview_web_s1.html>-->
'''))
    w.login()


    
def test__get_status__with_card_expiry_date__reads_date():
    w = wpl.LibraryAccount(MyCard(), MyOpener('', '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"> <html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>Kitchener and Waterloo Public Libraries                                    /WPL</title>
<base target="_self"/>
<link rel="stylesheet" type="text/css" href="/scripts/ProStyles.css" />
<link rel="stylesheet" type="text/css" href="/screens/w-stylesheet3.css" />
<link rel="shortcut icon" type="ximage/icon" href="/screens/favicon.ico" />
<script type="text/javascript" src="/scripts/common.js"></script>
<script type="text/javascript" src="/scripts/features.js"></script>
<script type="text/javascript" src="/scripts/elcontent.js"></script>

<link rel="icon" href="/screens/favicon.ico"><meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
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
<div id="header-nav" align=center><ul><li><a href="http://books.kpl.org/selfreg~S3/">Get a Card</a></li><li><a href="https://books.kpl.org/iii/cas/login?service=http://books.kpl.org/patroninfo~S3/j_acegi_cas_security_check&lang=eng&scope=3" class="navline">My Account</a></li><li><a href="http://www.wpl.ca/location">Hours & Locations</a></li><li><a href="http://www.wpl.ca/contact">Contact Us</a></li></ul></div>
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
<ul><li><a href="http://www.wpl.ca" class="navline">Home</a></li><li><a href="http://books.kpl.org/search~S3">Catalogue</a></li><li><a href="http://www.wpl.ca/ebooks">eBooks</a></li><li><a href="http://www.wpl.ca/ebranch">eBranch</a></li><li><a href="http://www.wpl.ca/book-a-computer">Book a Computer</a></li><li><a href="http://www.wpl.ca/blogs-more">Blogs</a></li><li><a href="http://www.wpl.ca/ebranch/diy/">DIY</a></li></ul>
</div>
</div>
<div align=center>
<a href="http://wplreads.wpl.ca">WPL Reads</a> |
<a href="http://books.kpl.org/screens/newitems.html">New Items</a> | <a href="http://www.wpl.ca/about/borrowing/interlibrary-loan-form/">Interlibrary Loan</a>  | <a href="http://www.wpl.ca/ebranch/databases-and-weblinks">Databases and WebLinks</a> | <a href="http://www.wpl.ca/services/ask-us/">Ask Us</a> 
</div>
<!--end toplogo.html-->
<br /><p align=center><font size=4 color=#0066cc>Kitchener and Waterloo Public Libraries                                    /WPL <br />You are logged in as HIPPO, LIBRARIAN.</font><p><br />
<br />
<div class="srchhelpHeader" align="center">
<form method="get" action="http://encore.kpl.org/iii/encore_wpl/Home,$Search.form.sdirect" name="form" id="form">	
<input name="formids" value="target" type="hidden">
<input name="lang" value="eng" type="hidden">
<input name="suite" value="def" type="hidden">
<input name="reservedids" value="lang,suite" type="hidden">
<input name="submitmode" value="" type="hidden">
<input name="submitname" value="" type="hidden">
<table>
<tr>
<td style="padding-right:10px;"><span style="font-family:'Times New Roman', Times, serif; font-size:1.7em;">Search:</span></td>
<td><input name="target" value="" id="target" type="text" style="border:1px solid #555; width:410px; height:30px; font-size:1.4em;"></td>
<td style="padding-left:10px;"><input type="image" src="/screens/go_button.png" value="submit"/></td>
</tr>
<tr>
<td></td>
<td align="right">
  <p><a href="http://encore.kpl.org/iii/encore_wpl/home?lang=eng&suite=kpl&advancedSearch=true&searchString=">Advanced Search</a></p></td>
<td></td></tr>
</table>
</form>	
<br />
<a name="content" id="content"></a>
<!--<form name="searchtool" action="/search~S3/">
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
<br />-->
<!--{patron}-->
<table>
<tr>
<td valign=top>
<div class="patNameAddress">
<strong>HIPPO, LIBRARIAN.</strong><br />
100 Regina Steet S<br />
WATERLOO, ON N2V 4A8<br />
519-885-1550<br />
EXP DATE:12-04-2009<br />
<br/>
<div>
</div>
<div>
<a href="/patroninfo~S3/1307788/holds" target="_self">14 requests (holds).</a>
</div>
<div>
<a href="/patroninfo~S3/1307788/items" target="_self">8 Items currently checked out</a>
</div>
</div>


</td>
<td>
<div style="text-align:left;">
<div>
<a href="#" onClick="return open_new_window( '/patroninfo~S3/1307788/modpinfo' )">Modify Personal Information</a>
</div>
<div><p>
<a href="/patroninfo~S3/1307788/readinghistory" target="_self">My Reading History</a>
</p></div>
<div><p>
<p>&nbsp;</p>
Classic Catalogue Features:
</p></div>
<div><p>
<a href="/patroninfo~S3/1307788/getpsearches" target="_self">Preferred Searches</a>
</p></div>
<div style="display:none;">
<a href="/patroninfo~S3/1307788/patreview" target="_self">My Reviews</a>
</div>
<div>
<a href="/patroninfo~S3/1307788/mylists" target="_self">My Lists</a>
</div>
</div>
</td>
</tr>
</table>
<table>
<tr>
<td>
<div class="patActionsLinks">
<!--
<p valign=top><a href="http://encore.kpl.org/iii/encore_wpl/home?component=pageWrapperComponent.patronToolsComponent.patronAccountLoginComponent.patronLogoutLinkComponent&lang=eng&page=HomePage&service=direct&session=T&suite=wpl" target="_self"><img src="/screens/b-logout.gif" alt="Log Out" border="0" /></a></p>-->
<p valign=top><a href="http://encore.kpl.org/iii/encore_wpl/home?component=pageWrapperComponent.patronToolsComponent.patronAccountLoginComponent.patronLogoutLinkComponent&lang=eng&page=HomePage&service=direct&session=T&suite=wpl" target="_self"><img src="/screens/b-logout.gif" alt="Log Out" border="0" /></a></p>
</div></td>
</tr>
</table>

<br/><br/>

<div class="patFuncArea" style="border:0px #555555;">
</div>

<br />
</div>
<div class="botlogo">
<br />
Your library account may not be available during scheduled system maintenance 10:00pm - 12:00am Mon to Thu, & 6pm - 8pm Fri to Sun.
<br />
</div>
</body>
</html>

<!--this is customized <screens/patronview_web_s3.html>-->
''', '', '', ''))
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
	    <a href="/patroninfo~S3/XXXXXXX/holds" target="_self">4 requests (holds).</a> 
	  </div> 
	  <div> 
	    <a href="/patroninfo~S3/XXXXXXX/items" target="_self">5 Items currently checked out</a> 
	  </div> 
	</div> 
      </td> 
      <td> 
	<div class="patActionsLinks"> 
	  <div> 
	    <a href="#" onClick="return open_new_window( '/patroninfo~S3/XXXXXXX/newpin' )">Modify your PIN</a> 
	  </div> 
	  <div><p> 
	      <a href="/patroninfo~S3/XXXXXXX/readinghistory" target="_self">My Reading History</a> 
	  </p></div> 
	  <div><p> 
	      <a href="/patroninfo~S3/XXXXXXX/getpsearches" target="_self">Preferred Searches</a> 
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
    assert 'https://books.kpl.org/patroninfo~S3/XXXXXXX/holds' == status.holds[0].holds_url


def test__get_status__wpl_login_no_holds__finds_no_holds():
    w = wpl.LibraryAccount(MyCard(), MyOpener('#login', '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"> 
<body > 
  <table> 
    <tr> 
      <td valign=top> 
	<div class="patNameAddress"> 
	  <div> 
	    <a href="/patroninfo~S3/XXXXXXX/items" target="_self">5 Items currently checked out</a> 
	  </div> 
	</div> 
      </td> 
      <td> 
	<div class="patActionsLinks"> 
	  <div> 
	    <a href="#" onClick="return open_new_window( '/patroninfo~S3/XXXXXXX/newpin' )">Modify your PIN</a> 
	  </div> 
	  <div><p> 
	      <a href="/patroninfo~S3/XXXXXXX/readinghistory" target="_self">My Reading History</a> 
	  </p></div> 
	  <div><p> 
	      <a href="/patroninfo~S3/XXXXXXX/getpsearches" target="_self">Preferred Searches</a> 
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
	    <a href="/patroninfo~S3/XXXXXXX/holds" target="_self">4 requests (holds).</a> 
	  </div> 
	</div> 
      </td> 
      <td> 
	<div class="patActionsLinks"> 
	  <div> 
	    <a href="#" onClick="return open_new_window( '/patroninfo~S3/XXXXXXX/newpin' )">Modify your PIN</a> 
	  </div> 
	  <div><p> 
	      <a href="/patroninfo~S3/XXXXXXX/readinghistory" target="_self">My Reading History</a> 
	  </p></div> 
	  <div><p> 
	      <a href="/patroninfo~S3/XXXXXXX/getpsearches" target="_self">Preferred Searches</a> 
	  </p></div> 
	</div> 
      </td> 
    </tr> 
  </table>
</body> 
</html>''', '#holds', '#items', '#logout'))
    status = w.get_status()
    assert status.items == []

def test__login_wpl_format_2013_06_07__can_parse_the_login_screen():
    w = wpl.LibraryAccount(MyCard(), MyOpener('''
 	<form id="fm1" class="fm-v clearfix" method="post" action="/iii/cas/login?service=https://books.kpl.org/patroninfo~S3/j_acegi_cas_security_check&amp;lang=eng&amp;scope=3">
	<!--display any errors-->
	
	<!-- Message from client webapp to be displayed on the CAS login screen -->
  	<div id="clientmessage">
	<!--display any errors-->
	
  	</div> <!-- end clientmessage -->
  	<!--start theForm2-->
	
									
	<!-- Message from client webapp to be displayed on the CAS login screen -->
  	<div id="clientmessage">
	<!--display any errors-->
  	</div> <!-- end clientmessage -->
	   
	<!--display login form-->
	<span style="padding-left:1.8em;"><h3>Library Account Login</h3></span>
	<div id="login">
	   <fieldset>
	        <label for="name">First and Last Name:</label>
            <div class="loginField">
              <input id="name" name="name" class="required" tabindex="3" accesskey="n" type="text" value="" size="20" maxlength="40"/>
	        </div>
	      
            <fieldset class="barcodeAltChoice">
            <!--<legend>Enter your barcode or login name</legend>-->
                    
              <label for="code">Library card number<br />(no spaces):</label>
              <div class="loginField">
        	    <input id="code" name="code" class="required" tabindex="4" accesskey="b" type="text" size="20" maxlength="40" />
		      </div>
                  
            </fieldset>
            
			<!--<div id="ipssopinentry">
            <label for="pin">Personal Identification Number (PIN):</label>
            <div class="loginFieldBg">
              <input id="pin" name="pin" class="required" tabindex="6" accesskey="p" type="password" value="" size="20" maxlength="40" />
	        </div>
			</div>-->
	<!--end theForm2-->
	<!--start theForm3-->

        <!-- This button is hidden unless using mobile devices. Even if hidden it enables Enter key to submit. -->
        <input type="submit" name="Log In" class="loginSubmit" tabindex="35" />
	  </fieldset>
	</div>  <!-- end login -->
    <div class="clearfloats"></div>
    <div class="formButtons">
    	<a href="#" onclick="document.forms['fm1'].submit();" tabindex="40"><div onmousedown="this.className='pressedState';" onmouseout="this.className='';" onmouseup="this.className='';"><div class="buttonSpriteDiv"><span class="buttonSpriteSpan1">
<span class="buttonSpriteSpan2">Submit</span></span></div></div></a>
  	</div>

  	<!--end theForm3-->
	<!-- Spring Web Flow requirements must be in a certain place -->
	<input type="hidden" name="lt" value="_cF3646058-103E-2F3B-C9DB-0C9931EDB267_k24CDA5F8-E174-085D-7570-0D56ADBFE0E7" />
	<input type="hidden" name="_eventId" value="submit" />
	</form>''',
                                              '''"patNameAddress"''')) # "patNameAddress" is enough to make the login think it worked
    w.login()

