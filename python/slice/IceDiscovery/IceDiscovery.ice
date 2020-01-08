//
// Copyright (c) ZeroC, Inc. All rights reserved.
//

#pragma once

[["cpp:doxygen:include:IceDiscovery/IceDiscovery.h"]]
[["cpp:header-ext:h"]]

[["ice-prefix"]]

[["js:module:ice"]]

[["python:pkgdir:IceDiscovery"]]

#include <Ice/Identity.ice>

[["java:package:com.zeroc"]]

module IceDiscovery
{

interface LookupReply
{
    void foundObjectById(Ice::Identity id, Object* prx);

    void foundAdapterById(string id, Object* prx, bool isReplicaGroup);
}

interface Lookup
{
    idempotent void findObjectById(string domainId, Ice::Identity id, LookupReply* reply);

    idempotent void findAdapterById(string domainId, string id, LookupReply* reply);
}

}