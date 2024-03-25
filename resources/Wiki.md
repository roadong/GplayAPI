# Analysis


#### 코드분석에 필요한 정보 (관련 레퍼런스 모음) 

----

### HEADER

----

- `X-DFE-Device-Id` 안드로이드 기기 ID
- `X-DFE-Enabled-Experiments`
- `X-DFE-Unsupported-Experiments`
- `X-DFE-Client-Id` exmaple: `am-unknown`, `am-android-google`
- `X-DFE-Logging-Id`
- `X-DFE-Request-Params` 재시도 정책 `timeoutMs=2500`
- `X-DFE-Filter-Level` 콘텐츠 필터링 `3`
- `X-DFE-No-Prefetch` `세부정보 프리패칭 방지` ex: `true`

### User-Agent
#### 기기정보에 따라서 응답이 변함 (윈도우, 모바일, 태블릿)

----

- `sdk` SDK version(28, 33, 34)
- `device`
- `product`
- `platformVersionRelease` 릴리즈 버전
- `model`
- `buildId`
- `supportedAbis` 기기에서 지원되는 플랫폼

### Encrypted

----

- `DFE_TARGETS` 아직 파악하지 못함 (레퍼런스 하드코딩 그대로 가져옴)
- `GOOGLE_PUBKEY` GooglePlay Console 라이센스 키 (추측)
- `ACCOUNT` AC2DM 하드코딩으로 제공 (googleapis)

### DEVICE 
#### 안드로이드 디바이스 정보

----

- `Build.HARDWARE` 하드웨어 정보
- `Build.BOOTLOADER` 부트로더이름
- `Build.FINGERPRINT` 안드로이드 핑거프린트(정보 조합)
- `Build.BRAND` 기기브랜드
- `Build.DEVICE` 기기이름
- `Build.VERSION_SDK_INT` 안드로이드 SDK 버전 (숫자)
- `Build.MODEL` 기기모델이름
- `Build.MANUFACTURER` 제조사
- `Build.PRODUCT` 기기별칭
- `Build.ID` 빌드아이디
- `Build.VERSION.RELEASE` 릴리즈 버전
- `Platforms` 지원 플랫폼
- `Locales` 국가설정
- `GSF.version`
- `Vending.version` 구글플레이 앱 버전 (apk version)
- `Vending.versionString` 구글플레이 앱 버전 (apk string version)
- `TimeZone` 타임존
- `GL.Extensions` 그래픽 지원 정보

### PARAMETERS
#### 파라미터 정보

----

- `scat` sub-category
- `ctr` category
- `stcid` rank category
- `enpt` next offset