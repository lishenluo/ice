# **********************************************************************
#
# Copyright (c) 2003-2014 ZeroC, Inc. All rights reserved.
#
# This copy of Ice is licensed to you under the terms described in the
# ICE_LICENSE file included in this distribution.
#
# **********************************************************************

%define ruby 0
%define mono 0

%if "%{dist}" == ".el6"
  %define ruby 1
%endif
%if "%{dist}" == ".el7"
  %define ruby 1
%endif
%if "%{dist}" == ".amzn1"
  %define ruby 1
%endif
%if "%{dist}" == ".sles11"
  %define ruby 1
#  %define mono 1
%endif

%define buildall 1
%define makeopts -j1

%define core_arches %{ix86} x86_64

#
# See http://fedoraproject.org/wiki/Packaging/Python
#
# We put everything in sitearch because we're building a single
# ice-python arch-specific package.
#
%{!?python_sitearch: %define python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}

%if %{ruby}
#
# See http://fedoraproject.org/wiki/Packaging/Ruby
#
# We put everything in sitearch because we're building a single
# ice-ruby arch-specific package.
#
%if "%{dist}" == ".el7"
%{!?ruby_sitearch: %define ruby_sitearch %(ruby -rrbconfig -e 'puts RbConfig::CONFIG["sitearchdir"]')}
%else
%{!?ruby_sitearch: %define ruby_sitearch %(ruby -rrbconfig -e 'puts Config::CONFIG["sitearchdir"]')}
%endif
%endif

Name: ice
Version: 3.6b
Summary: Files common to all Ice packages 
Release: 1%{?dist}
License: GPL with exceptions
Group: System Environment/Libraries
Vendor: ZeroC, Inc.
URL: http://www.zeroc.com/
Source0: Ice-%{version}.tar.gz
Source1: Ice-rpmbuild-%{version}.tar.gz

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%define soversion 36b
%define dotnetversion 3.6.51
%define mmversion 3.6

%define commonversion 1.8.0
%define formsversion 1.8.0
%define looksversion 2.6.0

#
# RHEL7 includes Berkeley DB 5.3.21, on other platforms we supply 5.3.28.
#
%if "%{dist}" == ".el7"
%define dbversion 5.3.21
%else
%define dbversion 5.3.28
%endif

BuildRequires: openssl-devel >= 0.9.7a
BuildRequires: mcpp-devel >= 2.7.2

%if "%{dist}" == ".el7"
BuildRequires: libdb-cxx-devel >= %{dbversion}, libdb-java-devel >= %{dbversion}
BuildRequires: javapackages-tools
BuildRequires: ant
%else
BuildRequires: db53-devel >= %{dbversion}, db53-java >= %{dbversion}
BuildRequires: jpackage-utils
%endif

#
# Prerequisites for building Ice for Java:
#
# - a recent version of ant
# - %{_javadir}/jgoodies-common-%{commonversion}.jar
# - %{_javadir}/jgoodies-forms-%{formsversion}.jar
# - %{_javadir}/jgoodies-looks-%{looksversion}.jar
# - %{_javadir}/proguard.jar
#
# Use find-jar to verify that the JAR files are present:
#
# $ find-jar proguard.jar
#

%if %{ruby}
BuildRequires: ruby-devel
%endif

%if %{mono}
BuildRequires: mono-core >= 2.0.1, mono-devel >= 2.0.1
%endif

%if "%{dist}" == ".el6"
BuildRequires: bzip2-devel >= 1.0.5
BuildRequires: expat-devel >= 2.0.1
BuildRequires: php-devel >= 5.3.2
BuildRequires: python-devel >= 2.6.5
%endif
%if "%{dist}" == ".el7"
BuildRequires: bzip2-devel >= 1.0.6
BuildRequires: expat-devel >= 2.1
BuildRequires: php-devel >= 5.4
BuildRequires: python-devel >= 2.7
%endif
%if "%{dist}" == ".amzn1"
BuildRequires: bzip2-devel >= 1.0.6
BuildRequires: expat-devel >= 2.0.1
BuildRequires: php-devel >= 5.3.2
BuildRequires: php-devel < 5.4
BuildRequires: python-devel >= 2.6.5
%endif
%if "%{dist}" == ".sles11"
BuildRequires: php53-devel >= 5.3.0
BuildRequires: python-devel >= 2.6.0
%endif

%description
Ice is a modern object-oriented toolkit that enables you to build
distributed applications with minimal effort. Ice allows you to focus
your efforts on your application logic while it takes care of all
interactions with low-level network programming interfaces. With Ice,
there is no need to worry about details such as opening network
connections, serializing and deserializing data for network
transmission, or retrying failed connection attempts (to name but a
few of dozens of such low-level details).

#
# We create both noarch and arch-specific packages for these GAC files.
# Please delete the arch-specific packages after the build: we create
# them only to keep rpmbuild happy (it does not want to create dangling
# symbolic links (the GAC symlinks used for development)).
#
%if %{mono}
%package mono
Summary: The Ice run time for .NET (mono)
Group: System Environment/Libraries
Requires: ice = %{version}-%{release}, mono-core >= 1.2.2
Obsoletes: ice-dotnet < %{version}-%{release}
%description mono
The Ice run time for .NET (mono).
%endif

#
# Arch-independent packages
#
%ifarch noarch
%package -n libice3.6-java
Summary: The Ice run time libraries for Java.
Group: System Environment/Libraries
%description -n libice3.6-java
The Ice run time libraries for Java.

%package -n libfreeze3.6-java
Summary: The Freeze library for Java.
Group: System Environment/Libraries
Requires: libice3.6-java = %{version}-%{release}
%if "%{dist}" == ".el7"
Requires: libdb-java
%else
Requires: db53-java
%endif
%description -n libfreeze3.6-java
The Freeze library for Java.

%package -n libice-js
Summary: The Ice run time libraries for JavaScript.
Group: System Environment/Libraries
%description -n libice-js
The Ice run time libraries for JavaScript.

%package slice
Summary: Slice files for the Ice run time
Group: System Environment/Libraries
%description slice
Slice files for the Ice run time.

%package utils-java
Summary: Java-based Ice utilities and admin tools.
Group: Applications/System
%description utils-java
Graphical IceGrid administrative tool and command-line
certificate authority utility.
%endif

#
# Arch-dependent packages
#
%ifarch %{core_arches}
%package -n libice3.6
Summary: The Ice run time libraries for C++.
Group: System Environment/Libraries
Requires: bzip2
%description -n libice3.6
The Ice run time libraries for C++.

%package -n libfreeze3.6
Summary: The Freeze library for C++.
Group: System Environment/Libraries
Requires: libice3.6 = %{version}-%{release}
%if "%{dist}" == ".el7"
Requires: libdb
%else
Requires: db53
%endif
%description -n libfreeze3.6
The Freeze library for C++.

%package utils
Summary: Ice utilities and admin tools.
Group: Applications/System
Requires: libfreeze3.6 = %{version}-%{release}
%description utils
Command-line administrative tools to manage Ice servers (IceGrid,
IceStorm, IceBox, etc.), plus various Ice-related utilities.

%package -n icegrid
Summary: IceGrid servers.
Group: System Environment/Daemons
Requires: ice-utils = %{version}-%{release}
# Requirements for the users
%if "%{dist}" == ".sles11"
Requires(pre): pwdutils
%else
Requires(pre): shadow-utils
%endif
# Requirements for the init.d services
Requires(post): /sbin/chkconfig
Requires(preun): /sbin/chkconfig
Requires(preun): /sbin/service
%description -n icegrid
IceGrid servers.

%package -n icebox
Summary: IceBox server.
Group: System Environment/Daemons
Requires: ice-utils = %{version}-%{release}
# Requirements for the users
%if "%{dist}" == ".sles11"
Requires(pre): pwdutils
%else
Requires(pre): shadow-utils
%endif
# Requirements for the init.d services
Requires(post): /sbin/chkconfig
Requires(preun): /sbin/chkconfig
Requires(preun): /sbin/service
%description -n icebox
IceBox server.

%package -n glacier2
Summary: Glacier2 server.
Group: System Environment/Daemons
# Requirements for the users
%if "%{dist}" == ".sles11"
Requires(pre): pwdutils
%else
Requires(pre): shadow-utils
%endif
# Requirements for the init.d services
Requires(post): /sbin/chkconfig
Requires(preun): /sbin/chkconfig
Requires(preun): /sbin/service
%description -n glacier2
Glacier2 server.

%package -n icepatch2
Summary: IcePatch2 server.
Group: System Environment/Daemons
Requires: ice-utils = %{version}-%{release}
# Requirements for the users
%if "%{dist}" == ".sles11"
Requires(pre): pwdutils
%else
Requires(pre): shadow-utils
%endif
# Requirements for the init.d services
Requires(post): /sbin/chkconfig
Requires(preun): /sbin/chkconfig
Requires(preun): /sbin/service
%description -n icepatch2
IcePatch2 server.

%package -n libicestorm3.6
Summary: IceStorm service.
Group: System Environment/Libraries
Requires: icebox = %{version}-%{release}, libfreeze3.6 = %{version}-%{release}
%description -n libicestorm3.6
IceStorm service.

%package -n libice-cxx-devel
Summary: Tools, libraries and headers for developing Ice applications in C++.
Group: Development/Tools
Requires: libice3.6 = %{version}-%{release}, ice-slice = %{version}-%{release}
%description -n libice-cxx-devel
Tools, libraries and headers for developing Ice applications in C++.

%package -n libice-java-devel
Summary: Tools for developing Ice applications in Java.
Group: Development/Tools
Requires: libice3.6-java = %{version}-%{release}, libice3.6 = %{version}-%{release}, ice-slice = %{version}-%{release}
%description -n libice-java-devel
Tools for developing Ice applications in Java.

%package -n libice-js-devel
Summary: Tools for developing Ice applications in JavaScript.
Group: Development/Tools
Requires: libice-js = %{version}-%{release}, libice3.6 = %{version}-%{release}, ice-slice = %{version}-%{release}
%description -n libice-js-devel
Tools for developing Ice applications in JavaScript.

%if %{mono}
%package libice-mono-devel
Summary: Tools for developing Ice applications in C#.
Group: Development/Tools
Requires: ice-mono = %{version}-%{release}, libice3.6 = %{version}-%{release}, pkgconfig, ice-slice = %{version}-%{release}
Obsoletes: ice-csharp-devel < %{version}-%{release}
%description libice-mono-devel
Tools for developing Ice applications in C#.
%endif

%if %{ruby}
%package ruby
Summary: The Ice run time for Ruby.
Group: System Environment/Libraries
Requires: libice3.6 = %{version}-%{release}
#
# Amazon Linux 2014.03 defaults to Ruby 2.0
#
%if "%{dist}" == ".amzn1"
Requires: ruby18
%else
Requires: ruby
%endif
%description ruby
The Ice run time for Ruby.

%package ruby-devel
Summary: Tools for developing Ice applications in Ruby.
Group: Development/Tools
Requires: ice-ruby = %{version}-%{release}, ice-slice = %{version}-%{release}
%description ruby-devel
Tools for developing Ice applications in Ruby.
%endif

%package python
Summary: The Ice run time for Python.
Group: System Environment/Libraries
Requires: libice3.6 = %{version}-%{release}, python
%description python
The Ice run time for Python.

%package python-devel
Summary: Tools for developing Ice applications in Python.
Group: Development/Tools
Requires: ice-python = %{version}-%{release}, ice-slice = %{version}-%{release}
%description python-devel
Tools for developing Ice applications in Python.

%package php
Summary: The Ice run time for PHP.
Group: System Environment/Libraries
Requires: libice3.6 = %{version}-%{release}
%if "%{dist}" == ".sles11"
Requires: php53
%endif
%if "%{dist}" == ".el6"
Requires: php
%endif
%if "%{dist}" == ".el7"
Requires: php
%endif
%if "%{dist}" == ".amzn1"
Requires: php < 5.4
%endif
%description php
The Ice run time for PHP.

%package php-devel
Summary: Tools for developing Ice applications in PHP.
Group: Development/Tools
Requires: ice-php = %{version}-%{release}, ice-slice = %{version}-%{release}
%description php-devel
Tools for developing Ice applications in PHP.
%endif

%prep

%if %{buildall}
%setup -n Ice-%{version} -q
%setup -q -n Ice-rpmbuild-%{version} -T -b 1
%endif

%build

%ifarch %{core_arches}

cd $RPM_BUILD_DIR/Ice-%{version}/cpp/src
make %{makeopts} OPTIMIZE=yes embedded_runpath_prefix=""

cd $RPM_BUILD_DIR/Ice-%{version}/py
make %{makeopts} OPTIMIZE=yes embedded_runpath_prefix=""

cd $RPM_BUILD_DIR/Ice-%{version}/php
make %{makeopts} OPTIMIZE=yes embedded_runpath_prefix=""

%if %{ruby}
cd $RPM_BUILD_DIR/Ice-%{version}/rb
make %{makeopts} OPTIMIZE=yes embedded_runpath_prefix=""
%endif

# Build the ant tasks JAR because it's included in the java-devel package
cd $RPM_BUILD_DIR/Ice-%{version}/java
ant tasks

%else

#
# Build only what we need in C++.
#
cd $RPM_BUILD_DIR/Ice-%{version}/cpp/src/IceUtil
make %{makeopts} OPTIMIZE=yes embedded_runpath_prefix=""

cd $RPM_BUILD_DIR/Ice-%{version}/cpp/src/Slice
make %{makeopts} OPTIMIZE=yes embedded_runpath_prefix=""

cd $RPM_BUILD_DIR/Ice-%{version}/cpp/src/slice2java
make %{makeopts} OPTIMIZE=yes embedded_runpath_prefix=""

cd $RPM_BUILD_DIR/Ice-%{version}/cpp/src/slice2js
make %{makeopts} OPTIMIZE=yes embedded_runpath_prefix=""

cd $RPM_BUILD_DIR/Ice-%{version}/cpp/src/slice2freezej
make %{makeopts} OPTIMIZE=yes embedded_runpath_prefix=""

%if %{mono}
cd $RPM_BUILD_DIR/Ice-%{version}/cpp/src/slice2cs
make %{makeopts} OPTIMIZE=yes embedded_runpath_prefix=""
%endif

cd $RPM_BUILD_DIR/Ice-%{version}/java
%if "%{dist}" == ".el7"
export CLASSPATH=`build-classpath db jgoodies-common-%{commonversion} jgoodies-forms-%{formsversion} jgoodies-looks-%{looksversion} proguard`
%else
export CLASSPATH=`build-classpath db-%{dbversion} jgoodies-common-%{commonversion} jgoodies-forms-%{formsversion} jgoodies-looks-%{looksversion} proguard`
%endif
JGOODIES_COMMON=`find-jar jgoodies-common-%{commonversion}`
JGOODIES_FORMS=`find-jar jgoodies-forms-%{formsversion}`
JGOODIES_LOOKS=`find-jar jgoodies-looks-%{looksversion}`
ant -Djgoodies.common=$JGOODIES_COMMON -Djgoodies.forms=$JGOODIES_FORMS -Djgoodies.looks=$JGOODIES_LOOKS dist-jar

cd $RPM_BUILD_DIR/Ice-%{version}/js
make

# 
# Define the environment variable KEYFILE to strong-name sign the
# assemblies with your own key file.
#

%if %{mono}
cd $RPM_BUILD_DIR/Ice-%{version}/cs/src
make %{makeopts} OPTIMIZE=yes
%endif

%endif


%install

rm -rf $RPM_BUILD_ROOT

#
# Arch-specific packages
#
%ifarch %{core_arches}

#
# C++
#
mkdir -p $RPM_BUILD_ROOT/lib

cd $RPM_BUILD_DIR/Ice-%{version}/cpp
make prefix=$RPM_BUILD_ROOT embedded_runpath_prefix="" install

mkdir -p $RPM_BUILD_ROOT%{_bindir}
mv $RPM_BUILD_ROOT/bin/* $RPM_BUILD_ROOT%{_bindir}

mkdir -p $RPM_BUILD_ROOT%{_libdir}
mv $RPM_BUILD_ROOT/%_lib/* $RPM_BUILD_ROOT%{_libdir}
mkdir -p $RPM_BUILD_ROOT%{_includedir}
mv $RPM_BUILD_ROOT/include/* $RPM_BUILD_ROOT%{_includedir}

#
# Python
#
cd $RPM_BUILD_DIR/Ice-%{version}/py
make prefix=$RPM_BUILD_ROOT embedded_runpath_prefix="" install

mkdir -p $RPM_BUILD_ROOT%{python_sitearch}/Ice
mv $RPM_BUILD_ROOT/python/* $RPM_BUILD_ROOT%{python_sitearch}/Ice
cp -p $RPM_BUILD_DIR/Ice-rpmbuild-%{version}/ice.pth $RPM_BUILD_ROOT%{python_sitearch}

#
# PHP
#
cd $RPM_BUILD_DIR/Ice-%{version}/php
make prefix=$RPM_BUILD_ROOT install

%if "%{dist}" == ".el6"
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/php.d
cp -p $RPM_BUILD_DIR/Ice-rpmbuild-%{version}/ice.ini $RPM_BUILD_ROOT%{_sysconfdir}/php.d
mkdir -p $RPM_BUILD_ROOT%{_libdir}/php/modules
mv $RPM_BUILD_ROOT/php/IcePHP.so $RPM_BUILD_ROOT%{_libdir}/php/modules
mkdir -p $RPM_BUILD_ROOT%{_datadir}/php
mv $RPM_BUILD_ROOT/php/* $RPM_BUILD_ROOT%{_datadir}/php
%endif

%if "%{dist}" == ".el7"
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/php.d
cp -p $RPM_BUILD_DIR/Ice-rpmbuild-%{version}/ice.ini $RPM_BUILD_ROOT%{_sysconfdir}/php.d
mkdir -p $RPM_BUILD_ROOT%{_libdir}/php/modules
mv $RPM_BUILD_ROOT/php/IcePHP.so $RPM_BUILD_ROOT%{_libdir}/php/modules
mkdir -p $RPM_BUILD_ROOT%{_datadir}/php
mv $RPM_BUILD_ROOT/php/* $RPM_BUILD_ROOT%{_datadir}/php
%endif

%if "%{dist}" == ".amzn1"
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/php.d
cp -p $RPM_BUILD_DIR/Ice-rpmbuild-%{version}/ice.ini $RPM_BUILD_ROOT%{_sysconfdir}/php.d
mkdir -p $RPM_BUILD_ROOT%{_libdir}/php/modules
mv $RPM_BUILD_ROOT/php/IcePHP.so $RPM_BUILD_ROOT%{_libdir}/php/modules
mkdir -p $RPM_BUILD_ROOT%{_datadir}/php
mv $RPM_BUILD_ROOT/php/* $RPM_BUILD_ROOT%{_datadir}/php
%endif

%if "%{dist}" == ".sles11"
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/php5/conf.d
cp -p $RPM_BUILD_DIR/Ice-rpmbuild-%{version}/ice.ini $RPM_BUILD_ROOT%{_sysconfdir}/php5/conf.d
mkdir -p $RPM_BUILD_ROOT%{_libdir}/php5/extensions
mv $RPM_BUILD_ROOT/php/IcePHP.so $RPM_BUILD_ROOT%{_libdir}/php5/extensions
mkdir -p $RPM_BUILD_ROOT%{_datadir}/php5
mv $RPM_BUILD_ROOT/php/* $RPM_BUILD_ROOT%{_datadir}/php5
%endif

#
# Ruby
# 
%if %{ruby}
cd $RPM_BUILD_DIR/Ice-%{version}/rb
make prefix=$RPM_BUILD_ROOT embedded_runpath_prefix="" install
mkdir -p $RPM_BUILD_ROOT%{ruby_sitearch}
mv $RPM_BUILD_ROOT/ruby/* $RPM_BUILD_ROOT%{ruby_sitearch}
%endif

#
# ant-ice.jar
#
mkdir -p $RPM_BUILD_ROOT%{_javadir}
cp -p $RPM_BUILD_DIR/Ice-%{version}/java/lib/ant-ice.jar $RPM_BUILD_ROOT%{_javadir}/ant-ice-%{version}.jar
ln -s ant-ice-%{version}.jar $RPM_BUILD_ROOT%{_javadir}/ant-ice.jar 

#
# JavaScript - for the -devel RPM
#
cd $RPM_BUILD_DIR/Ice-%{version}/js
make prefix=$RPM_BUILD_ROOT install
mkdir -p $RPM_BUILD_ROOT%{_datadir}/javascript/ice-%{mmversion}
mv $RPM_BUILD_ROOT/lib/Ice.js $RPM_BUILD_ROOT%{_datadir}/javascript/ice-%{mmversion}
mv $RPM_BUILD_ROOT/lib/Ice.js.gz $RPM_BUILD_ROOT%{_datadir}/javascript/ice-%{mmversion}
mv $RPM_BUILD_ROOT/lib/Glacier2.js $RPM_BUILD_ROOT%{_datadir}/javascript/ice-%{mmversion}
mv $RPM_BUILD_ROOT/lib/Glacier2.js.gz $RPM_BUILD_ROOT%{_datadir}/javascript/ice-%{mmversion}
mv $RPM_BUILD_ROOT/lib/IceStorm.js $RPM_BUILD_ROOT%{_datadir}/javascript/ice-%{mmversion}
mv $RPM_BUILD_ROOT/lib/IceStorm.js.gz $RPM_BUILD_ROOT%{_datadir}/javascript/ice-%{mmversion}
mv $RPM_BUILD_ROOT/lib/IceGrid.js $RPM_BUILD_ROOT%{_datadir}/javascript/ice-%{mmversion}
mv $RPM_BUILD_ROOT/lib/IceGrid.js.gz $RPM_BUILD_ROOT%{_datadir}/javascript/ice-%{mmversion}
rm -rf $RPM_BUILD_ROOT/node_modules

%if %{mono}

#
# Mono: for iceboxnet.exe and GAC symlinks
#
cd $RPM_BUILD_DIR/Ice-%{version}/cs
make prefix=$RPM_BUILD_ROOT GACINSTALL=yes GAC_ROOT=$RPM_BUILD_ROOT%{_prefix}/lib install
for f in Ice Glacier2 IceBox IceGrid IcePatch2 IceStorm
do
    #mv $RPM_BUILD_ROOT/Assemblies/$f.xml $RPM_BUILD_ROOT%{_prefix}/lib/mono/gac/$f/%{dotnetversion}.*/
    mv $RPM_BUILD_ROOT%{_prefix}/lib/mono/$f/$f.xml $RPM_BUILD_ROOT%{_prefix}/lib/mono/gac/$f/%{dotnetversion}.*/
done
mv $RPM_BUILD_ROOT/bin/* $RPM_BUILD_ROOT%{_bindir}

#
# .NET spec files (for mono-devel)
#
if test ! -d $RPM_BUILD_ROOT%{_libdir}/pkgconfig
then
    mv $RPM_BUILD_ROOT/lib/pkgconfig $RPM_BUILD_ROOT%{_libdir}
fi

%endif

#
# initrd files (for servers)
#
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}
cp $RPM_BUILD_DIR/Ice-rpmbuild-%{version}/*.conf $RPM_BUILD_ROOT%{_sysconfdir}
mkdir -p $RPM_BUILD_ROOT%{_initrddir}
for i in icegridregistry icegridnode glacier2router
do
    cp $RPM_BUILD_DIR/Ice-rpmbuild-%{version}/$i.%{_vendor} $RPM_BUILD_ROOT%{_initrddir}/$i
done

#
# Some python scripts and related files
#
mkdir -p $RPM_BUILD_ROOT%{_datadir}/Ice-%{version}
mv $RPM_BUILD_ROOT/config/* $RPM_BUILD_ROOT%{_datadir}/Ice-%{version}

#
# Man pages
#
mkdir -p $RPM_BUILD_ROOT%{_mandir}/man1
# TODO: We should really do this:
#mv -f $RPM_BUILD_ROOT/man/man1/* $RPM_BUILD_ROOT%{_mandir}/man1
rm -r $RPM_BUILD_ROOT/man
cp -p $RPM_BUILD_DIR/Ice-%{version}/man/man1/*.1 $RPM_BUILD_ROOT%{_mandir}/man1

#
# Cleanup extra files
#
rm -f $RPM_BUILD_ROOT/CHANGES
rm -f $RPM_BUILD_ROOT/ICE_LICENSE
rm -f $RPM_BUILD_ROOT/LICENSE
rm -f $RPM_BUILD_ROOT/RELEASE_NOTES
rm -fr $RPM_BUILD_ROOT/doc/reference
rm -fr $RPM_BUILD_ROOT/slice
rm -f $RPM_BUILD_ROOT%{_libdir}/libIceStormService.so
rm -f $RPM_BUILD_ROOT%{_libdir}/libIceDiscovery.so
rm -f $RPM_BUILD_ROOT%{_libdir}/libGlacier2CryptPermissionsVerifier.so
rm -f $RPM_BUILD_ROOT%{_libdir}/libIceXML.so

%if !%{mono}
rm -f $RPM_BUILD_ROOT%{_bindir}/slice2cs
rm -f $RPM_BUILD_ROOT%{_mandir}/man1/slice2cs.1
rm -f $RPM_BUILD_ROOT%{_mandir}/man1/iceboxnet.1
%endif

%if !%{ruby}
rm -f $RPM_BUILD_ROOT%{_bindir}/slice2rb
%endif

%endif

#
# Arch-independent packages
#
%ifarch noarch

#
# Doc
#
mkdir -p $RPM_BUILD_ROOT%{_defaultdocdir}/%{name}-%{version}
cp -p $RPM_BUILD_DIR/Ice-%{version}/RELEASE_NOTES $RPM_BUILD_ROOT%{_defaultdocdir}/%{name}-%{version}/RELEASE_NOTES
cp -p $RPM_BUILD_DIR/Ice-%{version}/CHANGES $RPM_BUILD_ROOT%{_defaultdocdir}/%{name}-%{version}/CHANGES
cp -p $RPM_BUILD_DIR/Ice-rpmbuild-%{version}/README.Linux-RPM $RPM_BUILD_ROOT%{_defaultdocdir}/%{name}-%{version}/README
cp -p $RPM_BUILD_DIR/Ice-rpmbuild-%{version}/THIRD_PARTY_LICENSE.Linux $RPM_BUILD_ROOT%{_defaultdocdir}/%{name}-%{version}/THIRD_PARTY_LICENSE
cp -p $RPM_BUILD_DIR/Ice-rpmbuild-%{version}/SOURCES.Linux $RPM_BUILD_ROOT%{_defaultdocdir}/%{name}-%{version}/SOURCES

#
# iceca
#
mkdir -p $RPM_BUILD_ROOT%{_bindir}
cp -p $RPM_BUILD_DIR/Ice-%{version}/cpp/src/ca/iceca $RPM_BUILD_ROOT%{_bindir}
mkdir -p $RPM_BUILD_ROOT%{_datadir}/Ice-%{version}
cp -p $RPM_BUILD_DIR/Ice-%{version}/cpp/src/ca/ImportKey.class $RPM_BUILD_ROOT%{_datadir}/Ice-%{version}
mkdir -p $RPM_BUILD_ROOT%{_mandir}/man1
cp -p $RPM_BUILD_DIR/Ice-%{version}/man/man1/iceca.1 $RPM_BUILD_ROOT%{_mandir}/man1

#
# Java install (using jpackage conventions)
# 
cd $RPM_BUILD_DIR/Ice-%{version}/java
ant -Dprefix=$RPM_BUILD_ROOT install

mkdir -p $RPM_BUILD_ROOT%{_javadir}
mv $RPM_BUILD_ROOT/lib/Ice.jar $RPM_BUILD_ROOT%{_javadir}/Ice-%{version}.jar
ln -s  Ice-%{version}.jar $RPM_BUILD_ROOT%{_javadir}/Ice-%{mmversion}.jar 

mv $RPM_BUILD_ROOT/lib/Freeze.jar $RPM_BUILD_ROOT%{_javadir}/Freeze-%{version}.jar
ln -s  Freeze-%{version}.jar $RPM_BUILD_ROOT%{_javadir}/Freeze-%{mmversion}.jar

mv $RPM_BUILD_ROOT/lib/Glacier2.jar $RPM_BUILD_ROOT%{_javadir}/Glacier2-%{version}.jar
ln -s  Glacier2-%{version}.jar $RPM_BUILD_ROOT%{_javadir}/Glacier2-%{mmversion}.jar

mv $RPM_BUILD_ROOT/lib/IceBox.jar $RPM_BUILD_ROOT%{_javadir}/IceBox-%{version}.jar
ln -s  IceBox-%{version}.jar $RPM_BUILD_ROOT%{_javadir}/IceBox-%{mmversion}.jar

mv $RPM_BUILD_ROOT/lib/IceGrid.jar $RPM_BUILD_ROOT%{_javadir}/IceGrid-%{version}.jar
ln -s  IceGrid-%{version}.jar $RPM_BUILD_ROOT%{_javadir}/IceGrid-%{mmversion}.jar

mv $RPM_BUILD_ROOT/lib/IcePatch2.jar $RPM_BUILD_ROOT%{_javadir}/IcePatch2-%{version}.jar
ln -s  IcePatch2-%{version}.jar $RPM_BUILD_ROOT%{_javadir}/IcePatch2-%{mmversion}.jar

mv $RPM_BUILD_ROOT/lib/IceStorm.jar $RPM_BUILD_ROOT%{_javadir}/IceStorm-%{version}.jar
ln -s  IceStorm-%{version}.jar $RPM_BUILD_ROOT%{_javadir}/IceStorm-%{mmversion}.jar

mv $RPM_BUILD_ROOT/lib/IceDiscovery.jar $RPM_BUILD_ROOT%{_javadir}/IceDiscovery-%{version}.jar
ln -s  IceDiscovery-%{version}.jar $RPM_BUILD_ROOT%{_javadir}/IceDiscovery-%{mmversion}.jar

#
# JavaScript
#
cd $RPM_BUILD_DIR/Ice-%{version}/js
make prefix=$RPM_BUILD_ROOT OPTIMIZE=yes install
mkdir -p $RPM_BUILD_ROOT%{_datadir}/javascript/ice-%{mmversion}
mv $RPM_BUILD_ROOT/lib/Ice.min.js $RPM_BUILD_ROOT%{_datadir}/javascript/ice-%{mmversion}
mv $RPM_BUILD_ROOT/lib/Ice.min.js.gz $RPM_BUILD_ROOT%{_datadir}/javascript/ice-%{mmversion}
mv $RPM_BUILD_ROOT/lib/Glacier2.min.js $RPM_BUILD_ROOT%{_datadir}/javascript/ice-%{mmversion}
mv $RPM_BUILD_ROOT/lib/Glacier2.min.js.gz $RPM_BUILD_ROOT%{_datadir}/javascript/ice-%{mmversion}
mv $RPM_BUILD_ROOT/lib/IceStorm.min.js $RPM_BUILD_ROOT%{_datadir}/javascript/ice-%{mmversion}
mv $RPM_BUILD_ROOT/lib/IceStorm.min.js.gz $RPM_BUILD_ROOT%{_datadir}/javascript/ice-%{mmversion}
mv $RPM_BUILD_ROOT/lib/IceGrid.min.js $RPM_BUILD_ROOT%{_datadir}/javascript/ice-%{mmversion}
mv $RPM_BUILD_ROOT/lib/IceGrid.min.js.gz $RPM_BUILD_ROOT%{_datadir}/javascript/ice-%{mmversion}
rm -rf $RPM_BUILD_ROOT/node_modules
# These are only used in the -devel RPM
rm $RPM_BUILD_ROOT/lib/Ice.js
rm $RPM_BUILD_ROOT/lib/Ice.js.gz
rm $RPM_BUILD_ROOT/lib/Glacier2.js
rm $RPM_BUILD_ROOT/lib/Glacier2.js.gz
rm $RPM_BUILD_ROOT/lib/IceStorm.js
rm $RPM_BUILD_ROOT/lib/IceStorm.js.gz
rm $RPM_BUILD_ROOT/lib/IceGrid.js
rm $RPM_BUILD_ROOT/lib/IceGrid.js.gz

#
# IceGridGUI
#
cp -p $RPM_BUILD_DIR/Ice-%{version}/java/lib/IceGridGUI.jar $RPM_BUILD_ROOT%{_javadir}/IceGridGUI-%{version}.jar
ln -s IceGridGUI-%{version}.jar $RPM_BUILD_ROOT%{_javadir}/IceGridGUI.jar 
cp -p $RPM_BUILD_DIR/Ice-%{version}/java/bin/icegridgui.rpm $RPM_BUILD_ROOT%{_bindir}/icegridgui

%if %{mono}
#
# Mono
#
cd $RPM_BUILD_DIR/Ice-%{version}/cs
make prefix=$RPM_BUILD_ROOT GACINSTALL=yes GAC_ROOT=$RPM_BUILD_ROOT%{_prefix}/lib install
for f in Ice Glacier2 IceBox IceGrid IcePatch2 IceStorm
do
    #mv $RPM_BUILD_ROOT/Assemblies/$f.xml $RPM_BUILD_ROOT%{_prefix}/lib/mono/gac/$f/%{dotnetversion}.*/
    mv $RPM_BUILD_ROOT%{_prefix}/lib/mono/$f/$f.xml $RPM_BUILD_ROOT%{_prefix}/lib/mono/gac/$f/%{dotnetversion}.*/
done
%endif

#
# License files
#
mv $RPM_BUILD_ROOT/ICE_LICENSE $RPM_BUILD_ROOT%{_defaultdocdir}/%{name}-%{version}
mv $RPM_BUILD_ROOT/LICENSE $RPM_BUILD_ROOT%{_defaultdocdir}/%{name}-%{version}

#
# Slice files
#
mkdir -p $RPM_BUILD_ROOT%{_datadir}/Ice-%{version}
mv $RPM_BUILD_ROOT/slice $RPM_BUILD_ROOT%{_datadir}/Ice-%{version}

#
# Cleanup extra files
#
rm -f $RPM_BUILD_ROOT/lib/IceGridGUI.jar $RPM_BUILD_ROOT/lib/ant-ice.jar
rm -f $RPM_BUILD_ROOT/CHANGES
rm -f $RPM_BUILD_ROOT/RELEASE_NOTES

%if %{mono}

rm -f $RPM_BUILD_ROOT/bin/iceboxnet.exe
rm -r $RPM_BUILD_ROOT/man

for f in Ice Glacier2 IceBox IceGrid IcePatch2 IceStorm
do 
     rm -r $RPM_BUILD_ROOT%{_prefix}/lib/mono/$f
done

rm -r $RPM_BUILD_ROOT/lib/pkgconfig

%endif

%else # %ifarch noarch

rm -f $RPM_BUILD_ROOT/lib/ImportKey.class
rm -f $RPM_BUILD_ROOT%{_bindir}/iceca
rm -f $RPM_BUILD_ROOT%{_mandir}/man1/iceca.1

%endif

%clean
rm -rf $RPM_BUILD_ROOT

#
# mono package; see comment above about why we create
# "useless" arch-specific packages
#
%if %{mono}
%files mono
%defattr(-, root, root, -)
%dir %{_prefix}/lib/mono/gac/Glacier2
%{_prefix}/lib/mono/gac/Glacier2/%{dotnetversion}.*/
%dir %{_prefix}/lib/mono/gac/Ice
%{_prefix}/lib/mono/gac/Ice/%{dotnetversion}.*/
%dir %{_prefix}/lib/mono/gac/IceBox
%{_prefix}/lib/mono/gac/IceBox/%{dotnetversion}.*/
%dir %{_prefix}/lib/mono/gac/IceGrid
%{_prefix}/lib/mono/gac/IceGrid/%{dotnetversion}.*/
%dir %{_prefix}/lib/mono/gac/IcePatch2
%{_prefix}/lib/mono/gac/IcePatch2/%{dotnetversion}.*/
%dir %{_prefix}/lib/mono/gac/IceStorm
%{_prefix}/lib/mono/gac/IceStorm/%{dotnetversion}.*/
%dir %{_prefix}/lib/mono/gac/policy.%{mmversion}.Glacier2
%{_prefix}/lib/mono/gac/policy.%{mmversion}.Glacier2/0.*/
%dir %{_prefix}/lib/mono/gac/policy.%{mmversion}.Ice
%{_prefix}/lib/mono/gac/policy.%{mmversion}.Ice/0.*/
%dir %{_prefix}/lib/mono/gac/policy.%{mmversion}.IceBox
%{_prefix}/lib/mono/gac/policy.%{mmversion}.IceBox/0.*/
%dir %{_prefix}/lib/mono/gac/policy.%{mmversion}.IceGrid
%{_prefix}/lib/mono/gac/policy.%{mmversion}.IceGrid/0.*/
%dir %{_prefix}/lib/mono/gac/policy.%{mmversion}.IcePatch2
%{_prefix}/lib/mono/gac/policy.%{mmversion}.IcePatch2/0.*/
%dir %{_prefix}/lib/mono/gac/policy.%{mmversion}.IceStorm
%{_prefix}/lib/mono/gac/policy.%{mmversion}.IceStorm/0.*/
%endif

#
# noarch file packages
# 
%ifarch noarch
%files
# TODO: Meta package
#%defattr(-, root, root, -)
#%dir %{_datadir}/Ice-%{version}
#%{_datadir}/Ice-%{version}/slice
#%{_defaultdocdir}/%{name}-%{version}

%files slice
%defattr(-, root, root, -)
%dir %{_datadir}/Ice-%{version}
%{_datadir}/Ice-%{version}/slice
%{_defaultdocdir}/%{name}-%{version}

%files -n libice3.6-java
%defattr(-, root, root, -)
%{_javadir}/Ice-%{version}.jar
%{_javadir}/Ice-%{mmversion}.jar

%{_javadir}/Glacier2-%{version}.jar
%{_javadir}/Glacier2-%{mmversion}.jar

%{_javadir}/IceBox-%{version}.jar
%{_javadir}/IceBox-%{mmversion}.jar

%{_javadir}/IceGrid-%{version}.jar
%{_javadir}/IceGrid-%{mmversion}.jar

%{_javadir}/IcePatch2-%{version}.jar
%{_javadir}/IcePatch2-%{mmversion}.jar

%{_javadir}/IceStorm-%{version}.jar
%{_javadir}/IceStorm-%{mmversion}.jar

%{_javadir}/IceDiscovery-%{version}.jar
%{_javadir}/IceDiscovery-%{mmversion}.jar

%files -n libfreeze3.6-java
%defattr(-, root, root, -)
%{_javadir}/Freeze-%{version}.jar
%{_javadir}/Freeze-%{mmversion}.jar

%files -n libice-js
%defattr(-, root, root, -)
%{_datadir}/javascript/ice-%{mmversion}/Ice.min.js
%{_datadir}/javascript/ice-%{mmversion}/Ice.min.js.gz
%{_datadir}/javascript/ice-%{mmversion}/Glacier2.min.js
%{_datadir}/javascript/ice-%{mmversion}/Glacier2.min.js.gz
%{_datadir}/javascript/ice-%{mmversion}/IceStorm.min.js
%{_datadir}/javascript/ice-%{mmversion}/IceStorm.min.js.gz
%{_datadir}/javascript/ice-%{mmversion}/IceGrid.min.js
%{_datadir}/javascript/ice-%{mmversion}/IceGrid.min.js.gz

%files utils-java
%defattr(-, root, root, -)
%{_bindir}/iceca
%{_mandir}/man1/iceca.1.gz
%{_bindir}/icegridgui
%{_javadir}/IceGridGUI-%{version}.jar
%{_javadir}/IceGridGUI.jar
%dir %{_datadir}/Ice-%{version}
%{_datadir}/Ice-%{version}/ImportKey.class

%endif

#
# arch-specific packages
#
%ifarch %{core_arches}
%files -n libice3.6
%defattr(-, root, root, -)
%{_libdir}/libGlacier2.so.%{version}
%{_libdir}/libGlacier2.so.%{soversion}
%{_libdir}/libGlacier2CryptPermissionsVerifier.so.%{version}
%{_libdir}/libGlacier2CryptPermissionsVerifier.so.%{soversion}
%{_libdir}/libIceBox.so.%{version}
%{_libdir}/libIceBox.so.%{soversion}
%{_libdir}/libIceDiscovery.so.%{version}
%{_libdir}/libIceDiscovery.so.%{soversion}
%{_libdir}/libIcePatch2.so.%{version}
%{_libdir}/libIcePatch2.so.%{soversion}
%{_libdir}/libIce.so.%{version}
%{_libdir}/libIce.so.%{soversion}
%{_libdir}/libIceSSL.so.%{version}
%{_libdir}/libIceSSL.so.%{soversion}
%{_libdir}/libIceStorm.so.%{version}
%{_libdir}/libIceStorm.so.%{soversion}
%{_libdir}/libIceUtil.so.%{version}
%{_libdir}/libIceUtil.so.%{soversion}
%{_libdir}/libSlice.so.%{version}
%{_libdir}/libSlice.so.%{soversion}
%{_libdir}/libIceGrid.so.%{version}
%{_libdir}/libIceGrid.so.%{soversion}

%post -n libice3.6 -p /sbin/ldconfig
%postun -n libice3.6 -p /sbin/ldconfig

%files -n libfreeze3.6
%defattr(-, root, root, -)
%{_libdir}/libFreeze.so.%{version}
%{_libdir}/libFreeze.so.%{soversion}
%{_libdir}/libIceXML.so.%{version}
%{_libdir}/libIceXML.so.%{soversion}

%post -n libfreeze3.6 -p /sbin/ldconfig
%postun -n libfreeze3.6 -p /sbin/ldconfig

%files -n libicestorm3.6
%defattr(-, root, root, -)
%{_libdir}/libIceStormService.so.%{version}
%{_libdir}/libIceStormService.so.%{soversion}

%post -n libicestorm3.6 -p /sbin/ldconfig
%postun -n libicestorm3.6 -p /sbin/ldconfig

%files utils
%defattr(-, root, root, -)
%{_bindir}/dumpdb
%{_mandir}/man1/dumpdb.1.gz
%{_bindir}/transformdb
%{_mandir}/man1/transformdb.1.gz
%{_bindir}/iceboxadmin
%{_mandir}/man1/iceboxadmin.1.gz
%{_bindir}/icepatch2calc
%{_mandir}/man1/icepatch2calc.1.gz
%{_bindir}/icepatch2client
%{_mandir}/man1/icepatch2client.1.gz
%{_bindir}/icestormadmin
%{_mandir}/man1/icestormadmin.1.gz
%{_bindir}/icestormmigrate
%{_mandir}/man1/icestormmigrate.1.gz
%{_bindir}/slice2html
%{_mandir}/man1/slice2html.1.gz
%{_bindir}/icegridadmin
%{_mandir}/man1/icegridadmin.1.gz

%post utils -p /sbin/ldconfig
%postun utils -p /sbin/ldconfig

%files -n icegrid
%defattr(-, root, root, -)
%{_bindir}/icegridnode
%{_mandir}/man1/icegridnode.1.gz
%{_bindir}/icegridregistry
%{_mandir}/man1/icegridregistry.1.gz
%dir %{_datadir}/Ice-%{version}
%{_datadir}/Ice-%{version}/templates.xml
%attr(755,root,root) %{_datadir}/Ice-%{version}/upgradeicegrid33.py*
%attr(755,root,root) %{_datadir}/Ice-%{version}/upgradeicegrid35.py*
%{_datadir}/Ice-%{version}/icegrid-slice.3.1.ice.gz
%{_datadir}/Ice-%{version}/icegrid-slice.3.2.ice.gz
%{_datadir}/Ice-%{version}/icegrid-slice.3.3.ice.gz
%{_datadir}/Ice-%{version}/icegrid-slice.3.5.ice.gz
%attr(755,root,root) %{_initrddir}/icegridregistry
%attr(755,root,root) %{_initrddir}/icegridnode
%config(noreplace) %{_sysconfdir}/icegridregistry.conf
%config(noreplace) %{_sysconfdir}/icegridnode.conf

%pre -n icegrid
getent group ice > /dev/null || groupadd -r ice
getent passwd ice > /dev/null || \
       useradd -r -g ice -d %{_localstatedir}/lib/ice \
       -s /sbin/nologin -c "Ice Service account" ice
test -d %{_localstatedir}/lib/ice/icegrid/registry || \
       mkdir -p %{_localstatedir}/lib/ice/icegrid/registry; chown -R ice.ice %{_localstatedir}/lib/ice
test -d %{_localstatedir}/lib/ice/icegrid/node1 || \
       mkdir -p %{_localstatedir}/lib/ice/icegrid/node1; chown -R ice.ice %{_localstatedir}/lib/ice
exit 0

%post -n icegrid
/sbin/ldconfig
%if "%{dist}" != ".sles11"
/sbin/chkconfig --add icegridregistry
/sbin/chkconfig --add icegridnode
%endif

%preun -n icegrid
if [ $1 = 0 ]; then
%if "%{dist}" == ".sles11"
        /sbin/service icegridnode stop >/dev/null 2>&1 || :
        /sbin/insserv -r icegridnode
	/sbin/service icegridregistry stop >/dev/null 2>&1 || :
        /sbin/insserv -r icegridregistry
%else
        /sbin/service icegridnode stop >/dev/null 2>&1 || :
        /sbin/chkconfig --del icegridnode
	/sbin/service icegridregistry stop >/dev/null 2>&1 || :
        /sbin/chkconfig --del icegridregistry
%endif
fi

%postun -n icegrid
if [ "$1" -ge "1" ]; then
        /sbin/service icegridnode condrestart >/dev/null 2>&1 || :
	/sbin/service icegridregistry condrestart >/dev/null 2>&1 || :
fi
/sbin/ldconfig

%files -n glacier2
%defattr(-, root, root, -)
%{_bindir}/glacier2router
%{_mandir}/man1/glacier2router.1.gz
%attr(755,root,root) %{_initrddir}/glacier2router
%config(noreplace) %{_sysconfdir}/glacier2router.conf

%pre -n glacier2
getent group ice > /dev/null || groupadd -r ice
getent passwd ice > /dev/null || \
       useradd -r -g ice -d %{_localstatedir}/lib/ice \
       -s /sbin/nologin -c "Ice Service account" ice
exit 0

%post -n glacier2
/sbin/ldconfig
%if "%{dist}" != ".sles11"
/sbin/chkconfig --add glacier2router
%endif

%preun -n glacier2
if [ $1 = 0 ]; then
%if "%{dist}" == ".sles11"
        /sbin/service glacier2router stop >/dev/null 2>&1 || :
        /sbin/insserv -r glacier2router
%else
        /sbin/service glacier2router stop >/dev/null 2>&1 || :
        /sbin/chkconfig --del glacier2router
%endif
fi

%postun -n glacier2
if [ "$1" -ge "1" ]; then
        /sbin/service glacier2router condrestart >/dev/null 2>&1 || :
fi
/sbin/ldconfig

%files -n icepatch2
%defattr(-, root, root, -)
%{_bindir}/icepatch2server
%{_mandir}/man1/icepatch2server.1.gz

%pre -n icepatch2
getent group ice > /dev/null || groupadd -r ice
getent passwd ice > /dev/null || \
       useradd -r -g ice -d %{_localstatedir}/lib/ice \
       -s /sbin/nologin -c "Ice Service account" ice
exit 0

%post -n icepatch2
/sbin/ldconfig

%postun -n icepatch2
/sbin/ldconfig

%files -n icebox
%defattr(-, root, root, -)
%{_bindir}/icebox
%{_mandir}/man1/icebox.1.gz

%pre -n icebox
getent group ice > /dev/null || groupadd -r ice
getent passwd ice > /dev/null || \
       useradd -r -g ice -d %{_localstatedir}/lib/ice \
       -s /sbin/nologin -c "Ice Service account" ice
exit 0

%post -n icebox
/sbin/ldconfig

%postun -n icebox
/sbin/ldconfig

%files -n libice-cxx-devel
%defattr(-, root, root, -)

%{_bindir}/slice2cpp
%{_mandir}/man1/slice2cpp.1.gz
%{_bindir}/slice2freeze
%{_mandir}/man1/slice2freeze.1.gz
%{_includedir}/Freeze
%{_includedir}/Glacier2
%{_includedir}/Ice
%{_includedir}/IceBox
%{_includedir}/IceGrid
%{_includedir}/IcePatch2
%{_includedir}/IceSSL
%{_includedir}/IceStorm
%{_includedir}/IceUtil
%{_includedir}/Slice
%{_libdir}/libFreeze.so
%{_libdir}/libGlacier2.so
%{_libdir}/libIceBox.so
%{_libdir}/libIceGrid.so
%{_libdir}/libIcePatch2.so
%{_libdir}/libIce.so
%{_libdir}/libIceSSL.so
%{_libdir}/libIceStorm.so
%{_libdir}/libIceUtil.so
%{_libdir}/libSlice.so

%if %{mono}
%files mono-devel
%defattr(-, root, root, -)
%{_bindir}/slice2cs
%{_mandir}/man1/slice2cs.1.gz
%{_libdir}/pkgconfig/Ice.pc
%{_libdir}/pkgconfig/Glacier2.pc
%{_libdir}/pkgconfig/IceBox.pc
%{_libdir}/pkgconfig/IceGrid.pc
%{_libdir}/pkgconfig/IcePatch2.pc
%{_libdir}/pkgconfig/IceStorm.pc
%{_prefix}/lib/mono/Glacier2/
%{_prefix}/lib/mono/Ice/
%{_prefix}/lib/mono/IceBox/
%{_prefix}/lib/mono/IceGrid/
%{_prefix}/lib/mono/IcePatch2/
%{_prefix}/lib/mono/IceStorm/
%endif

%files -n libice-java-devel
%defattr(-, root, root, -)
%{_bindir}/slice2java
%{_mandir}/man1/slice2java.1.gz
%{_bindir}/slice2freezej
%{_mandir}/man1/slice2freezej.1.gz
%{_javadir}/ant-ice-%{version}.jar
%{_javadir}/ant-ice.jar

%files -n libice-js-devel
%defattr(-, root, root, -)
%{_bindir}/slice2js
%{_mandir}/man1/slice2js.1.gz
%{_datadir}/javascript/ice-%{mmversion}/Ice.js
%{_datadir}/javascript/ice-%{mmversion}/Ice.js.gz
%{_datadir}/javascript/ice-%{mmversion}/Glacier2.js
%{_datadir}/javascript/ice-%{mmversion}/Glacier2.js.gz
%{_datadir}/javascript/ice-%{mmversion}/IceStorm.js
%{_datadir}/javascript/ice-%{mmversion}/IceStorm.js.gz
%{_datadir}/javascript/ice-%{mmversion}/IceGrid.js
%{_datadir}/javascript/ice-%{mmversion}/IceGrid.js.gz

%files python
%defattr(-, root, root, -)
%{python_sitearch}/Ice
%{python_sitearch}/ice.pth

%files python-devel
%defattr(-, root, root, -)
%{_bindir}/slice2py
%{_mandir}/man1/slice2py.1.gz

%if %{ruby}
%files ruby
%defattr(-, root, root, -)
%{ruby_sitearch}/*

%files ruby-devel
%defattr(-, root, root, -)
%{_bindir}/slice2rb
%{_mandir}/man1/slice2rb.1.gz
%endif

%files php
%defattr(-, root, root, -)

%if "%{dist}" == ".el6"
%{_datadir}/php
%{_libdir}/php/modules/IcePHP.so
%config(noreplace) %{_sysconfdir}/php.d/ice.ini
%endif

%if "%{dist}" == ".el7"
%{_datadir}/php
%{_libdir}/php/modules/IcePHP.so
%config(noreplace) %{_sysconfdir}/php.d/ice.ini
%endif

%if "%{dist}" == ".amzn1"
%{_datadir}/php
%{_libdir}/php/modules/IcePHP.so
%config(noreplace) %{_sysconfdir}/php.d/ice.ini
%endif

%if "%{dist}" == ".sles11"
%{_datadir}/php5
%{_libdir}/php5/extensions
%config(noreplace) %{_sysconfdir}/php5/conf.d/ice.ini
%endif

%files php-devel
%defattr(-, root, root, -)
%{_bindir}/slice2php
%{_mandir}/man1/slice2php.1.gz
%endif

%changelog

* Thu Jul 18 2013 Mark Spruiell <mes@zeroc.com> 3.5.1
- Adding man pages.

* Thu Feb 7 2013 Mark Spruiell <mes@zeroc.com> 3.5.0
- Updates for the Ice 3.5.0 release.

* Mon Nov 19 2012 Mark Spruiell <mes@zeroc.com> 3.5b
- Updates for the Ice 3.5b release.

* Tue Dec 15 2009 Mark Spruiell <mes@zeroc.com> 3.4b
- Updates for the Ice 3.4b release.

* Wed Mar 4 2009 Bernard Normier <bernard@zeroc.com> 3.3.1
- Minor updates for the Ice 3.3.1 release.

* Wed Feb 27 2008 Bernard Normier <bernard@zeroc.com> 3.3b-1
- Updates for Ice 3.3b release:
 - Split main ice rpm into ice noarch (license and Slice files), ice-libs 
   (C++ runtime libraries), ice-utils (admin tools & utilities), ice-servers
   (icegridregistry, icebox etc.). This way, ice-libs 3.3.0 can coexist with
    ice-libs 3.4.0. The same is true for ice-mono, and to a lesser extent 
    other ice runtime packages
- Many updates derived from Mary Ellen Foster (<mefoster at gmail.com>)'s 
  Fedora RPM spec for Ice.
 - The Ice jar files are now installed in %{_javalibdir}, with 
   jpackage-compliant names
 - New icegridgui shell script to launch the IceGrid GUI
 - The .NET files are now packaged using gacutil with the -root option.
 - ice-servers creates a new user (ice) and installs three init.d services:
   icegridregistry, icegridnode and glacier2router.
 - Python, Ruby and PHP files are now installed in the correct directories.

* Fri Jul 27 2007 Bernard Normier <bernard@zeroc.com> 3.2.1-1
- Updated for Ice 3.2.1 release

* Wed Jun 13 2007 Bernard Normier <bernard@zeroc.com>
- Added patch with new IceGrid.Node.AllowRunningServersAsRoot property.

* Wed Dec 6 2006 ZeroC Staff <support@zeroc.com>
- See source distributions or the ZeroC website for more information
  about the changes in this release
