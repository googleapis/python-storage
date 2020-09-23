# Changelog

[PyPI History][1]

[1]: https://pypi.org/project/google-cloud-storage/#history

### [1.31.2](https://www.github.com/googleapis/python-storage/compare/v1.31.1...v1.31.2) (2020-09-23)


### Documentation

* fix docstring example for 'blob.generate_signed_url' ([#278](https://www.github.com/googleapis/python-storage/issues/278)) ([2dc91c9](https://www.github.com/googleapis/python-storage/commit/2dc91c947e3693023b4478a15c460693808ea2d9))

### [1.31.1](https://www.github.com/googleapis/python-storage/compare/v1.31.0...v1.31.1) (2020-09-16)


### Bug Fixes

* add requests as a dependency ([#271](https://www.github.com/googleapis/python-storage/issues/271)) ([ec52b38](https://www.github.com/googleapis/python-storage/commit/ec52b38df211fad18a86d7e16d83db79de59d5f5))
* preserve existing blob hashes when 'X-Goog-Hash header' is not present ([#267](https://www.github.com/googleapis/python-storage/issues/267)) ([277afb8](https://www.github.com/googleapis/python-storage/commit/277afb83f464d77b163f2722272092df4180411e))
* **blob:** base64 includes additional characters ([#258](https://www.github.com/googleapis/python-storage/issues/258)) ([cf0774a](https://www.github.com/googleapis/python-storage/commit/cf0774aa8ffd45d340aff9a7d2236d8d65c8ae93))


### Documentation

* add docs signed_url expiration take default utc ([#250](https://www.github.com/googleapis/python-storage/issues/250)) ([944ab18](https://www.github.com/googleapis/python-storage/commit/944ab1827b3ca0bd1d3aafc2829245290e9bde59))

## [1.31.0](https://www.github.com/googleapis/python-storage/compare/v1.30.0...v1.31.0) (2020-08-26)


### Features

* add configurable checksumming for blob uploads and downloads ([#246](https://www.github.com/googleapis/python-storage/issues/246)) ([23b7d1c](https://www.github.com/googleapis/python-storage/commit/23b7d1c3155deae3c804c510dee3a7cec97cd46c))
* add support for 'Blob.custom_time' and lifecycle rules ([#199](https://www.github.com/googleapis/python-storage/issues/199)) ([180873d](https://www.github.com/googleapis/python-storage/commit/180873de139f7f8e00b7bef423bc15760cf68cc2))
* error message return from api ([#235](https://www.github.com/googleapis/python-storage/issues/235)) ([a8de586](https://www.github.com/googleapis/python-storage/commit/a8de5868f32b45868f178f420138fcd2fe42f5fd))
* **storage:** add support of daysSinceNoncurrentTime and noncurrentTimeBefore ([#162](https://www.github.com/googleapis/python-storage/issues/162)) ([136c097](https://www.github.com/googleapis/python-storage/commit/136c0970f8ef7ad4751104e3b8b7dd3204220a67))
* pass 'client_options' to base class ctor ([#225](https://www.github.com/googleapis/python-storage/issues/225)) ([e1f91fc](https://www.github.com/googleapis/python-storage/commit/e1f91fcca6c001bc3b0c5f759a7a003fcf60c0a6)), closes [#210](https://www.github.com/googleapis/python-storage/issues/210)
* rename 'Blob.download_as_{string,bytes}', add 'Blob.download_as_text' ([#182](https://www.github.com/googleapis/python-storage/issues/182)) ([73107c3](https://www.github.com/googleapis/python-storage/commit/73107c35f23c4a358e957c2b8188300a7fa958fe))


### Bug Fixes

* change datetime.now to utcnow ([#251](https://www.github.com/googleapis/python-storage/issues/251)) ([3465d08](https://www.github.com/googleapis/python-storage/commit/3465d08e098edb250dee5e97d1fb9ded8bae5700)), closes [#228](https://www.github.com/googleapis/python-storage/issues/228)
* extract hashes correctly during download ([#238](https://www.github.com/googleapis/python-storage/issues/238)) ([23cfb65](https://www.github.com/googleapis/python-storage/commit/23cfb65c3a3b10759c67846e162e4ed77a3f5307))
* repair mal-formed docstring ([#255](https://www.github.com/googleapis/python-storage/issues/255)) ([e722376](https://www.github.com/googleapis/python-storage/commit/e722376371cb8a3acc46d6c84fb41f4e874f41aa))


### Documentation

* update docs build (via synth) ([#222](https://www.github.com/googleapis/python-storage/issues/222)) ([4c5adfa](https://www.github.com/googleapis/python-storage/commit/4c5adfa6e05bf018d72ee1a7e99679fd55f2c662))

## [1.30.0](https://www.github.com/googleapis/python-storage/compare/v1.29.0...v1.30.0) (2020-07-24)


### Features

* add timeouts to Blob methods where missing ([#185](https://www.github.com/googleapis/python-storage/issues/185)) ([6eeb855](https://www.github.com/googleapis/python-storage/commit/6eeb855aa0e6a7835d1d4f6e72951e43af22ab57))
* auto-populate standard headers for non-chunked downloads ([#204](https://www.github.com/googleapis/python-storage/issues/204)) ([d8432cd](https://www.github.com/googleapis/python-storage/commit/d8432cd65a4e9b38eebd1ade2ff00f2f44bb0ef6)), closes [#24](https://www.github.com/googleapis/python-storage/issues/24)
* migrate to Service Account Credentials API ([#189](https://www.github.com/googleapis/python-storage/issues/189)) ([e4990d0](https://www.github.com/googleapis/python-storage/commit/e4990d06043dbd8d1a417f3a1a67fe8746071f1c))


### Bug Fixes

* add multiprocessing.rst to synthool excludes ([#186](https://www.github.com/googleapis/python-storage/issues/186)) ([4d76e38](https://www.github.com/googleapis/python-storage/commit/4d76e3882210ed2818a43256265f6df31348d410))


### Documentation

* fix indent in code blocks ([#171](https://www.github.com/googleapis/python-storage/issues/171)) ([62d1543](https://www.github.com/googleapis/python-storage/commit/62d1543e18040b286b23464562aa6eb998074c54)), closes [#170](https://www.github.com/googleapis/python-storage/issues/170)
* remove doubled word in docstring ([#209](https://www.github.com/googleapis/python-storage/issues/209)) ([7a4e7a5](https://www.github.com/googleapis/python-storage/commit/7a4e7a5974abedb0b7b2e110cacbfcd0a40346b6))


### Documentation

* fix indent in code blocks ([#171](https://www.github.com/googleapis/python-storage/issues/171)) ([62d1543](https://www.github.com/googleapis/python-storage/commit/62d1543e18040b286b23464562aa6eb998074c54)), closes [#170](https://www.github.com/googleapis/python-storage/issues/170)
* remove doubled word in docstring ([#209](https://www.github.com/googleapis/python-storage/issues/209)) ([7a4e7a5](https://www.github.com/googleapis/python-storage/commit/7a4e7a5974abedb0b7b2e110cacbfcd0a40346b6))


### Dependencies

* prep for grmp-1.0.0 release ([#211](https://www.github.com/googleapis/python-storage/issues/211)) ([55bae9a](https://www.github.com/googleapis/python-storage/commit/55bae9a0e7c0db512c10c6b3b621cd2ef05c9729))


## [1.29.0](https://www.github.com/googleapis/python-storage/compare/v1.28.1...v1.29.0) (2020-06-09)


### Features

* add *generation*match args into Blob.compose() ([#122](https://www.github.com/googleapis/python-storage/issues/122)) ([dc01c59](https://www.github.com/googleapis/python-storage/commit/dc01c59e036164326aeeea164098cf2e6e0dc12c))
* add Bucket.reload() and Bucket.update() wrappers to restrict generation match args ([#153](https://www.github.com/googleapis/python-storage/issues/153)) ([76dd9ac](https://www.github.com/googleapis/python-storage/commit/76dd9ac7e8b7765defc5b521cfe059e08e33c65c)), closes [#127](https://www.github.com/googleapis/python-storage/issues/127)
* add helper for bucket bound hostname URLs ([#137](https://www.github.com/googleapis/python-storage/issues/137)) ([b26f9fa](https://www.github.com/googleapis/python-storage/commit/b26f9fa8a767b7d5affea8d2c4b87163ce979fd2)), closes [#121](https://www.github.com/googleapis/python-storage/issues/121)
* add if*generation*match support for Bucket.rename_blob() ([#141](https://www.github.com/googleapis/python-storage/issues/141)) ([f52efc8](https://www.github.com/googleapis/python-storage/commit/f52efc807355c82aa3ea621cdadcc316175f0abf))
* add if*generation*Match support, pt1 ([#123](https://www.github.com/googleapis/python-storage/issues/123)) ([0944442](https://www.github.com/googleapis/python-storage/commit/094444280dd7b7735e24071e5381508cbd392260))
* add offset and includeTrailingPrefix options to list_blobs ([#125](https://www.github.com/googleapis/python-storage/issues/125)) ([d84c0dd](https://www.github.com/googleapis/python-storage/commit/d84c0ddfd00fa731acfe9899c668041456b08ab7))
* Create CODEOWNERS ([#135](https://www.github.com/googleapis/python-storage/issues/135)) ([32a8d55](https://www.github.com/googleapis/python-storage/commit/32a8d55b6ec56a9f7c0a3502fbe23c1ba1cc8ad2))


### Bug Fixes

* add documentaion of list_blobs with user project ([#147](https://www.github.com/googleapis/python-storage/issues/147)) ([792b21f](https://www.github.com/googleapis/python-storage/commit/792b21fd2263b518d56f79cab6a4a1bb06c6e4e7))
* add projection parameter to blob.reload method ([#146](https://www.github.com/googleapis/python-storage/issues/146)) ([ddad20b](https://www.github.com/googleapis/python-storage/commit/ddad20b3c3d2e6bf482e34dad85fa4b0ff90e1b1))
* add unused variables to method generation match ([#152](https://www.github.com/googleapis/python-storage/issues/152)) ([f6574bb](https://www.github.com/googleapis/python-storage/commit/f6574bb84c60c30989d05dba97b423579360cdb2))
* change the method names in snippets file ([#161](https://www.github.com/googleapis/python-storage/issues/161)) ([e516ed9](https://www.github.com/googleapis/python-storage/commit/e516ed9be518e30df4e201d3242f979c0b081086))
* fix upload object with bucket cmek enabled ([#158](https://www.github.com/googleapis/python-storage/issues/158)) ([5f27ffa](https://www.github.com/googleapis/python-storage/commit/5f27ffa3b1b55681453b594a0ef9e2811fc5f0c8))
* set default POST policy scheme to "http" ([#172](https://www.github.com/googleapis/python-storage/issues/172)) ([90c020d](https://www.github.com/googleapis/python-storage/commit/90c020d69a69ebc396416e4086a2e0838932130c))

### [1.28.1](https://www.github.com/googleapis/python-storage/compare/v1.28.0...v1.28.1) (2020-04-28)


### Bug Fixes

* anonymous credentials for private bucket ([#107](https://www.github.com/googleapis/python-storage/issues/107)) ([6152ab4](https://www.github.com/googleapis/python-storage/commit/6152ab4067d39ba824f9b6a17b83859dd7236cec))
* add bucket name into POST policy conditions ([#118](https://www.github.com/googleapis/python-storage/issues/118)) ([311ecab](https://www.github.com/googleapis/python-storage/commit/311ecabf8acc3018cef0697dd29483693f7722b9))

## [1.28.0](https://www.github.com/googleapis/python-storage/compare/v1.27.0...v1.28.0) (2020-04-22)


### Features

* add arguments for *GenerationMatch uploading options ([#111](https://www.github.com/googleapis/python-storage/issues/111)) ([b11aa5f](https://www.github.com/googleapis/python-storage/commit/b11aa5f00753b094580847bc62c154ae0e584dbc))


### Bug Fixes

* fix incorrect mtime by UTC offset ([#42](https://www.github.com/googleapis/python-storage/issues/42)) ([76bd652](https://www.github.com/googleapis/python-storage/commit/76bd652a3078d94e03e566b6a387fc488ab26910))
* remove expiration strict conversion ([#106](https://www.github.com/googleapis/python-storage/issues/106)) ([9550dad](https://www.github.com/googleapis/python-storage/commit/9550dad6e63e249110fc9dcda245061b76dacdcf)), closes [#105](https://www.github.com/googleapis/python-storage/issues/105)

## [1.27.0](https://www.github.com/googleapis/python-storage/compare/v1.26.0...v1.27.0) (2020-04-01)


### Features

* generate signed URLs for blobs/buckets using virtual hostname ([#58](https://www.github.com/googleapis/python-storage/issues/58)) ([23df542](https://www.github.com/googleapis/python-storage/commit/23df542d0669852b05139023d5ef1ae14a09f4c7))
* Add cname support for V4 signature ([#72](https://www.github.com/googleapis/python-storage/issues/72)) ([cc853af](https://www.github.com/googleapis/python-storage/commit/cc853af6bf8e44e5b16e8cdfb3a275629ffb1f27))
* add conformance tests for virtual hosted style signed URLs ([#83](https://www.github.com/googleapis/python-storage/issues/83)) ([5adc8b0](https://www.github.com/googleapis/python-storage/commit/5adc8b0e6ffe28185a4085cd1fc8c1b4998094aa))
* add get notification method ([#77](https://www.github.com/googleapis/python-storage/issues/77)) ([f602252](https://www.github.com/googleapis/python-storage/commit/f6022521bee0824e1b291211703afc5eae6c6891))
* improve v4 signature query parameters encoding ([#48](https://www.github.com/googleapis/python-storage/issues/48)) ([8df0b55](https://www.github.com/googleapis/python-storage/commit/8df0b554a1904787889309707f08c6b8683cad44))


### Bug Fixes

* fix blob metadata to None regression ([#60](https://www.github.com/googleapis/python-storage/issues/60)) ([a834d1b](https://www.github.com/googleapis/python-storage/commit/a834d1b54aa96152ced4d841c4e0c241acd2d8d8))
* add classifer for Python 3.8 ([#63](https://www.github.com/googleapis/python-storage/issues/63)) ([1b9b6bc](https://www.github.com/googleapis/python-storage/commit/1b9b6bc2601ee336a8399266852fb850e368b30a))
* make v4 signing formatting consistent w/ spec ([#56](https://www.github.com/googleapis/python-storage/issues/56)) ([8712da8](https://www.github.com/googleapis/python-storage/commit/8712da84c93600a736e72a097c42a49b4724347d))
* use correct IAM object admin role ([#71](https://www.github.com/googleapis/python-storage/issues/71)) ([2e27edd](https://www.github.com/googleapis/python-storage/commit/2e27edd3fe65cd5e17c12bf11f2b58f611937d61))
* remove docstring of retrun in reload method ([#78](https://www.github.com/googleapis/python-storage/issues/78)) ([4abeb1c](https://www.github.com/googleapis/python-storage/commit/4abeb1c0810c4e5d716758536da9fc204fa4c2a9))
* use OrderedDict while encoding POST policy ([#95](https://www.github.com/googleapis/python-storage/issues/95)) ([df560e1](https://www.github.com/googleapis/python-storage/commit/df560e178369a6d03140e412a25af6ec7444f5a1))

## [1.26.0](https://www.github.com/googleapis/python-storage/compare/v1.25.0...v1.26.0) (2020-02-12)


### Features

* add support for signing URLs using token ([#9889](https://www.github.com/googleapis/google-cloud-python/issues/9889)) ([ad280bf](https://www.github.com/googleapis/python-storage/commit/ad280bf506d3d7a37c402d06eac07422a5fe80af))
* add timeout parameter to public methods ([#44](https://www.github.com/googleapis/python-storage/issues/44)) ([63abf07](https://www.github.com/googleapis/python-storage/commit/63abf0778686df1caa001270dd22f9df0daf0c78))


### Bug Fixes

* fix documentation of max_result parameter in list_blob ([#43](https://www.github.com/googleapis/python-storage/issues/43)) ([ff15f19](https://www.github.com/googleapis/python-storage/commit/ff15f19d3a5830acdd540181dc6e9d07ca7d88ee))
* fix system test and change scope for iam access token ([#47](https://www.github.com/googleapis/python-storage/issues/47)) ([bc5375f](https://www.github.com/googleapis/python-storage/commit/bc5375f4c88f7e6ad1afbe7667c49d9a846e9757))
* remove low version error assertion from iam conditions system tests ([#53](https://www.github.com/googleapis/python-storage/issues/53)) ([8904aee](https://www.github.com/googleapis/python-storage/commit/8904aee9ad5dc01ab83e1460b6f186a739668eb7))

## 1.25.0

01-16-2020 11:00 PST

### Implementation Changes
- fix: replace unsafe six.PY3 with PY2 for better future compatibility with Python 4 ([#10081](https://github.com/GoogleCloudPlatform/google-cloud-python/pull/10081))
- fix(storage): fix document of delete blob ([#10015](https://github.com/GoogleCloudPlatform/google-cloud-python/pull/10015))

### New Features
- feat(storage): support optionsRequestedPolicyVersion ([#9989](https://github.com/GoogleCloudPlatform/google-cloud-python/pull/9989))

### Dependencies
- chore(storage): bump core dependency to 1.2.0 ([#10160](https://github.com/GoogleCloudPlatform/google-cloud-python/pull/10160))

## 1.24.1

01-02-2020 13:20 PST


### Implementation Changes
- Add 'ARCHIVE' storage class ([#9533](https://github.com/googleapis/google-cloud-python/pull/9533))

## 1.24.0

01-02-2020 10:39 PST


### Implementation Changes
-str() metadata for for blob ([#9796](https://github.com/googleapis/google-cloud-python/pull/9796))

### New Features
- Add timeout parameter to Batch interface to match google-cloud-core ([#10010](https://github.com/googleapis/google-cloud-python/pull/10010))

## 1.23.0

11-12-2019 12:57 PST


### Implementation Changes
- Move `create_bucket` implementation from `Bucket` to `Client`. ([#8604](https://github.com/googleapis/google-cloud-python/pull/8604))

### New Features
- Add opt-in raw download support. ([#9572](https://github.com/googleapis/google-cloud-python/pull/9572))

### Dependencies
- Pin `google-resumable-media >= 0.5.0, < 0.6dev`. ([#9572](https://github.com/googleapis/google-cloud-python/pull/9572))

### Documentation
- Add python 2 sunset banner to documentation. ([#9036](https://github.com/googleapis/google-cloud-python/pull/9036))

### Internal / Testing Changes
- Fix query-string order dependent assert. ([#9728](https://github.com/googleapis/google-cloud-python/pull/9728))
- Normalize VPCSC configuration in system tests. ([#9616](https://github.com/googleapis/google-cloud-python/pull/9616))

## 1.22.0

11-05-2019 10:22 PST


### New Features
- Add UBLA attrs to IAMConfiguration. ([#9475](https://github.com/googleapis/google-cloud-python/pull/9475))

## 1.21.0

10-28-2019 21:52 PDT

### Implementation Changes
- Add gcloud-python header to user agent ([#9551](https://github.com/googleapis/google-cloud-python/pull/9551))
- Don't report a gapic version for storage ([#9549](https://github.com/googleapis/google-cloud-python/pull/9549))
- Update storage endpoint from www.googleapis.com to storage.googleapis.com ([#9543](https://github.com/googleapis/google-cloud-python/pull/9543))
- Call anonymous client method to remove dependency of google application credentials ([#9455](https://github.com/googleapis/google-cloud-python/pull/9455))
- Enable CSEK w/ V4 signed URLs ([#9450](https://github.com/googleapis/google-cloud-python/pull/9450))

### New Features
- Support predefined ACLs in `Bucket.create` ([#9334](https://github.com/googleapis/google-cloud-python/pull/9334))

### Documentation
- Add `hmac_key` and notification documentation rst files ([#9529](https://github.com/googleapis/google-cloud-python/pull/9529))
- Remove references to the old authentication credentials ([#9456](https://github.com/googleapis/google-cloud-python/pull/9456))
- Clarify docstring for `Blob.download_as_string` ([#9332](https://github.com/googleapis/google-cloud-python/pull/9332))

## 1.20.0

09-26-2019 06:45 PDT


### New Features
- Add `user_project` param to HMAC-related methods. ([#9237](https://github.com/googleapis/google-cloud-python/pull/9237))
- Add `Blob.from_string` and `Bucket.from_string` factories. ([#9143](https://github.com/googleapis/google-cloud-python/pull/9143))

### Documentation
- Fix intersphinx reference to `requests`. ([#9294](https://github.com/googleapis/google-cloud-python/pull/9294))
- Fix deep / broken URL for service account setup. ([#9164](https://github.com/googleapis/google-cloud-python/pull/9164))

### Internal / Testing Changes
- Fix typo in `_helpers.py`. ([#9239](https://github.com/googleapis/google-cloud-python/pull/9239))
- In systests, retry bucket creation on 503. ([#9248](https://github.com/googleapis/google-cloud-python/pull/9248))
- Avoid using `REGIONAL` / `MULTI_REGIONAL` in examples, tests. ([#9205](https://github.com/googleapis/google-cloud-python/pull/9205))
- Move `benchwrapper` into `tests/perf`. ([#9246](https://github.com/googleapis/google-cloud-python/pull/9246))
- Add support for `STORAGE_EMULATOR_HOST`; add `benchwrapper` script. ([#9219](https://github.com/googleapis/google-cloud-python/pull/9219))


## 1.19.0

08-28-2019 09:45 PDT

### Implementation Changes
- Expose 'HMACKeyMetadata.id' field. ([#9115](https://github.com/googleapis/google-cloud-python/pull/9115))
- Make 'Blob.bucket' a readonly property. ([#9113](https://github.com/googleapis/google-cloud-python/pull/9113))
- Clarify 'response_type' for signed_url methods. ([#8942](https://github.com/googleapis/google-cloud-python/pull/8942))

### New Features
- Add `client_options` to constructors for manual clients. ([#9054](https://github.com/googleapis/google-cloud-python/pull/9054))

### Documentation
- Remove compatability badges from READMEs. ([#9035](https://github.com/googleapis/google-cloud-python/pull/9035))

### Internal / Testing Changes
- Remove CI for gh-pages, use googleapis.dev for api_core refs. ([#9085](https://github.com/googleapis/google-cloud-python/pull/9085))
- Fix tests broken by yesterday's google-resumable-media release. ([#9119](https://github.com/googleapis/google-cloud-python/pull/9119))
- Harden 'test_access_to_public_bucket' systest against 429 / 503 errors. ([#8997](https://github.com/googleapis/google-cloud-python/pull/8997))

## 1.18.0

08-07-2019 00:37 PDT


### New Features
- Add HMAC key support. ([#8430](https://github.com/googleapis/google-cloud-python/pull/8430))

### Documentation
- Mark old storage classes as legacy, not deprecated. ([#8887](https://github.com/googleapis/google-cloud-python/pull/8887))

### Internal / Testing Changes
- Normalize 'lint' / 'blacken' support under nox. ([#8831](https://github.com/googleapis/google-cloud-python/pull/8831))
- Update intersphinx mapping for requests. ([#8805](https://github.com/googleapis/google-cloud-python/pull/8805))

## 1.17.0

07-24-2019 12:37 PDT


### New Features
- Add `Bucket.location_type` property. ([#8570](https://github.com/googleapis/google-cloud-python/pull/8570))
- Add `Client.list_blobs(bucket_or_name)`. ([#8375](https://github.com/googleapis/google-cloud-python/pull/8375))


### Implementation Changes
- Retry bucket creation in signing setup. ([#8620](https://github.com/googleapis/google-cloud-python/pull/8620))
- Fix URI -> blob name conversion in `Client download_blob_to_file`. ([#8440](https://github.com/googleapis/google-cloud-python/pull/8440))
- Avoid escaping tilde in blob public / signed URLs. ([#8434](https://github.com/googleapis/google-cloud-python/pull/8434))
- Add generation to 'Blob.__repr__'. ([#8423](https://github.com/googleapis/google-cloud-python/pull/8423))

### Documentation
- Link to googleapis.dev documentation in READMEs. ([#8705](https://github.com/googleapis/google-cloud-python/pull/8705))
- Add compatibility check badges to READMEs. ([#8288](https://github.com/googleapis/google-cloud-python/pull/8288))
- Fix example in `Client.download_blob_to_file` docstring. ([#8629](https://github.com/googleapis/google-cloud-python/pull/8629))
- Remove typing information for kwargs to not conflict with type checkers ([#8546](https://github.com/googleapis/google-cloud-python/pull/8546))

### Internal / Testing Changes
- Skip failing `test_bpo_set_unset_preserves_acls` systest. ([#8617](https://github.com/googleapis/google-cloud-python/pull/8617))
- Add nox session 'docs'. ([#8478](https://github.com/googleapis/google-cloud-python/pull/8478))
- Add docs job to publish to googleapis.dev. ([#8464](https://github.com/googleapis/google-cloud-python/pull/8464))

## 1.16.1

06-04-2019 11:09 PDT


### Dependencies
- Don't pin `google-api-core` in libs using `google-cloud-core`. ([#8213](https://github.com/googleapis/google-cloud-python/pull/8213))

### Documentation
- Fix example in `download_blob_to_file` docstring. ([#8201](https://github.com/googleapis/google-cloud-python/pull/8201))
- Tweak `fields` docstring further. ([#8040](https://github.com/googleapis/google-cloud-python/pull/8040))
- Improve docs for `fields` argument to `Bucket.list_blobs`. ([#8023](https://github.com/googleapis/google-cloud-python/pull/8023))
- Fix docs typo. ([#8027](https://github.com/googleapis/google-cloud-python/pull/8027))

### Internal / Testing Changes
- Retry harder in face of 409/429 during module teardown. ([#8113](https://github.com/googleapis/google-cloud-python/pull/8113))
- Add more retries for 429s during teardown operations. ([#8112](https://github.com/googleapis/google-cloud-python/pull/8112))

## 1.16.0

05-16-2019 12:55 PDT


### New Features
- Update `Client.create_bucket` to take a Bucket object or string. ([#7820](https://github.com/googleapis/google-cloud-python/pull/7820))
- Update `Client.get_bucket` to take a `Bucket` object or string. ([#7856](https://github.com/googleapis/google-cloud-python/pull/7856))
- Add `Client.download_blob_to_file` method. ([#7949](https://github.com/googleapis/google-cloud-python/pull/7949))
- Add `client_info` support to client / connection. ([#7872](https://github.com/googleapis/google-cloud-python/pull/7872))

### Dependencies
- Pin `google-cloud-core >= 1.0.0, < 2.0dev`. ([#7993](https://github.com/googleapis/google-cloud-python/pull/7993))
- Pin `google-auth >= 1.2.0`. ([#7798](https://github.com/googleapis/google-cloud-python/pull/7798))

## 1.15.0

04-17-2019 15:37 PDT

### New Features
- Add support for V4 signed URLs ([#7460](https://github.com/googleapis/google-cloud-python/pull/7460))
- Add generation arguments to bucket / blob methods. ([#7444](https://github.com/googleapis/google-cloud-python/pull/7444))

### Implementation Changes
- Remove classifier for Python 3.4 for end-of-life. ([#7535](https://github.com/googleapis/google-cloud-python/pull/7535))
- Ensure that 'Blob.reload' passes encryption headers. ([#7441](https://github.com/googleapis/google-cloud-python/pull/7441))

### Documentation
- Update client library documentation URLs. ([#7307](https://github.com/googleapis/google-cloud-python/pull/7307))

### Internal / Testing Changes
- Fix failing system tests ([#7714](https://github.com/googleapis/google-cloud-python/pull/7714))
- Increase number of retries for 429 errors. ([#7484](https://github.com/googleapis/google-cloud-python/pull/7484))
- Un-flake KMS integration tests expecting empty bucket. ([#7479](https://github.com/googleapis/google-cloud-python/pull/7479))

## 1.14.0

02-06-2019 12:49 PST


### New Features
- Add 'Bucket.iam_configuration' property, enabling Bucket-Policy-Only. ([#7066](https://github.com/googleapis/google-cloud-python/pull/7066))

### Documentation
- Improve docs for 'generate_signed_url'. ([#7201](https://github.com/googleapis/google-cloud-python/pull/7201))

## 1.13.2

12-17-2018 17:02 PST


### Implementation Changes
- Update `Blob.update_storage_class` to support rewrite tokens. ([#6527](https://github.com/googleapis/google-cloud-python/pull/6527))

### Internal / Testing Changes
- Skip signing tests for insufficient credentials ([#6917](https://github.com/googleapis/google-cloud-python/pull/6917))
- Document Python 2 deprecation ([#6910](https://github.com/googleapis/google-cloud-python/pull/6910))
- Normalize docs for `page_size` / `max_results` / `page_token`. ([#6842](https://github.com/googleapis/google-cloud-python/pull/6842))

## 1.13.1

12-10-2018 13:31 PST


### Implementation Changes
- Import `iam.policy` from `google.api_core`. ([#6741](https://github.com/googleapis/google-cloud-python/pull/6741))
- Accomodate new back-end restriction on retention period. ([#6388](https://github.com/googleapis/google-cloud-python/pull/6388))
- Avoid deleting a blob renamed to itself ([#6365](https://github.com/googleapis/google-cloud-python/pull/6365))

### Dependencies
- Update dependency to google-cloud-core ([#6835](https://github.com/googleapis/google-cloud-python/pull/6835))
- Bump minimum `api_core` version for all GAPIC libs to 1.4.1. ([#6391](https://github.com/googleapis/google-cloud-python/pull/6391))

### Documentation
- Normalize use of support level badges ([#6159](https://github.com/googleapis/google-cloud-python/pull/6159))

### Internal / Testing Changes
- Blacken libraries ([#6794](https://github.com/googleapis/google-cloud-python/pull/6794))
- Add templates for flake8, coveragerc, noxfile, and black. ([#6642](https://github.com/googleapis/google-cloud-python/pull/6642))
- Harden teardown in system tests. ([#6444](https://github.com/googleapis/google-cloud-python/pull/6444))
- Harden `create_bucket` call in systests vs. 429 TooManyRequests. ([#6401](https://github.com/googleapis/google-cloud-python/pull/6401))
- Skip public bucket test in VPC Service Controls  ([#6230](https://github.com/googleapis/google-cloud-python/pull/6230))
- Fix lint failure. ([#6219](https://github.com/googleapis/google-cloud-python/pull/6219))
- Disable test running in VPC Service Controls  restricted environment ([#6215](https://github.com/googleapis/google-cloud-python/pull/6215))
- Use new Nox ([#6175](https://github.com/googleapis/google-cloud-python/pull/6175))

## 1.13.0

### New Features
- Add support for bucket retention policies ([#5534](https://github.com/googleapis/google-cloud-python/pull/5534))
- Allow `destination.content_type` to be None in `Blob.compose`. ([#6031](https://github.com/googleapis/google-cloud-python/pull/6031))

### Implementation Changes
- Ensure that `method` for `Blob.generate_signed_url` is uppercase. ([#6110](https://github.com/googleapis/google-cloud-python/pull/6110))

### Documentation
- Clarify GCS URL signing limitations on GCE ([#6104](https://github.com/googleapis/google-cloud-python/pull/6104))
- Redirect renamed 'usage.html'/'client.html' -> 'index.html'. ([#5996](https://github.com/googleapis/google-cloud-python/pull/5996))

## 1.12.0

### New Features
- Add support for Python 3.7, drop support for Python 3.4. ([#5942](https://github.com/GoogleCloudPlatform/google-cloud-python/pull/5942))
- Add lifecycle rules helpers to bucket. ([#5877](https://github.com/GoogleCloudPlatform/google-cloud-python/pull/5877))

### Implementation Changes
- Add 'stacklevel=2' to deprecation warnings. ([#5897](https://github.com/GoogleCloudPlatform/google-cloud-python/pull/5897))

### Documentation
- Storage docs: fix typos. ([#5933](https://github.com/GoogleCloudPlatform/google-cloud-python/pull/5933))
- Prep storage docs for repo split. ([#5923](https://github.com/GoogleCloudPlatform/google-cloud-python/pull/5923))

### Internal / Testing Changes
- Harden systest teardown further. ([#5900](https://github.com/GoogleCloudPlatform/google-cloud-python/pull/5900))
- Nox: use inplace installs ([#5865](https://github.com/GoogleCloudPlatform/google-cloud-python/pull/5865))

## 1.11.0

### Implementation Changes
- Preserve message / args from an `InvalidResponse`. (#5492)
- Fix generating signed urls for blobs with non-ascii names. (#5625)
- Move bucket location specification to `Bucket.create`; deprecate `Bucket.location` setter (#5808)

### New Features
- Add `Client.get_service_account_email`. (#5765)

### Documentation
- Clarify `None` values for resource-backed properties. (#5509)
- Elaborate docs for `{Bucket,Blob}.make_{public,private}`; note how to enable anonymous accesss to `Blob.public_url`. (#5767)

### Internal / Testing Changes
- Harden `create_bucket` systest against 429 responses. (#5535)
- Add system test: signed URLs w/ non-ASCII blob name. (#5626)
- Harden `tearDownModule` against 429 TooManyRequests. (#5701)
- Retry `notification.create()` on `503 ServiceUnavailable`. (#5741)
- Fix failing KMS system tests. (#5832, #5837, #5860)

## 1.10.0

### New Features
- Add support for KMS keys (#5259)
- Add `{Blob,Bucket}make_private` method (#5336)

### Internal / Testing Changes
- Modify system tests to use prerelease versions of grpcio (#5304)

## 1.9.0

### Implementation Changes
- Change GCS batch endpoint from `/batch` to `/batch/storage/v1` (#5040)

### New Features
- Allow uploading files larger than 2GB by using Resumable Media Requests (#5187)
- Add range downloads (#5081)

### Documentation
- Update docstring to reflect correct units (#5277)
- Replace link to 404 object IAM docs with a note on limited utility. (#5181)
- Update doc reference in GCS client documentation (#5084)
- Add see also for `Bucket.create` method call for `Client.create_bucket()` documentation. (#5073)
- Link out to requester pays docs. (#5065)

### Internal / Testing Changes
- Add testing support for Python 3.7; remove testing support for Python 3.4. (#5295)
- Fix bad trove classifier
- Remove unused var (flake8 warning) (#5280)
- Fix unit test moving batch to batch/storage/v1 (#5082)

## 1.8.0

### New features

- Implement predefined acl (#4757)
- Add support for resumable signed url generation (#4789)

### Implementation changes

- Do not quote embedded slashes for public / signed URLs (#4716)

### Dependencies

- Update dependency range for api-core to include v1.0.0 releases (#4944)

### Documentation

- Missing word in docstring (#4763)

### Testing and internal changes

- Install local dependencies when running lint (#4936)
- Re-enable lint for tests, remove usage of pylint (#4921)
- Normalize all setup.py files (#4909)

## 1.7.0

### Features

- Enable anonymous access to blobs in public buckets (#4315)
- Make project optional / overridable for storage client (#4381)
- Relax regex used to test for valid project IDs (#4543)
- Add support for `source_generation` parameter to `Bucket.copy_blob` (#4546)

## 1.6.0

### Documentation

- Added link to "Python Development Environment Setup Guide" in
  project README (#4187, h/t to @michaelawyu)

### Dependencies

- Upgrading to `google-cloud-core >= 0.28.0` and adding dependency
  on `google-api-core` (#4221, #4280)
- Requiring `google-resumable-media >= 0.3.1` (#4244)

PyPI: https://pypi.org/project/google-cloud-storage/1.6.0/
