// **********************************************************************
//
// Copyright (c) 2001
// MutableRealms, Inc.
// Huntsville, AL, USA
//
// All Rights Reserved
//
// **********************************************************************

#include <string>
#include <sstream>
#include <Ice/Network.h>
#include <Ice/Security.h>
#include <Ice/SecurityException.h>
#include <Ice/SslConnectionOpenSSLClient.h>

#include <Ice/TraceLevels.h>
#include <Ice/Logger.h>

using IceSecurity::Ssl::ShutdownException;
using IceSecurity::Ssl::SystemPtr;

using namespace IceInternal;
using namespace std;

using std::string;
using std::ostringstream;
using std::hex;
using std::dec;

////////////////////////////////////////////////
////////// SslConnectionOpenSSLClient //////////
////////////////////////////////////////////////

//
// Public Methods
//

IceSecurity::Ssl::OpenSSL::ClientConnection::ClientConnection(SSL* connection, const SystemPtr& system) :
                                            Connection(connection, system)
{
}

IceSecurity::Ssl::OpenSSL::ClientConnection::~ClientConnection()
{
    ICE_METHOD_INV("OpenSSL::ClientConnection::~ClientConnection()");

    ICE_METHOD_RET("OpenSSL::ClientConnection::~ClientConnection()");
}

void
IceSecurity::Ssl::OpenSSL::ClientConnection::shutdown()
{
    ICE_METHOD_INV("OpenSSL::ClientConnection::shutdown()");

    Connection::shutdown();

    ICE_METHOD_RET("OpenSSL::ClientConnection::shutdown()");
}

int
IceSecurity::Ssl::OpenSSL::ClientConnection::init(int timeout)
{
    ICE_METHOD_INV("OpenSSL::ClientConnection::init()");

    int retCode = SSL_is_init_finished(_sslConnection);

    while (!retCode)
    {
        int i = 0;

        _readTimeout = timeout > _handshakeReadTimeout ? timeout : _handshakeReadTimeout;

        if (_initWantRead)
        {
            i = readSelect(_readTimeout);
        }
        else if (_initWantWrite)
        {
            i = writeSelect(timeout);
        }

        if (_initWantRead && i == 0)
        {
            return 0;
        }

        if (_initWantWrite && i == 0)
        {
            return 0;
        }

        _initWantRead = 0;
        _initWantWrite = 0;

        int result = connect();

        // Find out what the error was (if any).
        int code = getLastError();

        printGetError(code);

        switch (code)
        {
            case SSL_ERROR_WANT_READ:
            {
                _initWantRead = 1;
                break;
            }

            case SSL_ERROR_WANT_WRITE:
            {
                _initWantWrite = 1;
                break;
            }

            
            case SSL_ERROR_NONE:
            case SSL_ERROR_WANT_X509_LOOKUP:
            {
                // Retry connect.
                break;
            }

            case SSL_ERROR_SYSCALL:
            {
                // This is a SOCKET_ERROR, but we don't use
                // this define here as OpenSSL doesn't refer
                // to it as a SOCKET_ERROR (but that's what it is
                // if you look at their code).
                if(result == -1)
                {
                    // IO Error in underlying BIO

                    if (interrupted())
                    {
                        break;
                    }

                    if (wouldBlock())
                    {
                        readSelect(_readTimeout);
                        break;
                    }

                    if (connectionLost())
                    {
                        ICE_DEV_DEBUG("ClientConnection::init(): Throwing ConnectionLostException... SslConnectionOpenSSLClient.cpp, 177");
                        ConnectionLostException ex(__FILE__, __LINE__);
                        ex.error = getSocketErrno();
                        throw ex;
                    }
                    else
                    {
                        ICE_DEV_DEBUG("ClientConnection::init(): Throwing SocketException... SslConnectionOpenSSLClient.cpp, 184");
                        SocketException ex(__FILE__, __LINE__);
                        ex.error = getSocketErrno();
                        throw ex;
                    }
                }
                else    // result == 0
                {
                    ProtocolException protocolEx(__FILE__, __LINE__);

                    // Protocol Error: Unexpected EOF
                    protocolEx._message = "Encountered an EOF during handshake that violates the SSL Protocol.\n";

                    ICE_SSLERRORS(protocolEx._message);
                    ICE_EXCEPTION(protocolEx._message);

                    throw protocolEx;
                }
            }

            case SSL_ERROR_SSL:
            {
                ProtocolException protocolEx(__FILE__, __LINE__);

                protocolEx._message = "Encountered a violation of the SSL Protocol during handshake.\n";

                ICE_SSLERRORS(protocolEx._message);
                ICE_EXCEPTION(protocolEx._message);

                throw protocolEx;
            }
        }

        retCode = SSL_is_init_finished(_sslConnection);

        if (retCode > 0)
        {
            // Init finished, look at the connection information.
            showConnectionInfo();
        }
    }

    ICE_METHOD_RET("OpenSSL::ClientConnection::init()");

    return retCode;
}

int
IceSecurity::Ssl::OpenSSL::ClientConnection::read(Buffer& buf, int timeout)
{
    ICE_METHOD_INV("OpenSSL::ClientConnection::read(Buffer&,int)");

    int totalBytesRead = 0;

    // Initialization to 1 is a cheap trick to ensure we enter the loop.
    int bytesRead = 1;

    // We keep reading until we're done.
    while ((buf.i != buf.b.end()) && bytesRead)
    {
        // Copy over bytes from _inBuffer to buf.
        bytesRead = readInBuffer(buf);

        // Nothing in the _inBuffer?
        if (!bytesRead)
        {
            // Read from SSL.
            bytesRead = readSSL(buf, timeout);
        }

        // Keep track of the total number of bytes read.
        totalBytesRead += bytesRead;
    }

    ICE_METHOD_RET("OpenSSL::ClientConnection::read(Buffer&,int)");

    return totalBytesRead;
}

int
IceSecurity::Ssl::OpenSSL::ClientConnection::write(Buffer& buf, int timeout)
{
    ICE_METHOD_INV("OpenSSL::ClientConnection::write(Buffer&,int)");

    int totalBytesWritten = 0;
    int bytesWritten = 0;

    int packetSize = buf.b.end() - buf.i;

#ifdef WIN32
    //
    // Limit packet size to avoid performance problems on WIN32.
    // (blatantly ripped off from Marc Laukien)
    //
    if (packetSize > 64 * 1024)
    {
        packetSize = 64 * 1024;
    }
#endif

    int initReturn = 0;

    // We keep reading until we're done
    while (buf.i != buf.b.end())
    {
        // Ensure we're initialized.
        initReturn = initialize(timeout);

        if (initReturn <= 0)
        {
            // Retry the initialize call
            continue;
        }

        // initReturn must be > 0, so we're okay to try a write

        // Perform a select on the socket.
        if (!writeSelect(timeout))
        {
            // We're done here.
            break;
        }

        bytesWritten = sslWrite((char *)buf.i, packetSize);

        switch (getLastError())
        {
            case SSL_ERROR_NONE:
            {
                if (bytesWritten > 0)
                {
                    if (_traceLevels->network >= 3)
                    {
                        ostringstream s;
                        s << "sent " << bytesWritten << " of " << packetSize;
                        s << " bytes via ssl\n" << fdToString(SSL_get_fd(_sslConnection));
                       _logger->trace(_traceLevels->networkCat, s.str());
                    }

                    totalBytesWritten += bytesWritten;

                    buf.i += bytesWritten;

                    if (packetSize > buf.b.end() - buf.i)
                    {
                        packetSize = buf.b.end() - buf.i;
                    }
                }
                else
                {
                    // TODO: The client application performs a cleanup at this point,
                    //       not even shutting down SSL - it just frees the SSL
                    //       structure. I'm ignoring this, at the moment, as I'm sure
                    //       the demo is handling it in an artificial manner.

                    ICE_PROTOCOL("Error SSL_ERROR_NONE: Repeating as per protocol.");
                }
                continue;
            }

            case SSL_ERROR_WANT_WRITE:
            {
                // Repeat with the same arguments! (as in the OpenSSL documentation)
                // Whatever happened, the last write didn't actually write anything
                // for us.  This is effectively a retry.

                ICE_PROTOCOL("Error SSL_ERROR_WANT_WRITE: Repeating as per protocol.");

                continue;
            }

            case SSL_ERROR_WANT_READ:
            {
                // If we get this error here, it HAS to be because
                // the protocol wants to do something handshake related.
                // In the case that we might actually get some application data,
                // we will use the base SSL read method, using the _inBuffer.

                ICE_PROTOCOL("Error SSL_ERROR_WANT_READ.");

                readSSL(_inBuffer, timeout);

                continue;
            }

            case SSL_ERROR_WANT_X509_LOOKUP:
            {
                // Perform another read.  The read should take care of this.

                ICE_PROTOCOL("Error SSL_ERROR_WANT_X509_LOOKUP: Repeating as per protocol.");

                continue;
            }

            case SSL_ERROR_SYSCALL:
            {
                // NOTE:  The demo client only throws an exception if there were actually bytes
                //        written.  This is considered to be an error status requiring shutdown.
                //        If nothing was written, the demo client stops writing - we continue.
                //        This is potentially something wierd to watch out for.
                if (bytesWritten == -1)
                {
                    // IO Error in underlying BIO

                    if (interrupted())
                    {
                        break;
                    }

                    if (wouldBlock())
	            {
                        break;
                    }

                    if (connectionLost())
	            {
                        ICE_DEV_DEBUG("ClientConnection::write(): Throwing ConnectionLostException... SslConnectionOpenSSLClient.cpp, 390");
		        ConnectionLostException ex(__FILE__, __LINE__);
		        ex.error = getSocketErrno();
		        throw ex;
	            }
	            else
	            {
                        ICE_DEV_DEBUG("ClientConnection::write(): Throwing SocketException... SslConnectionOpenSSLClient.cpp, 397");
		        SocketException ex(__FILE__, __LINE__);
		        ex.error = getSocketErrno();
		        throw ex;
	            }
                }
                else if (bytesWritten > 0)
                {
                    ProtocolException protocolEx(__FILE__, __LINE__);

                    // Protocol Error: Unexpected EOF
                    protocolEx._message = "Encountered an EOF that violates the SSL Protocol.\n";

                    ICE_SSLERRORS(protocolEx._message);
                    ICE_EXCEPTION(protocolEx._message);

                    throw protocolEx;
                }
                else // bytesWritten == 0
                {
                    // Didn't write anything, continue, should be fine.

                    ICE_PROTOCOL("Error SSL_ERROR_SYSCALL: Repeating as per protocol.");

                    break;
                }
            }

            case SSL_ERROR_SSL:
            {
                ProtocolException protocolEx(__FILE__, __LINE__);

                protocolEx._message = "Encountered a violation of the SSL Protocol.\n";

                ICE_SSLERRORS(protocolEx._message);
                ICE_EXCEPTION(protocolEx._message);

                throw protocolEx;
            }

            case SSL_ERROR_ZERO_RETURN:
            {
                ICE_EXCEPTION("SSL_ERROR_ZERO_RETURN");

		ConnectionLostException ex(__FILE__, __LINE__);
		ex.error = getSocketErrno();
		throw ex;
            }
        }
    }

    ICE_METHOD_RET("OpenSSL::ClientConnection::write(Buffer&,int)");

    return totalBytesWritten;
}

//
// Protected Methods
//

// This code blatantly stolen from OpenSSL demos, slightly repackaged, and completely ugly...
void
IceSecurity::Ssl::OpenSSL::ClientConnection::showConnectionInfo()
{
    ICE_METHOD_INV("OpenSSL::ClientConnection::showConnectionInfo()");

    // Only in extreme cases do we enable this, partially because it doesn't use the Logger.
    if (ICE_SECURITY_LEVEL_PROTOCOL_DEBUG && 0)
    {
        ICE_PROTOCOL_DEBUG("Begin Connection Information");

        BIO* bio = BIO_new_fp(stdout, BIO_NOCLOSE);

        showCertificateChain(bio);

        showPeerCertificate(bio,"Client");

        // Something extra for the client
        showClientCAList(bio, "Client");

        showSharedCiphers(bio);

        showSelectedCipherInfo(bio);

        showHandshakeStats(bio);

        showSessionInfo(bio);

        ICE_PROTOCOL_DEBUG("End of Connection Information");

        if (bio != 0)
        {
            BIO_free(bio);
            bio = 0;
        }
    }

    ICE_METHOD_RET("OpenSSL::ClientConnection::showConnectionInfo()");
}
