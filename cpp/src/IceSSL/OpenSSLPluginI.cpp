// **********************************************************************
//
// Copyright (c) 2001
// MutableRealms, Inc.
// Huntsville, AL, USA
//
// All Rights Reserved
//
// **********************************************************************

//
// This needs to be first since <openssl/e_os.h> #include <windows.h>
// without our configuration settings.
//
#include <IceUtil/Mutex.h>
#include <IceUtil/RecMutex.h>
#include <Ice/Logger.h>
#include <Ice/Properties.h>
#include <Ice/ProtocolPluginFacade.h>
#include <IceSSL/OpenSSLPluginI.h>
#include <IceSSL/Exception.h>
#include <IceSSL/ConfigParser.h>
#include <IceSSL/OpenSSLJanitors.h>
#include <IceSSL/OpenSSLUtils.h>
#include <IceSSL/SslConnectionOpenSSL.h>
#include <IceSSL/DefaultCertificateVerifier.h>
#include <IceSSL/SingleCertificateVerifier.h>
#include <IceSSL/SslEndpoint.h>
#include <IceSSL/TraceLevels.h>

#include <IceSSL/RSAPrivateKey.h>
#include <IceSSL/DHParams.h>

#include <openssl/e_os.h>
#include <openssl/rand.h>
//#include <openssl/dh.h>

#include <sstream>

#define OPENSSL_THREAD_DEFINES
#include <openssl/opensslconf.h>
#if defined(THREADS)
#else
#error "Thread support not enabled"
#endif

using namespace std;
using namespace Ice;
using namespace IceInternal;
using namespace IceSSL;

//
// Plugin factory function
//
extern "C"
{

ICE_SSL_API Ice::Plugin*
create(const CommunicatorPtr& communicator, const string& name, const StringSeq& args)
{
    ProtocolPluginFacadePtr facade = getProtocolPluginFacade(communicator);

    IceSSL::OpenSSL::PluginI* plugin = new IceSSL::OpenSSL::PluginI(facade);
    try
    {
        plugin->configure();
    }
    catch (...)
    {
        Ice::PluginPtr ptr = plugin; // Reclaim the plug-in instance
        throw;
    }

    //
    // Install the SSL endpoint factory
    //
    EndpointFactoryPtr sslEndpointFactory = new SslEndpointFactory(plugin);
    facade->addEndpointFactory(sslEndpointFactory);

    return plugin;
}

}

//
// Thread safety implementation for OpenSSL
//
namespace IceSSL
{

extern "C"
{
    void lockingCallback(int, int, const char*, int);
}

class SslLockKeeper
{
public:

    SslLockKeeper();
    ~SslLockKeeper();

    IceUtil::Mutex sslLocks[CRYPTO_NUM_LOCKS];

};

SslLockKeeper lockKeeper;

}

void IceSSL::lockingCallback(int mode, int type, const char *file, int line)
{
    if (mode & CRYPTO_LOCK)
    {
        lockKeeper.sslLocks[type].lock();
    }
    else
    {
        lockKeeper.sslLocks[type].unlock();
    }
}

IceSSL::SslLockKeeper::SslLockKeeper()
{
    CRYPTO_set_locking_callback((void (*)(int, int, const char*, int))IceSSL::lockingCallback);
}

IceSSL::SslLockKeeper::~SslLockKeeper()
{
    CRYPTO_set_locking_callback(NULL);
}

//
// PluginI implementation
//
IceSSL::ConnectionPtr
IceSSL::OpenSSL::PluginI::createConnection(ContextType connectionType, int socket)
{
    IceUtil::RecMutex::Lock sync(_configMutex);

    if (connectionType == ClientServer)
    {
        UnsupportedContextException unsupportedException(__FILE__, __LINE__);

        unsupportedException._message = "unable to create client/server connections";

        throw unsupportedException;
    }

    // Configure the context if need be.
    if (!isConfigured(connectionType))
    {
        configure(connectionType);
    }

    IceSSL::ConnectionPtr connection;

    if (connectionType == Client)
    {
        connection = _clientContext.createConnection(socket, this);
    }
    else if (connectionType == Server)
    {
        connection = _serverContext.createConnection(socket, this);
    }

    return connection;
}

bool
IceSSL::OpenSSL::PluginI::isConfigured(ContextType contextType)
{
    IceUtil::RecMutex::Lock sync(_configMutex);

    bool retCode = false;

    switch (contextType)
    {
        case Client :
        {
            retCode = _clientContext.isConfigured();
            break;
        }

        case Server :
        {
            retCode = _serverContext.isConfigured();
            break;
        }

        case ClientServer :
        {
            retCode = _clientContext.isConfigured() && _serverContext.isConfigured();
            break;
        }
    }

    return retCode;
}

void
IceSSL::OpenSSL::PluginI::configure()
{
    string clientConfigFile = _properties->getProperty("IceSSL.Client.Config");
    string serverConfigFile = _properties->getProperty("IceSSL.Server.Config");
    
    bool clientConfig = (clientConfigFile.empty() ? false : true);
    bool serverConfig = (serverConfigFile.empty() ? false : true);

    if (clientConfig && serverConfig)
    {
        configure(ClientServer);
    }
    else if (clientConfig)
    {
        configure(Client);
    }
    else if (serverConfig)
    {
        configure(Server);
    }
}

void
IceSSL::OpenSSL::PluginI::configure(ContextType contextType)
{
    IceUtil::RecMutex::Lock sync(_configMutex);

    switch (contextType)
    {
        case Client :
        {
            string configFile = _properties->getProperty("IceSSL.Client.Config");
            string certPath   = _properties->getProperty("IceSSL.Client.CertPath");
            loadConfig(Client, configFile, certPath);
            break;
        }

        case Server :
        {
            string configFile = _properties->getProperty("IceSSL.Server.Config");
            string certPath   = _properties->getProperty("IceSSL.Server.CertPath");
            loadConfig(Server, configFile, certPath);
            break;
        }

        case ClientServer :
        {
            string clientConfigFile = _properties->getProperty("IceSSL.Client.Config");
            string clientCertPath   = _properties->getProperty("IceSSL.Client.CertPath");
            string serverConfigFile = _properties->getProperty("IceSSL.Server.Config");
            string serverCertPath   = _properties->getProperty("IceSSL.Server.CertPath");

            // Short cut, so that we only have to load the file once.
            if ((clientConfigFile == serverConfigFile) && (clientCertPath == serverCertPath))
            {
                loadConfig(ClientServer, clientConfigFile, clientCertPath);
            }
            else
            {
                loadConfig(Client, clientConfigFile, clientCertPath);
                loadConfig(Server, serverConfigFile, serverCertPath);
            }
            break;
        }
    }
}

void
IceSSL::OpenSSL::PluginI::loadConfig(ContextType contextType,
                                     const std::string& configFile,
                                     const std::string& certPath)
{
    if (configFile.empty())
    {
        ConfigurationLoadingException configEx(__FILE__, __LINE__);

        string contextString;

        switch (contextType)
        {
            case Client :
            {
                contextString = "client";
                break;
            }

            case Server :
            {
                contextString = "server";
                break;
            }

            case ClientServer :
            {
                contextString = "client/server";
                break;
            }
        }

        configEx._message = "no ssl configuration file specified for ";
        configEx._message += contextString;

        throw configEx;
    }

    ConfigParser sslConfig(configFile, certPath);

    sslConfig.setTrace(_traceLevels);
    sslConfig.setLogger(_logger);

    // Actually parse the file now.
    sslConfig.process();

    if ((contextType == Client || contextType == ClientServer))
    {
        GeneralConfig clientGeneral;
        CertificateAuthority clientCertAuth;
        BaseCertificates clientBaseCerts;

        // Walk the parse tree, get the Client configuration.
        if (sslConfig.loadClientConfig(clientGeneral, clientCertAuth, clientBaseCerts))
        {
            initRandSystem(clientGeneral.getRandomBytesFiles());

            _clientContext.configure(clientGeneral, clientCertAuth, clientBaseCerts);
        }
    }

    if ((contextType == Server || contextType == ClientServer))
    {
        GeneralConfig serverGeneral;
        CertificateAuthority serverCertAuth;
        BaseCertificates serverBaseCerts;
        TempCertificates serverTempCerts;

        // Walk the parse tree, get the Server configuration.
        if (sslConfig.loadServerConfig(serverGeneral, serverCertAuth, serverBaseCerts, serverTempCerts))
        {
            initRandSystem(serverGeneral.getRandomBytesFiles());

            loadTempCerts(serverTempCerts);

            _serverContext.configure(serverGeneral, serverCertAuth, serverBaseCerts);

            if (_traceLevels->security >= IceSSL::SECURITY_PROTOCOL)
            {
                ostringstream s;

                s << "temporary certificates (server)" << endl;
                s << "-------------------------------" << endl;
                s << serverTempCerts << endl;

                _logger->trace(_traceLevels->securityCat, s.str());
            }
        }
    }
}

RSA*
IceSSL::OpenSSL::PluginI::getRSAKey(int isExport, int keyLength)
{
    IceUtil::Mutex::Lock sync(_tempRSAKeysMutex);

    RSA* rsa_tmp = 0;

    RSAMap::iterator retVal = _tempRSAKeys.find(keyLength);

    // Does the key already exist?
    if (retVal != _tempRSAKeys.end())
    {
        // Yes!  Use it.
        rsa_tmp = (*retVal).second->get();

        assert(rsa_tmp != 0);
    }
    else
    {
        const RSACertMap::iterator& it = _tempRSAFileMap.find(keyLength);

        // First we try to load a private and public key from specified files
        if (it != _tempRSAFileMap.end())
        {
            CertificateDesc& rsaKeyCert = (*it).second;

            const string& privKeyFile = rsaKeyCert.getPrivate().getFileName();
            const string& pubCertFile = rsaKeyCert.getPublic().getFileName();

            RSA* rsaCert = 0;
            RSA* rsaKey = 0;
            BIO* bio = 0;

            if ((bio = BIO_new_file(pubCertFile.c_str(), "r")) != 0)
            {
                BIOJanitor bioJanitor(bio);

                rsaCert = PEM_read_bio_RSAPublicKey(bio, 0, 0, 0);
            }

            if (rsaCert != 0)
            {
                if ((bio = BIO_new_file(privKeyFile.c_str(), "r")) != 0)
                {
                    BIOJanitor bioJanitor(bio);

                    rsaKey = PEM_read_bio_RSAPrivateKey(bio, &rsaCert, 0, 0);
                }
            }

            // Now, if all was well, the Certificate and Key should both be loaded into
            // rsaCert. We check to ensure that both are not 0, because if either are,
            // one of the reads failed.

            if ((rsaCert != 0) && (rsaKey != 0))
            {
                rsa_tmp = rsaCert;
            }
            else
            {
                if (rsaCert != 0)
                {
                    RSA_free(rsaCert);
                    rsaCert = 0;
                }
            }
        }

        // Couldn't load file, last ditch effort - generate a key on the fly.
        if (rsa_tmp == 0)
        {
            rsa_tmp = RSA_generate_key(keyLength, RSA_F4, 0, 0);
        }

        // Save in our temporary key cache.
        if (rsa_tmp != 0)
        {
            _tempRSAKeys[keyLength] = new RSAPrivateKey(rsa_tmp);
        }
        else if (_traceLevels->security >= IceSSL::SECURITY_WARNINGS)
        {
            ostringstream errorMsg;

            errorMsg << "WRN Unable to obtain a " << dec << keyLength;
            errorMsg << "-bit RSA key." << endl;

            _logger->trace(_traceLevels->securityCat, errorMsg.str());
        }
    }

    return rsa_tmp;
}

DH*
IceSSL::OpenSSL::PluginI::getDHParams(int isExport, int keyLength)
{
    IceUtil::Mutex::Lock sync(_tempDHKeysMutex);

    DH* dh_tmp = 0;

    const DHMap::iterator& retVal = _tempDHKeys.find(keyLength);

    // Does the key already exist?
    if (retVal != _tempDHKeys.end())
    {
        // Yes!  Use it.
        dh_tmp = (*retVal).second->get();
    }
    else
    {
        const DHParamsMap::iterator& it = _tempDHParamsFileMap.find(keyLength);

        // First we try to load params from specified files
        if (it != _tempDHParamsFileMap.end())
        {
            DiffieHellmanParamsFile& dhParamsFile = (*it).second;

            string dhFile = dhParamsFile.getFileName();

            dh_tmp = loadDHParam(dhFile.c_str());
        }

        // If that doesn't work, use a compiled-in group.
        if (dh_tmp == 0)
        {
            switch (keyLength)
            {
                case 512 :
                {
                    dh_tmp = getTempDH512();
                    break;
                }
        
                case 1024 :
                {
                    dh_tmp = getTempDH1024();
                    break;
                }

                case 2048 :
                {
                    dh_tmp = getTempDH2048();
                    break;
                }

                case 4096 :
                {
                    dh_tmp = getTempDH4096();
                    break;
                }
            }
        }

        if (dh_tmp != 0)
        {
            // Cache the dh params for quick lookup - no
            // extra processing required then.
            _tempDHKeys[keyLength] = new DHParams(dh_tmp);
        }
        else if (_traceLevels->security >= IceSSL::SECURITY_WARNINGS)
        {
            ostringstream errorMsg;

            errorMsg << "WRN Unable to obtain a " << dec << keyLength;
            errorMsg << "-bit Diffie-Hellman parameter group." << endl;

            _logger->trace(_traceLevels->securityCat, errorMsg.str());
        }
    }

    return dh_tmp;
}

void
IceSSL::OpenSSL::PluginI::setCertificateVerifier(ContextType contextType,
                                                 const IceSSL::CertificateVerifierPtr& verifier)
{
    IceUtil::RecMutex::Lock sync(_configMutex);

    IceSSL::OpenSSL::CertificateVerifierPtr castVerifier;
    castVerifier = IceSSL::OpenSSL::CertificateVerifierPtr::dynamicCast(verifier);

    if (!castVerifier.get())
    {
        IceSSL::CertificateVerifierTypeException cvtEx(__FILE__, __LINE__);
        throw cvtEx;
    }

    if (contextType == Client || contextType == ClientServer)
    {
        _clientContext.setCertificateVerifier(castVerifier);
    }

    if (contextType == Server || contextType == ClientServer)
    {
        _serverContext.setCertificateVerifier(castVerifier);
    }
}

void
IceSSL::OpenSSL::PluginI::addTrustedCertificateBase64(ContextType contextType, const string& certString)
{
    IceUtil::RecMutex::Lock sync(_configMutex);

    if (contextType == Client || contextType == ClientServer)
    {
        _clientContext.addTrustedCertificateBase64(certString);
    }

    if (contextType == Server || contextType == ClientServer)
    {
        _serverContext.addTrustedCertificateBase64(certString);
    }
}

void
IceSSL::OpenSSL::PluginI::addTrustedCertificate(ContextType contextType, const Ice::ByteSeq& certSeq)
{
    IceUtil::RecMutex::Lock sync(_configMutex);

    if (contextType == Client || contextType == ClientServer)
    {
        _clientContext.addTrustedCertificate(certSeq);
    }

    if (contextType == Server || contextType == ClientServer)
    {
        _serverContext.addTrustedCertificate(certSeq);
    }
}

void
IceSSL::OpenSSL::PluginI::setRSAKeysBase64(ContextType contextType,
                                           const std::string& privateKey,
                                           const std::string& publicKey)
{
    IceUtil::RecMutex::Lock sync(_configMutex);

    if (contextType == Client || contextType == ClientServer)
    {
        _clientContext.setRSAKeysBase64(privateKey, publicKey);
    }

    if (contextType == Server || contextType == ClientServer)
    {
        _serverContext.setRSAKeysBase64(privateKey, publicKey);
    }
}

void
IceSSL::OpenSSL::PluginI::setRSAKeys(ContextType contextType,
                                     const ::Ice::ByteSeq& privateKey,
                                     const ::Ice::ByteSeq& publicKey)
{
    IceUtil::RecMutex::Lock sync(_configMutex);

    if (contextType == Client || contextType == ClientServer)
    {
        _clientContext.setRSAKeys(privateKey, publicKey);
    }

    if (contextType == Server || contextType == ClientServer)
    {
        _serverContext.setRSAKeys(privateKey, publicKey);
    }
}

IceSSL::CertificateVerifierPtr
IceSSL::OpenSSL::PluginI::getDefaultCertVerifier()
{
    return new DefaultCertificateVerifier(getTraceLevels(), getLogger());
}

IceSSL::CertificateVerifierPtr
IceSSL::OpenSSL::PluginI::getSingleCertVerifier(const ByteSeq& certSeq)
{
    return new SingleCertificateVerifier(certSeq);
}

void
IceSSL::OpenSSL::PluginI::destroy()
{
}

//
// Protected
//

IceSSL::OpenSSL::PluginI::PluginI(const ProtocolPluginFacadePtr& protocolPluginFacade) :
    PluginBaseI(protocolPluginFacade),
    _serverContext(getTraceLevels(), getLogger(), getProperties()),
    _clientContext(getTraceLevels(), getLogger(), getProperties())
{
    _randSeeded = 0;

    SSL_load_error_strings();

    OpenSSL_add_ssl_algorithms();
}

IceSSL::OpenSSL::PluginI::~PluginI()
{
}

//
// Private
//

int
IceSSL::OpenSSL::PluginI::seedRand()
{
#ifdef WINDOWS
    RAND_screen();
#endif

    char buffer[1024];
    const char* file = RAND_file_name(buffer, sizeof(buffer));

    if (file == 0)
    {
        return 0;
    }
    
    return RAND_load_file(file, -1);
}

long
IceSSL::OpenSSL::PluginI::loadRandFiles(const string& names)
{
    if (!names.empty())
    {
        return 0;
    }

    long tot = 0;
    int egd;

    // Make a modifiable copy of the string.
    char* namesString = new char[names.length() + 1];
    assert(namesString != 0);

    strcpy(namesString, names.c_str());

    char seps[5];

    sprintf(seps, "%c", LIST_SEPARATOR_CHAR);

    char* token = strtok(namesString, seps);

    while (token != 0)
    {
        egd = RAND_egd(token);

        if (egd > 0)
        {
            tot += egd;
        }
        else
        {
            tot += RAND_load_file(token, -1);
        }

        token = strtok(0, seps);
    }

    if (tot > 512)
    {
        _randSeeded = 1;
    }

    delete []namesString;

    return tot;
}

void
IceSSL::OpenSSL::PluginI::initRandSystem(const string& randBytesFiles)
{
    if (_randSeeded)
    {
        return;
    }

    long randBytesLoaded = seedRand();

    if (!randBytesFiles.empty())
    {
        randBytesLoaded += loadRandFiles(randBytesFiles);
    }

    if (!randBytesLoaded && !RAND_status() && (_traceLevels->security >= IceSSL::SECURITY_WARNINGS))
    {
        // In this case, there are two options open to us - specify a random data file using the
        // RANDFILE environment variable, or specify additional random data files in the
        // SSL configuration file.
        _logger->trace(_traceLevels->securityCat,
                       "WRN there is a lack of random data, consider specifying additional random data files");
    }

    _randSeeded = (randBytesLoaded > 0 ? 1 : 0);
}

void
IceSSL::OpenSSL::PluginI::loadTempCerts(TempCertificates& tempCerts)
{
    RSAVector::iterator iRSA = tempCerts.getRSACerts().begin();
    RSAVector::iterator eRSA = tempCerts.getRSACerts().end();

    while (iRSA != eRSA)
    {
        _tempRSAFileMap[(*iRSA).getKeySize()] = *iRSA;
        iRSA++;
    }

    DHVector::iterator iDHP = tempCerts.getDHParams().begin();
    DHVector::iterator eDHP = tempCerts.getDHParams().end();

    while (iDHP != eDHP)
    {
        _tempDHParamsFileMap[(*iDHP).getKeySize()] = *iDHP;
        iDHP++;
    }
}
