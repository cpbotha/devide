# Error at startup: ImportError: /usr/lib64/libstdc++.so.6: version `GLIBCXX\_3.4.11' not found (required by /home/cbotha/devide-re-v12.2.7-lin64/wx/lib/libwx\_baseu-2.8.so.0) #

This means your libstdc++.so.6 is quite old, perhaps even as old as that shipped by SLED 11. Brrr...

To fix, download my [libstdc++.so.6 (64bit}](http://graphics.tudelft.nl/~cpbotha/files/devide/lin64/support/libstdc++.so.6) and save it to your devide-dir/wx/lib. You should now have flawless startups, like a boss.

# Error at startup: ImportError: libjpeg.so.62: cannot open shared object file: No such file or directory #

By default, Ubuntu 12.04 installs with a newer version of libjpeg. Fix this by doing the following at the shell prompt:

```
sudo apt-get install libjpeg62
```

... and then trying again.

# Error at startup: ERROR:root:code for hash md5 was not found #

The python 2.7.2 that is part of DeVIDE was built with and requires the openssl library. If you see this error, it means that it can't find openssl.

On Ubuntu 11.10 for example, you can install openssl as follows:
```
sudo apt-get install libssl0.9.8
```

## more detail ##
You can do:
```
ldd devide/python/lib/python2.7/lib-dynload/_hashlib.so
```
to see what openssl / libssl libraries exactly Python requires.

# How can I squeeze a bit more memory out of Win32? #

On a normally configured Windows system, you'll see that as soon as DeVIDE allocates more than about 1G in total, the system will crash.

Using a 64bit version of DeVIDE on a 64bit OS is the best solution, but if you really have to do this in Win32, please try the following entry from the VTK FAQ: [How can a user process access more than 2 GB of ram in 32-bit Windows?](http://www.vtk.org/Wiki/VTK_FAQ#How_can_a_user_process_access_more_than_2_GB_of_ram_in_32-bit_Windows.3F)

You only have to apply point 1. and NOT point 2.

_At the moment I'm building a test case for this.  Will report back with details soon._

# Loading a network with a CodeRunner fails #

The source code that you have entered in the CodeRunner can confuse the network parser, thus resulting in failure to load the network.

You can edit the DVN file with a text editor and fix or remove the offending CodeRunner source.  Common problems you could check for include:
  * The occurrence of '%(' in your code.  If you're doing string substitution, remember to add a space between the '%' and the '('.