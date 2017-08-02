Name: dawbrn
Version: 1.0.0
Release: 1%{?dist}
Summary: Documentation Autobuilds Would Be Really Nice
License: ASL 2.0
BuildArch: noarch
Url: https://github.com/ASzc/dawbrn
Source0: https://github.com/ASzc/dawbrn/archive/dawbrn-%{version}.tar.gz
Requires: rh-git29, rh-python35
BuildRequires: rh-python35

# Turn off brp-python-bytecompile
%global __os_install_post %(echo '%{__os_install_post}' | sed -e 's!/usr/lib[^[:space:]]*/brp-python-bytecompile!!g')

%description
Daemon for automatic documentation build and deployment

%prep
%setup -q -n dawbrn-dawbrn-%{version}

%build

%install
mkdir -p %{buildroot}%{_usr}/lib/dawbrn/
cp -r dawbrn %{buildroot}%{_usr}/lib/dawbrn/
# Manually invoke brp-python-bytecompile
scl enable rh-python35 -- %{py_byte_compile} python %{buildroot}%{_usr}/lib/dawbrn/dawbrn

cd packaging/install
install -Dm644 usr/lib/systemd/system/dawbrn.service %{buildroot}%{_usr}/lib/systemd/system/dawbrn.service
install -Dm440 etc/sudoers.d/10-dawbrn %{buildroot}%{_sysconfdir}/sudoers.d/10-dawbrn
install -Dm600 etc/sysconfig/dawbrn %{buildroot}%{_sysconfdir}/sysconfig/dawbrn
install -Dm755 usr/bin/dawbrn_dockerbuild %{buildroot}%{_bindir}/dawbrn_dockerbuild

%clean
rm -rf $RPM_BUILD_ROOT

%pre
getent group dawbrn > /dev/null || /usr/sbin/groupadd -r dawbrn
getent passwd dawbrn > /dev/null || /usr/sbin/useradd -r -g dawbrn \
       -d %{_localstatedir}/lib/dawbrn -s /sbin/nologin dawbrn
:

%files
%defattr(-,root,root)
%doc README.md LICENSE
%{_usr}/lib/dawbrn/*
%{_usr}/lib/systemd/system/dawbrn.service
%{_sysconfdir}/sudoers.d/10-dawbrn
%config(noreplace) %{_sysconfdir}/sysconfig/dawbrn
%{_bindir}/dawbrn_dockerbuiild
%dir %attr(-,dawbrn,dawbrn) %{_localstatedir}/lib/dawbrn

%changelog
* Wed Aug 02 2017 Alex Szczuczko <aszczucz@redhat.com> - 1.0.0-1
- Initial package
