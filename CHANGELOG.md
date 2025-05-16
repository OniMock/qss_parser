## [0.2.0] - 2025-05-14

qss-parser v0.2.0

### Overview
Version 0.2.0 of qss-parser.

## Changes
- Update: github action to automatize build for docs ([295c205](https://github.com/OniMock/qss_parser/commit/295c2059f6e04d36e8aab06f281a8f50fb67398f))
- Update: conf.py to get version from pyproject.toml ([1ef2a3f](https://github.com/OniMock/qss_parser/commit/1ef2a3fda9a097105ecccfd0592eedc9f700579d))
- Update: read docs parameters ([3d316c1](https://github.com/OniMock/qss_parser/commit/3d316c1087407aa9294028ed4a3d442741a7be68))
- Add: badge for read docs ([482a0eb](https://github.com/OniMock/qss_parser/commit/482a0eb11f7cf60c1bb2d1a20431769ee7c2db3e))
- Fix: sphinx version to python 3.8 ([92a0ff5](https://github.com/OniMock/qss_parser/commit/92a0ff56f882e99ba5cb82b93727bcb3661e10ca))
- Fix: path to conf.py ([d4bfa9a](https://github.com/OniMock/qss_parser/commit/d4bfa9af508d53796ebd5dc0c61aed571692c19d))
- Remove: from read docs obsolete system package ([ebb25d1](https://github.com/OniMock/qss_parser/commit/ebb25d1853cccf800b9ccc3c46bbc13b46dc2bd4))
- Add: yaml to readdocs ([2a05edf](https://github.com/OniMock/qss_parser/commit/2a05edfd7200252ce11e8f37adcff73cb68cac01))
- Add: docs with Sphinx ([c6065da](https://github.com/OniMock/qss_parser/commit/c6065dab6894b996acd8d9ba43f47d688f4cce75))
- Fix: 'type' object is not subscriptable ([b3e435f](https://github.com/OniMock/qss_parser/commit/b3e435f95da1c93a5fae23612d8e002c77e5b163))
- Fix: Pattern import for python <3.8 ([dfdf50a](https://github.com/OniMock/qss_parser/commit/dfdf50ab12420dfdf4a5e6586f98913aa2b4515c))
- Refactor: to pass in flake8 ([e20ce5c](https://github.com/OniMock/qss_parser/commit/e20ce5c3b7d28232839967b3e8438fad41fee5b9))
- Refactor: reorganize, refactor, separate responsibilities, and optimize code ([3e9de76](https://github.com/OniMock/qss_parser/commit/3e9de76cb85da0511dae2c6c2f148f9fcf666b25))
- Refactor: explicit imports in all ([d84da26](https://github.com/OniMock/qss_parser/commit/d84da2628c1a882f52bb3edf6d9ae24da20bfbca))
- Fix: readme.md image align ([1453cf7](https://github.com/OniMock/qss_parser/commit/1453cf73637e46a23255408551e6763908671453))
- Add: new tests to check pseudo-state and pseudo-element ([82b178d](https://github.com/OniMock/qss_parser/commit/82b178d9ac7584643e12083554a0b0c5765dadee))
- Update: example to refactored code ([5589dc3](https://github.com/OniMock/qss_parser/commit/5589dc3618de51d577c08466d6b2d7df9aff3cf8))
- Update: readme.md with refactored code ([491fedc](https://github.com/OniMock/qss_parser/commit/491fedcf26b288d72c7784cd23210de8db20c3fc))
- Update: ignore flake ([60a64d0](https://github.com/OniMock/qss_parser/commit/60a64d0ccfeb9c3464692a36b6b7b1df6235457d))
- Fix: QSSParser to handle undefined variables, class-ID selectors, and invalid attribute selector spacing ([8f6895a](https://github.com/OniMock/qss_parser/commit/8f6895a621bc52da6b802807d057b9f7cfe17192))
- Fix: false error on syntax ([49ee3f3](https://github.com/OniMock/qss_parser/commit/49ee3f3b10d5f83f751f07998a93d457b90abd45))
- Fix invalid property handling and semicolon validation in QSS parser ([a67263b](https://github.com/OniMock/qss_parser/commit/a67263b7259281182a3e4a85c428a1298c3f2197))
- Add: tests for get_styles_for edge cases ([76059d3](https://github.com/OniMock/qss_parser/commit/76059d3026bbe814ed56818c1f59b53e0c7fec1e))
- Fix: circular variable reference error reporting in VariableManager and QSSParser ([02009f2](https://github.com/OniMock/qss_parser/commit/02009f2f8d16d89d921b7071c8d480a75c4bbe36))
- Add: validation for invalid/duplicate selectors and invalid property names in QSSSyntaxChecker ([c1fa400](https://github.com/OniMock/qss_parser/commit/c1fa400235dd9b67547f427cd8940e9bf3130320))
- Add: support for invalid_rule_skipped event in QSSParser ([a103b4a](https://github.com/OniMock/qss_parser/commit/a103b4a9ebf02bbd547a7f766c4e0d6bb4231bc2))
- Add: support for parse_completed event in QSSParser ([6cea6a2](https://github.com/OniMock/qss_parser/commit/6cea6a263dfb19c90ae6778d17581053cec291b3))
- Add: support for variable_defined event in QSSParser and VariableManager ([f554897](https://github.com/OniMock/qss_parser/commit/f554897097d8a49e572a948783b00cac2484154e))
- Refactor: to organization and best performance ([3cdc287](https://github.com/OniMock/qss_parser/commit/3cdc2871b85f68224bf63b04a7010a1bd120cc12))
- Remove: blank spaces ([74c3bbb](https://github.com/OniMock/qss_parser/commit/74c3bbbd8c20fceb9a69749d812851185cf363c6))
- Implementing: parse to string in same qss format ([cfd52c7](https://github.com/OniMock/qss_parser/commit/cfd52c79dfb8633cc68fc63eba3f8d5902cd78db))
- Add: test for get the correctly format in to_string ([2ccaca1](https://github.com/OniMock/qss_parser/commit/2ccaca19755cc404c55607f65117c1f2c5832cac))
- Update: selector separate by commas and line are valid. ([fdfa416](https://github.com/OniMock/qss_parser/commit/fdfa41641225f765eb04237d1f3b8e97b3720d97))
- Update: selector separate by commas and line are valid. ([7def77e](https://github.com/OniMock/qss_parser/commit/7def77e030d8046cb57eeddad2712ffe984cc2cf))
- Add: check for invalid spaces ([6853907](https://github.com/OniMock/qss_parser/commit/685390773ffd51a283f77d16a9a0fddbbfad429b))
- Add: check for invalid spaces ([eef4d05](https://github.com/OniMock/qss_parser/commit/eef4d0514ced761e04682c6f73c6607c2e28d949))
- Fix: duplicate properties get the last value ([7093f28](https://github.com/OniMock/qss_parser/commit/7093f28622cdfff99b6cc99aa3469eeb7401500b))
- Fix: duplicate with pseudo_elements and overrides properties ([8ac31b9](https://github.com/OniMock/qss_parser/commit/8ac31b9a5947c12090f192aee4c8acb74ae085d5))
- Refactor: remove redundant and keep organization ([638c214](https://github.com/OniMock/qss_parser/commit/638c21409774336e4f50492a7aefa86239fa5961))
## Installation
```bash
pip install qss-parser==0.2.0
```

See the [README.md](README.md) for more details.

## [0.1.3] - 2025-05-09

qss-parser v0.1.3

### Overview
Version 0.1.3 of qss-parser.

## Changes
- Fix: sort imports ([0507feb](https://github.com/OniMock/qss_parser/commit/0507feb282f354d6052fa99d229a18eb16abb295))
- Fix: Match typing ([43d7b57](https://github.com/OniMock/qss_parser/commit/43d7b5761681b9a3a84791ff1a0721f3a607e9e2))
- Update: to include variable support ([35a3951](https://github.com/OniMock/qss_parser/commit/35a395119c8eeabd73fa62a26d2fd0d9b62232b4))
- Refactor: all code ([7c6aee8](https://github.com/OniMock/qss_parser/commit/7c6aee8464c70be68c7a6a081329a75150cbe05d))
- Fix: full example on readme ([37c6967](https://github.com/OniMock/qss_parser/commit/37c6967d5b515071ed90f649dc98e5498c8294d3))
## Installation
```bash
pip install qss-parser==0.1.3
```

See the [README.md](README.md) for more details.

## [0.1.2] - 2025-05-08

qss-parser v0.1.2

### Overview
Version 0.1.2 of qss-parser.

## Changes
- Update: requeriments and action ([44090df](https://github.com/OniMock/qss_parser/commit/44090dfba929949221eefd59f5674db45a10ba7b))
- Update: for isort ([92c5330](https://github.com/OniMock/qss_parser/commit/92c533078bfb87ce7e8c8ad31da2a8f4f2e8d1a9))
- Update: pytest-cov with stable version ([e0b6214](https://github.com/OniMock/qss_parser/commit/e0b621432e6038bac772e851b4270b6c33855b3b))
- Update/Refactor: All code with new features ([16db550](https://github.com/OniMock/qss_parser/commit/16db550c2e580287224a0a1fe8149ecb6fe86d85))
- Update: Unit tests with new features ([b212a84](https://github.com/OniMock/qss_parser/commit/b212a841642a289abe59613b106e4a3446e12323))
- Update: readme.md with new features ([4ae10eb](https://github.com/OniMock/qss_parser/commit/4ae10eb8f78e3cf2660bfa53e1bb8999328dd373))
- Update: Full example with new features ([cb9d034](https://github.com/OniMock/qss_parser/commit/cb9d0341943703503b8f82285c087a0d7730ed42))
- Update: Full example with new features ([c9eaa10](https://github.com/OniMock/qss_parser/commit/c9eaa10e8d0190c572848bee510f3542dc5c3f86))
- Update: Actions with more tests ([f0e7408](https://github.com/OniMock/qss_parser/commit/f0e74088b643cbcfdec2a9f068383405901ec1ca))
- Update: gitignore ([77072cb](https://github.com/OniMock/qss_parser/commit/77072cb51a5960b4e27e58a240e862930d704762))
- Add: all library for developer ([a6e9499](https://github.com/OniMock/qss_parser/commit/a6e94997b7458096a6885ebf6814ce452b1b1d39))
- Update: pyproject with flake8, mypy, isort ([c182a2c](https://github.com/OniMock/qss_parser/commit/c182a2ccecfce489bc93c44a2c18e8551a8653bf))
- Remove: config flake8 ([97d0f4c](https://github.com/OniMock/qss_parser/commit/97d0f4c8bf1e5d2b80694b5158eb49ba1087ad51))
## Installation
```bash
pip install qss-parser==0.1.2
```

See the [README.md](README.md) for more details.

## [0.1.1] - 2025-05-01

qss-parser v0.1.1

### Overview
Version 0.1.1 of qss-parser.

## Changes
- Fix: github action ([489998f](https://github.com/OniMock/qss_parser/commit/489998f7aaf5a4935bd12420cf2c7d22427f0bd8))
- Update: Readme ([197feb5](https://github.com/OniMock/qss_parser/commit/197feb598942800e116db01ffba529fb34dfbd23))
- Refactor: Tuple type ([a23b1ef](https://github.com/OniMock/qss_parser/commit/a23b1ef28ad711afb23ddbc99efbf0c4001038c0))
- Refactor: Tuple to tuple ([177c38a](https://github.com/OniMock/qss_parser/commit/177c38a4e9591d2eac7580ddea867e881ae541b0))
- Refactor: tuple to Tuple ([401a15e](https://github.com/OniMock/qss_parser/commit/401a15eac2c6047214c2e828bec6daf7c9a59961))
- Refactor: All code to use black formatter and flake8 ([1222216](https://github.com/OniMock/qss_parser/commit/12222164d6efcdb80ee088bda9108004801d3be3))
- Add: flake8 config ([5aeb2dc](https://github.com/OniMock/qss_parser/commit/5aeb2dc16399a7fd436b92a913079a2e6a7c5848))
- Fix: requirements file ([f9f1fdd](https://github.com/OniMock/qss_parser/commit/f9f1fdd57396f704aa0d88dc3b776aa76b9c98c4))
- Update: Versioning script ([6dfb3f6](https://github.com/OniMock/qss_parser/commit/6dfb3f632554a0a33ab6286fbc8a2deca4e212c9))
- Try-Fix: github actions ([b6b81c5](https://github.com/OniMock/qss_parser/commit/b6b81c505edc7d3666b2a0c4c34709e8cf8cd9fe))
- Add: Changelog, Code of conduct, Contributing, License, Manifest, Pyproject, README, requirements, update_version ([03ba1bc](https://github.com/OniMock/qss_parser/commit/03ba1bc7893499a4d8b386764bebf39bc2bc02cb))
- Add github action ([90b02cd](https://github.com/OniMock/qss_parser/commit/90b02cdbd3e067a4f6ec11de61db281635c418b9))
- Update: git ignore ([154680f](https://github.com/OniMock/qss_parser/commit/154680f85801c2426938d9c18155a832cce026d7))
- Add: examples ([3e2dfa8](https://github.com/OniMock/qss_parser/commit/3e2dfa882cd7d922f084ee0425f46e24cc4c06e5))
## Installation
```bash
pip install qss-parser==0.1.1
```

See the [README.md](README.md) for more details.

# Changelog

All notable changes to the **qss_parser** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
