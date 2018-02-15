# Setup API Manager for testing with External LDAP directory
import os
from com.vordel.es.xes import PortableESPKFactory


def configure(es, **kwargs) :
    print '--Configuring Entity Store with External ApacheDS LDAP'
    apachedsConf = os.path.join(os.path.dirname(os.path.realpath(__file__)), "apacheds.conf")
    es.importConf(apachedsConf)
    ldapServerPK = PortableESPKFactory.newInstance().createPortableESPK("<key type='LdapDirectoryGroup'><id field='name' value='LDAP Directories'/><key type='LdapDirectory'><id field='name' value='apacheds'/></key></key>")

    portalConfig = es.get("/[PortalConfiguration]")
    portalConfig.setBooleanField("useEmbedded", False)
    portalConfig.setStringField("adminDN", "cn=apiadmin,ou=private,dc=axway,dc=com")
    portalConfig.setStringField("organizationRoot", "ou=public,dc=axway,dc=com")
    portalConfig.setReferenceField("ldapServer", ldapServerPK)
    es.updateEntity(portalConfig)

