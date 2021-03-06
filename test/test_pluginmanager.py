# import os
# import sys
# import unittest
#
# from openalea.core.path import path as Path
# from openalea.core.path import tempdir
# from openalea.core.plugin.manager import PluginManager
# from openalea.core.service.plugin import PluginInstanceManager
#
#
# class Algo(object):
#
#     def __init__(self):
#         pass
#
#
# class AlgoPlugin1(object):
#
#     def __call__(self):
#         return Algo
#
#
# class AlgoPlugin2(object):
#
#     name = 'algo_2'
#
#     def __call__(self):
#         return Algo
#
#
# def install_package():
#     tmppath = tempdir()
#     pythonpath = tmppath / 'lib'
#
#     sys.path.insert(0, pythonpath)
#
#     testpath = Path(__file__).parent.abspath()
#     pythonpath.mkdir()
#
#     sys.path.insert(0, pythonpath / 'tstpkg1-0.1-py2.7.egg')
#     PYTHONPATH = os.environ.get('PYTHONPATH', None)
#     if PYTHONPATH:
#         PYTHONPATH = os.pathsep.join([pythonpath, PYTHONPATH])
#     else:
#         PYTHONPATH = pythonpath
#     os.environ['PYTHONPATH'] = PYTHONPATH
#
#     oldcwd = os.getcwd()
#     oldargs = list(sys.argv)
#     os.chdir(testpath / 'tstdistrib')
#     from setuptools import setup
#     setup(
#         name="tstpkg1",
#         version="0.1",
#         packages=['tstpkg1'],
#
#         entry_points={
#             'test.c1': [
#                 'Plugins = tstpkg1.plugin',
#             ],
#             'test.c2': [
#                 'Plugin1 = tstpkg1.plugin:C2Plugin1',
#                 'Plugin2 = tstpkg1.plugin:C2Plugin2',
#             ],
#             'test.err1': ['Plugin = tstpkg1.plugin:C3PluginDoNotExist'],
#             'test.err2': ['Plugin = tstpkg1.plugin:C3PluginFailInstantiation'],
#             'test.err3': ['Plugin = tstpkg1.plugin:C3PluginFailCall'],
#             'test.err4': ['Plugin = tstpkg1.plugin:C3PluginClassFailInstantiation'],
#         },
#         script_args=[
#             'install',
#             '--install-base=%s' % tmppath,
#             '--install-purelib=%s' % pythonpath,
#             '--install-platlib=%s' % pythonpath,
#             '--install-scripts=%s' % (tmppath / 'bin'),
#             '--install-headers=%s' % (tmppath / 'include'),
#             '--install-data=%s' % (tmppath / 'share'),
#         ]
#     )
#     os.chdir(oldcwd)
#     sys.argv = oldargs
#
#     return tmppath, pythonpath
#
#
# class TestPluginManager(unittest.TestCase):
#
#     @classmethod
#     def setupClass(cls):
#         cls.tmppath, cls.pythonpath = install_package()
#
#         import pkg_resources
#         dist = list(pkg_resources.find_distributions(cls.pythonpath))[0]
#         pkg_resources.working_set.add(dist)
#
#     def setUp(self):
#         self.pm = PluginManager()
#         self.pm.debug = False
#
#         self.pim = PluginInstanceManager(self.pm)
#
#     def test_autoload(self):
#         pm = PluginManager()
#         pm.items('test.c1')
#         assert 'test.c1' in pm._item
#         assert 'tstpkg1.plugin:C1Plugin1' in pm._item['test.c1']
#
#         pm = PluginManager(autoload=[])
#         pm.items('test.c1')
#         assert 'test.c1' in pm._item
#         assert 'tstpkg1.plugin:C1Plugin1' not in pm._item['test.c1']
#
#     def test_module_plugin_def(self):
#         assert self.pm.items('test.c1')
#
#         # check if right plugins have been found
#         assert self.pm.item('MyPlugin1', 'test.c1') is not None
#         assert self.pm.item('MyPlugin2', 'test.c1') is not None
#
#     def test_manual_plugin_def(self):
#         assert self.pm.items('test.c2')
#
#         # check if right plugins have been found
#         assert self.pm.item('C2Plugin1', 'test.c2') is not None
#         assert self.pm.item('C2Plugin2', 'test.c2') is not None
#
#     def test_interface_filter(self):
#         plugins = self.pm.items('test.c1')
#         assert len(plugins) == 2
#         plugins = self.pm.items('test.c1', criteria=dict(implement='IClass1'))
#         assert len(plugins) == 1
#         assert plugins[0].name == 'MyPlugin1'
#
#     def test_dynamic_plugin(self):
#         pl = self.pm.add(AlgoPlugin1, 'test.dynamic3')
#         self.pm.add(AlgoPlugin2, 'test.dynamic3')
#         assert len(self.pm.items('test.dynamic3')) == 2
#
#         objc3c1 = self.pim.instance('test.dynamic3', 'algo_1')
#         assert objc3c1
#         assert isinstance(objc3c1, Algo)
#         objc3c2 = self.pim.instance('test.dynamic3', 'algo_2')
#         assert objc3c2
#         assert isinstance(objc3c1, Algo)
#
#     def atest_proxy_plugin(self):
#         from openalea.core.plugin.manager import SimpleClassPluginProxy
#         self.pm.add('test.dynamic4', Algo, plugin_proxy=SimpleClassPluginProxy)
#         objc4c1 = self.pim.instance('test.dynamic4', 'Algo')
#         objc4c1_2 = self.pim.instance('test.dynamic4', 'Algo')
#         objc4c1_3 = self.pim.new('test.dynamic4', 'Algo')
#
#         assert objc4c1
#         self.assertIsInstance(objc4c1, Algo)
#         assert objc4c1 is objc4c1_2
#         assert objc4c1 is not objc4c1_3
#
#     def test_plugin_name(self):
#         import tstpkg1.plugin
#         import tstpkg1.impl
#
#         # Check manager use plugin name attribute if defined (instead of class name)
#         c1plugin1 = self.pm.item('MyPlugin1', 'test.c1')
#         self.assertIsInstance(c1plugin1, tstpkg1.plugin.C1Plugin1)
#
#         # Check there is no conflict if two plugins with same alias (in setup.py) but in different categories
#         # Check plugin name use class name if no attribute "name"
#         c2plugin1 = self.pm.item('C2Plugin1', 'test.c2')
#         self.assertIsInstance(c2plugin1, tstpkg1.plugin.C2Plugin1)
#
#     def test_new_instance(self):
#         import tstpkg1.impl
#
#         objc1c1 = self.pim.instance('test.c1', 'MyPlugin1')
#         assert objc1c1
#         assert isinstance(objc1c1, tstpkg1.impl.C1Class1)
#
#         objc1c2 = self.pim.instance('test.c1', 'MyPlugin2')
#         assert objc1c2
#         assert isinstance(objc1c2, tstpkg1.impl.C1Class2)
#
#         objc2c1 = self.pim.instance('test.c2', 'C2Plugin1')
#         assert objc2c1
#         assert isinstance(objc2c1, tstpkg1.impl.C2Class1)
#
#         objc2c2 = self.pim.instance('test.c2', 'C2Plugin2')
#         assert objc2c1
#         assert isinstance(objc2c2, tstpkg1.impl.C2Class2)
#
#         # Check instance return existing instance
#         objc1c1_2 = self.pim.instance('test.c1', 'MyPlugin1')
#         assert objc1c1 is objc1c1_2
#         assert self.pim.instances('test.c1', 'MyPlugin1')[0] is objc1c1_2
#
#     def test_multiple_instance(self):
#         # Assert weakref work correctly and plugin instances have been lost
#         assert not self.pim.instances('test.c1', 'MyPlugin1')
#
#         objc1c1_0 = self.pim.instance('test.c1', 'MyPlugin1')
#         objc1c1_1 = self.pim.new('test.c1', 'MyPlugin1')
#         objc1c1_2 = self.pim.new('test.c1', 'MyPlugin1')
#
#         # Assert all object have been created correctly
#         assert objc1c1_0
#         assert objc1c1_1
#         assert objc1c1_2
#
#         # Assert all instances are different as we use new instead of instance
#         assert objc1c1_0 is not objc1c1_1
#         assert objc1c1_1 is not objc1c1_2
#
#         objc1c2 = self.pim.new('test.c1', 'MyPlugin2')
#
#         assert len(self.pim.instances('test.c1', 'MyPlugin1')) == 3
#         assert len(self.pim.instances('test.c1')) == 4
#
#         del objc1c1_2
#
#         assert len(self.pim.instances('test.c1', 'MyPlugin1')) == 2
#         assert len(self.pim.instances('test.c1')) == 3
#
#         del objc1c2
#
#         assert len(self.pim.instances('test.c1', 'MyPlugin1')) == 2
#         assert len(self.pim.instances('test.c1', 'MyPlugin2')) == 0
#         assert len(self.pim.instances('test.c1')) == 2
#
#     def test_debug_ep_load(self):
#
#         self.pm.debug = True
#         with self.assertRaises(ImportError):
#             self.pm.items('test.err1')
#
#         self.pm.clear()
#         self.pm.debug = False
#         self.pm.items('test.err1')
#
#     @classmethod
#     def tearDownClass(cls):
#         cls.tmppath.rmtree()
