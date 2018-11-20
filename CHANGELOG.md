# ChangeLog

## 0.2.2 - 2018 Nov 20
* prepare_testbed_scheduler shouldbe OK, at least it runs inside the mosaic demo

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
