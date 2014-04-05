TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

#=============================
# Build the IOC application

PROD_IOC = logtest
# logtest.dbd will be created and installed
DBD += logtest.dbd

# logtest.dbd will be made up from these files:
logtest_DBD += base.dbd
logtest_DBD += caPutLog.dbd

# Include dbd files from all support applications:
#logtest_DBD += xxx.dbd

# Add all the support libraries needed by this IOC
logtest_LIBS += caPutLog

# logtest_registerRecordDeviceDriver.cpp derives from logtest.dbd
logtest_SRCS += logtest_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
logtest_SRCS_DEFAULT += logtestMain.cpp
logtest_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#logtest_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Finally link to the EPICS Base libraries
logtest_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE

