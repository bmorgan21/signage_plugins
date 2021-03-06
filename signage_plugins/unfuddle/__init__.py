import os
import requests

from signage_plugins import Plugin


class UnfuddlePlugin(Plugin):
    def __init__(self, subdomain, username, password, project_id, statuses=['new', 'closed'], map_target=None, sort_tickets=None, **kwargs):
        self.subdomain = subdomain
        self.username = username
        self.password = password
        self.project_id = project_id
        self.statuses = statuses
        self.map_target = map_target
        self.sort_tickets = sort_tickets
        Plugin.__init__(self, dirname=os.path.dirname(__file__), **kwargs)

    def init(self):
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.session.headers.update({'Accept': 'application/json'})

        self.people_map = {}
        people = self.session.get('https://{subdomain}.unfuddle.com/api/v1/people'.format(subdomain=self.subdomain))
        for person in people.json():
            first_name_last_initial = person['first_name']
            if person['last_name']:
                first_name_last_initial = '{} {}.'.format(first_name_last_initial, person['last_name'][0])
            self.people_map[person['id']] = first_name_last_initial

    def get_data(self):
        data = []

        milestones = self.session.get('https://{subdomain}.unfuddle.com/api/v1/projects/{project_id}/milestones/upcoming'.format(subdomain=self.subdomain, project_id=self.project_id))
        for milestone in milestones.json():
            tickets = self.session.get('https://{subdomain}.unfuddle.com//api/v1/projects/{project_id}/milestones/{milestone_id}/tickets'.format(subdomain=self.subdomain, project_id=self.project_id, milestone_id=milestone['id']))

            d = {}
            target = 'all.milestone-{}'.format(milestone['id'])
            if self.map_target:
                target = self.map_target(milestone)

            if target is None:
                # no one can see this, so continue
                continue

            for status in self.statuses:
                d[status] = []
            for ticket in tickets.json():
                d[ticket['status']].append(ticket)

            result = []
            for status in self.statuses:
                if self.sort_tickets:
                    tickets = sorted(d[status], self.sort_tickets)
                else:
                    tickets = sorted(d[status], lambda x, y: cmp(y['priority'], x['priority']))
                result.append((status, tickets))

            data.append({'milestone': milestone, 'people_map': self.people_map, 'data': result, 'target': target})

        return data
