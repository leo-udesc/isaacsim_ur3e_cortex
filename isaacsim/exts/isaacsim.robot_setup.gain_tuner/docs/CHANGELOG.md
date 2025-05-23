# Changelog

## [2.0.3] - 2025-01-21
### Changed
- Update extension description and add extension specific test settings

## [2.0.2] - 2024-12-03
### Changed
- Isaac Util menu to Tools->Robotics menu

## [2.0.1] - 2024-10-24
### Changed
- Updated dependencies and imports after renaming

## [2.0.0] - 2024-10-01
### Changed
- Extension renamed to isaacsim.robot_setup.gain_tuner.

## [1.1.2] - 2024-06-13
### Fixed
- Fixed bug where robot with zero-gains causes a math error in trying to take log(0).

## [1.1.1] - 2024-04-23
### Fixed
- Fixed post-test behavior where an Articulation is left with a non-zero velocity command.

## [1.1.0] - 2024-04-16
### Fixed
- Fixed bug where Gains Test Settings Panel had multiple ways of accumulating or forgetting state between tests when switching robots or toggling STOP/PLAY
### Added
- Added fields to add position and velocity impulses to the start of the robot trajectory.

## [1.0.1] - 2024-03-14
### Fixed
- Fixed logic around selecting Articulation on STOP/PLAY given new behavior in Core get_prim_object_type() function.
### Added
- Added helper text telling the user to click the play button to get started.
- Added more text clarifying Gains Test settings.

## [1.0.0] - 2024-03-08
### Added
- Initial version of Gain Tuner Extension
