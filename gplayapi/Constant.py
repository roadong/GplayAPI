def space_constants():
    def set_attr(self, name, value):
        if hasattr(self, name):
            raise AttributeError(
                "Cannot reassign members"
            )
        self.__dict__[name] = value
    cls = type('SpaceConstants', (), {
        '__setattr__': set_attr
    })
    return cls()


sc = space_constants()

sc.DFE_TARGETS = "CAEScFfqlIEG6gUYogFWrAISK1WDAg+hAZoCDgIU1gYEOIACFkLMAeQBnASLATlASUuyAyqCAjY5igOMBQzfA/IClwFbApUC4ANbtgKVAS7OAX8YswHFBhgDwAOPAmGEBt4OfKkB5weSB5AFASkiN68akgMaxAMSAQEBA9kBO7UBFE1KVwIDBGs3go6BBgEBAgMECQgJAQIEAQMEAQMBBQEBBAUEFQYCBgUEAwMBDwIBAgOrARwBEwMEAg0mrwESfTEcAQEKG4EBMxghChMBDwYGASI3hAEODEwXCVh/EREZA4sBYwEdFAgIIwkQcGQRDzQ2fTC2AjfVAQIBAYoBGRg2FhYFBwEqNzACJShzFFblAo0CFxpFNBzaAd0DHjIRI4sBJZcBPdwBCQGhAUd2A7kBLBVPngEECHl0UEUMtQETigHMAgUFCc0BBUUlTywdHDgBiAJ+vgKhAU0uAcYCAWQ/5ALUAw1UwQHUBpIBCdQDhgL4AY4CBQICjARbGFBGWzA1CAEMOQH+BRAOCAZywAIDyQZ2MgM3BxsoAgUEBwcHFia3AgcGTBwHBYwBAlcBggFxSGgIrAEEBw4QEqUCASsWadsHCgUCBQMD7QICA3tXCUw7ugJZAwGyAUwpIwM5AwkDBQMJA5sBCw8BNxBVVBwVKhebARkBAwsQEAgEAhESAgQJEBCZATMdzgEBBwG8AQQYKSMUkAEDAwY/CTs4/wEaAUt1AwEDAQUBAgIEAwYEDx1dB2wGeBFgTQ"
sc.GOOGLE_PUBKEY = "AAAAgMom/1a/v0lblO2Ubrt60J2gcuXSljGFQXgcyZWveWLEwo6prwgi3iJIZdodyhKZQrNWp5nKJ3srRXcUW+F1BD3baEVGcmEgqaLZUNBjm057pKRI16kB0YppeGx5qIQ5QjKzsR8ETQbKLNWgRY0QRNVz34kMJR3P/LgHax/6rmf5AAAAAwEAAQ=="
sc.ACCOUNT = "HOSTED_OR_GOOGLE"

sc.ssl_verify = True
sc.BASE = "https://android.clients.google.com/"
sc.PLAYSTORE_BASE = "https://play-fe.googleapis.com/"
sc.PLAYSTORE_FDFE = sc.PLAYSTORE_BASE + "fdfe/"
sc.FDFE = sc.BASE + "fdfe/"
sc.AUTH_URL = sc.BASE + "auth"
sc.CHECKIN_URL = sc.BASE + "checkin"
sc.SEARCH_URL = sc.FDFE + "search"
sc.UPLOAD_URL = sc.FDFE + "uploadDeviceConfig"
sc.TOC_URL = sc.FDFE + "toc"
sc.ACCEPT_TOS_URL = sc.FDFE + "acceptTos"
sc.LIST_TEST_URL = sc.PLAYSTORE_FDFE + "listTopChartItems"
sc.LIST_TEST_V2_URL = sc.PLAYSTORE_FDFE + "browseTopCharts"
sc.CONTENT_TYPE_URLENC = "application/x-www-form-urlencoded; charset=UTF-8"
sc.CONTENT_TYPE_PROTO = "application/x-protobuf"

# https://play-fe.googleapis.com/fdfe/browseTopCharts?c=3&cat=GAME&scat=GAME&stcid=apps_topselling_paid&ups=true
