#!./bin/linux-x86_64/logtest

dbLoadDatabase("dbd/logtest.dbd")
logtest_registerRecordDeviceDriver(pdbbase)

dbLoadRecords("test.db","")
asSetFilename("test.acf")
iocInit()

caPutLogInit("127.0.0.1:7004")
