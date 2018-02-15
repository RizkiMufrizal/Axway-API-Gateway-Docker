from ..processor import Processor
from ldapcommand import *

class StopLdapProcessor(Processor) :
    '''
    Processor for the stop ldap command.
    '''
    KEY = 'StopLdap'

    def __init__(self, engine, config) :
        super(StopLdapProcessor, self).__init__(engine, StopLdapProcessor.KEY, config)
        self.config = config

    def initial(self, container, node) :
        StopLdap(container, self.config).execute()
