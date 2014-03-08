from __future__ import unicode_literals
import json

from sendgrid.webapi import SendGridBase, HTTPError, DEBUG


class ListManager(SendGridBase):
    api_url = "/newsletter/lists/{}.json"

    def all(self):
        return self.get(None)

    def get(self, name):
        all_lists = name is None
        data = {}
        if not all_lists:
            data = {'list': name, }

        results = []
        try:
            results = self.call_api(self.api_url.format('get'), data)
        except HTTPError as e:
            if e.code == 401:
                return None  # list didn't exist; SG returns 401 Unauthorized in this case
            raise e

        if len(results) == 0:
            return None
        elif len(results) == 1 and name == results[0]['list']:
            return List(name=results[0]['list'], manager=self)
        else:
            return [List(name=result['list'], manager=self) for result in results]

    def create(self, name):
        # will raise an error if list already exists
        result = self.call_api(self.api_url.format('add'), {'list': name, })

        return List(**result)

    def get_or_create(self, name):
        l = self.get(name)
        if l is None:
            l = self.create(name)

        return l

    def save(self, list_obj):
        self.call_api(self.api_url.format('edit'), {'list': list_obj._base_name, 'newlist': list_obj.name, })

    def delete(self, list_obj):
        self.call_api(self.api_url.format('delete'), {'list': list_obj._base_name, })


class List(SendGridBase):
    api_url = "/newsletter/lists/email/{}.json"

    def __init__(self, name, manager, *args, **kwargs):
        self.name = self._base_name = name
        self.manager = manager
        if not self.manager or not isinstance(self.manager, ListManager):
            raise ValueError("Use ListManager to get List instances.")
        self.sg_username = self.manager.sg_username
        self.sg_password = self.manager.sg_password

        super(List, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return "List: {}".format(self.name)

    def __repr__(self):
        return self.__unicode__()

    def save(self):
        self.manager.save(self)

    def delete(self):
        self.manager.delete(self)

    def get_emails(self, *emails):
        data = {'list': self.name, }
        if emails:
            data['email'] = emails
        return self.call_api(self.api_url.format('get'), data,
                             contains_sequence=isinstance(emails, list))

    def add_emails(self, *emails):
        """
        Unlike get_emails and remove_emails, the arguments to this function should be dictionaries.

        Each has two required keys: 'email' and 'name'.  Addition of a dict without both will fail silently.
        """
        emails = [json.dumps(i) if isinstance(i, dict) else json.dumps({'email': i}) for i in emails]

        result = self.call_api(self.api_url.format('add'), {'list': self.name, 'data': emails, },
                               contains_sequence=True)

        if DEBUG:
            print "Added {} emails".format(result['inserted'])

        return result['inserted']

    def remove_emails(self, *emails):
        emails = [i if isinstance(i, str) else i['email'] for i in emails]

        result = self.call_api(self.api_url.format('delete'), {'list': self.name, 'email': emails, },
                               contains_sequence=True)

        if DEBUG:
            print "Removed {} emails".format(result['removed'])

        return result['removed']
