class Entry:
    def __init__(self):
        self.changes_save_state = True
        self.undo_func = None
        self.redo_func = None

        # This function is provided in case the entry points to data not managed by python
        # E.g. audio clips managed by the engine
        self.destroy_func = None

    def destroy(self):
        if self.destroy_func is not None:
            self.destroy_func()

class HistoryManager:
    def __init__(self):
        # This tracks the number of save state changing actions that have been performed.
        # Actions which cause save state changes increment/decrement this on do/redo and undo, respectively.
        # We can know whether we have unsaved changes by comparing the current change index with the last saved change index.
        self._current_change_index = 0
        self._saved_change_index = 0

        self._undo_stack = []
        self._redo_stack = []

        self._entry_active = False

    def destroy(self):
        for entry in self._redo_stack:
            entry.destroy()
        while len(self._undo_stack) > 0:
            self._undo_stack.pop().destroy()

    def add_entry(self, entry):
        assert not self._entry_active

        for entry in self._redo_stack:
            entry.destroy()
        self._redo_stack.clear()

        # If our last saved change index is in the redo stack, we'll never be able to reach it again
        if self._saved_change_index is not None and self._saved_change_index > self._current_change_index:
            self._saved_change_index = None

        self._undo_stack.append(entry)
        if entry.changes_save_state:
            self._current_change_index += 1

    def has_unsaved_changes(self):
        return self._saved_change_index != self._current_change_index

    def save(self):
        self._saved_change_index = self._current_change_index

    def clear_save_state(self):
        self._saved_change_index = None

    def can_undo(self):
        return len(self._undo_stack) > 0

    def can_redo(self):
        return len(self._redo_stack) > 0

    def undo(self):
        try:
            assert not self._entry_active
            self._entry_active = True
            entry = self._undo_stack.pop()
            self._redo_stack.append(entry)
            entry.undo_func()
            if entry.changes_save_state:
                self._current_change_index -= 1
        finally:
            self._entry_active = False

    def redo(self):
        try:
            assert not self._entry_active
            self._entry_active = True
            entry = self._redo_stack.pop()
            self._undo_stack.append(entry)
            entry.redo_func()
            if entry.changes_save_state:
                self._current_change_index += 1
        finally:
            self._entry_active = False
