import ssl
from base64 import b64decode, urlsafe_b64encode

import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
from cryptography.hazmat.primitives.serialization import load_der_public_key
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from urllib3.util import ssl_

from gplayapi import GooglePlay_pb2
from gplayapi.Constant import sc
from gplayapi.DeviceBuilder import DeviceBuilder
from gplayapi.Error import SecurityCheckError, LoginError
from gplayapi.helper import *


class SSLContext(ssl.SSLContext):
    def set_alpn_protocols(self, protocols):
        """
        ALPN headers cause Google to return 403 Bad Authentication.
        """
        pass


class AuthHTTPAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        """
        Secure settings from ssl.create_default_context(), but without
        ssl.OP_NO_TICKET which causes Google to return 403 Bad
        Authentication.
        ssl.OP_NO-TICKET -> 0x4000
        """
        context = SSLContext()
        context.set_ciphers(ssl_.DEFAULT_CIPHERS)
        context.verify_mode = ssl.CERT_REQUIRED
        context.options &= ~ssl.OP_NO_TICKET
        self.poolmanager = PoolManager(*args, ssl_context=context, **kwargs)


authAdapter = AuthHTTPAdapter()


class GoogleAuthAPI:

    def __init__(self, locale="ko_KR", time_zone="Asia/Seoul", device_profile="default", proxies_config=None):
        self.gsfId = None
        self.auth_sub_token = None
        self.device_checkin_consistency_token = None
        self.proxies_config = proxies_config
        self.dfeCookie = None
        self.device_config_token = None

        self.session = requests.session()
        self.session.mount('https://', authAdapter)

        # initialize device builder
        self.device_builder = DeviceBuilder(device_profile)
        self.device_builder.set_locale(locale)
        self.device_builder.set_timezone(time_zone)

    def set_auth_sub_token(self, auth_sub_token):
        self.auth_sub_token = auth_sub_token

    def encrypt_password(self, login, passwd):
        """Encrypt credentials using the google publickey, with the
        RSA algorithm"""

        # structure of the binary key:
        #
        # *-------------------------------------------------------*
        # | modulus_length | modulus | exponent_length | exponent |
        # *-------------------------------------------------------*
        #
        # modulus_length and exponent_length are uint32
        binary_key = b64decode(sc.GOOGLE_PUBKEY)
        # modulus
        i = read_int(binary_key, 0)
        modulus = to_big_int(binary_key[4:][0:i])
        # exponent
        j = read_int(binary_key, i + 4)
        exponent = to_big_int(binary_key[i + 8:][0:j])

        # calculate SHA1 of the pub key
        digest = hashes.Hash(hashes.SHA1(), backend=default_backend())
        digest.update(binary_key)
        h = b'\x00' + digest.finalize()[0:4]

        # generate a public key
        der_data = encode_dss_signature(modulus, exponent)
        public_key = load_der_public_key(der_data, backend=default_backend())

        # encrypt email and password using pubkey
        to_be_encrypted = login.encode() + b'\x00' + passwd.encode()
        ciphertext = public_key.encrypt(
            to_be_encrypted,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                algorithm=hashes.SHA1(),
                label=None
            )
        )

        return urlsafe_b64encode(h + ciphertext)

    def checkin(self, email, ac2dm_token):
        headers = self.get_headers()
        headers["Content-Type"] = sc.CONTENT_TYPE_PROTO

        request = self.device_builder.get_android_checkin_request()

        string_request = request.SerializeToString()
        res = self.session.post(sc.CHECKIN_URL, data=string_request,
                                headers=headers, verify=sc.ssl_verify,
                                proxies=self.proxies_config)
        response = GooglePlay_pb2.AndroidCheckinResponse()
        response.ParseFromString(res.content)
        self.device_checkin_consistency_token = response.deviceCheckinConsistencyToken

        # checkin again to upload gfsid
        request.id = response.androidId
        request.securityToken = response.securityToken
        request.accountCookie.append("[" + email + "]")
        request.accountCookie.append(ac2dm_token)
        string_request = request.SerializeToString()
        self.session.post(sc.CHECKIN_URL,
                          data=string_request,
                          headers=headers,
                          verify=sc.ssl_verify,
                          proxies=self.proxies_config)

        return response.androidId

    def login(self, email=None, password=None, gsf_id=None, auth_sub_token=None, return_params=False):
        """Login to your Google Account.
                For first time login you should provide:
                    * email
                    * password
                For the following logins you need to provide:
                    * gsfId
                    * authSubToken"""
        if email is not None and password is not None:
            # First time setup, where we obtain an ac2dm token and
            # upload device information

            encrypted_pass = self.encrypt_password(email, password).decode('utf-8')
            # AC2DM token
            params = self.device_builder.get_login_params(email, encrypted_pass)
            params['service'] = 'ac2dm'
            params['add_account'] = '1'
            params['callerPkg'] = 'com.google.android.gms'
            self.session.headers = {'User-Agent': 'GoogleAuth/1.4'}
            response = self.session.post(sc.AUTH_URL, data=params, verify=sc.ssl_verify, proxies=self.proxies_config)
            data = response.text.split()
            params = {}
            for d in data:
                if "=" not in d:
                    continue
                k, v = d.split("=", 1)
                params[k.strip().lower()] = v.strip()
            if "auth" in params:
                ac2dm_token = params["auth"]
            elif "error" in params:
                if "NeedsBrowser" in params["error"]:
                    # This callback is returned, but it doesn't appear to
                    # actually work for getting into your account
                    callback_url = params.get("url", None)
                    raise SecurityCheckError("Security check is needed, try to visit "
                                             "https://accounts.google.com/b/0/DisplayUnlockCaptcha "
                                             "to unlock, or setup an app-specific password. "
                                             f"Callback URL: {callback_url}")
                raise LoginError("server says: " + params["error"])
            else:
                raise LoginError("Auth token not found.")

            self.gsfId = self.checkin(email, ac2dm_token)
            self.get_auth_sub_token(email, encrypted_pass)
            self.upload_device_config()
            if return_params:
                return self.gsfId, self.auth_sub_token
        elif gsf_id is not None and auth_sub_token is not None:
            # no need to initialize API
            self.gsfId = gsf_id
            self.set_auth_sub_token(auth_sub_token)
            # check if token is valid with a simple search
            # self.search('drv')
        else:
            raise LoginError('Either (email,pass) or (gsfId, authSubToken) is needed')

    def get_auth_sub_token(self, email, passwd):
        request_params = self.device_builder.get_login_params(email, passwd)
        request_params['service'] = 'androidmarket'
        request_params['app'] = 'com.android.vending'
        self.session.headers = {'User-Agent': 'GoogleAuth/1.4', 'device': "{0:x}".format(self.gsfId)}
        response = self.session.post(sc.AUTH_URL, data=request_params, verify=sc.ssl_verify, proxies=self.proxies_config)
        data = response.text.split()
        params = {}
        for d in data:
            if "=" not in d:
                continue
            k, v = d.split("=", 1)
            params[k.strip().lower()] = v.strip()
        if "token" in params:
            master_token = params["token"]
            second_round_token = self.get_second_round_token(master_token, request_params)
            self.set_auth_sub_token(second_round_token)
        elif "error" in params:
            raise LoginError("server says: " + params["error"])
        else:
            raise LoginError("auth token not found.")

    def get_second_round_token(self, first_token, params):
        if self.gsfId is not None:
            params['androidId'] = "{0:x}".format(self.gsfId)
        params['Token'] = first_token
        params['check_email'] = '1'
        params['token_request_options'] = 'CAA4AQ=='
        params['system_partition'] = '1'
        params['_opt_is_called_from_account_manager'] = '1'
        params.pop('Email')
        params.pop('EncryptedPasswd')
        headers = self.device_builder.get_auth_headers(self.gsfId)
        headers['app'] = 'com.android.vending'
        response = self.session.post(sc.AUTH_URL, data=params,  headers=headers, verify=sc.ssl_verify, proxies=self.proxies_config)
        data = response.text.split()
        params = {}
        for d in data:
            if "=" not in d:
                continue
            k, v = d.split("=", 1)
            params[k.strip().lower()] = v.strip()
        if "auth" in params:
            return params["auth"]
        elif "error" in params:
            raise LoginError("server says: " + params["error"])
        else:
            raise LoginError("Auth token not found.")

    def upload_device_config(self):
        """Upload the device configuration of the fake device
        selected in the __init__ methodi to the google account."""

        upload = GooglePlay_pb2.UploadDeviceConfigRequest()
        upload.deviceConfiguration.CopyFrom(self.device_builder.get_device_config())
        headers = self.get_headers(upload_fields=True)
        string_request = upload.SerializeToString()
        response = self.session.post(sc.UPLOAD_URL, data=string_request,
                                     headers=headers,
                                     verify=sc.ssl_verify,
                                     timeout=60,
                                     proxies=self.proxies_config)
        response = GooglePlay_pb2.ResponseWrapper.FromString(response.content)
        try:
            if response.payload.HasField('uploadDeviceConfigResponse'):
                self.device_config_token = response.payload.uploadDeviceConfigResponse
                self.device_config_token = self.device_config_token.uploadDeviceConfigToken
        except ValueError:
            pass

    def get_headers(self, upload_fields=False):
        """Return the default set of request headers, which
        can later be expanded, based on the request type"""

        if upload_fields:
            headers = self.device_builder.get_device_upload_headers()
        else:
            headers = self.device_builder.get_base_headers()
        if self.gsfId is not None:
            headers["X-DFE-Device-Id"] = "{0:x}".format(self.gsfId)
        if self.auth_sub_token is not None:
            headers["Authorization"] = "GoogleLogin auth=%s" % self.auth_sub_token
        if self.device_config_token is not None:
            headers["X-DFE-Device-Config-Token"] = self.device_config_token
        if self.device_checkin_consistency_token is not None:
            headers["X-DFE-Device-Checkin-Consistency-Token"] = self.device_checkin_consistency_token
        if self.dfeCookie is not None:
            headers["X-DFE-Cookie"] = self.dfeCookie
        return headers
