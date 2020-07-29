from datetime import datetime
from time import time
import hashlib
import importlib.util
import os


def epoch_to_date(epoch, ms=True):
    """
    epoch_to_date

    Use this method to convert a UNIX timestamp (AKA Epoch time) in a date object.

    :param epoch: A timestamp expressed in epoch time
    :param ms: An optional flag to define the unit used for the passed epoch timestamp. Support milliseconds (True) or
    second (False)
    :return: The corresponding datetime object
    """

    # noinspection PyUnusedLocal
    timestamp_sec = 0
    if ms:
        timestamp_sec = epoch / 1000
    else:
        timestamp_sec = epoch
    date_obj = datetime.fromtimestamp(timestamp_sec)
    return date_obj


def unix_epoch_now():
    return int(time() * 1000)


def check_sha256(filename, checksum):
    with open(filename, "rb") as f:
        bin_file = f.read()  # read entire file as bytes
        readable_hash = str(hashlib.sha256(bin_file).hexdigest())
        if readable_hash.upper() == str(checksum).upper():
            return True, readable_hash
        else:
            return False, readable_hash


def secure_load_opentrons_module(module_name, file_path, filename, checksum, verify=True):
    """
    secure_load_opentrons_module

    Loads a python module from arbitrary file, provided that the SHA256 checksum of the file matches t

    :param file_path:  the target python file
    :param module_name: the name of the module you want to import from the target python file
    :param checksum: expected sha256 checksum of the file to be imported
    :param verify: a flag to ignore untrusted checksums
    :return: the "module" object from the target file, or None if the checksum verification fails
    """
    requested_path = os.path.join(file_path, filename)
    if os.path.commonprefix((os.path.realpath(requested_path), file_path)) != file_path:
        return None
    trusted, sha256sum = check_sha256(requested_path, checksum)
    if trusted or not verify:
        spec = importlib.util.spec_from_file_location(module_name, requested_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    else:
        print("Untrusted module")
        return None
