import time

def getUnixTimestamp():
    """
    Returns the current unix timestamp in milliseconds

    :return: Integer value of current unix timestamp in milliseconds
    :rtype: int
    """
    return int(time.time() * 1000)