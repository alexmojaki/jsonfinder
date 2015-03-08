``jsonfinder`` lets you find and extract JSON objects and arrays embedded within a string using a simple iterator. For example::

    >>> s = 'jack [1,2,3] john'
    >>> for start, end, obj in jsonfinder(s):
    ...     print start, ':', end
    ...     if obj is None:
    ...         print 'String:', repr(s[start:end])
    ...     else:
    ...         print 'List of length', len(obj)
    0 : 5
    String: 'jack '
    5 : 12
    List of length 3
    12 : 17
    String: ' john'
    >>> assert len(s) == end

Two other convenience methods are also provided: ``has_json`` and ``only_json``::

    >>> has_json('stuff {"key": "value"} things')
    True
    >>> has_json('stuff only')
    False
    >>> only_json('stuff {"key": "value"} things')[2]
    {u'key': u'value'}
    >>> only_json('stuff only')
    Traceback (most recent call last):
    ...
    ValueError: No JSON object found in argument.
    >>> only_json('{}{}')
    Traceback (most recent call last):
    ...
    ValueError: More than one JSON object found in the argument.

All the methods allow a custom JSONDecoder to be passed in for flexibility.

The library also includes a command-line tool to format JSON and filter out parts of the input based on whether JSON is present.
It's like a more flexible version of python's built in ``json.tool``, a ``grep -v`` for JSON, and more. For example::

    $ cat cli_example.txt
    This line contains no JSON and will be deleted by the --delete other-lines option.
    On the other hand {"json":   ["is", "formatted"]  } and text surrounding it is preserved (but can also be removed if desired).
    $ python -m jsonfinder -i cli_example.txt --delete other-lines
    On the other hand {
        "json": [
            "is",
            "formatted"
        ]
    } and text surrounding it is preserved (but can also be removed if desired).
    $ python -m jsonfinder -i cli_example.txt --delete other-lines | python -m jsonfinder --delete context --format tiny
    {"json":["is","formatted"]}

See the ``--help`` option in the command-line for more details.

Installation is as simple as::

    pip install jsonfinder

