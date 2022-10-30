'''Implement persistent storage of any objects.'''

import os
import pathlib
import pickle

from typing import Optional

SUFFIX = '.pickle'

SlotId = int


def _slot_id_to_prefix(idx: SlotId) -> str:
    return f'{idx:03}'


class Store:
    '''Implement storage of objects into "slots" that are just numbered
    files on the disk. This class keeps track of a "current" slot,
    which is updated when slots are loaded, saved and deleted.

    - Objects are always saved into a new slot, and this new slot
      becomes the current one.
    - Only current slot can be deleted, and there is no current slot
      anymore after the delete operation.
    - Load operations makes the loaded slot the current one.
    '''
    def _scan(self):
        self._files = sorted(self._base_dir.rglob(f'*{SUFFIX}'))
        self._slot_ids = [int(f.name[:-len(SUFFIX)]) for f in self._files]
        assert len(self._files) == len(self._slot_ids)
        # We need to compute the next available slot id that we
        # can use to save an object. Since slots can be deleted,
        # we find the max SlotId currently used and just add 1, or
        # start at 0 if no slot is in used.
        if len(self._slot_ids) <= 0:
            self._next_slot_id = 0
        else:
            self._next_slot_id = max(self._slot_ids) + 1

    def __init__(self, base_dir: str):
        self._base_dir = pathlib.Path(base_dir)
        self._files = []
        self._slot_ids = []
        self._cur_idx = -1
        self._scan()

    def destroy(self) -> None:
        '''Destroy all slots and data in storage'''
        for path in self._files:
            path.unlink()
        if self._base_dir.exists():
            self._base_dir.rmdir()
        self._scan()

    def save(self, obj) -> SlotId:
        '''Saves the given object in a new slot'''
        self._base_dir.mkdir(parents=True, exist_ok=True)
        saved = self._next_slot_id
        prefix = _slot_id_to_prefix(saved)
        path = self._base_dir.joinpath(f'{prefix}{SUFFIX}')
        with path.open("wb") as fout:
            pickle.dump(obj, fout)
        self._scan()
        count = len(self._files)
        assert count > 0
        # Saving an object makes the slot it was saved into the
        # current one. Since we always save in the max slot id, which
        # should always be associated with the last index
        self._cur_idx = count - 1
        return saved

    def delete(self) -> Optional[SlotId]:
        '''Deletes the current slot'''
        index_to_delete = self._cur_idx
        if index_to_delete < 0:
            return None
        slot_id = self._slot_ids[index_to_delete]
        os.remove(self._files[index_to_delete])
        self._scan()
        self._cur_idx = -1
        return slot_id

    def can_load(self) -> bool:
        '''Returns whether we have anything to load'''
        return len(self._files) > 0

    def load(self, goto_next: bool):
        '''Loads the next or previous object'''
        count = len(self._files)
        assert count > 0
        inc = 1 if goto_next else -1
        if self._cur_idx < 0:
            self._cur_idx = count - 1 if goto_next else 0
        self._cur_idx = (self._cur_idx + inc) % count
        path = self._files[self._cur_idx]
        slot_id = self._slot_ids[self._cur_idx]
        with path.open("rb") as fin:
            return pickle.load(fin), slot_id
