### COVMATIC LocalWebServer changelog

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