#!/bin/sh

# go to the directory that contains rebase_dlls.sh (i.e. devide/installer)
cd `dirname $0`

# and now use rebase.exe to rebase all the DLLs for faster loading,
# improved memory use and better sharing of DLLs
# see:
# http://www.codeproject.com/dll/RebaseDll.asp
# http://msdn.microsoft.com/library/default.asp?url=/library/en-us/tools/tools/rebase.asp
# http://www.ddj.com/dept/windows/184416922
# http://discuss.fogcreek.com/joelonsoftware3/default.asp?cmd=show&ixPost=97146&ixReplies=7
# http://forums.amd.com/index.php?showtopic=42055
# http://blogs.msdn.com/larryosterman/archive/2004/07/06/174516.aspx
find distdevide -name "*.dll" > dll_list
find distdevide -name "*.pyd" >> dll_list
rebase -b 0x60000000 -e 0x1000000 @dll_list -v
cd ..

