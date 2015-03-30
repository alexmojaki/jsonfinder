from json import JSONDecoder

__decoder = JSONDecoder()


def jsonfinder(s, decoder=None, json_only=False, predicate=lambda s, e, o: True):
    """
    Return a generator that yields positions of JSON objects within the string s and the parsed results.

    Specifically, every iteration yields a ``(start, end, obj)`` tuple where
    ``s[start:end]`` is either a string containing no JSON objects/arrays (in which case ``obj``
    is ``None``) or consists entirely of a JSON object/array which is parsed into a python object
    contained in ``obj``. For example::

        >>> s = 'true [1,2,3] null'
        >>> for start, end, obj in jsonfinder(s):
        ...     print start, ':', end
        ...     if obj is None:
        ...         print 'String:', repr(s[start:end])
        ...     else:
        ...         print 'List of length', len(obj)
        0 : 5
        String: 'true '
        5 : 12
        List of length 3
        12 : 17
        String: ' null'
        >>> assert len(s) == end

    Note that JSON primitives are ignored if not contained within an object or array.

    Specifying ``json_only=True`` will cause plain strings to be left out of the iteration,
    i.e. ``obj`` will always be a parsed JSON object.

    Otherwise the first and last iterations will always represent strings (i.e. ``obj is None``),
    even if those strings are empty.

    Note that when testing if the current iteration is a string you probably want to write::

        if obj is not None:

    rather than::

        if obj:

    since the latter will pass if obj is an empty dict or list.

    Set ``predicate`` to a function returning True when you want a JSON object to actually be considered JSON and false
    if you want it to be merged with the strings: this is much easier than doing so manually. For example::

        >>> s = 'a list [1, 2] and an object {"a": 3} are here'
        >>> start, end, obj = next(jsonfinder(s))
        >>> s[start:end]
        'a list '
        >>> start, end, obj = next(jsonfinder(s, predicate=lambda s, e, o: isinstance(o, dict)))
        >>> s[start:end]
        'a list [1, 2] and an object '

    The arguments to the predicate are still ``start, end, obj``, just as they would be yielded, except that ``obj``
    is never None in this case.

    A customer JSONDecoder object (see the built in json module) can be passed in with the keyword
    argument ``decoder``.

    :type s: str | unicode
    :type decoder: JSONDecoder
    :rtype: __generator[(int, int, None | dict | list)]
    """

    decoder = decoder or __decoder
    string_start = find_start = 0
    while 1:
        start1 = s.find('{', find_start)
        start2 = s.find('[', find_start)
        if start1 == -1:
            if start2 == -1:
                if not json_only:
                    yield string_start, len(s), None
                return
            else:
                json_start = start2
        else:
            if start2 == -1:
                json_start = start1
            else:
                json_start = min(start1, start2)

        is_json = True
        obj = json_tuple = None

        try:
            obj, end = decoder.raw_decode(s, idx=json_start)
        except ValueError:
            is_json = False

        if is_json:
            json_tuple = (json_start, end, obj)
            if not predicate(*json_tuple):
                is_json = False

        if is_json:
            if not json_only:
                yield string_start, json_start, None
            yield json_tuple
            string_start = find_start = end
        else:
            find_start = json_start + 1


def has_json(s, decoder=None):
    """
    Return whether the given string s contains at least one JSON object/array, e.g.::

        >>> has_json('stuff {"key": "value"} things')
        True
        >>> has_json('stuff only')
        False

    A customer JSONDecoder object (see the built in json module) can be passed in with the keyword
    argument decoder.

    :type s: str | unicode
    :type decoder: JSONDecoder
    :rtype: bool
    """

    for _ in jsonfinder(s, decoder=decoder, json_only=True):
        return True
    return False


def only_json(s, decoder=None):
    """
    Return a single ``(start, end, obj)`` tuple corresponding to a parsed JSON object/array
    if the string s contains exactly one, else raise an exception, e.g.::

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

    A customer JSONDecoder object (see the built in json module) can be passed in with the keyword
    argument decoder.

    :type s: str | unicode
    :type decoder: JSONDecoder
    :rtype: dict | list
    """

    result = None
    for current in jsonfinder(s, decoder=decoder, json_only=True):
        if result is not None:
            raise ValueError("More than one JSON object found in the argument.")
        result = current
    if result is None:
        raise ValueError("No JSON object found in argument.")
    return result


def check_min_elements(obj, num):
    """
    Returns a boolean indicating if ``obj`` has at least ``num`` elements at its leaves when viewed as a tree.
    That is, it iterates recursively over lists and dicts, checking that the ``obj`` has at least ``num`` primitive
    values at the lowest levels. dict keys are not counted. For example::

        >>> obj = {"a": 1, "b": [2, 3]}
        >>> check_min_elements(obj, 4)
        False
        >>> check_min_elements(obj, 3)
        True

    :type num: int
    :return: bool
    """
    return __check_min_elements_helper(obj, num, 0) >= num


def __check_min_elements_helper(obj, num, count):
    values = ()
    if isinstance(obj, list):
        values = obj
    elif isinstance(obj, dict):
        values = obj.itervalues()
    else:
        count += 1

    for val in values:
        count = __check_min_elements_helper(val, num, count)
        if count >= num:
            break

    return count