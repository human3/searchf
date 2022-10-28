'''Implement persistent storage of any objects.'''

import os
import pathlib
import pickle

from typing import Optional

class Store:
    '''Implement storage of objects'''
    def _scan(self):
        self._files = sorted(self._base_dir.rglob('*.pickle'))
        self._next_load = len(self._files) - 1
        self._loaded = -1
        if len(self._files) <= 0:
            self._next_save = 0
        else:
            self._next_save = max(int(p.name[:-len('.pickle')]) for p in self._files) + 1

    def __init__(self, base_dir: str):
        self._base_dir = pathlib.Path(base_dir)
        self._files = []
        self._next_load = -1
        self._loaded = -1
        self._current = None
        self._scan()

    def destroy(self) -> None:
        '''Destroy all data in storage'''
        for path in self._files:
            path.unlink()
        if self._base_dir.exists():
            self._base_dir.rmdir()

    def save(self, obj) -> pathlib.Path:
        '''Saves the given object in a new slot'''
        self._base_dir.mkdir(parents=True, exist_ok=True)
        idx = self._next_save #len(self._files)
        path = self._base_dir.joinpath(f'{idx:03}.pickle')
        with path.open("wb") as fout:
            pickle.dump(obj, fout)
        self._scan()
        return path

    def delete(self) -> Optional[pathlib.Path]:
        '''Deletes the object that was last loaded'''
        if self._loaded < 0:
            return None
        path = self._files[self._loaded]
        os.remove(path)
        self._scan()
        return path

    def can_load(self) -> bool:
        '''Returns whether we have anything to load'''
        return len(self._files) > 0

    def load(self, goto_next: bool):
        '''Loads the next or previous object'''
        count = len(self._files)
        assert count > 0
        inc = -1 if goto_next else 1
        self._next_load = (self._next_load + inc) % count
        path = self._files[self._next_load]
        with path.open("rb") as fin:
            self._loaded = self._next_load
            return pickle.load(fin), path
