#!/usr/bin/env python

import datetime

import gael.testing
gael.testing.add_appsever_import_paths()

from BeautifulSoup import BeautifulSoup
import rwl
from data import Hold
from fakes import MyCard
from fakes import MyOpener


def test__parse_holds():
    response = BeautifulSoup('''<table id="myHolds_holdslist_table" class="holdsList sortable">
  <thead>
    <tr class="holdsHeader">
      <td colspan="1" rowspan="1" class="holdsAlert">
      </td>
      <td colspan="1" rowspan="1" class="sorttable_nosort">
      </td>
      <td colspan="1" rowspan="1" class="holdsID sorttable_alpha">
        <div class="myAccountHeader_div">Title/Author</div>
      </td>
      <td colspan="1" rowspan="1" class="holdsStatus sorttable_alpha">
        <div class="myAccountHeader_div">Status</div>
      </td>
      <td colspan="1" rowspan="1" class="holdsPickup sorttable_alpha">
        <div class="myAccountHeader_div">Pickup at:</div>
      </td>
      <td colspan="1" rowspan="1" class="holdsDate">
        <div class="myAccountHeader_div">Expires</div>
      </td>
      <td colspan="1" rowspan="1" class="holdsRank sorttable_numeric">
        <div class="myAccountHeader_div">Place in queue</div>
      </td>
    </tr>
  </thead>
  <tr class="pickupHoldsLine">
    <td colspan="1" rowspan="1" sorttable_customkey="2" class="holdsAlert">
    </td>
    <td colspan="1" rowspan="1" class="holdsCoverArt">
      <input title="Select It's a wiggly world collection/3 compact discs, box set" tabindex="41"
             class="holdsCheckbox" id="checkbox_14c1f3406f2" name="checkbox" type="checkbox" />
      <img id="checkbox_14c1f3406f2_icon" class="t-error-icon t-invisible" alt=""
           src="/client/assets/ea21eb42ef509455/core/spacer.gif" />
      <div id="docId_0" class="hidden">ent://SD_ILS/0/SD_ILS:1235577|115675</div>
      <div id="holdInitialCover_115675" class="myAccountCoverArt">
        <img id="holdsImage_1" title="Cover image for It's a wiggly world collection/3 compact discs, box set"
             alt="Cover image for It's a wiggly world collection/3 compact discs, box set"
             class="accountCoverImage" src="/client/assets/ea21eb42ef509455/ctx/images/no_image.png" />
        <div title="Cover image for It's a wiggly world collection/3 compact discs, box set"
             class="no_image_text"
             id="holdsImage_1Title">It's a wiggly world collection/3 compact discs, box set</div>
      </div>
    </td>
    <td colspan="1" rowspan="1" class="holdsID">
      <div id="holdTitleLinkDiv_115675">
        <div>
          <div class="detailPanel" id="detailPanel0">
            <div class="t-zone" id="detailZone0">
            </div>
          </div>
          <a shape="rect" tabindex="42"
             title="It's a wiggly world collection/3compact discs, box set"
             href="#" zoneid="detailZone0" class="hideIE"
             id="detailClick">It's a wiggly world collection/3 compact discs, box set</a>
        </div>
      </div>
      <p class="authBreak">The Wiggles,<br />
        <span id="holdItemIdSpan_115675">WR130026-1001</span>
      </p>
    </td>
    <td colspan="1" rowspan="1" class="holdsStatus">Suspended</td>
    <td colspan="1" rowspan="1" class="holdsPickup">Baden Branch Library</td>
    <td colspan="1" rowspan="1" class="holdsDate">
    </td>
    <td colspan="1" rowspan="1" class="holdsRank">1</td>
  </tr>
  <tr class='pickupHoldsLine'>
    <td colspan='1' rowspan='1' sorttable_customkey='2' class='holdsAlert'>
    </td>
    <td colspan='1' rowspan='1' class='holdsCoverArt'>
      <input title='Select Big Hero 6 [DVD]' tabIndex='45' class='holdsCheckbox' id='checkbox_14c25a8c22e_1'
             name='checkbox_1' type='checkbox'>
  </input>
  <img id='checkbox_14c25a8c22e_1_icon' class='t-error-icon t-invisible' alt=''
       src='/client/assets/ea21eb42ef509455/core/spacer.gif'/>
  <div id='docId_2' class='hidden'>ent://SD_ILS/0/SD_ILS:2540577|1669272</div>
  <div id='holdInitialCover_1669272' class='myAccountCoverArt'>
    <img id='holdsImage_3' title='Cover image for Big Hero 6 [DVD]' alt='Cover image for Big Hero 6 [DVD]'
         class='accountCoverImage' src='/client/assets/ea21eb42ef509455/ctx/images/no_image.png'/>
    <div title='Cover image for Big Hero 6 [DVD]' class='no_image_text' id='holdsImage_3Title'>Big Hero 6 [DVD]</div>
  </div>
    </td>
    <td colspan='1' rowspan='1' class='holdsID'>
      <div id='holdTitleLinkDiv_1669272'>
        <div>
          <div class='detailPanel' id='detailPanel2'>
            <div class='t-zone' id='detailZone2'>
            </div>
          </div>
          <a shape='rect' TABINDEX='46' title='Big Hero 6 [DVD]' href='#' zoneId='detailZone2' class='hideIE'
             id='detailClick_1'>Big Hero 6 [DVD]</a>
        </div>
      </div>
      <p class='authBreak'>
        Hall, Don.
        <br/>
        <span id='holdItemIdSpan_1669272'>2540577-1002</span>
      </p>
    </td>
    <td colspan='1' rowspan='1' class='holdsStatus'>Pending</td>
    <td colspan='1' rowspan='1' class='holdsPickup'>Baden Branch Library</td>
    <td colspan='1' rowspan='1' class='holdsDate'>
    </td>
    <td colspan='1' rowspan='1' class='holdsRank'>15</td>
  </tr>
  <tr class='pickupHoldsLine'>
    <td colspan='1' rowspan='1' sorttable_customkey='0' class='holdsAlert'>
      <img alt='' src='/client/images/account-icons/green!.png' title='Ready since 3/27/15'/>
    </td>
    <td colspan='1' rowspan='1' class='holdsCoverArt'>
      <input title='Select Preschool songs [DVD]' tabIndex='41' class='readyHoldsCheckbox' id='checkbox_14c749e37d4'
             name='checkbox' type='checkbox'>
</input>
<img id='checkbox_14c749e37d4_icon' class='t-error-icon t-invisible' alt=''
     src='/client/assets/ea21eb42ef509455/core/spacer.gif'/>
<div id='docId_0' class='hidden'>ent://SD_ILS/0/SD_ILS:1194280|1748738</div>
<div id='holdInitialCover_1748738' class='myAccountCoverArt'>
  <img id='holdsImage_1' title='Cover image for Preschool songs [DVD]' alt='Cover image for Preschool songs [DVD]'
       class='accountCoverImage' src='/client/assets/ea21eb42ef509455/ctx/images/no_image.png'/>
  <div title='Cover image for Preschool songs [DVD]' class='no_image_text'
       id='holdsImage_1Title'>Preschool songs [DVD]</div>
</div>
    </td>
    <td colspan='1' rowspan='1' class='holdsID'>
      <div id='holdTitleLinkDiv_1748738'>
        <div>
          <div class='detailPanel' id='detailPanel0'>
            <div class='t-zone' id='detailZone0'>
            </div>
          </div>
          <a shape='rect' TABINDEX='42' title='Preschool songs [DVD]' href='#' zoneId='detailZone0' class='hideIE'
             id='detailClick'>Preschool songs [DVD]</a>
        </div>
      </div>
      <p class='authBreak'>\nMusick, Gary.\n<br/>
        <span id='holdItemIdSpan_1748738'>36501003331993</span>
      </p>
    </td>
    <td colspan='1' rowspan='1' class='holdsStatus'>Pickup by: 4/4/15</td>
    <td colspan='1' rowspan='1' class='holdsPickup'>New Hamburg Branch Library</td>
    <td colspan='1' rowspan='1' class='holdsDate'></td>
    <td colspan='1' rowspan='1' class='holdsRank'>1</td>
  </tr>
</table>''')

    lib = rwl.LibraryAccount(MyCard(), MyOpener())
    holds = lib.parse_holds(response)

    wiggly_world_hold = holds[0]
    assert 'It\'s a wiggly world collection/3 compact discs, box set' == wiggly_world_hold.title
    assert 'The Wiggles,' == wiggly_world_hold.author
    assert 1 == wiggly_world_hold.status
    assert datetime.date.max == wiggly_world_hold.expires
    assert 'Baden Branch Library' == wiggly_world_hold.pickup
    assert ['frozen'] == wiggly_world_hold.status_notes

    big_hero_hold = holds[1]
    assert [] == big_hero_hold.status_notes

    preschool_songs_hold = holds[2]
    assert 'Preschool songs [DVD]' == preschool_songs_hold.title
    assert Hold.READY == preschool_songs_hold.status
