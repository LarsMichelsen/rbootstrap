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

FIXME

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
* FIXME ...working on more...

This list might not be always up-to-date, please take a look at the files
in the `distros` directory to get the real list of supported ones.

Maybe you can add one or two missing distributions? Would be appreciated!

## Reporting Bugs, Feature Requests

I decided to use GitHub for managing project related communication, you
can find the project at (https://github.com/LaMi-/rbootstrap).

## Licensing

All outcome of the project is licensed under the terms of the GNU GPL v2.
Take a look at the LICENSE file for details.
