from __future__ import unicode_literals

import time

from django.test import TestCase
from django.utils.module_loading import import_string

from ..exceptions import LockError

TEST_LOCK_1 = 'test lock 1'


class FileLockTestCase(TestCase):
    backend_string = 'lock_manager.backends.file_lock.FileLock'

    def setUp(self):
        self.locking_backend = import_string(self.backend_string)

    def test_exclusive(self):
        lock_1 = self.locking_backend.acquire_lock(name=TEST_LOCK_1)
        with self.assertRaises(LockError):
            self.locking_backend.acquire_lock(name=TEST_LOCK_1)

        # Cleanup
        lock_1.release()

    def test_release(self):
        lock_1 = self.locking_backend.acquire_lock(name=TEST_LOCK_1)
        lock_1.release()
        lock_2 = self.locking_backend.acquire_lock(name=TEST_LOCK_1)

        # Cleanup
        lock_2.release()

    def test_timeout_expired(self):
        self.locking_backend.acquire_lock(name=TEST_LOCK_1, timeout=1)

        # lock_1 not release and not expired, should raise LockError
        with self.assertRaises(LockError):
            self.locking_backend.acquire_lock(name=TEST_LOCK_1)

        time.sleep(1.01)
        # lock_1 not release but has expired, should not raise LockError
        lock_2 = self.locking_backend.acquire_lock(name=TEST_LOCK_1)

        # Cleanup
        lock_2.release()

    def test_double_release(self):
        lock_1 = self.locking_backend.acquire_lock(name=TEST_LOCK_1)
        lock_1.release()

    def test_release_expired(self):
        lock_1 = self.locking_backend.acquire_lock(name=TEST_LOCK_1, timeout=1)
        time.sleep(1.01)
        lock_1.release()
        # No exception is raised even though the lock has expired.
        # The logic is that checking for expired locks during release is
        # not necesary as any attempt by someone else to aquire the lock
        # would be successfull, even after an extended lapse of time

    def test_release_expired_reaquired(self):
        lock_1 = self.locking_backend.acquire_lock(name=TEST_LOCK_1, timeout=1)
        time.sleep(1.01)
        # TEST_LOCK_1 is expired so trying to acquire it should not return an
        # error.
        lock_2 = self.locking_backend.acquire_lock(name=TEST_LOCK_1, timeout=1)

        # Cleanup
        lock_2.release()


class ModelLockTestCase(FileLockTestCase):
    backend_string = 'lock_manager.backends.model_lock.ModelLock'
