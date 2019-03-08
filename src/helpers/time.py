import operator
import logging

class Time():
    """
    A Time object stores time data both in [h, m, s] and in sec format.
    It can be initialized with instance=helpers.Time(input), where input
    can either be a scalar or a tuple or list of length 3.
    Its value can be retrieved with time_in_sec = instance.sec() and 
    time_as_list = instance.list(). Mathematical operations can be 
    carried out with an instance of the class and either another
    instance of the class, a scalar or a list / tuple.
    """

    sec_=0.
    list_=[0.,0.,0.]

    def __init__(self,*args):
        if len(args) == 1:
            self.set(args[0])
        elif args:
            raise TypeError("__init__() takes at most one argument. "
                            +"{} given".format(len(args)))

    @property
    def sec(self):
        return(self.sec_)
    @property
    def list(self):
        return(self.list_)
    @property
    def str(self):
        return(":".join(str(i) for i in self.list_))
    def __call__(self):
        return(self.sec_)

    def set(self,*args):
        if len(args) != 1:
            raise TypeError("set() takes exactly one argument. "
                            +"{} given".format(len(args)))
        if self.islist(args[0]):
            self.list_ = list(args[0])
            self.sec_ = 3600*args[0][0] + 60*args[0][1] + args[0][2]
        else:
            self.sec_ = args[0]
            self.list_[0] = int(int(args[0])/3600)
            self.list_[1] = int(int(args[0])/60 - 60*self.list_[0])
            self.list_[2] = int(
                args[0] - 3600*self.list_[0]  - 60*self.list_[1])

    def islist(self, obj):
        if isinstance(obj,(list,tuple)):
            if len(obj) == 3:
                return True
            else:
                raise TypeError("List or tuple has to have length 3, "
                                +"but is {}.".format(len(obj)))
        else:
            return False

    def checkinstance(self, other, op):
        if isinstance(other,Time):
            return Time(op(self.sec_,other.sec_))
        elif self.islist(other):
            return Time([op(a,b) for a,b in zip(self.list_,list(other))])
        else:
            return Time(op(self.sec_,other))

    def __neg__(self):
        return Time(-self.sec_)
    def __add__(self, other):
        return self.checkinstance(other,operator.add)
    def __radd__(self, other):
        return self.checkinstance(other,operator.add)
    def __sub__(self, other):
        return self.checkinstance(other,operator.sub)
    def __rsub__(self, other):
        return -self.checkinstance(other,operator.sub)
    def __mul__(self, other):
        return Time(self.sec_*other)
    def __rmul__(self, other):
        return Time(self.sec_*other)
    def __truediv__(self, other):
        if isinstance(other,Time):
            return self.sec_/other.sec_
        else:
            return Time(self.sec_/other)
    def __floordiv__(self, other):
        if isinstance(other,Time):
            return self.sec_//other.sec_
        else:
            return Time(self.sec_//other)
    def __rdiv__(self, other):
        return float(other.sec_)/self.sec_
    def __pow__(self, other):
        return Time(self.sec_**other)
