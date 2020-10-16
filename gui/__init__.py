from api.utils import SingletonMeta
import argparse


class Args(argparse.Namespace, metaclass=SingletonMeta):
    pass


_kill_app: bool = True
