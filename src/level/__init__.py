from os.path import dirname, basename, isfile
import glob
modules = glob.glob(dirname(__file__)+"/*.py")
__all__ = []
for f in modules:
    tmp=f.split('/')
    if isfile(f) and not f.endswith('__init__.py') \
            and not (tmp[-1][:-3] == tmp[-2]):
        __all__.append(basename(f)[:-3])
