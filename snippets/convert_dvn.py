# convert old-style (up to DeVIDE 8.5) to new-style DVN network files
#
# usage:
# load your old network in DeVIDE 8.5, then execute this snippet in
# the main Python introspection window.  To open the main Python
# introspection window, select from the main DeVIDE menu: "Window |
# Python Shell".  In the window that opens, select "File | Open file
# to current edit" from the main menu to load the file.  Now select
# "File | Run current edit" to execute.

import ConfigParser
import os
import wx

# used to translate from old-style attributes to new-style
conn_trans = {
        'sourceInstanceName' : 'source_instance_name',
        'inputIdx' : 'input_idx',
        'targetInstanceName' : 'target_instance_name',
        'connectionType' : 'connection_type',
        'outputIdx' : 'output_idx'
        }

def save_network(pms_dict, connection_list, glyph_pos_dict, filename):
    """Given the serialised network representation as returned by
    ModuleManager._serialise_network, write the whole thing to disk
    as a config-style DVN file.
    """

    cp = ConfigParser.ConfigParser()
    # create a section for each module
    for pms in pms_dict.values():
        sec = 'modules/%s' % (pms.instanceName,)
        cp.add_section(sec)
        cp.set(sec, 'module_name', pms.moduleName)
        cp.set(sec, 'module_config_dict', pms.moduleConfig.__dict__)
        cp.set(sec, 'glyph_position', glyph_pos_dict[pms.instanceName])

    sec = 'connections'
    for idx, pconn in enumerate(connection_list):
        sec = 'connections/%d' % (idx,)
        cp.add_section(sec)
        attrs = pconn.__dict__.keys()
        for a in attrs:
            cp.set(sec, conn_trans[a], getattr(pconn, a))


    cfp = file(filename, 'wb')
    cp.write(cfp)
    cfp.close()

    mm = devide_app.get_module_manager()
    mm.log_message('Wrote NEW-style network %s.' % (filename,))
    

def save_current_network():
    """Pop up file selector to ask for filename, then save new-style
    network to that filename.
    """


    ge = devide_app._interface._graph_editor
    filename = wx.FileSelector(
            "Choose filename for NEW-style DVN",
            ge._last_fileselector_dir, "", "dvn",
            "NEW-style DeVIDE networks (*.dvn)|*.dvn|All files (*.*)|*.*",
            wx.SAVE)

    if filename:
        # make sure it has a dvn extension
        if os.path.splitext(filename)[1] == '':
            filename = '%s.dvn' % (filename,)

        glyphs = ge._get_all_glyphs()
        pms_dict, connection_list, glyph_pos_dict = ge._serialise_network(glyphs)
        save_network(pms_dict, connection_list, glyph_pos_dict,
                filename)


save_current_network()

