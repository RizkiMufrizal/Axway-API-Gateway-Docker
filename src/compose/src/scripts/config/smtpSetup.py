'''
Setup API Manager for testing with External SMTP Server
'''
import os
import util
import tempfile
from com.vordel.es.xes import PortableESPKFactory

def configure(es, **kwargs) :
    print '-- Configuring Defualt Portal SMTP server'
    smtpServerPK = PortableESPKFactory.newInstance().createPortableESPK("<key type='SMTPServerGroup'><id field='name' value='SMTP Servers'/><key type='SMTPServer'><id field='name' value='Portal SMTP'/></key></key>")
    smtpConfig = es.getEntity(smtpServerPK)
    smtpConfig.setStringField("smtpServer", "smtp")
    es.updateEntity(smtpConfig)

