#!/usr/bin/env python

import datetime

import gael.testing
gael.testing.add_appsever_import_paths()

from BeautifulSoup import BeautifulSoup
import rwl
from data import Hold
#from data import LoginError

from fakes import MyCard
from fakes import MyLibrary
from fakes import MyOpener

def test__parse_hold__vanilla_hold__understands_hold():
    response = BeautifulSoup('''<tr>
       <td class="accountstyle select">
          <input type="checkbox" name="HLD^TITLE^36501004469008^FIC Niffe^^287460" id="HLD^TITLE^36501004469008^FIC Niffe^^287460"> 
	   </td>
       <td class="accountstyle title">
      <!-- Title -->
        <label style="font-weight: normal" for="HLD^TITLE^36501004469008^FIC Niffe^^287460">Her fearful symmetry : a novel</label>
      </td>

       <td class="accountstyle availability">
         <!--not_available-->
                <em>Your position in the holds queue</em>:
                12
      </td>
       <td class="accountstyle pickup">St. Jacobs Branch Library</td>

      <td class="accountstyle expiration_date">
         30/11/2009
      </td>

      <td class="accountstyle status">
         Active
      </td>
     </tr>''')
    lib = rwl.LibraryAccount(MyCard(), MyOpener())
    hold = lib.parse_hold(response)
    assert 'Her fearful symmetry : a novel' == hold.title
    assert '' == hold.author
    assert 12 == hold.status
    assert datetime.date(2009, 11, 30) == hold.expires
    assert 'St. Jacobs Branch Library' == hold.pickup
    


def test__parse_hold__expires_does_not_have_leading_zeros__date_parsed():
    response = BeautifulSoup('''<tr>
       <td class="accountstyle select">
          <input type="checkbox" name="HLD^TITLE^36501004469008^FIC Niffe^^287460" id="HLD^TITLE^36501004469008^FIC Niffe^^287460"> 
	   </td>
       <td class="accountstyle title">
      <!-- Title -->
        <label style="font-weight: normal" for="HLD^TITLE^36501004469008^FIC Niffe^^287460">Her fearful symmetry : a novel</label>
      </td>

       <td class="accountstyle availability">
         <!--not_available-->
                <em>Your position in the holds queue</em>:
                12
      </td>
       <td class="accountstyle pickup">St. Jacobs Branch Library</td>

      <td class="accountstyle expiration_date">
         8/9/2010
      </td>

      <td class="accountstyle status">
         Active
      </td>
     </tr>
''')
    lib = rwl.LibraryAccount(MyCard(), MyOpener())
    hold = lib.parse_hold(response)
    assert 'Her fearful symmetry : a novel' == hold.title
    assert '' == hold.author
    assert 12 == hold.status
    assert datetime.date(2010, 9, 8) == hold.expires
    assert 'St. Jacobs Branch Library' == hold.pickup


def test__parse_hold__does_not_expire__expires_at_date_max():
    response = BeautifulSoup('''<tr>
       <td class="accountstyle select">
          <input type="checkbox" name="HLD^TITLE^36501004469008^FIC Niffe^^287460" id="HLD^TITLE^36501004469008^FIC Niffe^^287460"> 
	   </td>
       <td class="accountstyle title">
      <!-- Title -->
        <label style="font-weight: normal" for="HLD^TITLE^36501004469008^FIC Niffe^^287460">Her fearful symmetry : a novel</label>
      </td>

       <td class="accountstyle availability">
         <!--not_available-->
                <em>Your position in the holds queue</em>:
                12
      </td>
       <td class="accountstyle pickup">St. Jacobs Branch Library</td>

      <td class="accountstyle expiration_date">
         Never expires
      </td>

      <td class="accountstyle status">
         Active
      </td>
     </tr>
''')
    lib = rwl.LibraryAccount(MyCard(), MyOpener())
    hold = lib.parse_hold(response)
    assert 'Her fearful symmetry : a novel' == hold.title
    assert '' == hold.author
    assert 12 == hold.status
    assert datetime.date.max == hold.expires
    assert 'St. Jacobs Branch Library' == hold.pickup


def test__parse_item__vanilla_item__understands_item():
    row = BeautifulSoup('''<tr>
<td class="defaultstyle" align="left">
<!-- Title -->
            National geographic kids [2009]
        </td>
<td class="defaultstyle" align="left">
<!-- Author -->
            National Geographic Society (U.S.)
        </td>
<td class="defaultstyle" align="left">
<!-- Due Date -->
<strong>17/12/2009,23:59</strong>
</td>
<td class="defaultstyle" align="left">
<!-- Est Fines -->
            &nbsp;
        </td>
</tr>''')
    lib = rwl.LibraryAccount(MyCard(), MyOpener())
    item = lib.parse_item(row)
    assert 'National geographic kids [2009]' == item.title
    assert 'National Geographic Society (U.S.)' == item.author
    assert datetime.date(2009,12,17) == item.status
    
def test__parse_item__date_does_not_have_leading_zeros__date_parsed():
    row = BeautifulSoup('''<tr>
<td class="defaultstyle" align="left">
<!-- Title -->
            National geographic kids [2009]
        </td>
<td class="defaultstyle" align="left">
<!-- Author -->
            National Geographic Society (U.S.)
        </td>
<td class="defaultstyle" align="left">
<!-- Due Date -->
<strong>6/1/2010,23:59</strong>
</td>
<td class="defaultstyle" align="left">
<!-- Est Fines -->
            &nbsp;
        </td>
</tr>''')
    lib = rwl.LibraryAccount(MyCard(), MyOpener())
    item = lib.parse_item(row)
    assert 'National geographic kids [2009]' == item.title
    assert 'National Geographic Society (U.S.)' == item.author
    assert datetime.date(2010,1,6) == item.status
    
def test__parse_hold__ready__statis_is_ready():
    response = BeautifulSoup('''<tr>
          <td class="accountstyle">
            <input type="checkbox" name="HLD^TITLE^36501002723455^DAF FIC Magnu^^300734" id="HLD^TITLE^36501002723455^DAF FIC Magnu^^300734"> 
	  </td>
	
       <td class="accountstyle">

      <!-- Title -->
        <label style="font-weight: normal" for="HLD^TITLE^36501002723455^DAF FIC Magnu^^300734">Magnum P.I. The complete second season [DVD]</label>
      </td>
       <td class="accountstyle">
          <strong> Available</strong>
            <strong> Pickup at:</strong>

             STJACOBS
      </td>
       <td class="accountstyle">St. Jacobs Branch Library</td>

      <td class="accountstyle">
         Never expires
      </td>
     </tr>''')
    lib = rwl.LibraryAccount(MyCard(), MyOpener())
    hold = lib.parse_hold(response)
    assert 'Magnum P.I. The complete second season [DVD]' == hold.title
    assert Hold.READY == hold.status
    assert datetime.date.max == hold.expires
    assert 'St. Jacobs Branch Library' == hold.pickup
