# ChangeLog

## 0.6.2 - 2023 Nov 15

* no change in the library
* update readthedocs config so the doc builds fine again

## 0.6.1 - 2021 Jun 03

* attempt to fix pypi publishing code

## 0.6.0 - 2021 Jun 03

* patch to cope with a change in websockets-9.x

## 0.5.7 - 2019 Nov 06

* add newly supported b205 usrp type

## 0.5.6 - 2019 Jul 10

* fix packaging; install_requires could not be honored

## 0.5.3 - 2019 Feb 20

* Sidecar classes: url now optional; plus, doc on how to turn off SSL certificate verification
* fixed compliance with readthedocs, to use 3.6 so that f-strings don't break that build

## 0.5.2 - 2019 Feb 1

* fix import prepare that unintentionnally was calling trying to locate faraday.sh and r2labutils.sh
* available.py knows how to use default loose SSL policy when connecting to a wss://
* 0.5.1 had bugs wrt incremental broadcasts, and about using 'nodes' even with phones

## 0.5.0 - 2019 Jan 25

* first implementation of SidecarAsyncClient based on websockets
* examples/ now use this new model, and
* incorporate animate.py, a sidecar client formerly in the sidecar repo

## 0.2.4 - 2018 Dec 17
* find_local_embedded_script has more heuristics
* find_local_embedded_script raises FileNotFoundError in case of failure

## 0.2.3 - 2018 Nov 20
* prepare_testbed_scheduler should be OK, at least it runs inside the mosaic demo
* 0.2.2 and 0.2.1 were **broken**

## 0.2.1 - 2018 Nov 14
* new function prepare_testbed_scheduler

## 0.2.0 - 2018 Nov 13

* new class R2labMap for dealing with node 2D coordinates
* new class MapDataFrame
* these 2 being adequate for heatmap-oriented experiments
  like radiomap and batman-vs-olsr

## 0.1.1 - 2018 Mar 26

* r2lab_hostname now comes in 2 new variants r2lab_data and r2lab_reboot

## 0.1.0 - 2018 Mar 14

* sidecar has a debug mode

## 0.0.5 - 2018 Mar 13

* sidecar knows how to write stuff about nodes and phones too

## 0.0.4 - 2018 Mar 13

* hopefully `pip3 install r2lab` will now properly install
  the socketIO_client dependency
* adopting for sphinx same layout as asynciojobs/apssh
  with no source/ subdir

## 0.0.3 - 2018 Mar 12

* let's avoid f-strings for now, if only for `readthedocs`,
  plus not everyone can be assumed to have 3.6 yet

## 0.0.2 - 2018 Mar 12

* this release has the embryo of the R2labSidecar class
  for pulling node data from the testbed

## 0.0.1 - 2018 Mar 7

* mostly an empty shell for publishing / versioning
* just comes with listofchoices for now
