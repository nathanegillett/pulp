# sitelib for noarch packages, sitearch for others (remove the unneeded one)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}

# -- headers - pulp server ---------------------------------------------------

Name:           pulp
Version:        0.0.189
Release:        1%{?dist}
Summary:        An application for managing software content

Group:          Development/Languages
License:        GPLv2
URL:            https://fedorahosted.org/pulp/
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python2-devel
BuildRequires:  python-setuptools
BuildRequires:  python-nose	
BuildRequires:  rpm-python

Requires: %{name}-common = %{version}
Requires: pymongo >= 1.9
Requires: python-setuptools
Requires: python-webpy
Requires: python-simplejson >= 2.0.9
Requires: python-oauth2
Requires: python-httplib2
Requires: python-isodate >= 0.4.4
Requires: python-BeautifulSoup
Requires: grinder >= 0.0.102
Requires: httpd
Requires: mod_wsgi
Requires: mod_ssl
Requires: m2crypto
Requires: openssl
Requires: python-ldap
Requires: python-gofer >= 0.37
Requires: crontabs
Requires: acl
Requires: mongodb
Requires: mongodb-server
Requires: qpid-cpp-server
%if 0%{?fedora} || 0%{?rhel} > 5
# Fedora or RHEL-6 and beyond
Requires: mod_python
%endif
%if 0%{?el5}
# RHEL-5
Requires: python-uuid
Requires: python-ssl
Requires: python-ctypes
Requires: python-hashlib
%endif
%if 0%{?el6}
# RHEL-6
Requires: python-uuid
Requires: python-ctypes
Requires: python-hashlib
Requires: nss >= 3.12.9
Requires: curl => 7.19.7
%endif

# newer pulp builds should require same client version
Requires: %{name}-client >= %{version}


%description
Pulp provides replication, access, and accounting for software repositories.

# -- headers - pulp client ---------------------------------------------------

%package client
Summary:        Client side tools for managing content on pulp server
Group:          Development/Languages
BuildRequires:  rpm-python
Requires: python-simplejson
Requires: python-isodate >= 0.4.4
Requires: m2crypto
Requires: %{name}-common = %{version}
Requires: gofer >= 0.37
%if !0%{?fedora}
# RHEL
Requires: python-hashlib
%endif

%description client
A collection of tools to interact and perform content specific operations such as repo management, 
package profile updates etc.

# -- headers - pulp client ---------------------------------------------------

%package common
Summary:        Pulp common python packages.
Group:          Development/Languages
BuildRequires:  rpm-python

%description common
A collection of resources that are common between the pulp server and client.

# -- headers - pulp cds ------------------------------------------------------

%package cds
Summary:        Provides the ability to run as a pulp external CDS.
Group:          Development/Languages
BuildRequires:  rpm-python
Requires:       %{name}-common = %{version}
Requires:       gofer >= 0.37
Requires:       grinder
Requires:       httpd
Requires:       mod_wsgi
Requires:       mod_ssl
Requires:       m2crypto
%if 0%{?fedora} || 0%{?rhel} > 5
# Fedora
Requires: mod_python
%endif

%description cds
Tools necessary to interact synchronize content from a pulp server and serve that content
to clients.

# -- build -------------------------------------------------------------------

%prep
%setup -q

%build
pushd src
%{__python} setup.py build
popd

%install
rm -rf %{buildroot}
pushd src
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
popd

# Pulp Configuration
mkdir -p %{buildroot}/etc/pulp
cp etc/pulp/* %{buildroot}/etc/pulp

# Pulp Log
mkdir -p %{buildroot}/var/log/pulp

# Apache Configuration
mkdir -p %{buildroot}/etc/httpd/conf.d/
cp etc/httpd/conf.d/pulp.conf %{buildroot}/etc/httpd/conf.d/

# Pulp Web Services
cp -R srv %{buildroot}

# Pulp PKI
mkdir -p %{buildroot}/etc/pki/pulp
mkdir -p %{buildroot}/etc/pki/consumer
cp etc/pki/pulp/* %{buildroot}/etc/pki/pulp

mkdir -p %{buildroot}/etc/pki/content

# Pulp Runtime
mkdir -p %{buildroot}/var/lib/pulp
mkdir -p %{buildroot}/var/lib/pulp/published
mkdir -p %{buildroot}/var/www
ln -s /var/lib/pulp/published %{buildroot}/var/www/pub

# Client and CDS Gofer Plugins
mkdir -p %{buildroot}/etc/gofer/plugins
mkdir -p %{buildroot}/usr/lib/gofer/plugins
cp etc/gofer/plugins/*.conf %{buildroot}/etc/gofer/plugins
cp src/pulp/client/gofer/pulpplugin.py %{buildroot}/usr/lib/gofer/plugins
cp src/pulp/cds/gofer/cdsplugin.py %{buildroot}/usr/lib/gofer/plugins

# profile plugin
mkdir -p %{buildroot}/etc/yum/pluginconf.d/
mkdir -p %{buildroot}/usr/lib/yum-plugins/
cp etc/yum/pluginconf.d/*.conf %{buildroot}/etc/yum/pluginconf.d/
cp src/pulp/client/yumplugin/pulp-profile-update.py %{buildroot}/usr/lib/yum-plugins/

# Pulp and CDS init.d
mkdir -p %{buildroot}/etc/rc.d/init.d
cp etc/rc.d/init.d/* %{buildroot}/etc/rc.d/init.d/
ln -s etc/rc.d/init.d/goferd %{buildroot}/etc/rc.d/init.d/pulp-agent

# Remove egg info
rm -rf %{buildroot}/%{python_sitelib}/%{name}*.egg-info

# Touch ghost files (these won't be packaged)
mkdir -p %{buildroot}/etc/yum.repos.d
touch %{buildroot}/etc/yum.repos.d/pulp.repo

# Pulp CDS
# This should match what's in gofer_cds_plugin.conf and pulp-cds.conf
mkdir -p %{buildroot}/var/lib/pulp-cds

# Pulp CDS Logging
mkdir -p %{buildroot}/var/log/pulp-cds

# Apache Configuration
mkdir -p %{buildroot}/etc/httpd/conf.d/
cp etc/httpd/conf.d/pulp-cds.conf %{buildroot}/etc/httpd/conf.d/

%clean
rm -rf %{buildroot}

# -- post - pulp server ------------------------------------------------------

%post
setfacl -m u:apache:rwx /etc/pki/content/

# For Fedora, enable the mod_python handler in the httpd config
%if 0%{?fedora} || 0%{?rhel} > 5
# Remove the comment flags for the auth handler lines (special format on those is #-)
sed -i -e 's/#-//g' /etc/httpd/conf.d/pulp.conf
%endif

# -- post - pulp cds ---------------------------------------------------------

%post cds
setfacl -m u:apache:rwx /etc/pki/content/

# For Fedora, enable the mod_python handler in the httpd config
%if 0%{?fedora} || 0%{?rhel} > 5
# Remove the comment flags for the auth handler lines (special format on those is #-)
sed -i -e 's/#-//g' /etc/httpd/conf.d/pulp-cds.conf
%endif

# -- post - pulp client ------------------------------------------------------

%post client
pushd %{_sysconfdir}/rc.d/init.d
if [ "$1" = "1" ]; then
  ln -s goferd pulp-agent
fi
popd

%postun client
if [ "$1" = "0" ]; then
  rm -f %{_sysconfdir}/rc.d/init.d/pulp-agent
fi

# -- files - pulp server -----------------------------------------------------

%files
%defattr(-,root,root,-)
%doc
# For noarch packages: sitelib
%{python_sitelib}/pulp/server/
%{python_sitelib}/pulp/repo_auth/
%config %{_sysconfdir}/pulp/pulp.conf
%config %{_sysconfdir}/pulp/repo_auth.conf
%config %{_sysconfdir}/httpd/conf.d/pulp.conf
%ghost %{_sysconfdir}/yum.repos.d/pulp.repo
%attr(775, apache, apache) %{_sysconfdir}/pulp
%attr(775, apache, apache) /srv/pulp
%attr(750, apache, apache) /srv/pulp/webservices.wsgi
%attr(750, apache, apache) /srv/pulp/bootstrap.wsgi
%attr(3775, apache, apache) /var/lib/pulp
%attr(3775, apache, apache) /var/www/pub
%attr(3775, apache, apache) /var/log/pulp
%attr(3775, root, root) %{_sysconfdir}/pki/content
%attr(3775, root, root) %{_sysconfdir}/rc.d/init.d/pulp-server
%{_sysconfdir}/pki/pulp/ca.key
%{_sysconfdir}/pki/pulp/ca.crt

# -- files - common ----------------------------------------------------------

%files common
%defattr(-,root,root,-)
%doc
%{python_sitelib}/pulp/__init__.*
%{python_sitelib}/pulp/common/

# -- files - pulp client -----------------------------------------------------

%files client
%defattr(-,root,root,-)
%doc
# For noarch packages: sitelib
%{python_sitelib}/pulp/client/
%{_bindir}/pulp-admin
%{_bindir}/pulp-client
%{_bindir}/pulp-migrate
%{_exec_prefix}/lib/gofer/plugins/pulpplugin.*
%{_prefix}/lib/yum-plugins/pulp-profile-update.py*
%{_sysconfdir}/gofer/plugins/pulpplugin.conf
%{_sysconfdir}/yum/pluginconf.d/pulp-profile-update.conf
%attr(755,root,root) %{_sysconfdir}/pki/consumer/
%config(noreplace) %attr(644,root,root) %{_sysconfdir}/yum/pluginconf.d/pulp-profile-update.conf
%config(noreplace) %{_sysconfdir}/pulp/client.conf
%ghost %{_sysconfdir}/rc.d/init.d/pulp-agent

# -- files - pulp cds --------------------------------------------------------

%files cds
%defattr(-,root,root,-)
%doc
%{python_sitelib}/pulp/cds/
%{python_sitelib}/pulp/repo_auth/
%{_sysconfdir}/gofer/plugins/cdsplugin.conf
%{_exec_prefix}/lib/gofer/plugins/cdsplugin.*
%attr(775, apache, apache) /srv/pulp
%attr(750, apache, apache) /srv/pulp/cds.wsgi
%config %{_sysconfdir}/httpd/conf.d/pulp-cds.conf
%config %{_sysconfdir}/pulp/cds.conf
%config %{_sysconfdir}/pulp/repo_auth.conf
%attr(3775, root, root) %{_sysconfdir}/pki/content
%attr(3775, root, root) %{_sysconfdir}/rc.d/init.d/pulp-cds
%attr(3775, apache, apache) /var/lib/pulp-cds
%attr(3775, apache, apache) /var/log/pulp-cds

# -- changelog ---------------------------------------------------------------

%changelog
* Fri Jun 10 2011 Jay Dobies <jason.dobies@redhat.com> 0.0.189-1
- removing errata type constraint from help (skarmark@redhat.com)
- 704194 - Add path component of sync URL to event. (jortel@redhat.com)
- Allow for ---PRIVATE KEY----- without (RSA|DSA) (jortel@redhat.com)
- Fix pulp-client consumer bind to pass certificates to repolib.
  (jortel@redhat.com)
- Fix bundle.validate(). (jortel@redhat.com)
- 704599 - rephrase the select help menu (pkilambi@redhat.com)
- Fix global auth for cert consolidation. (jortel@redhat.com)
- 697206 - Added force option to CDS unregister to be able to remove it even if
  the CDS is offline. (jason.dobies@redhat.com)
- changing the epoch to a string; and if an non string is passed force it to be
  a str (pkilambi@redhat.com)
- migrate epoch if previously empty string  and set to int
  (pkilambi@redhat.com)
- Pass certificate PEM instead of paths on bind. (jortel@redhat.com)
- Fix merge weirdness. (jortel@redhat.com)
- Seventeen taken on master. (jortel@redhat.com)
- Adding a verbose option to yum plugin(on by default) (pkilambi@redhat.com)
- Merge branch 'master' into key-cert-consolidation (jortel@redhat.com)
- Migration chnages to convert pushcount from string to an integer value of 1
  (pkilambi@redhat.com)
- removing constraint for errata type (skarmark@redhat.com)
- 701830 - race condition fixed by pushing new scheduler assignment into the
  task queue (jconnor@redhat.com)
- removed re-raising of exceptions in task dispatcher thread to keep the
  dispatcher from exiting (jconnor@redhat.com)
- added docstring (jconnor@redhat.com)
- added more information on pickling errors for better debugging
  (jconnor@redhat.com)
- Add nss DB script to playpen. (jortel@redhat.com)
- Go back to making --key optional. (jortel@redhat.com)
- Move Bundle class to common. (jortel@redhat.com)
- Support CA, client key/cert in pulp.repo. (jortel@redhat.com)
- stop referencing feed_key option. (jortel@redhat.com)
- consolidate key/cert for repo auth certs. (jortel@redhat.com)
- consolidate key/cert for login & consumer certs. (jortel@redhat.com)

* Wed Jun 08 2011 Jeff Ortel <jortel@redhat.com> 0.0.188-1
- 709703 - set the right defaults for pushcount and epoch (pkilambi@redhat.com)
- removed callable from pickling in derived tasks that only can have one
  possible method passed in (jconnor@redhat.com)
- removed lock pickling (jconnor@redhat.com)
- added assertion error messages (jconnor@redhat.com)
- Automatic commit of package [PyYAML] minor release [3.09-14].
  (jmatthew@redhat.com)
- import PyYAML for brew (jmatthews@redhat.com)
- added overriden from_snapshot class methods for derived task classes that
  take different contructor arguments for re-constitution (jconnor@redhat.com)
- fixed snapshot id setting (jconnor@redhat.com)
- extra lines in errata list and search outputs and removing errata type
  constraint (skarmark@redhat.com)
- adding failure message for assert in intervalschedule test case
  (skarmark@redhat.com)
- added --orphaned flag for errata search (skarmark@redhat.com)
- re-arranging calls so that db gets cleaned up before async is initialized,
  keeping persisted tasks from being loaded (jconnor@redhat.com)
- fixing repo delete issue because of missing handling for checking whether
  repo sync invoked is completed (skarmark@redhat.com)
- added individual snapshot removal (jconnor@redhat.com)
- simply dropping whole snapshot collection in order to ensure old snapshots
  are deleted (jconnor@redhat.com)
- adding safe batch removal of task snapshots before enqueueing them
  (jconnor@redhat.com)
- added at scheduled task to get persisted (jconnor@redhat.com)
- Updated User Guide to include jconnor ISO8601 updates from wiki
  (tsanders@redhat.com)
- Bump to grinder 102 (jmatthews@redhat.com)
- Adding lock for creating a document's id because rhel5 uuid.uuid4() is not
  threadsafe (jmatthews@redhat.com)
- Adding checks to check status of the request return and raise exception if
  its not a success or redirect. Also have an optional handle_redirects param
  to tell the request to override urls (pkilambi@redhat.com)
- dont persist the scheduled time, let the scheduler figure it back out
  (jconnor@redhat.com)
- 700367 - bug fix + errata enhancement changes + errata search
  (skarmark@redhat.com)
- reverted custom lock pickling (jconnor@redhat.com)
- refactored and re-arranged functionality in snapshot storage
  (jconnor@redhat.com)
- added ignore_complete flag to find (jconnor@redhat.com)
- changed super calls and comments to new storage class name
  (jconnor@redhat.com)
- remove cusomt pickling of lock types (jconnor@redhat.com)
- consolidate hybrid storage into 1 class and moved loading of persisted tasks
  to async initialization (jconnor@redhat.com)
- moved all timedeltas to pickle fields (jconnor@redhat.com)
- removed complete callback from pickle fields (jconnor@redhat.com)
- added additional copy fields for other derived task classes
  (jconnor@redhat.com)
- reverted repo sync task back to individual fields (jconnor@redhat.com)
- fixed bug in snapshot id (jconnor@redhat.com)
- reverting back to individual field storage and pickling (jconnor@redhat.com)
- removing thread from the snapshot (jconnor@redhat.com)
- delete old thread module (jconnor@redhat.com)
- renamed local thread module (jconnor@redhat.com)
- one more try before having to rename local thread module (jconnor@redhat.com)
- change thread import (jconnor@redhat.com)
- changed to natice lock pickling and unpickling (jconnor@redhat.com)
- added custom pickling and unpickling of rlocks (jconnor@redhat.com)
- 681239 - user update and create now have 2 options of providing password,
  through command line or password prompt (skarmark@redhat.com)
- more thorough lock removal (jconnor@redhat.com)
- added return of None on duplicate snapshot (jconnor@redhat.com)
- added get and set state magic methods to PulpCollection for pickline
  (jconnor@redhat.com)
- using immediate only hybrid storage (jconnor@redhat.com)
- removed cached connections to handle AutoReconnect exceptions
  (jconnor@redhat.com)
- db version 16 for dropping all tasks serialzed in the old format
  (jconnor@redhat.com)
- more cleanup and control flow issues (jconnor@redhat.com)
- removed unused exception type (jconnor@redhat.com)
- fixed bad return on too many consecutive failures (jconnor@redhat.com)
- corrected control flow for exception paths through task execution
  (jconnor@redhat.com)
- using immutable default values for keyword arguments in constructor
  (jconnor@redhat.com)
- added timeout() method to base class and deprecation warnings for usage of
  dangerous exception injection (jconnor@redhat.com)
- removed pickling of individual fields and instead pickle the whole task
  (jconnor@redhat.com)
- comment additions and cleanup (jconnor@redhat.com)
- remove unused persistent storage (jconnor@redhat.com)
- removed unused code (jconnor@redhat.com)
- change in delimiter comments (jconnor@redhat.com)
- adding hybrid storage class that only takes snapshots of tasks with an
  immediate scheduler (jconnor@redhat.com)
- Adding progress call back to get incremental feedback on discovery
  (pkilambi@redhat.com)
- Need apache to be able to update this file as well as root.
  (jason.dobies@redhat.com)
- Adding authenticated repo support to client discovery (pkilambi@redhat.com)
- 704320 - Capitalize the first letter of state for consistency
  (jason.dobies@redhat.com)
- Return a 404 for the member list if the CDS is not part of a cluster
  (jason.dobies@redhat.com)
- Don't care about client certificates for mirror list
  (jason.dobies@redhat.com)
* Sat Jun 04 2011 Jay Dobies <jason.dobies@redhat.com> 0.0.187-1
- Don't need the ping file, the load balancer now supports a members option
  that will be used instead. (jason.dobies@redhat.com)
- Added ability to query just the members of the load balancer, without causing
  the balancing algorithm to take place or the URL generation to be returned.
  (jason.dobies@redhat.com)
- added safe flag to snapshot removal as re-enqueue of a quickly completing,
  but scheduled task can overlap the insertion of the new snapshot and the
  removal of the old without it (jconnor@redhat.com)
- Add 'id' to debug output (jmatthews@redhat.com)
- Fix log statement (jmatthews@redhat.com)
- Adding more info so we can debug a rhel5 intermittent unit test failure
  (jmatthews@redhat.com)
- Automatic commit of package [python-isodate] minor release [0.4.4-2].
  (jmatthew@redhat.com)
- Revert "Fixing test_sync_multiple_repos to use same logic as in the code to
  check running sync for a repo before deleting it" (jmatthews@redhat.com)
- Bug 710455 - Grinder cannot sync a Pulp protected repo (jmatthews@redhat.com)
- Removing unneeded log statements (jmatthews@redhat.com)
- Removed comment (jmatthews@redhat.com)
- Adding ping page (this may change, but want to get this in place now for
  RHUI)) (jason.dobies@redhat.com)
- Enhancements to Discovery Module: (pkilambi@redhat.com)
- Reload CDS before these calls so saved info isn't wiped out
  (jason.dobies@redhat.com)
- Added better check for running syncsI swear I fixed this once...
  (jconnor@redhat.com)
- adding more information to conclicting operation exception
  (jconnor@redhat.com)
- added tear-down to for persistence to unittests (jconnor@redhat.com)
- typo fix (jconnor@redhat.com)
- Revert "renamed _sync to sycn as it is now a public part of the api"
  (jconnor@redhat.com)
- web service for cds task history (jconnor@redhat.com)
- web service for repository task history (jconnor@redhat.com)
- removed old unittests (jconnor@redhat.com)
- new task history api module (jconnor@redhat.com)
- Changed default file name handling so they can be changed in test cases.
  (jason.dobies@redhat.com)
- Refactored CDS "groups" to "cluster". (jason.dobies@redhat.com)
- updating repo file associations (pkilambi@redhat.com)
- update file delete to use new location (pkilambi@redhat.com)
- 709318 - Changing the file store path to be more unique (pkilambi@redhat.com)

* Thu Jun 02 2011 Jeff Ortel <jortel@redhat.com> 0.0.186-1
- Reduce sync logging (jmatthew@redhat.com)
- Fix for moving get_synchronizer from RepoApi to repo_sync
  (jmatthew@redhat.com)
* Wed Jun 01 2011 Jeff Ortel <jortel@redhat.com> 0.0.185-1
- Fix broken repo delete command. (jortel@redhat.com)
- Fixing test_sync_multiple_repos to use same logic as in the code to check
  running sync for a repo before deleting it (skarmark@redhat.com)

* Wed Jun 01 2011 Jeff Ortel <jortel@redhat.com> 0.0.184-1
- Fixed missing close in CDS repo list. Added call to clean up protection for
  removed repos. (jason.dobies@redhat.com)
- Incorrect section name (jason.dobies@redhat.com)
- 708416 - Order the sync list before determining most recent sync
  (jason.dobies@redhat.com)
- The CDS plugin needs access to the server conf properties.
  (jason.dobies@redhat.com)
- 709476 - Our conf files should be replaced by default.
  (jason.dobies@redhat.com)

* Wed Jun 01 2011 Jay Dobies <jason.dobies@redhat.com> 0.0.183-1
- Added configuration for CA certificate for server's SSL certificate and
  sending of it to CDS instances. (jason.dobies@redhat.com)

* Tue May 31 2011 John Matthews <jmatthew@redhat.com> 0.0.182-1
- Bump to grinder 0.100 (jmatthews@redhat.com)
- Cleanup with merge of repo sync refactoring (jmatthews@redhat.com)
- Refactored repo_sync/synchronizers.  repo_sync is now high level 'sync'
  interface (jmatthews@redhat.com)
- Updated docs for CR 12 (jason.dobies@redhat.com)
- Update for CR-12 (jortel@redhat.com)
- Changed phrasing of log message to not sound like an error
  (jason.dobies@redhat.com)
- Added log message when group membership isn't updated
  (jason.dobies@redhat.com)
- Make the cds repo list a hidden file (jason.dobies@redhat.com)
- Fixed CDS repo list saving (jason.dobies@redhat.com)
- Hardened group change logic (jason.dobies@redhat.com)
- Refactored CDS communications to only send auth information in the sync call
  itself to clean up places we need to handle communication errors. The group
  information is also sent during the sync call as a redundency in case the CDS
  missed the original call. (jason.dobies@redhat.com)
- Added CDS group repo normalization functionality (jason.dobies@redhat.com)
- re-license to GPLv2 or later as well as updated (C) date (mmccune@redhat.com)
- bumping timeout (pkilambi@redhat.com)
- adding some checks to the plugin (pkilambi@redhat.com)
- adding timeout to pulp server connection class (pkilambi@redhat.com)
- The CDS needs these directories owned by apache (jason.dobies@redhat.com)
- If the CDS isn't in a group, the load balancer call just returns itself as
  the host (jason.dobies@redhat.com)
- Automatic commit of package [pulp] release [0.0.181-1]. (jortel@redhat.com)
- updating the dev script to link yum plugins (pkilambi@redhat.com)
- Yum plugin to invoke package profile update on post yum transactions
  (pkilambi@redhat.com)
- Hooked in CDS group update to file storage (jason.dobies@redhat.com)
- Added file storage mechanism for cds host list and tied it into the load
  balancer web app (jason.dobies@redhat.com)
- Initial framework for CDS load balancer web app (jason.dobies@redhat.com)
- Added dividers to make it more readable (jason.dobies@redhat.com)
- 707341 - fixed client to use new server-side scheduler information to
  properly determine if a sync is actually currently in progress
  (jconnor@redhat.com)
- added logic to look through a list of syncs and find a running one
  (jconnor@redhat.com)
- added scheduler information to the task serialization (and comments)
  (jconnor@redhat.com)
- copy the renamed file during build (pkilambi@redhat.com)
- renaming gofer's pulp.py to pulpplugin.py to fix the conflict with top level
  class while module is loaded (pkilambi@redhat.com)
- bug 703275 - Python naively uses __cmp__ for equality and membership if
  __eq__ is not present added custom __eq__ to fix assertion bugs
  (jconnor@redhat.com)
- fixing bug in missed runs reporting (off by one error) (jconnor@redhat.com)
- added comment (jconnor@redhat.com)
- Fixed test (jason.dobies@redhat.com)
- Added server -> CDS infrastructure to send CDS group information when it is
  changed on the server (jason.dobies@redhat.com)
- Include size info in MANIFEST files (pkilambi@redhat.com)
- Added group membership messages and cleaned up exception handling in the CDS
  dispatcher. (jason.dobies@redhat.com)

* Wed May 25 2011 Jeff Ortel <jortel@redhat.com> 0.0.181-1
- 707341 - fixed client to use new server-side scheduler information to
  properly determine if a sync is actually currently in progress
  (jconnor@redhat.com)
- added logic to look through a list of syncs and find a running one
  (jconnor@redhat.com)
- added scheduler information to the task serialization (and comments)
  (jconnor@redhat.com)

* Tue May 24 2011 Jeff Ortel <jortel@redhat.com> 0.0.180-1
- bug 703275 - Python naively uses __cmp__ for equality and membership if
  __eq__ is not present added custom __eq__ to fix assertion bugs
  (jconnor@redhat.com)

* Fri May 20 2011 Jeff Ortel <jortel@redhat.com> 0.0.179-1
- Fix qpid SSL: pass URL to heartbeat & async task listener.
  (jortel@redhat.com)
- 705394 - added condition to skip adding unused schedule variables to the
  update delta (jconnor@redhat.com)
- 705393 - adding schedule validation and standardization method that will add
  missing tzinformation (jconnor@redhat.com)
- Added update CDS API and CLI hooks. (jason.dobies@redhat.com)
- Added API call for update CDS. (jason.dobies@redhat.com)
- Added group ID to CDS register and display calls (jason.dobies@redhat.com)
- Added group ID to CDS instances (plus DB migrate script)
  (jason.dobies@redhat.com)
* Wed May 18 2011 Jeff Ortel <jortel@redhat.com> 0.0.178-1
- Change wording for cancel sync in CLI (jmatthew@redhat.com)
- 705476 - Allow a SSL ca cert to be passed into a repo to use for verifcation
  (jmatthew@redhat.com)
- Removed use of assertIn/assertNotIn, they fail on older versions of python
  (jmatthew@redhat.com)
- Bump to grinder 0.98 (jmatthew@redhat.com)
- minor refactor to pkg profile module to be extendable (pkilambi@redhat.com)
- updating user docs for sprint23 (pkilambi@redhat.com)
- Append a slash for base urls (pkilambi@redhat.com)
- convert the file size to int before persisting in db (pkilambi@redhat.com)
* Fri May 13 2011 Jeff Ortel <jortel@redhat.com> 0.0.177-1
- adding python-isodate to client spec (pkilambi@redhat.com)
- 682226 - filename must be unique within a repo (jmatthews@redhat.com)
- Moving RepoSyncTask out of tasking module (jmatthews@redhat.com)
- merged in upstream (jconnor@redhat.com)
- Enhance errata delete to check for references before allowing a delete.
  remove_errata orphanes the errata from the repo. (pkilambi@redhat.com)
- using task constants removed pulp-admin specific error message from server-
  side error (jconnor@redhat.com)
- 704316 - added removal of scheduled syncs as first part of repo delete
  (jconnor@redhat.com)
- Better approach to agent proxies. (jortel@redhat.com)
- Allow ssl cacert to be used by itself during a repo sync
  (jmatthews@redhat.com)
- Initial dump of the wordpress theme (need to strip out some unused images
  eventually). (jason.dobies@redhat.com)
- removing rhn sync specific options from pulp.conf (pkilambi@redhat.com)
- cut script name down to basename in error message (jconnor@redhat.com)
- added None reponse code to no credentials error (jconnor@redhat.com)
- adding credentials detection before establishing connection to server
  (jconnor@redhat.com)
- 697208 - Added check to make sure the repo is present before trying to delete
  it. (jason.dobies@redhat.com)
- 688297 - Fixed incorrect substitutions for name and hostname
  (jason.dobies@redhat.com)
- update repositories webservices documentation to reflect iso8601 format
  (jconnor@redhat.com)
- added default behaviour of ommitting start time for sync schedules in help
  (jconnor@redhat.com)
- fixed broken optpars import (jconnor@redhat.com)
- 696676 - removed premature exit due to lack of credentials
  (jconnor@redhat.com)
- use either -a -u set of options (jconnor@redhat.com)
- fix for interval schedule parsing (jconnor@redhat.com)
- removed superfluous base class methods (jconnor@redhat.com)
- added new iso format support for package installs (jconnor@redhat.com)
- we now support sync scheduling when registering a cds (jconnor@redhat.com)
- added repo sync scheduling support (jconnor@redhat.com)
- added utility functions to parse iso8601 schedules and handle parse errors
  (jconnor@redhat.com)
- 697872 - RFE: add a call to remove packages from repos (jmatthews@redhat.com)
- removing more references to auditing.initialize (pkilambi@redhat.com)
- dont try depsolving during add_errata if there are no packages
  (pkilambi@redhat.com)
- 676701 - fixing typo in error message (pkilambi@redhat.com)
- validate input params to depsolver call; mkae recursive an optional param
  (pkilambi@redhat.com)
- 670284 - [RFE] Add an option to package group queries to restrict to packages
  available on server. (jmatthews@redhat.com)
* Tue May 10 2011 Jay Dobies <jason.dobies@redhat.com> 0.0.176-1
- This is needed to be able to build this subproject (jason.dobies@redhat.com)

* Tue May 10 2011 Jay Dobies <jason.dobies@redhat.com> 0.0.175-1
- 703553 - change the skipp urls msg to be on only in debug mode
  (pkilambi@redhat.com)
- 700508 - fast sync/cancel_sync locks up task subsystem (jmatthews@redhat.com)
- Allows test_packages to run as non-root (moved CACHE_DIR to constants.py and
  override in testutil) (jmatthews@redhat.com)
- Update import of RepoSyncTask (jmatthews@redhat.com)
- 700508 - partial fix, fixes fast sync/cancel leaving repo in a
  ConflictingOperation (jmatthews@redhat.com)
- Update script to cause httpd lockup from fast sync/cancel_sync
  (jmatthews@redhat.com)
- adding more clarity to discovery select statement (pkilambi@redhat.com)
- globalize the selection list and keep it unique across multiple selection
  (pkilambi@redhat.com)
- 701380 - adding vendor info to pkg details. Also adding some input validation
  (pkilambi@redhat.com)
- New date format (changelog snipped)
* Mon May 09 2011 Jeff Ortel <jortel@redhat.com> 0.0.174-1
- Fix xml.dom.minidom import. (jortel@redhat.com)
- 701829 - Clear the repo listing file on empty syncs and delete_all calls
  (jason.dobies@redhat.com)
- removing audit initialize (pkilambi@redhat.com)
- fixing auditing event collection reference (jconnor@redhat.com)
- Fix repo file cleanup when consumer deleted. (jortel@redhat.com)
- Allow client to add and remove text only errata (pkilambi@redhat.com)
- 702434 - create a new UpdateNotice instance for each errata
  (pkilambi@redhat.com)
- 669397 - Enforcing ID restrictions on repo, consumer, consumergroup etc. and
  changing unit test to comply with ID regex (skarmark@redhat.com)
- Secure server/agent RMI with shared secret. (jortel@redhat.com)
- fixed broken import of xml.dom.minidom (jconnor@redhat.com)
- fixed retry decorator to account for previous binding of im_self to passed in
  method (jconnor@redhat.com)
- removed auditing initialization (jconnor@redhat.com)
- 692969 new pulp collection wrapper class that allows for AutoReconnect
  handling (jconnor@redhat.com)
- getting rid of last users of get_object_db (jconnor@redhat.com)
- more help usage fixing to match the standard (pkilambi@redhat.com)
- fixing help usage to match the standard (pkilambi@redhat.com)
- remove extra / while joining urls (pkilambi@redhat.com)
- 700917 - cli inconsistencies in content --help fixed (skarmark@redhat.com)
- 700918 - cli inconsistencies in repo --help fixed (skarmark@redhat.com)
- Removing legacy RHN support from pulp (pkilambi@redhat.com)
- CR-11, website index. (jortel@redhat.com)
- Better heartbeat logging. (jortel@redhat.com)
- fixed comparison for None scheduled_time (jconnor@redhat.com)

* Tue May 03 2011 Jeff Ortel <jortel@redhat.com> 0.0.173-1
- Require gofer 0.35. (jortel@redhat.com)
- 700371 - support for text only errata (pkilambi@redhat.com)
- 700371 - support for text only errata (pkilambi@redhat.com)
- Making the discovery module extendable for other discovery types
  (pkilambi@redhat.com)
- Fixing url validate to work on el5 (pkilambi@redhat.com)
- Bump to gofer 0.34 to support mocks change in unit tests. (jortel@redhat.com)
- Refit to use gofer mocks. (jortel@redhat.com)
- Support for Repo Discovery (pkilambi@redhat.com)
- 428819 - check user credentials for pulp-client (pkilambi@redhat.com)
- Update 'add_package' api doc under 'repositories' (jmatthews@redhat.com)
- Update api docs for feed_cert/consumer_cert on repository create
  (jmatthews@redhat.com)
- 695707 - repo delete should detect ongoing sync before deleting it
  (skarmark@redhat.com)
- 629718 - adding sane default language encoding (jconnor@redhat.com)

* Wed Apr 27 2011 Jay Dobies <jason.dobies@redhat.com> 0.0.172-1
- 700122 - Fixed ISO date formatting for python 2.4 compatibility.
  (jason.dobies@redhat.com)
- Require grinder 0.96 (jmatthews@redhat.com)
- 697833, 698344 - update sync status error details (jmatthews@redhat.com)
- 697971 - Changed error message to non-confusing sync in progress message
  instead of 'sync completed' or 'no sync to cancel' (skarmark@redhat.com)
- 699543 - fixed fix, splitting on the wrong character (jconnor@redhat.com)
- 699543 - we were leaving the GET parameters in the request url, which was
  screwing up the oath credentials (jconnor@redhat.com)
- 698577 - fixed lack of parens around variable for string formatting
  (jconnor@redhat.com)
- fixing the package info call to display fields correctly
  (pkilambi@redhat.com)
- Adding support for additional fields in the package model
  (pkilambi@redhat.com)

* Thu Apr 21 2011 Jeff Ortel <jortel@redhat.com> 0.0.170-1
- Update test; repodata/ created when repo is created.  So, after a repo is
  created, the symlinks and relative path may no longer be changed.
  (jortel@redhat.com)
