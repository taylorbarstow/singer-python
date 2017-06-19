import sys
import json
import os
import logging
import logging.config

from singer import utils
from singer import transform

class Message(object):
    '''Base class for messages.'''

    def __eq__(self, other):
        return isinstance(other, Message) and self.asdict() == other.asdict()

    def __repr__(self):
        pairs = ["{}={}".format(k, v) for k, v in self.asdict().items()]
        attrstr = ", ".join(pairs)
        return "{}({})".format(self.__class__.__name__, attrstr)

    def __str__(self):
        return str(self.asdict)

class RecordMessage(Message):
    '''RECORD message.

    >>> msg = singer.RecordMessage(
    >>>     stream='users',
    >>>     record={'id': 1, 'name': 'Mary'})

    '''

    def __init__(self, stream, record, version=None):
        self.stream = stream
        self.record = record
        self.version = version

    def asdict(self):
        result = {
            'type': 'RECORD',
            'stream': self.stream,
            'record': self.record,
        }
        if self.version is not None:
            result['version'] = self.version
        return result

    def __str__(self):
        return str(self.asdict)

class SchemaMessage(Message):
    '''SCHEMA message.

    >>> msg = singer.SchemaMessage(
    >>>     stream='users',
    >>>     schema={'type': 'object',
    >>>             'properties': {
    >>>                 'id': {'type': 'integer'},
    >>>                 'name': {'type': 'string'}
    >>>             }
    >>>            },
    >>>     key_properties=['id'])

    '''
    def __init__(self, stream, schema, key_properties):
        self.stream = stream
        self.schema = schema
        self.key_properties = key_properties

    def asdict(self):
        return {
            'type': 'SCHEMA',
            'stream': self.stream,
            'schema': self.schema,
            'key_properties': self.key_properties
        }


class StateMessage(Message):
    '''STATE message.

    >>> msg = singer.StateMessage(
    >>>     value={'users': '2017-06-19T00:00:00'})

    '''
    def __init__(self, value):
        self.value = value

    def asdict(self):
        return {
            'type': 'STATE',
            'value': self.value
        }

class ActivateVersionMessage(Message):
    '''ACTIVATE_VERSION message.

    >>> msg = singer.ActivateVersionMessage(
    >>>     stream='users',
    >>>     version=2)

    '''
    def __init__(self, stream, version):
        self.stream = stream
        self.version = version

    def asdict(self):
        return {
            'type': 'ACTIVATE_VERSION',
            'stream': self.stream,
            'version': self.version
        }

def format_message(message):
    return json.dumps(message.asdict())

def write_message(message):
    sys.stdout.write(format_message(message) + '\n')
    sys.stdout.flush()


def write_record(stream_name, record):
    """Write a single record for the given stream.

    >>> write_record("users", {"id": 2, "email": "mike@stitchdata.com"})
    """
    write_message(RecordMessage(stream=stream_name, record=record))


def write_records(stream_name, records):
    """Write a list of records for the given stream.

    >>> chris = {"id": 1, "email": "chris@stitchdata.com"}
    >>> mike = {"id": 2, "email": "mike@stitchdata.com"}
    >>> write_records("users", [chris, mike])
    """
    for record in records:
        write_record(stream_name, record)


def write_schema(stream_name, schema, key_properties):
    """Write a schema message.

    >>> stream = 'test'
    >>> schema = {'properties': {'id': {'type': 'integer'}, 'email': {'type': 'string'}}}  # nopep8
    >>> key_properties = ['id']
    >>> write_schema(stream, schema, key_properties)
    """
    if isinstance(key_properties, (str, bytes)):
        key_properties = [key_properties]
    if not isinstance(key_properties, list):
        raise Exception("key_properties must be a string or list of strings")
    write_message(
        SchemaMessage(
            stream=stream_name,
            schema=schema,
            key_properties=key_properties))


def write_state(value):
    """Write a state message.

    >>> write_state({'last_updated_at': '2017-02-14T09:21:00'})
    """
    write_message(StateMessage(value=value))


def _required_key(msg, k):
    if k not in msg:
        raise Exception("Message is missing required key '{}': {}".format(
            k, msg))
    return msg[k]


def parse_message(msg):
    """Parse a message string into a Message object."""
    obj = json.loads(msg)
    msg_type = _required_key(obj, 'type')

    if msg_type == 'RECORD':
        return RecordMessage(stream=_required_key(obj, 'stream'),
                             record=_required_key(obj, 'record'),
                             version=obj.get('version'))

    elif msg_type == 'SCHEMA':
        return SchemaMessage(stream=_required_key(obj, 'stream'),
                             schema=_required_key(obj, 'schema'),
                             key_properties=_required_key(obj, 'key_properties'))

    elif msg_type == 'STATE':
        return StateMessage(value=_required_key(obj, 'value'))


def get_logger():
    """Return a Logger instance appropriate for using in a Tap or a Target."""
    this_dir, _ = os.path.split(__file__)
    path = os.path.join(this_dir, 'logging.conf')
    logging.config.fileConfig(path)
    return logging.getLogger('root')


if __name__ == "__main__":
    import doctest
    doctest.testmod()
