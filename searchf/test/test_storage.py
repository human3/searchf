'''Unit tests for storage'''

# pylint: disable=too-few-public-methods

from .. import storage

class MyObject:
    '''Dummy oject to store'''
    some_text: str

    def __init__(self, text: str):
        self.some_text = text

def test_store():
    '''Test store'''
    store = storage.Store('.searchf.test')
    assert not store.can_load()
    path = store.save(MyObject('My object 1'))
    assert path
    obj, path2 = store.load(False)
    assert obj.some_text == 'My object 1'
    assert path == path2
    path3 = store.delete()
    assert path == path3
    assert not store.delete()
    path = store.save(MyObject('My object 2'))
    store.destroy()
