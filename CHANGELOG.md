# Changelog

All notable changes to the Session Converter project will be documented in this file.

## [Unreleased]

### Added - Multi-Format Support (2026-07-09)

#### New Format Support
- **Cursor IDE format** - Parse and emit Cursor IDE sessions (JSONL exports)
- **Pi AI format** - Parse and emit Pi AI sessions with tree structure support
- **OpenCode format** - Parse and emit OpenCode sessions (JSONL exports)

#### Features
- Multi-format auto-detection supporting 5 formats (Claude, Codex, Cursor, Pi, OpenCode)
- Confidence-based format detection with scoring system
- All-to-all format conversion matrix (25 conversion paths)
- Enhanced CLI with new format choices: `--to [claude|codex|cursor|pi|opencode]`

#### Parsers
- `session_converter/parsers/cursor.py` - Cursor IDE JSONL parser
- `session_converter/parsers/pi.py` - Pi AI tree structure parser
- `session_converter/parsers/opencode.py` - OpenCode JSONL parser

#### Emitters
- `session_converter/emitters/cursor.py` - Cursor IDE format emitter
- `session_converter/emitters/pi.py` - Pi AI format emitter with tree structure
- `session_converter/emitters/opencode.py` - OpenCode format emitter

#### Testing
- Added 10 new comprehensive tests in `tests/test_new_formats.py`
- Format-specific parsing tests
- Round-trip conversion tests
- Cross-format conversion tests
- Format feature validation tests
- **Total: 32 tests passing**

#### Documentation
- New `FORMATS.md` - Comprehensive format documentation
  - Format structures and key features
  - Detection indicators
  - Conversion matrix
  - Format-specific limitations
  - Resources and links
- Updated `README.md` - Multi-format features and examples
- Updated `QUICKSTART.md` - Usage examples for new formats
- New `CHANGELOG.md` - Project change tracking

#### Example Sessions
- `examples/cursor_session.jsonl` - Sample Cursor IDE session
- `examples/pi_session.jsonl` - Sample Pi AI session with tool calls
- `examples/opencode_session.jsonl` - Sample OpenCode session

### Changed
- Enhanced `detect_format()` in `session_converter/utils.py` to recognize 5 formats
- Updated CLI command options to include new format choices
- Expanded conversion capabilities from 2 formats to 5 formats

### Technical Details
- **Lines of code added**: ~1,200
- **New files**: 16
- **Modified files**: 5
- **Test coverage**: 32 tests, all passing
- **Conversion matrix**: 25 conversion paths (5x5 formats)

## [Initial Release] - 2026-07-09

### Added
- Initial session converter implementation
- Claude Code format parser and emitter
- Codex CLI format parser and emitter
- Intermediate data model with Pydantic validation
- CLI with commands: `convert`, `info`, `validate`, `batch`
- Auto-detection for Claude and Codex formats
- Explicit target format requirement for extensibility
- Comprehensive test suite
- Documentation (README, QUICKSTART, DESIGN, VALIDATION)

### Features
- Bidirectional Claude ↔ Codex conversion
- Format validation
- Session inspection
- Batch processing
- Pretty printing
- Statistics reporting
- Verbose logging
- Round-trip conversion support

### Testing
- Unit tests for parsers and emitters
- Edge case tests
- Round-trip tests
- Auto-detection tests
- **Total: 22 tests passing**
