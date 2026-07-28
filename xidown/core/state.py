import json
import os
import threading
from typing import List, Dict, Any, Optional, Tuple
from xidown.core.config import HISTORY_FILE

class AppStateManager:
    """Thread-safe application state manager for scan items and undo/redo stacks."""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._scan_data: List[Dict[str, Any]] = []
        self._undo_stack: List[Dict[str, Any]] = []
        self._redo_stack: List[Dict[str, Any]] = []

    def get_items(self) -> List[Dict[str, Any]]:
        """Return a shallow copy of scan_data items."""
        with self._lock:
            return list(self._scan_data)

    def set_items(self, items: List[Dict[str, Any]]) -> None:
        """Replace all scan_data items safely."""
        with self._lock:
            self._scan_data = list(items)

    def add_item(self, item: Dict[str, Any]) -> bool:
        """
        Add item if it is not a duplicate url_dl.
        Returns True if added, False if duplicate.
        """
        with self._lock:
            url_dl = item.get('url_dl')
            if any(existing.get('url_dl') == url_dl for existing in self._scan_data):
                return False
            self._scan_data.append(item)
            return True

    def remove_item(self, item: Dict[str, Any], is_redo: bool = False) -> bool:
        """Remove a single item and push to undo stack."""
        with self._lock:
            if item in self._scan_data:
                if not is_redo:
                    self._redo_stack.clear()
                self._undo_stack.append({'type': 'single', 'data': dict(item)})
                self._scan_data.remove(item)
                return True
            return False

    def batch_delete(self) -> List[Dict[str, Any]]:
        """Remove all selected items and return the deleted items list."""
        with self._lock:
            to_delete = [d for d in self._scan_data if d.get('selected', False)]
            if not to_delete:
                return []
            
            self._undo_stack.append({'type': 'batch', 'data': to_delete})
            self._redo_stack.clear()
            self._scan_data = [d for d in self._scan_data if not d.get('selected', False)]
            return to_delete

    def clear_unlocked(self) -> List[Dict[str, Any]]:
        """Clear all non-locked items and return deleted items."""
        with self._lock:
            to_delete = [d for d in self._scan_data if not d.get('locked', False)]
            if not to_delete:
                return []
            
            self._undo_stack.append({'type': 'batch', 'data': to_delete})
            self._redo_stack.clear()
            self._scan_data = [d for d in self._scan_data if d.get('locked', False)]
            return to_delete

    def batch_lock(self, status_lock: bool) -> bool:
        """Pin or unpin selected items. Returns True if any state changed."""
        with self._lock:
            changed = False
            for item in self._scan_data:
                if item.get('selected', False):
                    if item.get('locked', False) != status_lock:
                        item['locked'] = status_lock
                        changed = True
            return changed

    def toggle_all_selection(self, status: bool) -> None:
        """Set selected status for all items."""
        with self._lock:
            for item in self._scan_data:
                item['selected'] = status

    def undo(self) -> Tuple[Optional[str], List[Dict[str, Any]]]:
        """Perform undo action. Returns (message, items_affected)."""
        with self._lock:
            if not self._undo_stack:
                return None, []
            action = self._undo_stack.pop()
            self._redo_stack.append(action)
            
            if action['type'] == 'single':
                item = action['data']
                self._scan_data.append(item)
                return "Undo: Item restored.", [item]
            elif action['type'] == 'batch':
                items = action['data']
                for item in items:
                    self._scan_data.append(item)
                return f"Undo: {len(items)} items restored.", items
            return None, []

    def redo(self) -> Tuple[Optional[str], List[Dict[str, Any]]]:
        """Perform redo action. Returns (message, items_removed)."""
        with self._lock:
            if not self._redo_stack:
                return None, []
            action = self._redo_stack.pop()
            self._undo_stack.append(action)
            
            items_to_remove = [action['data']] if action['type'] == 'single' else action['data']
            removed = []
            for item in items_to_remove:
                # Find matching item by url_dl
                target = next((d for d in self._scan_data if d.get('url_dl') == item.get('url_dl')), None)
                if target:
                    self._scan_data.remove(target)
                    removed.append(target)
            
            msg = "Redo: Item deleted." if action['type'] == 'single' else f"Redo: {len(removed)} items deleted."
            return msg, removed

    def can_undo(self) -> bool:
        with self._lock:
            return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        with self._lock:
            return len(self._redo_stack) > 0

    def sort_locked_first(self) -> None:
        with self._lock:
            self._scan_data.sort(key=lambda x: x.get('locked', False), reverse=True)

    def swap_items(self, item_a: Dict[str, Any], item_b: Dict[str, Any]) -> bool:
        with self._lock:
            try:
                idx_a = self._scan_data.index(item_a)
                idx_b = self._scan_data.index(item_b)
                self._scan_data[idx_a], self._scan_data[idx_b] = self._scan_data[idx_b], self._scan_data[idx_a]
                return True
            except ValueError:
                return False

    def load_history(self) -> List[Dict[str, Any]]:
        """Load items from history JSON file."""
        with self._lock:
            if os.path.exists(HISTORY_FILE):
                try:
                    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if data and isinstance(data, list):
                            clean_data = [item for item in data if 'url_dl' in item and 'title' in item]
                            for item in clean_data:
                                if 'selected' not in item: item['selected'] = True
                                if 'locked' not in item: item['locked'] = False
                            self._scan_data = clean_data
                except Exception as e:
                    print(f"[State] Error loading history: {e}")
            return list(self._scan_data)

    def save_history(self) -> None:
        """Save current items to history JSON file."""
        with self._lock:
            try:
                parent_dir = os.path.dirname(HISTORY_FILE)
                if not os.path.exists(parent_dir):
                    os.makedirs(parent_dir, exist_ok=True)
                with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                    json.dump(self._scan_data, f, indent=4)
            except Exception as e:
                print(f"[State] Error saving history: {e}")
