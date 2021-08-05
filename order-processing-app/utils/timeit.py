import time
import logging

def time_it(func):
    def timed(*args, **kwargs):
        ts = time.time()
        result = func(*args, **kwargs)
        te = time.time()
        logging.debug(f'Timing {func.__name__} {round((te - ts)*1000,1)} ms')
        return result
    return timed
