# -*- python -*-
#
#       OpenAlea.Core: OpenAlea Core
#
#       Copyright or (C) or Copr. 2006 INRIA - CIRAD - INRA  
#
#       File author(s): Christophe Pradal <christophe.prada@cirad.fr>
#                       Samuel Dufour-Kowalski <samuel.dufour@sophia.inria.fr>
#
#       Distributed under the Cecill-C License.
#       See accompanying file LICENSE.txt or copy at
#           http://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html
# 
#       OpenAlea WebSite : http://openalea.gforge.inria.fr
#


__doc__="""
This module defines all the base class for the OpenAlea Kernel
(Node, Package...)
"""

__license__= "Cecill-C"
__revision__=" $Id$ "



# Exceptions

class UnknownNodeError (Exception):
    pass

class RecursionError (Exception):
    pass

class InstantiationError(Exception):
    pass

###############################################################################

from observer import Observed, AbstractListener
import imp
import os

class Node(Observed):
    """
    Base class for all Nodes.
    A Node is a callable object with typed inputs and outputs.
    """

    def __init__(self):

        Observed.__init__(self)

        # Values
        self.inputs = []
        self.outputs = []

        # Description (list of tuple (name, interface))
        self.input_desc = []
        self.output_desc = []
        
        
        self.map_index_in = {}
        self.map_index_out = {}

        # Input states : "connected", "hidden"
        self.input_states = []

        # Node State
        self.modified = True

        # Factory
        self.factory = None

        # Internal Data (caption...)
        self.internal_data = {}
        self.internal_data['caption'] = str(self.__class__.__name__)
        

    def __call__(self, inputs = ()):
        """ Call function. Must be overriden """
        
        raise RuntimeError('Node function not implemented.')

    # Accessor
    
    def get_factory(self):
        """ Return the factory of the node (if any) """
        return self.factory


    # Internal data accessor
    def set_caption(self, newcaption):
        """ Define the node caption """
        self.internal_data['caption'] = newcaption
        self.notify_listeners( ("caption_modified",) )


    def set_data(self, key, value):
        """ Set internal node data """
        self.internal_data[key] = value
        self.notify_listeners( ("data_modified",) )


    # Status
    def unvalidate_input(self, input_index):
        """ Unvalidate node and notify listeners """
        self.modified = True
        self.notify_listeners( ("input_modified",input_index) )


    # Declarations
    def add_input(self, name, interface, value = None):
        """ Create an input port """

        self.inputs.append( value )
        self.input_desc.append( (name, interface) )
        self.input_states.append(None)
        self.map_index_in[name]= len(self.inputs) - 1


    def add_output(self, name, interface):
        """ Create an output port """

        self.outputs.append( None )
        self.output_desc.append( (name, interface) )
        self.map_index_out[name]= len(self.outputs) - 1


    # I/O Functions
    def get_input_interface_by_key(self, key):
        """ Return the interface of an input port """
        index = self.map_index_in[key]
        return self.input_desc[index][1]


    def get_output_interface_by_key(self, key):
        """ Return the interface of an output port """
        index = self.map_index_out[key]
        return self.output_desc[index][1]

    
    def get_input_by_key(self, key):
        """ Return the input value for the specified port name (key)"""
        index = self.map_index_in[key]
        return self.inputs[index]


    def set_input_by_key(self, key, val):
        """ Set the input value for the specified port name (key)"""
        index = self.map_index_in[key]
        self.set_input(index, val)
        

    def get_output_by_key(self, key):
        """ Return the output value for the specified port name (key)"""
        index = self.map_index_out[key]
        return self.outputs[index]


    def set_output_by_key(self, key, val):
        """ Set the output value for the specified port name (key)"""
        index = self.map_index_out[key]
        self.outputs[index] =  val

    
    def get_input(self, index):
        """ Return an input port value """

        return self.inputs[index]


    def set_input(self, index, val):
        """ Define the input value for the specified index """

        if(self.inputs[index] != val):
            self.inputs[index] = val
            self.unvalidate_input(index)


    def get_output(self, index):
        """ Return the output for the specified index """
        return self.outputs[index]


    def set_output(self, index, val):
        """ Set the output value for the specified index """
        self.outputs[index] = val


    def get_input_state(self, index):
        return self.input_states[index]

    
    def set_input_state(self, index, state):
        """ Set the state of the input index (state is a string) """

        self.input_states[index] = state
        self.unvalidate_input(index)


    def get_input_index(self, key):
        """ Return the index of input identified by key """
        return self.map_index_in[key]
    
        
    def get_nb_input(self):
        """ Return the nb of input ports """
        return len(self.inputs)

    
    def get_nb_output(self):
        """ Return the nb of output ports """
        return len(self.outputs)


    
    # Functions used by the node evaluator
    def eval(self):
        """
        Evaluate the node by calling __call__
        Return True if the node has been calculated
        """

        # lazy evaluation
        if(not self.modified):
            return False

        self.modified = False
        
        outlist = self.__call__(self.inputs)
        self.notify_listeners( ("status_modified",self.modified) )

        if(not outlist) : return True
        
        if(not isinstance(outlist, tuple) and
           not isinstance(outlist, list)):
            outlist = (outlist,)

        for i in range( min ( len(outlist), len(self.outputs))):
            self.outputs[i] = outlist[i]

        return True



###############################################################################


class NodeFactory(Observed):
    """
    A Node factory is able to create nodes on demand,
    and their associated widgets.
    """

    mimetype = "openalea/nodefactory"

    def __init__(self,
                 name,
                 description = '',
                 category = '',
                 nodemodule = '',
                 nodeclass = None,
                 widgetmodule = None,
                 widgetclass = None,
                 **kargs):
        
        """
        Create a node factory.
        
        @param name : user name for the node (must be unique)
        @param description : description of the node
        @param category : category of the node
        @param nodemodule : 'python module to import for node'
        @param nodeclass :  node class name to be created
        @param widgetmodule : 'python module to import for widget'
        @param widgetclass : widget class name
        
        @type name : String
        @type description : String
        @type category : String
        @type nodemodule : String
        @type nodeclass : String
        @type widgetmodule : String
        @type widgetclass : String
        """
        
        Observed.__init__(self)
        
        self.name = name
        self.description = description
        self.category = category
        self.nodemodule_name = nodemodule
        self.nodeclass_name = nodeclass
        self.widgetmodule_name = widgetmodule
        self.widgetclass_name = widgetclass

        self.package = None

        # Cache
        self.nodeclass = None
        self.nodemodule = None
        self.nodemodule_path = None
        

    def get_id(self):
        """ Return the node factory Id """
        return self.name


    def get_tip(self):
        """ Return the node description """

        return "Name : %s\n"%(self.name,) +\
               "Category  : %s\n"%(self.category,) +\
               "Description : %s\n"%(self.description,)

       
    def instantiate(self, call_stack=[]):
        """ Return a node instance
        @param call_stack : the list of NodeFactory id already in call stack
        (in order to avoir infinite recursion)
        """

        module = self.get_node_module()
        classobj = module.__dict__[self.nodeclass_name]
        node = classobj()
        node.factory = self
        return node
                    

    def instantiate_widget(self, node, parent=None, edit = False):
        """ Return the corresponding widget initialised with node """

        if(node == None):
            node = self.instantiate()

        modulename = self.widgetmodule_name
        if(not modulename) :   modulename = self.nodemodule_name

        if(modulename and self.widgetclass_name):

            (file, pathname, desc) = imp.find_module(modulename)
            module = imp.load_module(modulename, file, pathname, desc)
            if(file) : file.close()

            widgetclass = module.__dict__[self.widgetclass_name]

            return widgetclass(node, parent)
        
        else:
            try:
                # if no widget declared, we create a default one
                from openalea.visualea.node_widget import DefaultNodeWidget
                return DefaultNodeWidget(node, parent)
            
            except ImportError:
                raise
                #raise InstantiationError()
                

    def get_xmlwriter(self):
        """ Return an instance of a xml writer """

        from pkgreader import NodeFactoryXmlWriter
        return NodeFactoryXmlWriter(self)


    def get_node_module(self):
        """
        Return the python module object (if available)
        Raise an Import Error if no module is associated
        """

        if(self.nodemodule and self.nodemodule_path):
            return self.nodemodule

        if(self.nodemodule_name):
            try:
                (file, pathname, desc) = imp.find_module(self.nodemodule_name)
                self.nodemodule_path = pathname
                self.nodemodule = imp.load_module(self.nodemodule_name, file, pathname, desc)
                
                if(file) :
                    file.close()
                return self.nodemodule
                
            except ImportError:
                #raise InstantiationError()
                raise
        else :
            raise ImportError()
    

    def get_node_src(self):
        """
        Return a string containing the node src
        Return None if src is not available
        """

        module = self.get_node_module()

        import inspect
        try:
            # get the code
            cl = module.__dict__[self.nodeclass_name]
            return inspect.getsource(cl)
        except:
            return None


    def apply_new_src(self, newsrc):
        """
        Execute new src
        """

        module = self.get_node_module()
        # Run src
        exec newsrc in module.__dict__


    def save_new_src(self, newsrc):
        
        module = self.get_node_module()
        nodesrc = self.get_node_src()
        
        # Run src
        exec newsrc in module.__dict__

        # get the module code
        import inspect
        modulesrc = inspect.getsource(module)

        # Pass if no modications
        if(nodesrc == newsrc) : return
        
        # replace old code with new one
        modulesrc = modulesrc.replace(nodesrc, newsrc)

        # write file
        file = open(self.nodemodule_path, 'w')
        file.write(modulesrc)
        file.close()

        # unload module
        if(self.nodemodule) : del(self.nodemodule)
        self.nodemodule = None

        # Recompile
        import py_compile
        py_compile.compile(self.nodemodule_path)
        
        


#class Factory:
Factory = NodeFactory


class UserFactory(NodeFactory):
    """ Node Factory created by a user """

    def __init__(self, **kargs):

        NodeFactory.__init__(self, **kargs)

        # get local openalea dir
        localdir = get_wralea_home_dir()

        # create a module

        template = 'from openalea.core import *\n'+\
                   '\n'+\
                   'class %s(Node):\n'%(self.name)+\
                   '    """  Doc... """ \n'+\
                   '\n'+\
                   '    def __init__(self):\n'+\
                   '        Node.__init__(self)\n'+\
                   '        self.add_input( name = "X", interface = None, value = None)\n'+\
                   '        self.add_output( name = "Y", interface = None) \n'+\
                   '\n'+\
                   '\n'+\
                   '    def __call__(self, inputs):\n'+\
                   '        return inputs\n'
        
        self.nodemodule_path = os.path.join(localdir, "%s.py"%(self.name))
        self.nodemodule_name = self.name
        self.nodeclass_name = self.name

        file = open(self.nodemodule_path, 'w')
        file.write(template)
        file.close()


    def get_node_module(self):
        """ Return the associated module """

        if(self.nodemodule):
            return self.nodemodule

        if(self.nodemodule_name):
            try:
                file = open(self.nodemodule_path, 'r')
                self.nodemodule = imp.load_module(self.nodemodule_name,
                                                  file, self.nodemodule_path,
                                                  ('.py','U',1))
                
                if(file) :
                    file.close()
                return self.nodemodule
                
            except ImportError:
                #raise InstantiationError()
                raise
        else :
            raise ImportError()

                 


###############################################################################

class NodeWidget(AbstractListener):
    """
    Base class for all node widget classes.
    """

    def __init__(self, node):
        """ Init the widget with the associated node """
        self.__node = node

        # register to observed node
        self.initialise(node)


    def get_node(self):
        """ Return the associated node """
        return self.__node


    def set_node(self, node):
        """ Define the associated node """
        self.__node = node

    node = property(get_node, set_node)


    def notify(self, sender, event):
        """
        This function is called by the Observed objects
        and must be overloaded
        """
        pass

    def is_empty( self ):
        return False


###############################################################################

        

class Package(dict):
    """
    A Package is a dictionnary of node factory.
    Each node factory is able to generate node and their widget

    Meta informations are associated with a package.
    """

    mimetype = "openalea/package"


    def __init__(self, name, metainfo) :
	"""
        Create a Package

        @param name : a unique string used as a unique identifier for the package
        @param metainfo : a dictionnary for metainformation. Attended keys are :
            license : a string ex GPL, LGPL, Cecill, Cecill-C
            version : a string
            authors : a string
            institutes : a string
            url : a string
            description : a string for the package description
            publication : optional string for publications
            
	"""

        dict.__init__(self)
        
        self.name = name
        self.metainfo = metainfo

        # association between node name and node factory
        #self.__node_factories = {}


    def get_id(self):
        """ Return the package id """
        return self.name


    def get_tip(self):
        """ Return the package description """

        str= "Package : %s\n"%(self.name,)
        try: str+= "Description : %s\n"%(self.metainfo['description'],)
        except : pass
        try: str+= "Institutes : %s\n"%(self.metainfo['institutes'],)
        except : pass 

        try: str+= "URL : %s\n"%(self.metainfo['url'],)
        except : pass 

        return str


    def get_metainfo(self, key):
        """
        Return a meta information.
        See the standard key in the __init__ function documentation.
        """
        try:
            return self.metainfo[key]
        except:
            return ""


    def add_factory(self, factory):
        """ Add to the package a factory ( node or subgraph ) """

        if(self.has_key(factory.name)):
            print "Factory %s already defined. Ignored !"%(factory.name,)
            return
        
        self[factory.name] = factory
        factory.package = self


    def get_names(self):
        """ Return all the factory names in a list """

        return self.keys()
    

    def get_factory(self, id):
        """ Return the factory associated with id """

        try:
            factory = self[id]
        except KeyError:
            raise UnknownNodeError()

        return factory



        


