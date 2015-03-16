#!/usr/bin/env python

import datetime

import gael.testing
gael.testing.add_appsever_import_paths()

from BeautifulSoup import BeautifulSoup
import rwl
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
    <td colspan="1" rowspan="1" class="holdsStatus">Pending</td>
    <td colspan="1" rowspan="1" class="holdsPickup">Baden Branch Library</td>
    <td colspan="1" rowspan="1" class="holdsDate">
    </td>
    <td colspan="1" rowspan="1" class="holdsRank">1</td>
  </tr>
</table>''')

    lib = rwl.LibraryAccount(MyCard(), MyOpener())
    hold = lib.parse_holds(response)[0]
    assert 'It\'s a wiggly world collection/3 compact discs, box set' == hold.title
    assert 1 == hold.status
    assert datetime.date.max == hold.expires
    assert 'Baden Branch Library' == hold.pickup
