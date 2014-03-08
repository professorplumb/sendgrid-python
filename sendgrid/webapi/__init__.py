import json

try:
    import urllib.request as urllib_request
    from urllib.parse import urlencode
    from urllib.error import URLError, HTTPError
except ImportError:  # Python 2
    import urllib2 as urllib_request
    from urllib2 import URLError, HTTPError
    from urllib import urlencode

_SG_USER, _SG_PWD = None, None
DEBUG = True

def set_credentials(username, password):
    global _SG_USER, _SG_PWD
    _SG_USER, _SG_PWD = username, password


class SendGridBase(object):
    """
    Base class for other API classes.  Automatically loads the SendGrid username and password on instantiation.
    """
    _api_baseurl = "https://api.sendgrid.com/api"

    def __init__(self, *args, **kwargs):
        # First look in global variables set by set_credentials
        self.sg_username, self.sg_password = _SG_USER, _SG_PWD

        # then in constructor kwargs
        if self.sg_username is None or self.sg_password is None:
            self.sg_username, self.sg_password = kwargs.pop('SG_USER', None), kwargs.pop('SG_PWD', None)

        super(SendGridBase, self).__init__(*args, **kwargs)

    def call_api(self, relative_url, data, contains_sequence=False):
        relative_url = relative_url if relative_url.startswith('/') else "/{}".format(relative_url)

        data.update(dict(api_user=self.sg_username, api_key=self.sg_password))
        data = urlencode(data, contains_sequence).encode('utf-8')
        req = urllib_request.Request(self._api_baseurl + relative_url, data)
        if DEBUG:
            print "Opening {}?{}".format(req.get_full_url(), req.get_data())
        response = urllib_request.urlopen(req)
        body = response.read()
        if response.getcode() >= 400:
            raise URLError("HTTP {}: {}".format(response.getcode(), ))

        result = json.loads(body)
        try:
            if result.pop('message', None) == 'error':
                raise ValueError("API error at {}: {}".format(relative_url,
                                                              ', '.join(e for e in result.get('errors'))))
        except TypeError:
            # SG returned a list instead of a dict, indicating that there were no errors
            pass

        return result