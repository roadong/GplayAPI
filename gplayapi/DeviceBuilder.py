import configparser
from os import path
from re import match
from time import time

from gplayapi import GooglePlay_pb2
from gplayapi.Constant import sc
from gplayapi.Error import InvalidTimezoneError, InvalidLocaleError


class DeviceBuilder(object):

    def __init__(self, device):
        self.device = {}
        self.filepath = path.join(path.dirname(path.realpath(__file__)), '../resources/Device.properties')
        self.config = configparser.ConfigParser()
        self.config.read(self.filepath)
        for (key, value) in self.config.items(device):
            self.device[key] = value

    def set_locale(self, locale):
        # test if provided locale is valid
        if locale is None or type(locale) is not str:
            raise InvalidLocaleError()

        # check if locale matches the structure of a common
        # value like "en_US"
        if match(r'[a-z]{2}_[A-Z]{2}', locale) is None:
            raise InvalidLocaleError()
        self.locale = locale

    def set_timezone(self, timezone):
        if timezone is None or type(timezone) is not str:
            timezone = self.device.get('timezone')
            if timezone is None:
                raise InvalidTimezoneError()
        self.timezone = timezone

    def get_base_headers(self):
        return {"Accept-Language": self.locale.replace('_', '-'),
                "X-DFE-Encoded-Targets": sc.DFE_TARGETS,
                "User-Agent": self.get_user_agent(),
                "X-DFE-Client-Id": "am-android-google",
                "X-DFE-MCCMNC": self.device.get('celloperator'),
                "X-DFE-Network-Type": "4",
                "X-DFE-Content-Filters": "",
                "X-DFE-Request-Params": "timeoutMs=4000"}

    def get_device_upload_headers(self):
        headers = self.get_base_headers()
        headers["X-DFE-Enabled-Experiments"] = "cl:billing.select_add_instrument_by_default"
        headers["X-DFE-Unsupported-Experiments"] = ("nocache:billing.use_charging_poller,"
                                                    "market_emails,buyer_currency,prod_baseline,checkin.set_asset_paid_app_field,"
                                                    "shekel_test,content_ratings,buyer_currency_in_app,nocache:encrypted_apk,recent_changes")
        headers["X-DFE-SmallestScreenWidthDp"] = "240"
        headers["X-DFE-Filter-Level"] = "3"
        return headers

    def get_user_agent(self):
        version_string = self.device.get('vending.versionstring')
        if version_string is None:
            version_string = '8.4.19.V-all [0] [FP] 175058788'
        return ("Android-Finsky/{versionString} ("
                "api=3"
                ",versionCode={versionCode}"
                ",sdk={sdk}"
                ",device={device}"
                ",hardware={hardware}"
                ",product={product}"
                ",platformVersionRelease={platform_v}"
                ",model={model}"
                ",buildId={build_id}"
                ",isWideScreen=0"
                ",supportedAbis={supported_abis}"
                ")").format(versionString=version_string,
                            versionCode=self.device.get('vending.version'),
                            sdk=self.device.get('build.version.sdk_int'),
                            device=self.device.get('build.device'),
                            hardware=self.device.get('build.hardware'),
                            product=self.device.get('build.product'),
                            platform_v=self.device.get('build.version.release'),
                            model=self.device.get('build.model'),
                            build_id=self.device.get('build.id'),
                            supported_abis=self.device.get('platforms').replace(',', ';'))

    def get_auth_headers(self, gsfid):
        headers = {"User-Agent": ("GoogleAuth/1.4 ("
                                  "{device} {id}"
                                  ")").format(device=self.device.get('build.device'),
                                              id=self.device.get('build.id'))}
        if gsfid is not None:
            headers['device'] = "{0:x}".format(gsfid)
        return headers

    def get_login_params(self, email, encrypted_passwd):
        return {"Email": email,
                "EncryptedPasswd": encrypted_passwd,
                "add_account": "1",
                "accountType": sc.ACCOUNT,
                "google_play_services_version": self.device.get('gsf.version'),
                "has_permission": "1",
                "source": "android",
                "device_country": self.locale[0:2],
                "lang": self.locale,
                "client_sig": "38918a453d07199354f8b19af05ec6562ced5788",
                "callerSig": "38918a453d07199354f8b19af05ec6562ced5788",
                "droidguard_results": "dummy123"}

    def get_android_checkin_request(self):
        request = GooglePlay_pb2.AndroidCheckinRequest()
        request.id = 0
        request.checkin.CopyFrom(self.get_android_checkin())
        request.locale = self.locale
        request.timeZone = self.timezone
        request.version = 3
        request.deviceConfiguration.CopyFrom(self.get_device_config())
        request.fragment = 0
        return request

    def get_device_config(self):
        libList = self.device['sharedlibraries'].split(",")
        featureList = self.device['features'].split(",")
        localeList = self.device['locales'].split(",")
        glList = self.device['gl.extensions'].split(",")
        platforms = self.device['platforms'].split(",")

        hasFiveWayNavigation = (self.device['hasfivewaynavigation'] == 'true')
        hasHardKeyboard = (self.device['hashardkeyboard'] == 'true')
        deviceConfig = GooglePlay_pb2.DeviceConfigurationProto()
        deviceConfig.touchScreen = int(self.device['touchscreen'])
        deviceConfig.keyboard = int(self.device['keyboard'])
        deviceConfig.navigation = int(self.device['navigation'])
        deviceConfig.screenLayout = int(self.device['screenlayout'])
        deviceConfig.hasHardKeyboard = hasHardKeyboard
        deviceConfig.hasFiveWayNavigation = hasFiveWayNavigation
        deviceConfig.screenDensity = int(self.device['screen.density'])
        deviceConfig.screenWidth = int(self.device['screen.width'])
        deviceConfig.screenHeight = int(self.device['screen.height'])
        deviceConfig.glEsVersion = int(self.device['gl.version'])
        for x in platforms:
            deviceConfig.nativePlatform.append(x)
        for x in libList:
            deviceConfig.systemSharedLibrary.append(x)
        for x in featureList:
            deviceConfig.systemAvailableFeature.append(x)
        for x in localeList:
            deviceConfig.systemSupportedLocale.append(x)
        for x in glList:
            deviceConfig.glExtension.append(x)
        return deviceConfig

    def get_android_build(self):
        android_build = GooglePlay_pb2.AndroidBuildProto()
        android_build.id = self.device['build.fingerprint']
        android_build.product = self.device['build.hardware']
        android_build.carrier = self.device['build.brand']
        android_build.radio = self.device['build.radio']
        android_build.bootloader = self.device['build.bootloader']
        android_build.device = self.device['build.device']
        android_build.sdkVersion = int(self.device['build.version.sdk_int'])
        # androidBuild.sdkVersion = int('33')
        android_build.model = self.device['build.model']
        android_build.manufacturer = self.device['build.manufacturer']
        android_build.buildProduct = self.device['build.product']
        android_build.client = self.device['client']
        android_build.otaInstalled = False
        android_build.timestamp = int(time() / 1000)
        android_build.googleServices = int(self.device['gsf.version'])
        return android_build

    def get_android_checkin(self):
        androidCheckin = GooglePlay_pb2.AndroidCheckinProto()
        androidCheckin.build.CopyFrom(self.get_android_build())
        androidCheckin.lastCheckinMsec = 0
        androidCheckin.cellOperator = self.device['celloperator']
        androidCheckin.simOperator = self.device['simoperator']
        androidCheckin.roaming = self.device['roaming']
        androidCheckin.userNumber = 0
        return androidCheckin