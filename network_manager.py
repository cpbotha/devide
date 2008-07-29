# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

import ConfigParser
from ConfigParser import NoOptionError
from module_kits.misc_kit.mixins import SubjectMixin
from module_manager import PickledModuleState, PickledConnection
import time


class NetworkManager(SubjectMixin):
    """Contains all logic to do with network handling.

    This is still work in progress: code has to be refactored out of the
    ModuleManager and the GraphEditor.
    """

    def __init__(self, devide_app):
        self._devide_app = devide_app
        SubjectMixin.__init__(self)

    def close(self):
        SubjectMixin.close(self)

    def execute_network(self, meta_modules):
        """Execute network represented by all modules in the list
        meta_modules.

        """

        # trigger start event so that our observers can auto-save and
        # whatnot
        self.notify('execute_network_start')

        # convert all MetaModules to schedulerModules
        sms = self._devide_app.scheduler.meta_modules_to_scheduler_modules(
            meta_modules)

        print "STARTING network execute ----------------------------"
        print time.ctime()

        self._devide_app.scheduler.execute_modules(sms)
        
        self._devide_app.set_progress(100.0, 'Network execution complete.')

        print "ENDING network execute ------------------------------"        


    def load_network_DEPRECATED(self, filename):
        """Given a filename, read it as a DVN file and return a tuple with
        (pmsDict, connectionList, glyphPosDict) if successful.  If not
        successful, an exception will be raised.
        """
        
        f = None
        try:
            # load the fileData
            f = open(filename, 'rb')
            fileData = f.read()
        except Exception, e:
            if f:
                f.close()

            raise RuntimeError, 'Could not load network from %s:\n%s' % \
                  (filename,str(e))

        f.close()

        try:
            (headerTuple, dataTuple) = cPickle.loads(fileData)
            magic, major, minor, patch = headerTuple
            pmsDict, connectionList, glyphPosDict = dataTuple
            
        except Exception, e:
            raise RuntimeError, 'Could not interpret network from %s:\n%s' % \
                  (filename,str(e))
            

        if magic != 'DVN' and magic != 'D3N' or (major,minor,patch) != (1,0,0):
            raise RuntimeError, '%s is not a valid DeVIDE network file.' % \
                  (filename,)

        return (pmsDict, connectionList, glyphPosDict)

    def load_network(self, filename):
        """Given a filename, read it as a DVN file and return a tuple with
        (pmsDict, connectionList, glyphPosDict) if successful.  If not
        successful, an exception will be raised.
        """
        
        cp = ConfigParser.ConfigParser()

        try:
            # load the fileData
            cfp = open(filename, 'rb')
            cp.readfp(cfp)
        except Exception, e:
            if cfp:
                cfp.close()

            raise RuntimeError, 'Could not load network from %s:\n%s' % \
                  (filename,str(e))


        pms_dict = {}
        connection_list = []
        glyph_pos_dict = {}

        sections = cp.sections()

        # we use this dictionary to determine which ConfigParser get
        # method to use for the specific connection attribute.
        conn_attrs = {
                'source_instance_name' : 'get',
                'output_idx' : 'getint',
                'target_instance_name' : 'get',
                'input_idx' : 'getint',
                'connection_type' : 'getint'
                }

        for sec in sections:
            if sec.startswith('modules/'):
                pms = PickledModuleState()
                pms.instance_name = sec.split('/')[-1]
                try:
                    pms.module_name = cp.get(sec, 'module_name')
                except NoOptionError:
                    # there's no module name, so we're ignoring this
                    # section
                    continue

                try:
                    mcd = cp.get(sec, 'module_config_dict')
                except NoOptionError:
                    # no config in DVN file, pms will have default
                    # module_config
                    pass
                else:
                    # we have to use this relatively safe eval trick to
                    # unpack and interpret the dict
                    cd = eval(mcd,
                            {"__builtins__": {}, 
                             'True' : True, 'False' : False})
                    pms.module_config.__dict__.update(cd)

                # store in main pms dict
                pms_dict[pms.instance_name] = pms

                try:
                    # same eval trick to get out the glyph position
                    gp = eval(cp.get(sec, 'glyph_position'),
                             {"__builtins__": {}})
                except NoOptionError:
                    # no glyph_pos, so we assign it the default origin
                    gp = (0,0)

                glyph_pos_dict[pms.instance_name] = gp

            elif sec.startswith('connections/'):
                pc = PickledConnection()

                for a, getter in conn_attrs.items():
                    get_method = getattr(cp, getter) 
                    try:
                        setattr(pc, a, get_method(sec, a))
                    except NoOptionError:
                        # if an option is missing, we discard the
                        # whole connection
                        break
                else:
                    # this else clause is only entered if the for loop
                    # above was NOT broken out of, i.e. we only store
                    # valid connections
                    connection_list.append(pc)

        return pms_dict, connection_list, glyph_pos_dict

                


    def realise_network(self, pms_dict, connection_list):
        """Given pms_dict and connection_list as returned by load_network,
        realise the given network and return the realised new_modules_dict and
        new_connections.

        @TODO: move network-related code from mm.deserialise_module_instances
        here.
        """
        
        mm = self._devide_app.get_module_manager()
        
        new_modules_dict, new_connections = mm.deserialise_module_instances(
            pms_dict, connection_list)

        return new_modules_dict, new_connections

    def save_network(self, pms_dict, connection_list, glyph_pos_dict,
            filename):
        """Given the serialised network representation as returned by
        ModuleManager._serialise_network, write the whole thing to disk
        as a config-style DVN file.
        """

        cp = ConfigParser.ConfigParser()
        # create a section for each module
        for pms in pms_dict.values():
            sec = 'modules/%s' % (pms.instance_name,)
            cp.add_section(sec)
            cp.set(sec, 'module_name', pms.module_name)
            cp.set(sec, 'module_config_dict', pms.module_config.__dict__)
            cp.set(sec, 'glyph_position', glyph_pos_dict[pms.instance_name])

        sec = 'connections'
        for idx, pconn in enumerate(connection_list):
            sec = 'connections/%d' % (idx,)
            cp.add_section(sec)
            attrs = pconn.__dict__.keys()
            for a in attrs:
                cp.set(sec, a, getattr(pconn, a))


        cfp = file(filename, 'wb')
        cp.write(cfp)
        cfp.close()


    def clear_network(self):
        """Remove/close complete network.

        This method is only called during the non-view mode of operation by
        the scripting interface for example.
        """
        
        mm = self._devide_app.get_module_manager()
        mm.delete_all_modules()

