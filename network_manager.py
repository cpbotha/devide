# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

import ConfigParser
from ConfigParser import NoOptionError
import copy
from module_kits.misc_kit.mixins import SubjectMixin
from module_manager import PickledModuleState, PickledConnection
import os
import time
import types


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

        All occurrences of %(dvn_dir)s will be expanded to the
        directory that the DVN file is being loaded from.
        """
      
        # need this for substitution during reading of
        # module_config_dict
        dvn_dir = os.path.dirname(filename)

        cp = ConfigParser.ConfigParser({'dvn_dir' : dvn_dir})

        try:
            # load the fileData
            cfp = open(filename, 'rb')
        except Exception, e:
            raise RuntimeError, 'Could not open network file %s:\n%s' % \
                    (filename,str(e))

        try:
            cp.readfp(cfp)
        except Exception, e:
            raise RuntimeError, 'Could not load network from %s:\n%s' % \
                  (filename,str(e))
        finally:
            cfp.close()


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

    def _transform_relative_paths(self, module_config_dict, dvn_dir):
        """Given a module_config_dict and the directory that a DVN is
        being saved to, transform all values of which the keys contain
        'filename' or 'file_name' so that:
        * if the value is a directory somewhere under the dvn_dir,
          replace the dvn_dir part with %(dvn_dir)s
        * if the value is a list of directories, do the substitution
          for each element.
        """

        def transform_single_path(p):
            p = os.path.abspath(p)
            if p.find(dvn_dir) == 0:
                # do the modification in the copy.
                # (probably not necessary to be this
                # careful)
                p = p.replace(dvn_dir, '%(dvn_dir)s')
                p = p.replace('\\', '/')

            return p

        # make a copy, we don't want to modify what the user
        # gave us.
        new_mcd = copy.deepcopy(module_config_dict)
        # then we iterate through the original
        for k in module_config_dict:
            if k.find('filename') >= 0 or \
                    k.find('file_name') >= 0:

                v = module_config_dict[k]
                if type(v) in [
                        types.StringType,
                        types.UnicodeType]:
                    new_mcd[k] = transform_single_path(v)

                elif type(v) == types.ListType:
                    # it's a list, so try to transform every element
                    # copy everything into a new list new_v
                    new_v = v[:]
                    for i,p in enumerate(v):
                        if type(p) in [
                                types.StringType,
                                types.UnicodeType]:
                            new_v[i] = transform_single_path(p)


                    new_mcd[k] = new_v

        return new_mcd

    def save_network(self, pms_dict, connection_list, glyph_pos_dict,
            filename, export=False):
        """Given the serialised network representation as returned by
        ModuleManager._serialise_network, write the whole thing to disk
        as a config-style DVN file.

        @param export: If True, will transform all filenames that are
        below the network directory to relative pathnames.  These will
        be expanded (relative to the loaded network) at load-time.
        """

        cp = ConfigParser.ConfigParser()

        # general section with network configuration
        sec = 'general'
        cp.add_section(sec)
        cp.set(sec, 'export', export)

        if export:
            # convert all stored filenames, if they are below the
            # network directory, to relative pathnames with
            # substitutions: $(dvn_dir)s/the/rest/somefile.txt
            # on ConfigParser.read we'll supply the NEW dvn_dir
            dvn_dir = os.path.abspath(os.path.dirname(filename))

        # create a section for each module
        for pms in pms_dict.values():
            sec = 'modules/%s' % (pms.instance_name,)
            cp.add_section(sec)
            cp.set(sec, 'module_name', pms.module_name)

            if export:
                mcd = self._transform_relative_paths(
                        pms.module_config.__dict__, dvn_dir)
                        
            else:
                # no export, so we don't have to transform anything
                mcd = pms.module_config.__dict__

            cp.set(sec, 'module_config_dict', mcd)
            cp.set(sec, 'glyph_position', glyph_pos_dict[pms.instance_name])

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

