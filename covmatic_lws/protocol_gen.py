import tkinter as tk
import json
from abc import ABCMeta, abstractmethod
from .args import Args
import os
import re


with open(os.path.join(os.path.dirname(__file__), "templates", "protocol.py")) as f:
    _template = f.read()


class ProtocolArgument(metaclass=ABCMeta):
    @property
    @abstractmethod
    def key(self) -> str:
        pass
    
    @property
    @abstractmethod
    def verbose_name(self) -> str:
        pass
    
    @abstractmethod
    def get(self):
        pass
    
    def check(self) -> bool:
        return True
    
    @property
    def err_msg(self) -> str:
        return "Argument check failed: {}\n{}\nIllegal value: {}".format(self.key, self.verbose_name, self.get())
    
    def check_get(self):
        if self.check():
            return self.get()
        raise ValueError(self.err_msg)


class IntegerArgument(tk.IntVar, ProtocolArgument, metaclass=ABCMeta):
    @property
    def key(self) -> str:
        return self._name


class PositiveArgument(IntegerArgument, metaclass=ABCMeta):
    def check(self) -> bool:
        return self.get() > 0 and super(PositiveArgument, self).check()
    
    @property
    def err_msg(self) -> str:
        return "{}\n{}".format(ProtocolArgument.err_msg.fget(self), "Argument should be positive")


class NumSamples(PositiveArgument):
    @property
    def verbose_name(self) -> str:
        return "Number of Samples"
    
    def __init__(self, *args, **kwargs):
        kwargs["name"] = kwargs.get("name", "num_samples")
        super(NumSamples, self).__init__(*args, **kwargs)


class NumCycles(PositiveArgument):
    @property
    def verbose_name(self) -> str:
        return "Number of Cycles"
    
    def __init__(self, *args, **kwargs):
        kwargs["name"] = kwargs.get("name", "num_cycles")
        super(NumCycles, self).__init__(*args, **kwargs)


class StartAt(tk.StringVar, ProtocolArgument):
    def __init__(self, *args, **kwargs):
        kwargs["name"] = kwargs.get("name", "start_at")
        super(StartAt, self).__init__(*args, **kwargs)
    
    @property
    def key(self) -> str:
        return self._name
    
    def get(self):
        return super(StartAt, self).get() or None
    
    @property
    def verbose_name(self) -> str:
        return "Start at"

class StringListArgument(tk.StringVar, ProtocolArgument):
    @staticmethod
    def getListFromValue(values: str) -> list:
        retlist = None
        if values:
            values = values.replace(",", " ").replace(";", " ")  # all delimiters to whitespaces
            values = " ".join(values.split())  # joining multiple whitespaces
            splitted = values.split(" ")
            retlist = list()
            for s in splitted:
                retlist.append(s.strip())
        return retlist

    def get(self):
        value = super(StringListArgument, self).get() or None
        return self.getListFromValue(value)


class ControlsPosition(StringListArgument):
    def __init__(self, *args, **kwargs):
        kwargs["name"] = kwargs.get("name", "control_well_positions")
        super(ControlsPosition, self).__init__(*args, **kwargs)

    @property
    def key(self) -> str:
        return self._name

    @property
    def verbose_name(self) -> str:
        return "Controls positions"


_classes = {
    "A-24": ("covmatic_stations.a.technogenetics", "StationATechnogenetics24", NumSamples),
    "A": ("covmatic_stations.a.technogenetics", "StationATechnogenetics48", NumSamples),
    "B": ("covmatic_stations.b.technogenetics", "StationBTechnogenetics", NumSamples),
    "C": ("covmatic_stations.c.technogenetics", "StationCTechnogenetics", NumSamples),
    "Elution Removal": ("covmatic_stations.b.technogenetics_short", "StationBTechnogeneticsElutionRemoval", NumSamples, NumCycles),
    "Wash B Removal": ("covmatic_stations.b.technogenetics_short", "StationBTechnogeneticsWashBRemoval", NumSamples, NumCycles),
    "BioerPrep": ("covmatic_stations.bioer.Bioer_full_dw", "BioerPreparationToBioer", NumSamples),
    "BioerPCR": ("covmatic_stations.bioer.Bioer_full_dw", "BioerPreparationToPcr", NumSamples, ControlsPosition)
}


if Args().start_at:
    _classes = {k: (*v, StartAt) for k, v in _classes.items()}


def protocol_gen(cls: str, log_level: str = "INFO", apiLevel='2.7', **prot_kwargs) -> str:
    if cls not in _classes:
        raise KeyError("Class {} is not supported: supported classes are: {}".format(cls, ", ".join(_classes.keys())))
    module, cls = _classes[cls][:2]
    return _template.format(
        copen="{",
        cclose="}",
        module=module,
        cls=cls,
        log_level=log_level,
        apiLevel=apiLevel,
        prot_kwargs=json.dumps(prot_kwargs),
    )


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
