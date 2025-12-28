'''Unit tests for storage'''

import dataclasses
import json

from .. import enums
from .. import storage
from .. import models

@dataclasses.dataclass
class Dummy():
    object: any = None


def test_store():
    '''Test store'''
    store = storage.Store('.searchf.test')
    store.destroy()
    assert not store.can_load()

    # Check we can save and then load
    slot_id = store.save(Dummy({'text': 'My object 1'}))
    assert store.can_load()
    assert slot_id == 0

    # Check we load expected object
    obj, slot_id2 = store.load(False)
    assert slot_id == slot_id2
    assert obj['object']['text'] == 'My object 1'

    # Check we can delete
    slot_id3 = store.delete()
    assert slot_id == slot_id3

    # Check we cannot delete when we have no current slot
    assert not store.delete()

    # Save a new object
    slot_id = store.save(Dummy({'text': 'My object 2'}))
    assert slot_id == 0

    # Create a brand new store and check we can load
    store = storage.Store('.searchf.test')
    assert store.can_load()
    obj, slot_id = store.load(False)
    assert slot_id == 0
    assert obj['object']['text'] == 'My object 2'

    # Check destroying
    store.destroy()


# # Capture the original error-raising function
# original_error = yaml.representer.SafeRepresenter.represent_undefined

# def debug_representer(self, data):
#     print(f"DEBUG: Attempting to represent type: {type(data)}")
#     print(f"DEBUG: Data value: {data}")
#     return original_error(self, data)

# # Apply the patch
# yaml.representer.SafeRepresenter.represent_undefined = debug_representer

# def clean_for_yaml(data):
#     # Round-trip through JSON to strip non-standard types
#     # (like Path, NumPy types, or custom objects)
#     return json.loads(json.dumps(data, default=str))

def test_model_persists():
    '''Test model persists'''
    print('test_model_persists')

    store = storage.Store('.searchf.test')
    store.destroy()
    f = models.Filter()
    slot_id = store.save(f)
    print(f'models.Filter: {slot_id}')
    f2 = store.load(models.Filter, True)
    print(f'loaded {f2}')

    vc = models.ViewConfig()
    vc.line_visibility = enums.LineVisibility.CONTEXT_1
    vc.colorize_mode = enums.ColorizeMode.LINE
    slot_id = store.save(vc)
    print(f'models.ViewConfig: {slot_id}')
    vc2 = store.load(models.ViewConfig, True)
    print(f'loaded {vc2}')
    assert vc.line_visibility == enums.LineVisibility.CONTEXT_1
    assert vc.colorize_mode == enums.ColorizeMode.LINE

    vc = models.ViewConfig()
    vc.line_visibility = enums.LineVisibility.CONTEXT_1
    vc.colorize_mode = enums.ColorizeMode.LINE
    f = models.Filter()
    f.add('something')
    vc.filters.append(f)
    f = models.Filter()
    f.add('bad')
    vc.filters.append(f)
    slot_id = store.save(vc)
    print(f'models.ViewConfig: {slot_id}')
    vc2 = store.load(models.ViewConfig, True)
    vc2 = store.load(models.ViewConfig, True)
    print(f'loaded {vc2}')
    assert vc.line_visibility == enums.LineVisibility.CONTEXT_1
    assert vc.colorize_mode == enums.ColorizeMode.LINE

# test_store()
test_model_persists()

