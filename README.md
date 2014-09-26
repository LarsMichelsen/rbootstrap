# rboostrap - Install RPM based Linux into Chroot Jails

rbootstrap is a tool for setting up RPM based Linux distributions in chroot
jails. The goal of the project is to have a tool like debootstrap for Debian and
Ubuntu for RPM based distributions like CentOS, RedHat, OpenSuSE, SLES and so on.

I started development of rbootstrap to create a lighweight tool which offers a
fast forward way to create installations of the mentioned Linux distributions
without the need to set-up a full blown virtualisation environment.

In my case I needed it to create my own small build service for compiling a
software for different Linux distributions with different architectures. Based
on experiences from other projects I knew that full or para virtualized
environments were too much overhead for my needs. After setting up the build
service for Debian and Ubuntu I started searching for working lightweight
solutions for OpenSUSE, CentOS etc., but I was unable to find up-to-date and
usable ones. So I decided to start this small project.

Hope it is usable for someone out there. Let me know!

## Usage

The common use case is to call rbootstrap once for setting up a chroot jail
below a path of your choice.

For example, to create a jail for CentOS 6.0 in the directory
`/var/lib/centos_6.0_jail` on my Ubuntu system, I used the following command:

```
> sudo rbootstrap centos_6.0 /var/lib/centos_6.0_jail
+- Initializing jail -----------------------------------------------------------
+- Creating device nodes -------------------------------------------------------
+- Mounting needed filesystems -------------------------------------------------
+- Reading repository meta information -----------------------------------------
+- Resolving package dependencies ----------------------------------------------
+- Loading repositories GPG key ------------------------------------------------
+- Loading packages ------------------------------------------------------------
+- Unpacking packages to create initial system ---------------------------------
+- Installing base packages ----------------------------------------------------
(...)
+- Cleaning up jail mounts and processes ---------------------------------------
```

After starting the command, rbootstrap does its work and, when no error happend,
leaves the prepared jail in `/var/lib/centos_6.0_jail`. You can now use it
for whatever you like. The most simple task would now be to change into the
jail and, for example, install additional needed packages.

```
> sudo chroot /var/lib/centos_6.0_jail
> yum install vim
(...)
```

To have a more complete working environment, you might need to perform some
other actions before changing into the jail, for example mount the /proc and
/sys filesystems. Maybe you also like to set a custom prompt (`PS1`) which
might prevent you from accidental command execution within or outer the jail.

*Please be aware:* When you have mounted filesystems to the jail and try to
remove it e.g. with `rm -rf`, you might delete contents of these filesystems
by accident. So always ensure that you have unmounted all filesystems from
a jail before trying to delete the jail.

Take a look at the output of `rbootstrap --help` for details about how to
call rbootstrap and which options are available.

## Prerequisites

rbootstrap is written in Python. This is the major requirement for make this
tool work. It has been developed on Ubuntu 14.04 with Python 2.7, but it aims
to work with Python down till 2.4. If you experience any problems with older
Python versions, please report it!

This tools makes use of several system utilities, which need to be available
to make it work. These are at the moment:

* chroot
* mount / umount
* rpm2cpio
* cpio

I am trying to keep the dependencies as small as possible. Please let me know
when you got easy solutions to remove one of the dependencies mentioned above.

## Supported Linux Distributions for jailing

At the moment there is support to install the following distributions in a chroot:

* OpenSUSE 13.1
* CentOS 6.0 - 7.0
* Fedora 18 - 20

This list might not be always up-to-date, please take a look at the files
in the `distros` directory to get the real list of supported ones.

Maybe you can add one or two missing distributions? Would be appreciated!

## Reporting Bugs, Feature Requests

I decided to use GitHub for managing project related communication, you
can find the project at (https://github.com/LaMi-/rbootstrap).

## Licensing

All outcome of the project is licensed under the terms of the GNU GPL v2.
Take a look at the LICENSE file for details.
