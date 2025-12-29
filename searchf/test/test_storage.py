'''Unit tests for storage'''

import pydantic

from .. import enums
from .. import storage
from .. import models


class Dummy(pydantic.BaseModel):
    '''Dummy class for tests'''
    a_int: int = 0
    a_bool: bool = False
    a_str: str = ''

    def setup(self, _int: int, _bool: bool, _str: str):
        '''Pseudo init function'''
        self.a_int = _int
        self.a_bool = _bool
        self.a_str = _str


def test_store():
    '''Test store'''
    store = storage.Store('.searchf.test')
    store.destroy()
    assert not store.can_load()

    # Check we can save and then load
    o1 = Dummy()
    o1.setup(123, True, "o1")
    slot_id = store.save(o1)
    assert store.can_load()
    assert slot_id == 0

    # Check we load expected object
    obj, slot_id1 = store.load(Dummy, True)
    assert slot_id == slot_id1
    assert obj == o1

    # Check we can delete
    slot_id2 = store.delete()
    assert slot_id == slot_id2

    # Check we cannot delete when we have no current slot
    assert not store.delete()

    # Save a new object
    o2 = Dummy()
    o2.setup(123, True, "o2")

    slot_id = store.save(o2)
    assert slot_id == 0

    # Create a brand new store and check we can load
    store = storage.Store('.searchf.test')
    assert store.can_load()
    obj, slot_id = store.load(Dummy, False)
    assert slot_id == 0
    assert obj == o2

    # Check destroying
    store.destroy()


def test_model_persists():
    '''Test model persists'''

    store = storage.Store('.searchf.test')
    store.destroy()
    assert not store.can_load()

    f = models.Filter()
    store.save(f)
    f2 = store.load(models.Filter, True)
    assert f == f2, f'{f} {f2}'

    vc = models.ViewConfig()
    vc.line_visibility = enums.LineVisibility.CONTEXT_1
    vc.colorize_mode = enums.ColorizeMode.LINE
    store.save(vc)
    vc2 = store.load(models.ViewConfig, True)
    assert vc2 == vc

    vc = models.ViewConfig()
    vc.line_visibility = enums.LineVisibility.CONTEXT_1
    vc.colorize_mode = enums.ColorizeMode.LINE
    f = models.Filter()
    f.add('something')
    vc.filters.append(f)
    f = models.Filter()
    f.add('bad')
    vc.filters.append(f)
    store.save(vc)
    vc2 = store.load(models.ViewConfig, True)
    assert vc == vc2
    vc2 = store.load(models.ViewConfig, True)


test_store()
test_model_persists()
