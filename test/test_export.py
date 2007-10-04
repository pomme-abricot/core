
from openalea.core import export_app
from openalea.core.pkgmanager import PackageManager
from openalea.core import *

import os, sys

def test_export():
    pm = PackageManager()
    pm.init()

    sg = CompositeNode()

    # build the compositenode factory
    addid = sg.add_node ( pm.get_node("Catalog.Math", "+"))
    val1id = sg.add_node ( pm.get_node("Catalog.Data", "float")) 
    val2id = sg.add_node ( pm.get_node("Catalog.Data", "float"))
    val3id = sg.add_node ( pm.get_node("Catalog.Data", "float"))

    sg.connect (val1id, 0, addid, 0)
    sg.connect (val2id, 0, addid, 1)
    sg.connect (addid, 0, val3id, 0)

    sgfactory = CompositeNodeFactory("addition")
    sg.to_factory(sgfactory)

    export_app.export_app("ADD", "app.py", sgfactory)

    f = open("app.py")
    assert f
    
    import app
    app.main(sys.argv)


