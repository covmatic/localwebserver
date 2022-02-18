### COVMATIC LocalWebServer changelog

## v2.9.0
### Note
- Needs **stations >= v2.15.0**
- Needs **dashboard >= v0.10.0**
- Needs **webserver >= v0.9.0**

### Added
- *dashboard_input* parameter retrieved from station is passed through to *dashboard*.

## v2.8.0
### Notes
- Needs **Dashboard >= v0.9.1**

### Added
- More run fields passed to Dashboard;
- Deleted barcode server now managed by Dashboard;

## v2.7.1
- Added Bioer preparation to PCR with Technogenetics mastermix.

## v2.7.0
### Added
- Station A: Added bioer preparation protocol with P1000 and station A.
- Watchdog enable parameter is now appended to uploaded protocol. Needs *covmatic_stations* >= v2.12.0

## v2.6.3
### Fixed
- BioerPrep protocol updated to be used with *covmatic-stations* v2.10.0
- Fixed workflow for *libsystemd-dev* package

## v2.6.1
### Fixed
- Error from protocol execution is retrieved and added to the Dashboard message. Needs **covmatic-stations >= v2.6.0**
- Upload Protocol interface does not go in error with empty tip_log.json file on robot.
- Non-ASCII characters on barcode request are handled correctly and do not cause internal server error.

## v2.6.0
### Added
- Check function now have _stage_ field in the _runinfo_ dictionary to pass information to dashboard

## v2.5.1
### Added
- Yumi task: start, stop and barcode reading action
- Disabled version check at startup because the PyPI service is unavailable.

## Fixed
- Bug on PCR Task that returned _null_ during the task.

## v2.4.1
### Added
- Paired pipette station B Techogenetics protocol can now be loaded to robot;
- Bioer protocol now can be loaded to robot with covmatic-stations from v2.3.0;

## v2.3.2
- Fixed bug on thread creation that filled available memory;

## v2.3.1
### Fixed
- Compatibility issue with robot with Opentrons version 4.x.x

## v2.3.0
### Added
- Opentrons apiLevel in protocols set to 2.7 to use new has_tip functionality.

## v2.2.1
### Fixed
- Support HTTP commands for Opentrons v4.1.1
- Modified barcode message deleting "rack" word: it is used also for deepwell and PCR plate

### Added
- OT SSH log is now printed in the LWS console window.

## v2.1.1

- Initial release for this changelog