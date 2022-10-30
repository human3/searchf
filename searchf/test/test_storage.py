'''Unit tests for storage'''

from .. import storage


def test_store():
    '''Test store'''
    store = storage.Store('.searchf.test')
    store.destroy()
    assert not store.can_load()

    # Check we can save and then load
    slot_id = store.save({'text': 'My object 1'})
    assert store.can_load()
    assert slot_id == 0

    # Check we load expected object
    obj, slot_id2 = store.load(False)
    assert slot_id == slot_id2
    assert obj['text'] == 'My object 1'

    # Check we can delete
    slot_id3 = store.delete()
    assert slot_id == slot_id3

    # Check we cannot delete when we have no current slot
    assert not store.delete()

    # Save a new object
    slot_id = store.save({'text': 'My object 2'})
    assert slot_id == 0

    # Create a brand new store and check we can load
    store = storage.Store('.searchf.test')
    assert store.can_load()
    obj, slot_id = store.load(False)
    assert slot_id == 0
    assert obj['text'] == 'My object 2'

    # Check destroying
    store.destroy()
