# rboostrap - Install RPM based Linux into Chroot Jails

rbootstrap is a  tool for setting up RPM based Linux distributions in chroot
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

Hope it is usable for someone out there.

## Reporting Bugs, Feature Requests

I decided to use GitHub for managing project related communication, you
can find the project at (https://github.com/LaMi-/rbootstrap).
