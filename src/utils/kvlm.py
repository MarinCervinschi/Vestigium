from typing import Optional


def kvlm_parse(raw: bytes, start: int = 0, dct: Optional[dict] = None) -> dict:
    """
    Parse KVLM (Key-Value List with Message) format used in Git objects.

    The KVLM format consists of:
    - Key-value pairs separated by spaces
    - Continuation lines that start with a space
    - A final message after a blank line (stored with key None)

    Args:
        raw (bytes): The raw data to parse
        start (int): Starting position in the byte array (default: 0)
        dct (Optional[dict]): Existing dictionary to populate (default: None)

    Returns:
        dict: Dictionary containing key-value pairs and the final message.
              Duplicate keys are stored as lists.
              The final message is stored with key None.

    Example:
        >>> data = b"author John Doe\ncommitter Jane Smith\n\nCommit message"
        >>> result = kvlm_parse(data)
        >>> result[b'author']
        b'John Doe'
        >>> result[None]
        b'Commit message'
    """
    if not dct:
        dct = dict()

    spc = raw.find(b" ", start)
    nl = raw.find(b"\n", start)

    # Base case: if newline comes before space (or there's no space),
    # the rest of the content is the final message
    if (spc < 0) or (nl < spc):
        assert nl == start
        dct[None] = raw[start + 1 :]
        return dct

    # Recursive case: extract a key-value pair
    key = raw[start:spc]

    # Find the end of the value handling continuation lines
    end = start
    while True:
        end = raw.find(b"\n", end + 1)
        if raw[end + 1] != ord(" "):
            break

    # Extract the value removing leading spaces from continuation lines
    value = raw[spc + 1 : end].replace(b"\n ", b"\n")

    # Handle duplicate keys by creating lists
    if key in dct:
        if type(dct[key]) == list:
            dct[key].append(value)
        else:
            dct[key] = [dct[key], value]
    else:
        dct[key] = value

    return kvlm_parse(raw, start=end + 1, dct=dct)


def kvlm_serialize(kvlm: dict) -> bytes:
    """
    Serialize a KVLM dictionary back to bytes format.

    Converts a dictionary containing key-value pairs and a message back to the
    KVLM (Key-Value List with Message) format used in Git objects. This is the
    inverse operation of kvlm_parse().

    Args:
        kvlm (dict): Dictionary containing key-value pairs and message.
                     The message should be stored with key None.
                     Values can be bytes or lists of bytes for duplicate keys.

    Returns:
        bytes: Serialized KVLM data in the format:
               - Key-value pairs as "key value\n"
               - Continuation lines with leading spaces
               - Blank line followed by the message

    Example:
        >>> kvlm_dict = {
        ...     b'author': b'John Doe',
        ...     b'committer': b'Jane Smith',
        ...     None: b'Commit message'
        ... }
        >>> result = kvlm_serialize(kvlm_dict)
        >>> result
        b'author John Doe\ncommitter Jane Smith\n\nCommit message'
    """

    ret = b""

    for k in kvlm.keys():
        # Skip the message itself
        if k == None:
            continue
        val = kvlm[k]
        # Normalize to a list to handle duplicate keys
        if type(val) != list:
            val = [val]

        for v in val:
            # Add spaces after newlines for continuation lines
            ret += k + b" " + (v.replace(b"\n", b"\n ")) + b"\n"

    # Append blank line and message
    ret += b"\n" + kvlm[None]

    return ret
