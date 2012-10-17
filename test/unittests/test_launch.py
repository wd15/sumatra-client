"""
Unit tests for the sumatra.launch module
"""

from __future__ import with_statement
try:
    import unittest2 as unittest
except ImportError:
    import unittest
from sumatra.launch import SerialLaunchMode, DistributedLaunchMode, PlatformInformation
import sys
import os

try:
    import mpi4py.MPI
    have_mpi = True
except ImportError:
    have_mpi = False

class MockExecutable(object):
    requires_script = True
    def __init__(self, path):
        self.name = "foo"
        self.path = path
        self.options = "-t"


class TestPlatformInformation(unittest.TestCase):
    pass


class BaseTestLaunchMode(object):
    
    def write_valid_script(self):
        with open("valid_test_script.py", "w") as f:
            f.write("a = 2\n")
        
    def write_invalid_script(self):
        with open("invalid_test_script.py", "w") as f:
            f.write("@@@\n")
                  
    def write_parameter_file(self):
        with open("test_parameters", "w") as f:
            f.write("b = 3\n")

    def test__run__should_return_True_if_the_command_completed_successfully(self):
        self.write_valid_script()
        self.write_parameter_file()
        prog = MockExecutable(sys.executable)
        self.assertEqual(True, self.lm.run(prog, "valid_test_script.py", "test_parameters"))

    def test__run__should_raise_an_Exception_if_the_executable_does_not_exist(self):
        self.write_valid_script()
        self.write_parameter_file()
        prog = MockExecutable("/this/path/does/not/exist")
        self.assertRaises(IOError, self.lm.run, prog, "valid_test_script.py", "test_parameters")
    
    def test__run__should_raise_an_Exception_if_the_main_file_does_not_exist(self):
        self.write_parameter_file()
        prog = MockExecutable(sys.executable)
        self.assertRaises(IOError, self.lm.run, prog, "foo_script.py", "test_parameters") 
        
    def test__run__should_accept_None_for_the_parameter_file(self):
        prog = MockExecutable(sys.executable)
        self.write_valid_script()
        self.lm.run(prog, "valid_test_script.py", None)
    
    def test__run__should_return_False_if_the_command_failed(self):
        self.write_invalid_script()
        self.write_parameter_file()
        prog = MockExecutable(sys.executable)
        self.assertEqual(False, self.lm.run(prog, "invalid_test_script.py", "test_parameters"))

    def test__str(self):
        # just to make sure no errors are returned
        str(self.lm)
        

class TestSerialLaunchMode(unittest.TestCase, BaseTestLaunchMode):
    
    def setUp(self):
        self.lm = SerialLaunchMode()
    
    def tearDown(self):
        for path in "valid_test_script.py", "invalid_test_script.py", "test_parameters":
            if os.path.exists(path):
                os.remove(path)
    
    def test__get_platform_information__should_return_a_list_of_PlatformInformation_objects(self):
        pis = self.lm.get_platform_information()
        pi0 = pis[0]
        import platform
        self.assertEqual(pi0.version, platform.version())
         
    def test__equality(self):
        new_lm = SerialLaunchMode()
        self.assertEqual(self.lm, new_lm)
        assert self.lm != 42


class TestDistributedLaunchMode(unittest.TestCase, BaseTestLaunchMode):
    
    @unittest.skipUnless(have_mpi, "Need to install mpi4py")
    def setUp(self):
        self.lm = DistributedLaunchMode(2, "mpiexec", ["node1", "node2"])

    def tearDown(self):
        for path in "valid_test_script.py", "invalid_test_script.py", "test_parameters":
            if os.path.exists(path):
                os.remove(path)

    def test__init__should_not_raise_an_exception_if_the_mpiexec_is_not_found(self):
        lm = DistributedLaunchMode(2, "mpifoo", ["node1", "node2"])

    def test__generate_command__should_raise_an_exception_if_the_mpiexec_is_not_found(self):
        lm = DistributedLaunchMode(2, "mpifoo", ["node1", "node2"])
        lm.mpirun = "mpifoo"
        self.assertRaises(IOError, lm.generate_command, MockExecutable(sys.executable), "main_file", "arguments") # main_file does not exist either, but mpirun is checked first

    def test__init__should_set_mpirun_to_the_full_path(self):
        for path in "/usr/bin/mpiexec", "/usr/local/bin/mpiexec":
            if os.path.exists(path):
                self.assertEqual(self.lm.mpirun, path)
                break
            
    def test_getstate_should_return_an_appropriate_dict(self):
        self.assertEqual(self.lm.__getstate__(),
                         {'mpirun': self.lm.mpirun, 'n': 2, 'hosts': ["node1", "node2"], 'pfi_path': '/usr/local/bin/pfi.py'})


if __name__ == '__main__':
    unittest.main()
