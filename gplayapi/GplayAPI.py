from requests.utils import requote_uri

from gplayapi import GooglePlay_pb2
from gplayapi.Error import LoginError, RequestError
from gplayapi.GoogleAuth import GoogleAuthAPI, sc
from gplayapi.Helper import has_tos_token, parse_protobuf_obj, has_tos_content, has_cookie, has_doc, has_prefetch


class GplayAPI:
    def __init__(self, google_auth_context: GoogleAuthAPI):
        self.google_auth_context = google_auth_context
        self.auth_sub_token = self.google_auth_context.auth_sub_token
        self.proxies_config = self.google_auth_context.proxies_config
        self.dfeCookie = self.google_auth_context.dfeCookie

    def __get_headers__(self):
        return self.google_auth_context.get_headers()

    def __get_session__(self):
        return self.google_auth_context.session

    def __execute_request_api__(self, path, post_data=None, content_type=sc.CONTENT_TYPE_URLENC, params=None):
        if self.auth_sub_token is None:
            raise LoginError("You need to login before executing any request")
        headers = self.__get_headers__()
        headers["Content-Type"] = content_type

        if post_data is not None:
            response = self.__get_session__().post(path,
                                                   data=str(post_data),
                                                   headers=headers,
                                                   params=params,
                                                   verify=sc.ssl_verify,
                                                   timeout=60,
                                                   proxies=self.proxies_config)
        else:
            response = self.__get_session__().get(path,
                                                  headers=headers,
                                                  params=params,
                                                  verify=sc.ssl_verify,
                                                  timeout=60,
                                                  proxies=self.proxies_config)

        message = GooglePlay_pb2.ResponseWrapper.FromString(response.content)
        if message.commands.displayErrorMessage != "":
            raise RequestError(message.commands.displayErrorMessage)

        return message

    def __toc__(self):
        '''
        Table Of Contents
        :return:
        '''
        response = self.__get_session__().get(sc.TOC_URL,
                                              headers=self.__get_headers__(),
                                              verify=sc.ssl_verify,
                                              timeout=60,
                                              proxies=self.proxies_config)
        data = GooglePlay_pb2.ResponseWrapper.FromString(response.content)
        toc_response = data.payload.tocResponse
        if has_tos_content(toc_response) and has_tos_token(toc_response):
            self.__accept_tos__(toc_response.tosToken)
        if has_cookie(toc_response):
            self.dfeCookie = toc_response.cookie
        return parse_protobuf_obj(toc_response)

    def __accept_tos__(self, tos_token):
        '''
        accept action Team of Service
        :param tos_token:
        :return:
        '''
        params = {
            "tost": tos_token,
            "toscme": "false"
        }
        response = self.__get_session__().get(sc.ACCEPT_TOS_URL,
                                              headers=self.__get_headers__(),
                                              params=params,
                                              verify=sc.ssl_verify,
                                              timeout=60,
                                              proxies=self.proxies_config)
        data = GooglePlay_pb2.ResponseWrapper.FromString(response.content)
        return parse_protobuf_obj(data.payload.acceptTosResponse)

    def search(self, query):
        """ Search the play store for an app.

        nb_result (int): is the maximum number of result to be returned

        offset (int): is used to take result starting from an index.
        """
        if self.auth_sub_token is None:
            raise LoginError("You need to login before executing any request")

        path = sc.SEARCH_URL + "?c=3&q={}".format(requote_uri(query))
        # FIXME: not sure if this toc call should be here
        self.__toc__()
        data = self.__execute_request_api__(path)
        if has_prefetch(data):
            response = data.preFetch[0].response
        else:
            response = data
        res_iterator = response.payload.listResponse.doc
        return list(map(parse_protobuf_obj, res_iterator))

    def list_ranks(self, ctr, cat=None, next_page_url=None):
        """
        List top ranks for the given category and rank list.
        Args:
          cat (str) - Category ID.
          ctr (str) - Rank list ID.
          next_page_url (str) - Next page url for subsequent self.session.
        Returns:
          (a list of apps, next page url)
        """
        if next_page_url:
            path = sc.FDFE + next_page_url
            path += "&stcid={}".format(requote_uri(ctr))
        else:
            # path = sc.LIST_TEST_URL + "?c=3&n=7"
            path = sc.LIST_TEST_URL + "?c=3"
            path += "&stcid={}".format(requote_uri(ctr))
            if cat is not None:
                path += "&scat={}".format(requote_uri(cat))

        data = self.__execute_request_api__(path)
        apps = []
        for d in data.payload.listResponse.doc:  # categories
            for c in d.child:  # sub-category
                for a in c.child:  # app
                    apps.append(parse_protobuf_obj(a))
        try:
            # Sometimes we get transient very short response which indicates there's no more data
            next_page_url = data.payload.listResponse.doc[0].child[0].containerMetadata.nextPageUrl
        except Exception:
            return apps, ""

        return apps, next_page_url

    def details(self, package_name, version_code=False):
        """Get app details from a package name.

        packageName (str) is the app unique ID (usually starting with 'com.').
        versionCode (int) is the version code desired."""
        if version_code:
            path = sc.DETAILS_URL + "?doc={}&vc={}".format(requote_uri(package_name), requote_uri(str(version_code)))
        else:
            path = sc.DETAILS_URL + "?doc={}".format(requote_uri(package_name))
        data = self.__execute_request_api__(path)
        return parse_protobuf_obj(data.payload.detailsResponse.docV2)

    def bulk_details(self, package_names):
        """Get several apps details from a list of package names.

        This is much more efficient than calling N times details() since it
        requires only one request. If an item is not found it returns an empty object
        instead of throwing a RequestError('Item not found') like the details() function

        Args:
            package_names (list): a list of app IDs (usually starting with 'com.').

        Returns:
            a list of dictionaries containing docv2 data, or None
            if the app doesn't exist"""

        params = {'au': '1'}
        req = GooglePlay_pb2.BulkDetailsRequest()
        req.docid.extend(package_names)
        data = req.SerializeToString()
        message = self.__execute_request_api__(sc.BULK_URL,
                                               post_data=data.decode("utf-8"),
                                               content_type=sc.CONTENT_TYPE_PROTO,
                                               params=params)
        response = message.payload.bulkDetailsResponse
        return [None if not has_doc(entry) else
                parse_protobuf_obj(entry.doc)
                for entry in response.entry]

    def home(self, cat=None):
        path = sc.HOME_URL + "?c=3&nocache_isui=true"
        if cat is not None:
            path += "&cat={}".format(cat)
        data = self.__execute_request_api__(path)
        if has_prefetch(data):
            response = data.preFetch[0].response
        else:
            response = data
        res_iterator = response.payload.listResponse.doc
        return list(map(parse_protobuf_obj, res_iterator))

    def browse(self, cat=None, sub_cat=None):
        """Browse categories. If neither cat nor subcat are specified,
        return a list of categories, otherwise it return a list of apps
        using cat (category ID) and subCat (subcategory ID) as filters."""
        path = sc.BROWSE_URL + "?c=3"
        if cat is not None:
            path += "&cat={}".format(requote_uri(cat))
        if sub_cat is not None:
            path += "&ctr={}".format(requote_uri(sub_cat))
        data = self.__execute_request_api__(path)

        return parse_protobuf_obj(data.payload.browseResponse)
