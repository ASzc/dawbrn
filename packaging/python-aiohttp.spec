# http://pkgs.fedoraproject.org/cgit/rpms/python-aiohttp.git/plain/python-aiohttp.spec

%global srcname aiohttp

Name:           rh-python35-%{srcname}
Version:        2.2.4
Release:        1%{?dist}
Summary:        Python HTTP client/server for asyncio

License:        ASL 2.0
URL:            https://github.com/aio-libs/aiohttp/
Source0:        https://github.com/aio-libs/aiohttp/archive/v%{version}.tar.gz#/%{srcname}-%{version}.tar.gz

Requires:       rh-python35-chardet
Requires:       rh-python35-multidict >= 2.1.4
Requires:       rh-python35-async-timeout >= 1.2.0
Requires:       rh-python35-yarl

Requires: rh-python35
BuildRequires: rh-python35

%global __python scl enable rh-python35 -- python
%global __python3 scl enable rh-python35 -- python

%description
Python HTTP client/server for asyncio which supports both the client and the
server side of the HTTP protocol, client and server websocket, and webservers
with middlewares and pluggable routing.

%prep
%setup -q -n "%(echo "$(tar -tf %{SOURCE0} | head -1 | tr -d '/')")"

%build
echo ------------------
echo ------------------
ls -lha /builddir/build/SOURCES/
tar -tvvf %{SOURCE0}
ls -laR
find -iname '*setup*'
echo ------------------
echo ------------------
CFLAGS="%{optflags}" %{__python3} setup.py build
sleep 1

%install
CFLAGS="%{optflags}" %{__python3} setup.py install -O1 --skip-build --root %{buildroot}/opt/rh/rh-python35/root

%files
%doc CHANGES.rst CONTRIBUTING.rst CONTRIBUTORS.txt HISTORY.rst README.rst
%license LICENSE.txt
%{python35python3_sitearch}/%{srcname}-*.egg-info/
%{python35python3_sitearch}/%{srcname}/

%changelog
* Thu Aug 03 2017 Fabian Affolter <mail@fabian-affolter.ch> - 2.2.4-1
- Update to new upstream version 2.2.4

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.2.3-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.2.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Thu Jul 06 2017 Fabian Affolter <mail@fabian-affolter.ch> - 2.2.3-1
- Update to new upstream version 2.2.3 (rhbz#1467742)

* Mon Jul 03 2017 Fabian Affolter <mail@fabian-affolter.ch> - 2.2.2-1
- Update to new upstream version 2.2.2 

* Mon Jul 03 2017 Fabian Affolter <mail@fabian-affolter.ch> - 2.2.1-1
- Update to new upstream version 2.2.1 (rhbz#1467114)

* Tue Jun 20 2017 Fabian Affolter <mail@fabian-affolter.ch> - 2.2.0-1
- Update to new upstream version 2.2.0 (rhbz#1463234)

* Sat May 27 2017 Fabian Affolter <mail@fabian-affolter.ch> - 2.1.0-1
- Update URL
- Update to new upstream version 2.1.0 (rhbz#1456063)

* Fri Apr 14 2017 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 2.0.7-1
- Update to 2.0.7

* Fri Apr 07 2017 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 2.0.6-1
- Update to 2.0.6

* Thu Mar 30 2017 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 2.0.5-1
- Update to 2.0.5

* Tue Mar 28 2017 Igor Gnatenko <ignatenko@redhat.com> - 2.0.4-1
- Update to 2.0.4

* Sat Mar 25 2017 Fabian Affolter <mail@fabian-affolter.ch> - 2.0.3-1
- Update to new upstream version 2.0.3 (rhbz#1435844)

* Thu Mar 23 2017 Igor Gnatenko <ignatenko@redhat.com> - 2.0.2-3
- Specify proper yarl version

* Thu Mar 23 2017 Igor Gnatenko <ignatenko@redhat.com> - 2.0.2-2
- Fix requires

* Thu Mar 23 2017 Fabian Affolter <mail@fabian-affolter.ch> - 2.0.2-1
- Update to new upstream version 2.0.2 (rhbz#1432690)

* Wed Mar 15 2017 Igor Gnatenko <ignatenko@redhat.com> - 1.3.4-1
- Update to 1.3.4

* Mon Feb 20 2017 Fabian Affolter <mail@fabian-affolter.ch> - 1.3.3-1
- Update to new upstream version 1.3.3 (rhbz#1423053)

* Thu Feb 09 2017 Igor Gnatenko <ignatenko@redhat.com> - 1.3-1
- Update to 1.3

* Sun Jan 22 2017 Fabian Affolter <mail@fabian-affolter.ch> - 1.2-1
- Update to new upstream version 1.2
- Add new requirement
- Add real description

* Sun Jan 01 2017 Igor Gnatenko <i.gnatenko.brain@gmail.com> - 1.0.5-3
- Add missing dependency on async-timeout (RHBZ #1391287)

* Mon Dec 19 2016 Miro Hrončok <mhroncok@redhat.com> - 1.0.5-2
- Rebuild for Python 3.6

* Mon Oct 31 2016 Fabian Affolter <mail@fabian-affolter.ch> - 1.0.5-1
- Update to new upstream version 1.0.5

* Tue Aug 30 2016 Fabian Affolter <mail@fabian-affolter.ch> - 0.22.5-1
- Update to new upstream version 0.22.5

* Wed Aug 10 2016 Igor Gnatenko <ignatenko@redhat.com> - 0.21.6-4
- Move requires under real subpackage

* Tue Jul 19 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.21.6-3
- https://fedoraproject.org/wiki/Changes/Automatic_Provides_for_Python_RPM_Packages

* Thu Jun 23 2016 Igor Gnatenko <ignatenko@redhat.com> - 0.21.6-2
- Add missing Requires: python3-multidict (RHBZ #1349576)

* Thu May 12 2016 Igor Gnatenko <ignatenko@redhat.com> - 0.21.6-1
- Update to 0.21.6

* Tue Mar 22 2016 Fabian Affolter <mail@fabian-affolter.ch> - 0.21.5-1
- Update to new upstream version 0.21.5

* Sat Mar 05 2016 Fabian Affolter <mail@fabian-affolter.ch> - 0.21.2-1
- Update to new upstream version 0.21.2

* Sun Feb 14 2016 Fabian Affolter <mail@fabian-affolter.ch> - 0.21.1-1
- Add requirements (rhbz#1300186)
- Update to new upstream version 0.21.1

* Thu Feb 04 2016 Fabian Affolter <mail@fabian-affolter.ch> - 0.21.0-1
- Update to new upstream version 0.21.0

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 0.19.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Fri Nov 27 2015 Fabian Affolter <mail@fabian-affolter.ch> - 0.19.0-1
- Update py3
- Update to new upstream version 0.19.0

* Tue Nov 10 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.17.4-2
- Rebuilt for https://fedoraproject.org/wiki/Changes/python3.5

* Fri Oct 16 2015 Fabian Affolter <mail@fabian-affolter.ch> - 0.17.4-1
- Update to new upstream version 0.17.4

* Sat Aug 01 2015 Fabian Affolter <mail@fabian-affolter.ch> - 0.16.6-2
- Fix license

* Sat Aug 01 2015 Fabian Affolter <mail@fabian-affolter.ch> - 0.16.6-1
- Update to lastest upstream release 0.16.6 (rhbz#1231670)

* Thu Jun 18 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.16.5-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Mon Jun 15 2015 Fabian Affolter <mail@fabian-affolter.ch> - 0.16.5-1
- Update to lastest upstream release 0.16.5 (rhbz#1231670)

* Wed Nov 26 2014 Fabian Affolter <mail@fabian-affolter.ch> - 0.10.2-1
- Update to lastest upstream release 0.10.2

* Wed Oct 08 2014 Fabian Affolter <mail@fabian-affolter.ch> - 0.9.1-2
- Build only a py3 package

* Wed Feb 26 2014 Fabian Affolter <mail@fabian-affolter.ch> - 0.9.1-1
- Initial package for Fedora
